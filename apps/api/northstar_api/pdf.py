"""Localized, paginated executive and detailed credit-memo PDFs."""

from __future__ import annotations

from decimal import Decimal
from io import BytesIO
from pathlib import Path
from xml.sax.saxutils import escape

from northstar_credit_app.models import AnalysisResult, MoneyValue
from reportlab.lib import colors  # type: ignore[import-untyped]
from reportlab.lib.enums import TA_LEFT  # type: ignore[import-untyped]
from reportlab.lib.pagesizes import letter  # type: ignore[import-untyped]
from reportlab.lib.styles import (  # type: ignore[import-untyped]
    ParagraphStyle,
    getSampleStyleSheet,
)
from reportlab.lib.units import inch  # type: ignore[import-untyped]
from reportlab.pdfbase import pdfmetrics  # type: ignore[import-untyped]
from reportlab.pdfbase.ttfonts import TTFont  # type: ignore[import-untyped]
from reportlab.platypus import (  # type: ignore[import-untyped]
    CondPageBreak,
    KeepTogether,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

INK = colors.HexColor("#13243A")
NAVY = colors.HexColor("#0D1D30")
COPPER = colors.HexColor("#9A4F2C")
MUTED = colors.HexColor("#627083")
LINE = colors.HexColor("#D8DEE6")
WASH = colors.HexColor("#F2F5F7")


def _money(value: MoneyValue) -> str:
    amount = Decimal(value.amount_minor) / (Decimal(10) ** value.minor_unit_exponent)
    return f"{value.currency} {amount:,.2f}"


def _zh_outcome(value: str) -> str:
    return {
        "Approve": "核准",
        "Approve with conditions": "附條件核准",
        "Reduce requested amount": "降低申請額度",
        "Refer to credit committee": "提交信審會",
        "Decline": "婉拒",
    }.get(value, value)


def _zh_condition(value: str) -> str:
    return {
        "Maximum total leverage tested quarterly with threshold set from policy and forecast headroom.": "最高總槓桿按季檢驗，門檻依政策及預測餘裕設定。",
        "Minimum DSCR tested quarterly with cure or waiver subject to lender approval.": "最低 DSCR 按季檢驗；補救或豁免須經貸方核准。",
        "Quarterly financial reporting within 45 days.": "每季財務報告應於 45 日內提交。",
        "Monthly liquidity reporting until downside headroom is restored.": "每月提交流動性報告，直到下行情境餘裕恢復。",
        "Perfect and maintain the proposed collateral security interest.": "完成並持續維持擬議擔保權益。",
    }.get(value, "依 API 核准條件執行並保留覆核證據。")


def _zh_status(value: str) -> str:
    return {
        "available": "可使用",
        "blocked": "已阻擋",
        "legacy_snapshot": "舊版單期快照",
        "strong": "強",
        "adequate": "良好",
        "moderate": "中等",
        "weak": "偏弱",
        "severe": "嚴重不足",
        "high": "高",
        "limited": "有限",
        "low": "低",
        "term_loan": "定期貸款",
        "revolver": "循環信用額度",
        "asset_based": "資產基礎融資",
    }.get(value, value)


def _zh_debt_source(value: str) -> str:
    return {
        "balance_sheet_aggregate": "資產負債表彙總",
        "instrument_schedule": "逐筆債務排程",
        "partial_schedule_with_residual": "部分排程（含殘餘）",
        "blocked_mismatch": "調節不符（已阻擋）",
    }.get(value, "未知債務來源")


ZH_TITLES = {
    "executive_recommendation": "執行建議",
    "borrower_overview": "借款人概況",
    "ownership_and_management": "所有權與管理",
    "business_model": "商業模式",
    "industry_risk": "產業風險",
    "loan_request": "貸款申請",
    "facility_structure": "授信結構",
    "loan_purpose": "貸款用途",
    "sources_and_uses": "資金來源與用途",
    "primary_repayment_source": "主要還款來源",
    "secondary_repayment_source": "次要還款來源",
    "historical_financial_performance": "歷史財務表現",
    "financial_adjustments": "財務調整",
    "capital_structure": "資本結構",
    "debt_maturity_schedule": "債務到期表",
    "key_ratios": "關鍵比率",
    "obligor_grade": "債務人評等",
    "facility_protection": "設施保障",
    "debt_capacity": "債務容量",
    "base_case": "基準情境",
    "downside_case": "下行情境",
    "severe_case": "嚴重壓力情境",
    "reverse_stress": "反向壓力測試",
    "collateral_or_borrowing_base": "擔保品或借款基礎",
    "indicative_pricing": "示意定價",
    "covenants": "財務契約",
    "policy_exceptions": "政策例外",
    "conditions_precedent": "先決條件",
    "monitoring": "監控",
    "data_limitations": "資料限制",
    "analyst_sign_off": "分析師簽核",
    "reviewer_sign_off": "覆核人簽核",
}


def _zh_sections(result: AnalysisResult) -> dict[str, list[str]]:
    base = next(item for item in result.scenarios if item.name == "base")
    downside = next(item for item in result.scenarios if item.name == "downside")
    severe = next(item for item in result.scenarios if item.name == "severe")
    reconciliation = result.debt_reconciliation
    assert reconciliation is not None
    mechanics = result.facility_mechanics
    assert mechanics is not None
    borrowing = (
        _money(result.borrowing_base.borrowing_base)
        if result.borrowing_base.borrowing_base is not None
        else "不適用或因缺少輸入而阻擋"
    )
    return {
        "executive_recommendation": [
            f"建議：{_zh_outcome(result.decision.outcome)}；申請額 {_money(result.capacity.requested)}；可支援額度 {_money(result.capacity.recommended)}；債務人評等 {result.scorecard.grade or '已阻擋'}。"
        ],
        "borrower_overview": [
            f"借款人：{result.case.borrower.legal_name}。業務、產業與所在地資料已保留於合成案件輸入。"
        ],
        "ownership_and_management": [
            "合成案件未提供所有權明細；管理評估以營運風險證據紀錄為基礎。"
        ],
        "business_model": ["合成案件已記錄業務模式說明；使用前仍須以獨立文件驗證。"],
        "industry_risk": [
            f"已記錄 {len(result.case.business_risk.risks)} 項主要風險及 {len(result.case.business_risk.strengths)} 項主要優勢。"
        ],
        "loan_request": [f"借款人申請 {_money(result.case.request.amount)}。"],
        "facility_structure": [
            f"統一授信機制：{_zh_status(mechanics.facility_type)}；攤還類型 {_zh_status(mechanics.amortization_type)}；狀態 {_zh_status(mechanics.status)}；到期 {mechanics.maturity_years} 年；攤還 {mechanics.amortization_years or mechanics.maturity_years} 年。",
            *mechanics.blocking_issues,
        ],
        "loan_purpose": [
            "貸款用途已記錄於合成案件輸入；實際使用前須取得並驗證支持文件。"
        ],
        "sources_and_uses": [
            f"擬議貸方資金來源 {_money(result.case.request.amount)}；用途依借款人輸入。未提供其他資金來源或用途。"
        ],
        "primary_repayment_source": [
            "營運現金流"
            if result.decision.primary_repayment_source == "Operating cash flow"
            else "依案件輸入之主要還款來源。"
        ],
        "secondary_repayment_source": [
            "合格擔保品與企業價值支援；分析未假設可成功再融資。"
        ],
        "historical_financial_performance": [
            f"營收 {_money(result.case.financials.revenue)}；報告 EBITDA {_money(result.adjustments.reported_ebitda)}；調整後 EBITDA {_money(result.adjustments.adjusted_ebitda)}。",
            f"LTM 狀態：{_zh_status(result.financial_spreading.ltm_status)}；來源快照 {result.financial_spreading.resolved_snapshot.snapshot_hash[:16] if result.financial_spreading.resolved_snapshot else '無'}。",
        ],
        "financial_adjustments": [
            f"已核准調整 {_money(result.adjustments.approved_adjustment)}；正向調整占比 {Decimal(result.adjustments.positive_adjustment_pct) * 100:.2f}%。"
        ],
        "capital_structure": [
            f"非受限現金 {_money(result.case.financials.unrestricted_cash)}；權益 {_money(result.case.financials.equity)}。",
            f"債務調節：{_zh_status(reconciliation.status)}；選定來源 {_zh_debt_source(reconciliation.selected_source)}；{reconciliation.coverage_basis_notice}",
        ],
        "debt_maturity_schedule": [
            f"已提供 {len(result.case.debt_instruments)} 項逐筆債務工具。"
            if result.case.debt_instruments
            else "未提供逐筆債務到期表。"
        ]
        + (
            [
                f"未排程殘餘債務 {_money(reconciliation.residual_debt)}；到期狀態 {reconciliation.residual_maturity_status}。"
            ]
            if reconciliation.residual_debt is not None
            else []
        ),
        "key_ratios": [
            f"總槓桿 {result.metrics['gross_leverage'].value or '不具意義'} 倍；利息保障 {result.metrics['interest_coverage'].value or '不具意義'} 倍；DSCR {result.metrics['dscr'].value or '不具意義'} 倍。"
        ],
        "obligor_grade": [
            f"分數 {result.scorecard.score or '已阻擋'}；評等 {result.scorecard.grade or '已阻擋'}；資料信心 {result.scorecard.confidence_score}/100。設施保障不會改變債務人評等。"
        ],
        "facility_protection": [
            f"設施保障分數 {result.facility_protection.score}；類別 {_zh_status(result.facility_protection.category)}；預期回收類別 {_zh_status(result.facility_protection.expected_recovery_category)}；申請／建議覆蓋率 {result.facility_protection.coverage_requested}x／{result.facility_protection.coverage_recommended}x。"
        ],
        "debt_capacity": [
            f"容量狀態 {result.capacity.status}；建議狀態 {result.capacity.recommendation_state}；申請 {_money(result.capacity.requested)}；建議 {_money(result.capacity.recommended)}；約束條件數 {len(result.capacity.binding_constraints)}。"
        ],
        "base_case": [
            f"首次財務契約違約年度：{base.first_breach_year or '三年內無'}。"
        ],
        "downside_case": [
            f"首次違約年度：{downside.first_breach_year or '三年內無'}；流動性耗盡年度：{downside.liquidity_exhaustion_year or '三年內無'}。"
        ],
        "severe_case": [
            f"首次違約年度：{severe.first_breach_year or '三年內無'}；流動性耗盡年度：{severe.liquidity_exhaustion_year or '三年內無'}。"
        ],
        "reverse_stress": [
            f"六個求解器中有 {sum(item.converged for item in result.reverse_stress.solvers)} 個已收斂；未收斂結果不顯示數值。",
            *[
                f"求解器 {index + 1}：{'已收斂' if item.converged else '未收斂'}；迭代 {item.iterations} 次；殘差 {item.residual or '無'}。"
                for index, item in enumerate(result.reverse_stress.solvers)
            ],
        ],
        "collateral_or_borrowing_base": [
            f"借款基礎：{borrowing}。預支率依版本化示意政策。"
        ],
        "indicative_pricing": [
            (
                f"參考基準利率 {Decimal(result.pricing.reference_base_rate) * 100:.2f}%；"
                f"風險利差 {result.pricing.risk_grade_spread_bps} bps；"
                + (
                    f"示意全包利率 {Decimal(result.pricing.indicative_all_in_rate) * 100:.2f}%。"
                    if result.pricing.indicative_all_in_rate is not None
                    else "示意全包利率：已阻擋，待有效債務人評等與財務期間來源。"
                )
            ),
            "僅供教育用途，不代表即時市場報價、銀行承諾或授信建議。",
        ],
        "covenants": [
            f"共產生 {len(result.covenants)} 項維持性、發生性或報告型財務契約。"
        ],
        "policy_exceptions": [
            f"共有 {len(result.decision.policy_exceptions)} 項政策警示需要授權處理。"
            if result.decision.policy_exceptions
            else "未識別政策例外。"
        ],
        "conditions_precedent": [
            _zh_condition(item) for item in result.decision.conditions
        ],
        "monitoring": [
            "每季財務報表、年度財務契約遵循證明，以及重大不利事件即時通知。"
        ],
        "data_limitations": [
            "本案件使用合成資料，未執行真實文件、法規、制裁、詐欺或法律盡職調查。僅供教育用途。",
            "目前財務展開仍有資料完整性或調節限制；詳細狀態以 API 輸出為準。",
        ],
        "analyst_sign_off": [
            "分析人員：____________________",
            f"資料基準日：{result.case.data_as_of}",
        ],
        "reviewer_sign_off": [
            "覆核人員：____________________",
            f"模型 {result.engine_version}；政策 {result.policy_version}。",
        ],
    }


def _styles(zh: bool) -> dict[str, ParagraphStyle]:
    if zh:
        try:
            pdfmetrics.getFont("NotoSansTC")
        except KeyError:
            font_path = (
                Path(__file__).parent / "assets" / "fonts" / "NotoSansTC-Regular.ttf"
            )
            pdfmetrics.registerFont(TTFont("NotoSansTC", str(font_path)))
        body_font = title_font = "NotoSansTC"
    else:
        body_font, title_font = "Helvetica", "Times-Roman"
    base = getSampleStyleSheet()
    return {
        "title": ParagraphStyle(
            "MemoTitle",
            parent=base["Title"],
            fontName=title_font,
            fontSize=20,
            leading=24,
            textColor=NAVY,
            alignment=TA_LEFT,
            spaceAfter=8,
        ),
        "borrower": ParagraphStyle(
            "Borrower",
            parent=base["Heading2"],
            fontName=title_font,
            fontSize=14,
            leading=18,
            textColor=INK,
            spaceAfter=12,
            wordWrap="CJK" if zh else None,
        ),
        "heading": ParagraphStyle(
            "Section",
            parent=base["Heading2"],
            fontName=title_font,
            fontSize=11,
            leading=14,
            textColor=COPPER,
            spaceBefore=8,
            spaceAfter=4,
            keepWithNext=True,
        ),
        "body": ParagraphStyle(
            "MemoBody",
            parent=base["BodyText"],
            fontName=body_font,
            fontSize=8.2,
            leading=11.2,
            textColor=INK,
            spaceAfter=4,
            wordWrap="CJK" if zh else None,
        ),
        "small": ParagraphStyle(
            "Small",
            parent=base["BodyText"],
            fontName=body_font,
            fontSize=6.8,
            leading=9,
            textColor=MUTED,
            wordWrap="CJK" if zh else None,
        ),
        "decision": ParagraphStyle(
            "Decision",
            parent=base["Heading1"],
            fontName=title_font,
            fontSize=16,
            leading=19,
            textColor=colors.white,
            spaceAfter=0,
            wordWrap="CJK" if zh else None,
        ),
    }


def _paragraph(text: str, style: ParagraphStyle) -> Paragraph:
    return Paragraph(escape(str(text)).replace("\n", "<br/>"), style)


def _footer(canvas: object, doc: SimpleDocTemplate, *, zh: bool, font: str) -> None:
    canvas.saveState()  # type: ignore[attr-defined]
    canvas.setStrokeColor(LINE)  # type: ignore[attr-defined]
    canvas.line(doc.leftMargin, 0.45 * inch, letter[0] - doc.rightMargin, 0.45 * inch)  # type: ignore[attr-defined]
    canvas.setFont(font, 6.5)  # type: ignore[attr-defined]
    canvas.setFillColor(MUTED)  # type: ignore[attr-defined]
    label = f"第 {doc.page} 頁" if zh else f"Page {doc.page}"
    canvas.drawRightString(letter[0] - doc.rightMargin, 0.28 * inch, label)  # type: ignore[attr-defined]
    canvas.drawString(doc.leftMargin, 0.28 * inch, "Northstar Credit Platform")  # type: ignore[attr-defined]
    canvas.restoreState()  # type: ignore[attr-defined]


def _metric_table(
    result: AnalysisResult, styles: dict[str, ParagraphStyle], zh: bool
) -> Table:
    rows = [
        [
            "申請額" if zh else "Requested",
            _money(result.capacity.requested),
            "建議額度" if zh else "Recommended",
            _money(result.capacity.recommended),
        ],
        [
            "債務人評等" if zh else "Obligor grade",
            str(result.scorecard.grade or ("已阻擋" if zh else "Blocked")),
            "設施保障" if zh else "Facility protection",
            f"{result.facility_protection.score} / 100",
        ],
        [
            "總槓桿" if zh else "Gross leverage",
            f"{result.metrics['gross_leverage'].value or ('不具意義' if zh else 'N/M')}x",
            "DSCR",
            f"{result.metrics['dscr'].value or ('不具意義' if zh else 'N/M')}x",
        ],
    ]
    table = Table(
        [[_paragraph(value, styles["small"]) for value in row] for row in rows],
        colWidths=[1.05 * inch, 1.62 * inch, 1.05 * inch, 1.62 * inch],
    )
    table.setStyle(
        TableStyle(
            [
                ("GRID", (0, 0), (-1, -1), 0.35, LINE),
                ("BACKGROUND", (0, 0), (-1, -1), WASH),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 7),
                ("RIGHTPADDING", (0, 0), (-1, -1), 7),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    return table


def render_memo_pdf(
    result: AnalysisResult, *, locale: str = "en", detailed: bool = False
) -> bytes:
    zh = locale.lower().startswith("zh")
    mechanics = result.facility_mechanics
    assert mechanics is not None
    styles = _styles(zh)
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        leftMargin=0.62 * inch,
        rightMargin=0.62 * inch,
        topMargin=0.55 * inch,
        bottomMargin=0.6 * inch,
        title=("北極星授信備忘錄" if zh else "Northstar Credit Memorandum"),
        author="Northstar Credit Platform",
        subject="Synthetic educational corporate-credit analysis",
        pdfVersion=(1, 4),
    )
    story: list[object] = [
        _paragraph(
            "北極星授信備忘錄" if zh else "NORTHSTAR CREDIT MEMORANDUM", styles["title"]
        ),
        _paragraph(result.case.borrower.legal_name, styles["borrower"]),
    ]
    decision_text = (
        _zh_outcome(result.decision.outcome) if zh else result.decision.outcome
    )
    decision_box = Table(
        [[_paragraph(decision_text, styles["decision"])]], colWidths=[7.25 * inch]
    )
    decision_box.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), NAVY),
                ("LEFTPADDING", (0, 0), (-1, -1), 14),
                ("RIGHTPADDING", (0, 0), (-1, -1), 14),
                ("TOPPADDING", (0, 0), (-1, -1), 11),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 11),
            ]
        )
    )
    story.extend(
        [
            decision_box,
            Spacer(1, 0.14 * inch),
            _metric_table(result, styles, zh),
            Spacer(1, 0.12 * inch),
        ]
    )

    if not detailed:
        strengths = (
            "；".join(result.case.business_risk.strengths[:3])
            if zh
            else "; ".join(result.case.business_risk.strengths[:3])
        )
        risks = (
            "；".join(result.case.business_risk.risks[:3])
            if zh
            else "; ".join(result.case.business_risk.risks[:3])
        )
        compact = [
            (
                "執行建議" if zh else "Executive recommendation",
                f"{_zh_outcome(result.decision.outcome) if zh else result.decision.outcome}. {('建議額度' if zh else 'Recommended exposure')}: {_money(result.capacity.recommended)}.",
            ),
            (
                "授信機制" if zh else "Facility mechanics",
                (
                    f"統一授信機制：{_zh_status(mechanics.facility_type)}；攤還類型 {_zh_status(mechanics.amortization_type)}；狀態 {_zh_status(mechanics.status)}。"
                    if zh
                    else f"Resolved mechanics: {mechanics.facility_type}; {mechanics.amortization_type}; status {mechanics.status}."
                ),
            ),
            (
                "主要優勢" if zh else "Key strengths",
                strengths or ("未提供。" if zh else "Not supplied."),
            ),
            (
                "主要風險" if zh else "Key risks",
                risks or ("未提供。" if zh else "Not supplied."),
            ),
            (
                "核准條件" if zh else "Conditions",
                " ".join(_zh_condition(item) for item in result.decision.conditions)
                if zh
                else " ".join(result.decision.conditions),
            ),
            (
                "限制" if zh else "Limitations",
                "合成示範資料；僅供教育用途，不構成授信、投資、會計或法律建議。"
                if zh
                else "Synthetic demonstration data. Educational and illustrative only; not lending, investment, accounting, or legal advice.",
            ),
        ]
        for title, body in compact:
            story.extend(
                [_paragraph(title, styles["heading"]), _paragraph(body, styles["body"])]
            )
        story.append(Spacer(1, 0.05 * inch))
        story.append(
            _paragraph(
                f"{('資料基準日' if zh else 'Data as of')}: {result.case.data_as_of} | {('模型' if zh else 'Model')}: {result.engine_version} | {('政策' if zh else 'Policy')}: {result.policy_version}",
                styles["small"],
            )
        )
    else:
        story.extend(
            [
                PageBreak(),
                _paragraph(
                    "詳細授信備忘錄" if zh else "DETAILED CREDIT MEMORANDUM",
                    styles["title"],
                ),
                _paragraph(
                    f"{('資料基準日' if zh else 'Data as of')}: {result.case.data_as_of}\n{('計算時間' if zh else 'Calculated')}: {result.calculated_at}\n{('模型' if zh else 'Model')}: {result.engine_version}\n{('政策' if zh else 'Policy')}: {result.policy_version} / {result.policy_hash[:12]}\n{('輸入雜湊' if zh else 'Input hash')}: {result.input_hash}",
                    styles["small"],
                ),
                Spacer(1, 0.14 * inch),
            ]
        )
        sections = _zh_sections(result) if zh else result.memo_sections
        for index, (key, paragraphs) in enumerate(sections.items(), start=1):
            title = (
                ZH_TITLES.get(key, key.replace("_", " "))
                if zh
                else key.replace("_", " ").title()
            )
            story.append(CondPageBreak(0.65 * inch))
            block: list[object] = [
                _paragraph(f"{index:02d}. {title}", styles["heading"])
            ]
            for paragraph in paragraphs or ["未提供。" if zh else "Not supplied."]:
                block.append(_paragraph(paragraph, styles["body"]))
            story.append(KeepTogether(block[:2]))
            story.extend(block[2:])

    font = "NotoSansTC" if zh else "Helvetica"
    doc.build(
        story,
        onFirstPage=lambda canvas, built: _footer(canvas, built, zh=zh, font=font),
        onLaterPages=lambda canvas, built: _footer(canvas, built, zh=zh, font=font),
    )
    return buffer.getvalue()
