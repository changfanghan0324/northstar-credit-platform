"""Deterministic localized PDF writer for executive and detailed credit memos."""

from __future__ import annotations

from decimal import Decimal
from textwrap import wrap

from northstar_credit_app.models import AnalysisResult, MoneyValue


def _escape(text: str) -> str:
    return text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


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
    }.get(value, value)


def _zh_term(value: str) -> str:
    return {
        "term_loan": "定期貸款",
        "revolver": "循環信用額度",
        "asset_based": "資產基礎融資",
        "leverage": "槓桿容量",
        "dscr": "償債覆蓋容量",
        "collateral": "擔保品容量",
        "policy": "政策上限",
        "valid": "有效",
        "blocked": "已阻擋",
        "policy_not_applicable": "政策不適用",
        "pass": "通過",
        "warning": "警示",
        "hard_stop": "硬性停止",
        "not_applicable": "不適用",
        "quarterly": "每季",
        "monthly": "每月",
        "annual": "每年",
        "base": "基準情境",
        "downside": "下行情境",
        "severe": "嚴重壓力情境",
    }.get(value, value.replace("_", " "))


def _zh_policy_label(value: str) -> str:
    return {
        "Maximum total leverage": "最高總槓桿",
        "Minimum interest coverage": "最低利息保障倍數",
        "Minimum DSCR": "最低償債覆蓋倍數",
        "Maximum maturity": "最長到期年限",
        "Minimum liquidity months": "最低流動性月數",
        "Allowed currency": "允許幣別",
        "Maximum exposure": "最高曝險",
        "Maximum eligible grade": "最高可核准評等",
        "Minimum collateral coverage": "最低擔保覆蓋率",
        "Maximum EBITDA adjustment": "最高 EBITDA 調整幅度",
        "Minimum data confidence": "最低資料信心",
        "Allowed facility type": "允許額度類型",
    }.get(value, value)


def _localized_lines(
    result: AnalysisResult, *, locale: str, detailed: bool
) -> list[str]:
    zh = locale.lower().startswith("zh")
    downside = next(item for item in result.scenarios if item.name == "downside")
    leverage = result.metrics["gross_leverage"]
    dscr = result.metrics["dscr"]
    coverage = result.metrics["interest_coverage"]
    if zh:
        grade = (
            "未完成" if result.scorecard.grade is None else str(result.scorecard.grade)
        )
        grade_label = (
            "已阻擋，請補齊關鍵輸入"
            if result.scorecard.grade is None
            else result.scorecard.grade_label
        )
        repayment = (
            "營運現金流"
            if result.decision.primary_repayment_source == "Operating cash flow"
            else result.decision.primary_repayment_source
        )
        lines = [
            "北極星授信備忘錄",
            result.case.borrower.legal_name,
            f"授信決策：{_zh_outcome(result.decision.outcome)}",
            f"內部評等：{grade}（{grade_label}）",
            f"申請額：{_money(result.capacity.requested)}",
            f"建議額度：{_money(result.capacity.recommended)}",
            f"總槓桿：{leverage.value or '不具意義'} 倍",
            f"DSCR：{dscr.value or '不具意義'} 倍",
            f"利息保障倍數：{coverage.value or '不具意義'} 倍",
            f"下行情境首次違約年度：{downside.first_breach_year or '三年內無'}",
            f"主要還款來源：{repayment}",
            "",
            "主要優勢",
            *result.case.business_risk.strengths,
            "",
            "主要風險",
            *result.case.business_risk.risks,
            "",
            "建議條件與財務契約",
            *[_zh_condition(item) for item in result.decision.conditions],
            "",
            "限制",
            "合成示範資料，不代表真實資料品質評估。",
            "僅供教育與說明用途，不構成授信、投資、會計或法律建議。",
        ]
    else:
        lines = [
            "NORTHSTAR CREDIT MEMORANDUM",
            result.case.borrower.legal_name,
            f"Decision: {result.decision.outcome}",
            f"Internal grade: {result.scorecard.grade or 'Blocked'} ({result.scorecard.grade_label})",
            f"Requested: {_money(result.capacity.requested)}",
            f"Recommended: {_money(result.capacity.recommended)}",
            f"Gross leverage: {leverage.value or 'Not meaningful'}x",
            f"DSCR: {dscr.value or 'Not meaningful'}x",
            f"Interest coverage: {coverage.value or 'Not meaningful'}x",
            f"Downside first breach year: {downside.first_breach_year or 'none within three years'}",
            f"Primary repayment: {result.decision.primary_repayment_source}",
            "",
            "KEY STRENGTHS",
            *result.case.business_risk.strengths,
            "",
            "KEY RISKS",
            *result.case.business_risk.risks,
            "",
            "PROPOSED TERMS AND COVENANTS",
            *result.decision.conditions,
            "",
            "LIMITATIONS",
            "Synthetic demonstration — not a real data-quality assessment.",
            "Educational and illustrative only; not lending, investment, accounting, or legal advice.",
        ]
    if detailed:
        if zh:
            lines.extend(
                [
                    "",
                    "借款人概況",
                    result.case.borrower.description,
                    f"產業：{result.case.borrower.industry}",
                    f"總部：{result.case.borrower.headquarters}",
                    "",
                    "申請與結構",
                    f"用途：{result.case.request.purpose}",
                    f"額度類型：{_zh_term(result.decision.facility_type)}",
                    f"到期／攤還：{result.decision.maturity_years}／{result.decision.amortization_years} 年",
                    f"擔保：{result.decision.collateral}",
                    f"保證：{result.decision.guarantee}",
                    "",
                    "EBITDA 調整與財務基礎",
                    f"正向 EBITDA 調整：{_money(result.case.financials.positive_ebitda_adjustments)}",
                    f"負向 EBITDA 調整：{_money(result.case.financials.negative_ebitda_adjustments)}",
                    f"維持性資本支出：{_money(result.case.financials.maintenance_capex)}",
                    f"營運資金增加：{_money(result.case.financials.working_capital_increase)}",
                    "",
                    "既有債務明細",
                    *(
                        [
                            f"{item.name}：本金 {_money(item.principal)}，利率 {item.annual_rate}，"
                            f"攤還 {_money(item.scheduled_amortization)}，第 {item.maturity_year} 年到期"
                            for item in result.case.debt_instruments
                        ]
                        or ["未提供逐筆債務明細；信心分數已反映此限制。"]
                    ),
                    "",
                    "容量與政策",
                    f"約束條件：{'、'.join(_zh_term(item) for item in result.capacity.binding_constraints)}",
                    *[
                        f"{_zh_policy_label(check.label)}：{check.actual}／{check.threshold}（{_zh_term(check.status)}）"
                        for check in result.policy_checks
                    ],
                    "",
                    "壓力測試與財務契約",
                    f"反向壓力營收跌幅：{result.reverse_stress.dscr_minimum_revenue_decline}%",
                    f"求解結果：{'已收斂' if result.reverse_stress.converged else '未收斂'}，迭代 {result.reverse_stress.iterations} 次",
                    *[
                        f"{_zh_term(scenario.name)}第 {year.year} 年：期初債務 {_money(year.beginning_debt)}，"
                        f"期末債務 {_money(year.ending_debt)}，DSCR {year.dscr}，"
                        f"現金缺口 {_money(year.cash_shortfall)}"
                        for scenario in result.scenarios
                        for year in scenario.years
                    ],
                    *[
                        f"{item.name}：{item.actual}／{item.threshold}（{_zh_term(item.status)}，{_zh_term(item.frequency)}）"
                        for item in result.covenants
                    ],
                    "",
                    "監控與例外",
                    *(
                        result.decision.monitoring
                        or ["依核准條件與財務契約頻率持續監控。"]
                    ),
                    *(
                        [
                            f"政策例外：{item}"
                            for item in result.decision.policy_exceptions
                        ]
                        or ["政策例外：無。"]
                    ),
                    "",
                    "資料品質、限制與簽核",
                    f"資料信心：{result.scorecard.confidence_score}/100（{result.scorecard.confidence}）",
                    *result.scorecard.confidence_penalties,
                    "本備忘錄使用合成資料，未執行真實世界文件、法規、制裁、詐欺或法律盡職調查。",
                    "模型結果須由具授權的授信人員獨立覆核後方可使用。",
                    "分析人員：________________  日期：________________",
                    "核准人員：________________  日期：________________",
                ]
            )
        else:
            for heading, paragraphs in result.memo_sections.items():
                lines.extend(["", heading.replace("_", " ").upper(), *paragraphs])
        lines.extend(
            [
                "",
                f"Input hash: {result.input_hash}",
                f"Policy: {result.policy_version} / {result.policy_hash[:12]}",
                f"Model: {result.engine_version}",
            ]
        )
    return lines


def _text_stream(lines: list[str], *, zh: bool) -> bytes:
    commands = ["BT", "/F1 9 Tf", "46 754 Td", "11 TL"]
    for index, line in enumerate(lines):
        if index:
            commands.append("T*")
        if zh:
            commands.append(f"<{line.encode('utf-16-be').hex().upper()}> Tj")
        else:
            commands.append(f"({_escape(line)}) Tj")
    commands.append("ET")
    return "\n".join(commands).encode("cp1252", errors="replace")


def render_memo_pdf(
    result: AnalysisResult, *, locale: str = "en", detailed: bool = False
) -> bytes:
    zh = locale.lower().startswith("zh")
    source_lines = _localized_lines(result, locale=locale, detailed=detailed)
    lines: list[str] = []
    for line in source_lines:
        if not line:
            lines.append("")
            continue
        width = 48 if zh else 92
        lines.extend(wrap(line, width=width, break_long_words=True) or [""])
    chunks = [lines[index : index + 62] for index in range(0, len(lines), 62)]
    if not chunks:
        chunks = [[""]]

    page_numbers = list(range(3, 3 + len(chunks)))
    content_numbers = list(range(3 + len(chunks), 3 + (2 * len(chunks))))
    font_number = 3 + (2 * len(chunks))
    cid_font_number = font_number + 1
    font = (
        f"<< /Type /Font /Subtype /Type0 /BaseFont /MSung-Light /Encoding /UniCNS-UCS2-H /DescendantFonts [{cid_font_number} 0 R] >>".encode()
        if zh
        else b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>"
    )
    objects: list[bytes] = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        (
            f"<< /Type /Pages /Kids [{' '.join(f'{number} 0 R' for number in page_numbers)}] "
            f"/Count {len(page_numbers)} >>"
        ).encode(),
    ]
    for content_number in content_numbers:
        objects.append(
            (
                f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
                f"/Resources << /Font << /F1 {font_number} 0 R >> >> "
                f"/Contents {content_number} 0 R >>"
            ).encode()
        )
    for chunk in chunks:
        stream = _text_stream(chunk, zh=zh)
        objects.append(
            b"<< /Length "
            + str(len(stream)).encode()
            + b" >>\nstream\n"
            + stream
            + b"\nendstream"
        )
    objects.append(font)
    if zh:
        objects.append(
            b"<< /Type /Font /Subtype /CIDFontType0 /BaseFont /MSung-Light /CIDSystemInfo << /Registry (Adobe) /Ordering (CNS1) /Supplement 4 >> >>"
        )
    pdf = bytearray(b"%PDF-1.4\n")
    offsets = [0]
    for number, obj in enumerate(objects, start=1):
        offsets.append(len(pdf))
        pdf.extend(f"{number} 0 obj\n".encode())
        pdf.extend(obj)
        pdf.extend(b"\nendobj\n")
    xref = len(pdf)
    pdf.extend(f"xref\n0 {len(objects) + 1}\n".encode())
    pdf.extend(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        pdf.extend(f"{offset:010d} 00000 n \n".encode())
    pdf.extend(
        f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode()
    )
    return bytes(pdf)
