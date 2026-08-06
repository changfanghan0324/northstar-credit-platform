"use client";

import {
  ArrowLeft,
  Check,
  CircleAlert,
  Download,
  Gauge,
  Info,
  LoaderCircle,
  Menu,
  RefreshCw,
  Save,
  SlidersHorizontal,
  X,
} from "lucide-react";
import Link from "next/link";
import { useEffect, useMemo, useRef, useState } from "react";
import { Header } from "./Header";
import { api, downloadMemo, money } from "@/lib/api";
import { type Language, prefix } from "@/lib/i18n";
import { formatMoneyInput, parseMoneyInput } from "@/lib/money";
import type {
  Analysis,
  CaseEnvelope,
  CaseInput,
  Money,
  ScenarioInput,
  ScenarioYear,
} from "@/lib/types";
import { workspaceSections } from "@/lib/workspace";
import { FacilityProtectionPage } from "./workspace/FacilityProtectionPage";
import { FinancialSpreadingPanel } from "./workspace/FinancialSpreadingPanel";
import { GlossaryDrawer } from "./workspace/GlossaryDrawer";
import { FinancialSpreadEditor } from "./workspace/FinancialSpreadEditor";
import {
  AdjustmentLogEditor,
  BorrowingBaseEditor,
} from "./workspace/AdjustmentCollateralEditors";
import { AuditHistory } from "./workspace/AuditHistory";

const labels = {
  en: [
    "Overview",
    "Inputs",
    "Financials",
    "Debt capacity",
    "Facility protection",
    "Risk",
    "Stress & covenants",
    "Decision & terms",
    "Credit memo",
  ],
  "zh-TW": [
    "總覽",
    "輸入資料",
    "財務分析",
    "債務容量",
    "設施保障",
    "風險評等",
    "壓力測試與契約",
    "決策與條件",
    "授信備忘錄",
  ],
};
const questions = {
  en: [
    "What is the credit recommendation?",
    "What information is this analysis based on?",
    "How has the borrower performed and generated cash?",
    "How much additional debt is supportable?",
    "How well is the lender protected?",
    "Why did the borrower receive this grade?",
    "What breaks under stress?",
    "What should the lender approve and under what structure?",
    "What should the credit committee know?",
  ],
  "zh-TW": [
    "授信建議是什麼？",
    "這份分析使用了哪些資料？",
    "借款人的營運與現金產生能力如何？",
    "借款人可承擔多少新增債務？",
    "貸方獲得多少結構性保障？",
    "借款人為何得到此評等？",
    "壓力下哪些條件會失效？",
    "貸方應核准什麼額度與結構？",
    "信審會需要知道什麼？",
  ],
};
const fieldName: Record<string, [string, string]> = {
  revenue: ["Revenue", "營收"],
  prior_revenue: ["Prior revenue", "前期營收"],
  ebit: ["Operating profit (EBIT)", "營業利益（EBIT）"],
  depreciation_amortization: ["Depreciation and amortization", "折舊與攤銷"],
  positive_ebitda_adjustments: [
    "Positive EBITDA adjustments",
    "正向 EBITDA 調整",
  ],
  negative_ebitda_adjustments: [
    "Negative EBITDA adjustments",
    "負向 EBITDA 調整",
  ],
  cfo: ["Cash from operations", "營業現金流"],
  capex: ["Capital spending", "資本支出"],
  maintenance_capex: ["Maintenance capital spending", "維持性資本支出"],
  cash_taxes: ["Cash taxes", "現金稅負"],
  working_capital_increase: ["Working-capital investment", "營運資金增加"],
  cash_interest: ["Cash interest", "現金利息"],
  scheduled_principal: ["Scheduled principal", "預定本金償還"],
  short_term_borrowings: ["Short-term borrowings", "短期借款"],
  current_maturities: ["Current maturities", "一年內到期債務"],
  long_term_debt: ["Long-term debt", "長期債務"],
  finance_leases: ["Finance leases", "融資租賃"],
  unrestricted_cash: ["Unrestricted cash", "非受限現金"],
  current_assets: ["Current assets", "流動資產"],
  current_liabilities: ["Current liabilities", "流動負債"],
  accounts_receivable: ["Accounts receivable", "應收帳款"],
  inventory: ["Inventory", "存貨"],
  undrawn_revolver: ["Undrawn revolver", "未動用循環額度"],
  minimum_operating_cash: ["Minimum operating cash", "最低營運現金"],
  collateral_capacity: ["Eligible collateral support", "合格擔保品支援額"],
};
const scenarioFieldName: Record<string, [string, string]> = {
  revenue_growth: ["Revenue growth", "營收成長率"],
  subsequent_growth: ["Subsequent growth", "後續成長率"],
  ebitda_margin_change: ["EBITDA margin change", "EBITDA 利潤率變動"],
  rate_shock: ["Rate shock", "利率衝擊"],
  working_capital_pct_revenue: [
    "Working capital as % of revenue",
    "營運資金占營收比率",
  ],
  maintenance_capex_pct_revenue: [
    "Maintenance capex as % of revenue",
    "維持性資本支出占營收比率",
  ],
};
const metricName: Record<string, [string, string]> = {
  gross_leverage: ["Gross leverage", "總槓桿"],
  net_leverage: ["Net leverage", "淨槓桿"],
  interest_coverage: ["Interest coverage", "利息保障"],
  dscr: ["DSCR", "DSCR"],
  free_cash_flow_margin: ["Free-cash-flow margin", "自由現金流利潤率"],
  current_ratio: ["Current ratio", "流動比率"],
  cash_conversion: ["Cash conversion", "現金轉換率"],
};

function ratio(value: string | null, status = "valid", zh = false) {
  if (value === null)
    return status === "missing_input"
      ? zh
        ? "缺少資料"
        : "Missing"
      : zh
        ? "不適用"
        : "Not meaningful";
  return `${value}x`;
}
function outcome(value: string, zh: boolean) {
  if (!zh) return value;
  return (
    (
      {
        Approve: "核准",
        "Approve with conditions": "附條件核准",
        "Reduce requested amount": "降低申請額度",
        "Refer to credit committee": "提交信審會",
        Decline: "婉拒",
      } as Record<string, string>
    )[value] ?? value
  );
}
function scenarioName(value: string, zh: boolean) {
  if (!zh) return value[0].toUpperCase() + value.slice(1);
  return (
    (
      { base: "基準", downside: "下行情境", severe: "嚴重壓力" } as Record<
        string,
        string
      >
    )[value] ?? value
  );
}
function uiStatus(value: string, zh: boolean) {
  if (!zh) return value.replaceAll("_", " ");
  return (
    (
      {
        valid: "有效",
        adverse: "不利",
        blocked: "已阻擋",
        pass: "通過",
        breach: "違反",
        not_applicable: "不適用",
        policy_not_applicable: "政策不適用",
        strong: "強",
        adequate: "良好",
        moderate: "中等",
        weak: "偏弱",
        severe: "嚴重不足",
        high: "高",
        medium: "中",
        low: "低",
        limited: "有限",
        draft: "草稿",
        stale: "已過期",
        analyzed: "已分析",
        archived: "已封存",
      } as Record<string, string>
    )[value] ?? "已記錄"
  );
}
function confidenceText(value: string, zh: boolean): string {
  if (!zh) return value;
  return (
    (
      {
        "Deterministic formulas": "確定性公式",
        "Versioned policy": "版本化政策",
        "Source components retained": "保留來源組成",
        "Instrument-level debt schedule supplied": "已提供逐筆債務表",
        "Replace synthetic values with independently verified borrower evidence":
          "以獨立驗證的借款人證據取代合成數值",
        "Provide an instrument-level debt schedule": "提供逐筆債務表",
        "Document and independently support EBITDA adjustments":
          "記錄並獨立佐證 EBITDA 調整",
      } as Record<string, string>
    )[value] ?? "提供更多獨立驗證資料"
  );
}
function structureText(value: string, zh: boolean): string {
  if (!zh) return value;
  return (
    (
      {
        "None — unsecured": "無擔保",
        "Eligible borrower assets subject to documented advance rates":
          "依文件化預支率計算的合格借款人資產",
        None: "無",
      } as Record<string, string>
    )[value] ?? value
  );
}
function purposeText(value: string, zh: boolean): string {
  if (!zh) return value;
  return (
    (
      {
        "Fund a new production line and refinance near-term maturities":
          "興建新產線並再融資近期到期債務",
        "Refinance existing debt and fund product development":
          "再融資既有債務並投入產品開發",
        "Acquire two regional distribution centers and expand working-capital capacity":
          "收購兩座區域配送中心並擴大營運資金融通",
      } as Record<string, string>
    )[value] ?? "依案件輸入所載的合成融資用途"
  );
}
function riskFactorLabel(value: string, zh: boolean) {
  if (!zh) return value.replaceAll("_", " ");
  return (
    (
      {
        leverage: "槓桿",
        coverage: "保障與償債",
        liquidity: "流動性",
        cash_flow: "現金流",
        profitability: "獲利能力",
        industry: "產業風險",
        competitive_position: "競爭地位",
        customer_concentration: "客戶集中度",
        diversification: "多元化",
        management_policy: "管理與財務政策",
        governance_event: "治理與事件風險",
      } as Record<string, string>
    )[value] ?? value
  );
}
function covenantLabel(value: string, zh: boolean) {
  if (!zh) return value;
  return (
    (
      {
        "Maximum total leverage": "最高總槓桿",
        "Minimum DSCR": "最低 DSCR",
        "Quarterly financial reporting": "每季財務報告",
        "Restricted distributions": "限制分配",
        "Capital expenditure control": "資本支出控制",
        "Borrowing-base availability": "借款基礎可用額",
        "Collateral reporting": "擔保品報告",
      } as Record<string, string>
    )[value] ?? "財務契約要求"
  );
}
function facilityType(value: string, zh: boolean) {
  if (!zh) return value.replaceAll("_", " ");
  return (
    (
      {
        term_loan: "定期貸款",
        revolver: "循環信用額度",
        asset_based: "資產基礎融資",
      } as Record<string, string>
    )[value] ?? value
  );
}
function policyCheckLabel(value: string, zh: boolean) {
  if (!zh) return value;
  return (
    (
      {
        maximum_leverage: "最高槓桿",
        minimum_dscr: "最低 DSCR",
        minimum_interest_coverage: "最低利息保障",
        maximum_maturity: "最長到期年限",
        minimum_liquidity: "最低流動性",
        reporting_currency: "報告幣別",
        positive_capacity: "正向容量",
        minimum_data_quality: "最低資料品質",
        maximum_adjustment_magnitude: "最高調整幅度",
        grade_eligibility: "評等資格",
        maximum_exposure: "最高曝險",
        minimum_collateral_coverage: "最低擔保覆蓋",
        facility_restrictions: "額度類型限制",
      } as Record<string, string>
    )[value] ?? "政策檢查"
  );
}
function bindingLabel(value: string, zh: boolean) {
  const labels = zh
    ? {
        requested_amount: "申請額",
        leverage_capacity: "槓桿容量",
        dscr_capacity: "DSCR 容量",
        collateral_capacity: "擔保品容量",
        policy_capacity: "政策上限",
      }
    : {
        requested_amount: "Requested amount",
        leverage_capacity: "Leverage capacity",
        dscr_capacity: "DSCR capacity",
        collateral_capacity: "Collateral capacity",
        policy_capacity: "Policy limit",
      };
  return (labels as Record<string, string>)[value] ?? value;
}
function priorityLabel(value: string, zh: boolean) {
  const labels = zh
    ? {
        zero_supported_exposure: "可支援曝險為零",
        critical_inputs_blocked: "關鍵輸入阻擋分析",
        policy_hard_stop: "政策硬性停止",
        risk_grade: "風險評等",
        risk_referral: "風險提交信審會",
        capacity_reduction: "容量降低",
        conditional_approval: "附條件核准",
        standard_approval: "標準核准",
      }
    : {
        zero_supported_exposure: "Zero supportable exposure",
        critical_inputs_blocked: "Critical inputs blocked",
        policy_hard_stop: "Policy hard stop",
        risk_grade: "Risk grade",
        risk_referral: "Credit-committee referral",
        capacity_reduction: "Capacity reduction",
        conditional_approval: "Conditional approval",
        standard_approval: "Standard approval",
      };
  return (labels as Record<string, string>)[value] ?? value;
}
function conditionText(value: string, zh: boolean) {
  if (!zh) return value;
  return (
    (
      {
        "Maximum total leverage tested quarterly with threshold set from policy and forecast headroom.":
          "最高總槓桿按季檢驗，門檻依政策及預測餘裕設定。",
        "Minimum DSCR tested quarterly with cure or waiver subject to lender approval.":
          "最低 DSCR 按季檢驗；補救或豁免須經貸方核准。",
        "Quarterly financial reporting within 45 days.":
          "每季財務報告應於 45 日內提交。",
        "Monthly liquidity reporting until downside headroom is restored.":
          "每月提交流動性報告，直到下行情境餘裕恢復。",
        "Perfect and maintain the proposed collateral security interest.":
          "完成並持續維持擬議擔保權益。",
      } as Record<string, string>
    )[value] ?? value
  );
}
function localizedText(value: string, zh: boolean) {
  if (!zh) return value;
  return (
    (
      {
        "Diversified OEM and aftermarket demand": "OEM 與售後市場需求多元",
        "Positive free cash flow through the cycle":
          "景氣循環中仍維持正自由現金流",
        "Experienced management team": "具經驗的管理團隊",
        "Exposure to industrial production cycles": "暴露於工業生產循環",
        "Working-capital needs rise during expansion": "擴張期營運資金需求上升",
        "New production line carries execution risk": "新產線具有執行風險",
        "Established regional footprint": "穩固的區域市場布局",
        "Broad supplier relationships": "廣泛的供應商關係",
        "Cyclical fleet demand": "車隊需求具週期性",
        "Top-five customer concentration": "前五大客戶集中度偏高",
        "Acquisition integration risk": "併購整合風險",
        "Recurring subscription revenue": "經常性訂閱收入",
        "Strong cash conversion": "現金轉換能力強",
        "Low customer concentration": "客戶集中度低",
        "Limited tangible collateral": "有形擔保品有限",
        "Product-obsolescence risk": "產品淘汰風險",
        "Retention depends on service quality": "續約率仰賴服務品質",
      } as Record<string, string>
    )[value] ?? value
  );
}
function memoParagraph(value: string, zh: boolean) {
  if (!zh) return value;
  const fixed = (
    {
      "None identified.": "未識別政策例外。",
      "Quarterly financial statements": "每季財務報表",
      "Annual covenant compliance certificate": "年度財務契約遵循證明",
      "Prompt notice of material adverse events": "重大不利事件應即時通知",
      "Prepared by: ____________________": "分析人員：____________________",
      "Reviewed by: ____________________": "覆核人員：____________________",
      "Synthetic demonstration — not a real data-quality assessment":
        "合成示範資料，不代表真實資料品質評估。",
    } as Record<string, string>
  )[value];
  if (fixed) return fixed;
  if (value.startsWith("Educational and illustrative only"))
    return "僅供教育用途，不構成授信、投資、會計或法律建議。";
  const translatedOutcome = outcome(value, true);
  if (translatedOutcome !== value) return translatedOutcome;
  const translatedCondition = conditionText(value, true);
  if (translatedCondition !== value) return translatedCondition;
  return localizedText(value, true);
}
function memoTitle(value: string, zh: boolean) {
  if (!zh) return value.replaceAll("_", " ");
  return (
    (
      {
        executive_recommendation: "執行建議",
        borrower_overview: "借款人概況",
        ownership_and_management: "所有權與管理",
        business_model: "商業模式",
        industry_risk: "產業風險",
        loan_request: "貸款申請",
        facility_structure: "授信結構",
        loan_purpose: "貸款用途",
        sources_and_uses: "資金來源與用途",
        primary_repayment_source: "主要還款來源",
        secondary_repayment_source: "次要還款來源",
        historical_financial_performance: "歷史財務表現",
        financial_adjustments: "財務調整",
        capital_structure: "資本結構",
        debt_maturity_schedule: "債務到期表",
        key_ratios: "關鍵比率",
        obligor_grade: "債務人評等",
        facility_protection: "設施保障",
        debt_capacity: "債務容量",
        base_case: "基準情境",
        downside_case: "下行情境",
        severe_case: "嚴重壓力情境",
        reverse_stress: "反向壓力測試",
        collateral_or_borrowing_base: "擔保品或借款基礎",
        indicative_pricing: "示意定價",
        covenants: "財務契約",
        policy_exceptions: "政策例外",
        conditions_precedent: "先決條件",
        monitoring: "監控",
        data_limitations: "資料限制",
        analyst_sign_off: "分析師簽核",
        reviewer_sign_off: "覆核人簽核",
      } as Record<string, string>
    )[value] ?? value
  );
}

function zhMemoSections(a: Analysis): Record<string, string[]> {
  const base = a.scenarios.find((item) => item.name === "base")!;
  const downside = a.scenarios.find((item) => item.name === "downside")!;
  const severe = a.scenarios.find((item) => item.name === "severe")!;
  const amount = (value: Money) => money(value, "zh-TW");
  const breach = (year: number | null) =>
    year ? `第 ${year} 年` : "三年預測期內無";
  return {
    executive_recommendation: [
      `建議：${outcome(a.decision.outcome, true)}；申請額 ${amount(a.capacity.requested)}；可支援額度 ${amount(a.capacity.recommended)}；債務人評等 ${a.scorecard.grade ?? "已阻擋"}。`,
    ],
    borrower_overview: [
      `借款人：${a.case.borrower.legal_name}。業務、產業與所在地資料已保留於合成案件輸入。`,
    ],
    ownership_and_management: [
      "合成案件未提供所有權明細；管理評估以營運風險證據紀錄為基礎。",
    ],
    business_model: [
      a.case.borrower.description
        ? "合成案件已提供業務模式說明；使用前仍須以獨立文件驗證。"
        : "未提供商業模式說明。",
    ],
    industry_risk: [
      `已記錄 ${a.case.business_risk.risks.length} 項主要風險及 ${a.case.business_risk.strengths.length} 項主要優勢。`,
    ],
    loan_request: [`借款人申請 ${amount(a.case.request.amount)}。`],
    facility_structure: [
      `額度類型 ${facilityType(a.decision.facility_type, true)}；${a.case.request.rate_type === "fixed" ? "固定" : "浮動"}利率；到期 ${a.decision.maturity_years} 年；攤還 ${a.decision.amortization_years} 年。`,
    ],
    loan_purpose: [purposeText(a.case.request.purpose, true)],
    sources_and_uses: [
      `擬議貸方資金來源 ${amount(a.case.request.amount)}；用途為${purposeText(a.case.request.purpose, true)}。未提供其他資金來源或用途。`,
    ],
    primary_repayment_source: [
      a.decision.primary_repayment_source === "Operating cash flow"
        ? "營運現金流"
        : a.decision.primary_repayment_source,
    ],
    secondary_repayment_source: [
      "合格擔保品與企業價值支援；分析未假設可成功再融資。",
    ],
    historical_financial_performance: [
      `營收 ${amount(a.case.financials.revenue as Money)}；報告 EBITDA ${amount(a.adjustments.reported_ebitda)}；調整後 EBITDA ${amount(a.adjustments.adjusted_ebitda)}。`,
      `LTM 狀態：${a.financial_spreading.ltm_status === "available" ? "可使用" : a.financial_spreading.ltm_status === "blocked" ? "已阻擋" : "舊版單期快照"}。`,
    ],
    financial_adjustments: [
      `已核准調整 ${amount(a.adjustments.approved_adjustment)}；正向調整占比 ${(Number(a.adjustments.positive_adjustment_pct) * 100).toFixed(2)}%。`,
    ],
    capital_structure: [
      `總債務與現金、權益均取自標準化 API 輸出；非受限現金 ${amount(a.case.financials.unrestricted_cash as Money)}；權益 ${amount(a.case.financials.equity as Money)}。`,
    ],
    debt_maturity_schedule: [
      a.case.debt_instruments.length
        ? `已提供 ${a.case.debt_instruments.length} 項逐筆債務工具與到期年度。`
        : "未提供逐筆債務到期表。",
    ],
    key_ratios: [
      `總槓桿 ${a.metrics.gross_leverage.value ?? "不具意義"} 倍；利息保障 ${a.metrics.interest_coverage.value ?? "不具意義"} 倍；DSCR ${a.metrics.dscr.value ?? "不具意義"} 倍。`,
    ],
    obligor_grade: [
      `分數 ${a.scorecard.score ?? "已阻擋"}；評等 ${a.scorecard.grade ?? "已阻擋"}；資料信心 ${a.scorecard.confidence_score}/100。設施保障不會改變債務人評等。`,
    ],
    facility_protection: [
      `設施保障分數 ${a.facility_protection.score}；類別 ${uiStatus(a.facility_protection.category, true)}；預期回收類別 ${uiStatus(a.facility_protection.expected_recovery_category, true)}。`,
    ],
    debt_capacity: [
      `申請 ${amount(a.capacity.requested)}；建議 ${amount(a.capacity.recommended)}；約束條件：${a.capacity.binding_constraints.map((item) => bindingLabel(item, true)).join("、")}。`,
    ],
    base_case: [`首次財務契約違約：${breach(base.first_breach_year)}。`],
    downside_case: [
      `首次財務契約違約：${breach(downside.first_breach_year)}；流動性耗盡：${breach(downside.liquidity_exhaustion_year)}。`,
    ],
    severe_case: [
      `首次財務契約違約：${breach(severe.first_breach_year)}；流動性耗盡：${breach(severe.liquidity_exhaustion_year)}。`,
    ],
    reverse_stress: [
      `六個求解器中有 ${a.reverse_stress.solvers.filter((item) => item.converged).length} 個已收斂；未收斂結果不顯示數值。`,
    ],
    collateral_or_borrowing_base: [
      a.borrowing_base.borrowing_base
        ? `最終借款基礎 ${amount(a.borrowing_base.borrowing_base)}。`
        : a.borrowing_base.applicable
          ? "借款基礎因缺少合格擔保品輸入而阻擋。"
          : "此額度不適用借款基礎。",
    ],
    indicative_pricing: [
      `參考基準利率 ${(Number(a.pricing.reference_base_rate) * 100).toFixed(2)}%；風險利差 ${a.pricing.risk_grade_spread_bps} bps；示意全包利率 ${(Number(a.pricing.indicative_all_in_rate) * 100).toFixed(2)}%。`,
      "僅供教育用途，不代表即時市場報價或銀行承諾。",
    ],
    covenants: [
      `共產生 ${a.covenants.length} 項維持性、發生性或報告型財務契約。`,
    ],
    policy_exceptions: [
      a.decision.policy_exceptions.length
        ? `共有 ${a.decision.policy_exceptions.length} 項政策警示需要授權處理。`
        : "未識別政策例外。",
    ],
    conditions_precedent: a.decision.conditions.map((item) =>
      conditionText(item, true),
    ),
    monitoring: [
      "每季財務報表、年度財務契約遵循證明，以及重大不利事件即時通知。",
    ],
    data_limitations: [
      "本案件使用合成資料，未執行真實文件、法規、制裁、詐欺或法律盡職調查。僅供教育用途。",
    ],
    analyst_sign_off: [
      "分析人員：____________________",
      `資料基準日：${a.case.data_as_of}`,
    ],
    reviewer_sign_off: [
      "覆核人員：____________________",
      `模型 ${a.engine_version}；政策 ${a.policy_version}。`,
    ],
  };
}
function isMoney(value: unknown): value is Money {
  return Boolean(value && typeof value === "object" && "amount_minor" in value);
}
function Stat({
  label,
  value,
  note,
  meaning,
}: {
  label: string;
  value: string;
  note?: string;
  meaning?: string;
}) {
  const explanation =
    meaning && /[\u3400-\u9fff]/.test(meaning)
      ? "這代表什麼？"
      : "What does this mean?";
  return (
    <div className="stat">
      <span>{label}</span>
      <strong>{value}</strong>
      {note && <small>{note}</small>}
      {meaning && (
        <details>
          <summary>
            <Info size={13} />
            {explanation}
          </summary>
          <p>{meaning}</p>
        </details>
      )}
    </div>
  );
}
function MoneyStat({
  label,
  value,
  locale,
  note,
  meaning,
}: {
  label: string;
  value: Money;
  locale: string;
  note?: string;
  meaning?: string;
}) {
  return (
    <Stat
      label={label}
      value={money(value, locale, true)}
      note={note}
      meaning={meaning}
    />
  );
}

function Overview({
  a,
  language,
  locale,
}: {
  a: Analysis;
  language: Language;
  locale: string;
}) {
  const zh = language === "zh-TW";
  const downside = a.scenarios.find((item) => item.name === "downside");
  return (
    <>
      <div className="decision-banner">
        <div>
          <p>{zh ? "授信建議" : "Credit recommendation"}</p>
          <h2>{outcome(a.decision.outcome, zh)}</h2>
          <span>
            {zh
              ? `決策優先規則：${priorityLabel(a.decision.decision_priority, true)}`
              : `Decision priority: ${priorityLabel(a.decision.decision_priority, false)}`}
          </span>
        </div>
        <div className="grade-seal">
          <span>{zh ? "內部評等" : "Internal grade"}</span>
          <strong>{a.scorecard.grade ?? "—"}</strong>
          <small>
            {zh
              ? `信心 ${a.scorecard.confidence_score}/100`
              : a.scorecard.grade_label}
          </small>
        </div>
      </div>
      <div className="stats-grid">
        <MoneyStat
          label={zh ? "申請額" : "Requested"}
          value={a.capacity.requested}
          locale={locale}
          meaning={
            zh
              ? "借款人要求的名目額度。"
              : "The nominal facility amount requested by the borrower."
          }
        />
        <MoneyStat
          label={zh ? "建議額度" : "Recommended"}
          value={a.capacity.recommended}
          locale={locale}
          note={a.capacity.binding_constraints
            .map((x) => bindingLabel(x, zh))
            .join(", ")}
          meaning={
            zh
              ? "所有適用容量限制中的最低值。"
              : "The minimum of all valid, applicable capacity constraints."
          }
        />
        <Stat
          label={zh ? "總槓桿" : "Gross leverage"}
          value={ratio(
            a.metrics.gross_leverage.value,
            a.metrics.gross_leverage.status,
            zh,
          )}
          meaning={
            zh
              ? "總債務相對於調整後 EBITDA。數值越低通常越有利。"
              : "Total debt relative to adjusted EBITDA; lower is generally stronger."
          }
        />
        <Stat
          label="DSCR"
          value={ratio(a.metrics.dscr.value, a.metrics.dscr.status, zh)}
          meaning={
            zh
              ? "可用現金流對年度債務服務的倍數。"
              : "Cash available for debt service divided by annual debt service."
          }
        />
      </div>
      <div className="overview-answer">
        <dl>
          <div>
            <dt>{zh ? "主要還款來源" : "Primary repayment source"}</dt>
            <dd>
              {zh &&
              a.decision.primary_repayment_source === "Operating cash flow"
                ? "營運現金流"
                : a.decision.primary_repayment_source}
            </dd>
          </div>
          <div>
            <dt>{zh ? "下行情境" : "Downside"}</dt>
            <dd>
              {downside?.first_breach_year
                ? `${zh ? "首次違約年度" : "First breach year"} ${downside.first_breach_year}`
                : zh
                  ? "三年內無違約"
                  : "No breach in three years"}
            </dd>
          </div>
          <div>
            <dt>{zh ? "約束條件" : "Binding constraint"}</dt>
            <dd>
              {a.capacity.binding_constraints
                .map((x) => bindingLabel(x, zh))
                .join(", ")}
            </dd>
          </div>
          <div>
            <dt>{zh ? "資料信心" : "Data confidence"}</dt>
            <dd>
              {a.scorecard.confidence} · {a.scorecard.confidence_score}/100
            </dd>
          </div>
        </dl>
      </div>
      <div className="two-column">
        <article className="panel">
          <h3>{zh ? "主要優勢" : "Three supporting factors"}</h3>
          <ul className="clean-list">
            {a.case.business_risk.strengths.slice(0, 3).map((x) => (
              <li key={x}>
                <Check size={17} />
                {localizedText(x, zh)}
              </li>
            ))}
          </ul>
        </article>
        <article className="panel">
          <h3>{zh ? "主要不利因素" : "Three adverse factors"}</h3>
          <ul className="clean-list risks">
            {a.case.business_risk.risks.slice(0, 3).map((x) => (
              <li key={x}>
                <CircleAlert size={17} />
                {localizedText(x, zh)}
              </li>
            ))}
          </ul>
        </article>
      </div>
    </>
  );
}

function Inputs({
  input,
  language,
  locale,
  mode,
  onSave,
}: {
  input: CaseInput;
  language: Language;
  locale: string;
  mode: string;
  onSave: (value: CaseInput) => Promise<void>;
}) {
  const zh = language === "zh-TW";
  const [draft, setDraft] = useState(() => structuredClone(input));
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const shown = Object.entries(draft.financials).filter(([, value]) =>
    isMoney(value),
  );
  function setFinancial(key: string, text: string) {
    const current = draft.financials[key];
    if (!isMoney(current)) return;
    const parsed = parseMoneyInput(text, current.minor_unit_exponent, language);
    if (!parsed.ok) {
      setError(parsed.message);
      return;
    }
    setError("");
    setDraft((value) => ({
      ...value,
      financials: {
        ...value.financials,
        [key]: {
          ...current,
          amount_minor: parsed.amountMinor,
        },
      },
    }));
  }
  async function save() {
    setBusy(true);
    setError("");
    try {
      await onSave(draft);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : String(cause));
    } finally {
      setBusy(false);
    }
  }
  return (
    <div className="panel editable-inputs">
      <div className="panel-head">
        <div>
          <h3>{zh ? "可編輯案件輸入" : "Editable case inputs"}</h3>
          <p>
            {mode === "guided"
              ? zh
                ? "引導模式以白話分組所有重要欄位，不隱藏任何數值。"
                : "Guided mode groups every material value in plain language; no values are hidden."
              : zh
                ? "分析師模式在相同數值上加入標準化來源與計算脈絡。"
                : "Analyst mode adds normalized source context to the same values."}
          </p>
        </div>
        <span className="as-of">{draft.data_as_of}</span>
      </div>
      <h4>{zh ? "借款人與申請" : "Borrower and request"}</h4>
      <div className="input-grid">
        <label>
          {zh ? "公司名稱" : "Company name"}
          <input
            value={draft.borrower.legal_name}
            onChange={(e) =>
              setDraft((v) => ({
                ...v,
                borrower: { ...v.borrower, legal_name: e.target.value },
              }))
            }
          />
        </label>
        <label>
          {zh ? "申請額" : "Requested amount"}
          <input
            inputMode="decimal"
            value={formatMoneyInput(draft.request.amount)}
            onChange={(e) => {
              const parsed = parseMoneyInput(
                e.target.value,
                draft.request.amount.minor_unit_exponent,
                language,
              );
              if (!parsed.ok) {
                setError(parsed.message);
                return;
              }
              setError("");
              setDraft((v) => ({
                ...v,
                request: {
                  ...v.request,
                  amount: {
                    ...v.request.amount,
                    amount_minor: parsed.amountMinor,
                  },
                },
              }));
            }}
          />
        </label>
        <label>
          {zh ? "用途" : "Purpose"}
          <input
            value={draft.request.purpose}
            onChange={(e) =>
              setDraft((v) => ({
                ...v,
                request: { ...v.request, purpose: e.target.value },
              }))
            }
          />
        </label>
        <label>
          {zh ? "到期年數" : "Maturity years"}
          <input
            type="number"
            min="1"
            value={draft.request.maturity_years}
            onChange={(e) =>
              setDraft((v) => ({
                ...v,
                request: {
                  ...v.request,
                  maturity_years: Number.parseInt(e.target.value, 10),
                },
              }))
            }
          />
        </label>
      </div>
      {mode === "analyst" && (
        <>
          <FinancialSpreadEditor
            value={draft.financial_spread}
            language={language}
            onChange={(financial_spread) =>
              setDraft((value) => ({ ...value, financial_spread }))
            }
          />
          <AdjustmentLogEditor
            input={draft}
            language={language}
            onError={setError}
            onChange={(normalization_adjustments) =>
              setDraft((value) => ({
                ...value,
                normalization_adjustments,
              }))
            }
          />
        </>
      )}
      <BorrowingBaseEditor
        input={draft}
        language={language}
        onError={setError}
        onChange={(borrowing_base) =>
          setDraft((value) => ({ ...value, borrowing_base }))
        }
      />
      <section className="pricing-editor">
        <h4>{zh ? "示意定價輸入" : "Indicative pricing inputs"}</h4>
        <div className="input-grid">
          <label>
            {zh ? "參考基準利率（小數）" : "Reference base rate (decimal)"}
            <input
              value={draft.pricing?.reference_base_rate ?? "0.04"}
              onChange={(event) =>
                setDraft((value) => ({
                  ...value,
                  pricing: {
                    reference_base_rate: event.target.value,
                    relationship_adjustment_bps:
                      value.pricing?.relationship_adjustment_bps ?? 0,
                    include_upfront_fee:
                      value.pricing?.include_upfront_fee ?? false,
                  },
                }))
              }
            />
          </label>
          <label>
            {zh ? "關係調整（bps）" : "Relationship adjustment (bps)"}
            <input
              type="number"
              min="-200"
              max="200"
              value={draft.pricing?.relationship_adjustment_bps ?? 0}
              onChange={(event) =>
                setDraft((value) => ({
                  ...value,
                  pricing: {
                    reference_base_rate:
                      value.pricing?.reference_base_rate ?? "0.04",
                    relationship_adjustment_bps: Number(event.target.value),
                    include_upfront_fee:
                      value.pricing?.include_upfront_fee ?? false,
                  },
                }))
              }
            />
          </label>
        </div>
      </section>
      <h4>{zh ? "財務與債務" : "Financials and debt"}</h4>
      <div className="input-grid">
        {shown.map(([key, value]) => (
          <label key={key}>
            {fieldName[key]?.[zh ? 1 : 0] ?? key.replaceAll("_", " ")}
            <input
              inputMode="decimal"
              value={formatMoneyInput(value as Money)}
              onChange={(e) => setFinancial(key, e.target.value)}
            />
            {mode === "analyst" && (
              <small>
                {money(value as Money, locale)} ·{" "}
                {zh ? "標準化案件輸入" : "Normalized case input"}
              </small>
            )}
          </label>
        ))}
      </div>
      {error && (
        <p className="error" role="alert">
          {error}
        </p>
      )}
      <div className="save-row">
        <button className="button primary" onClick={save} disabled={busy}>
          {busy ? (
            <LoaderCircle className="spin" size={16} />
          ) : (
            <Save size={16} />
          )}{" "}
          {zh ? "儲存變更" : "Save changes"}
        </button>
        <button
          className="button secondary"
          type="button"
          onClick={() => {
            setDraft(structuredClone(input));
            setError("");
          }}
        >
          {zh ? "復原未儲存變更" : "Revert unsaved changes"}
        </button>
        <span>
          {zh
            ? "儲存後舊分析會標記為過期，必須重新計算。"
            : "Saving marks the prior analysis stale and requires recalculation."}
        </span>
      </div>
    </div>
  );
}

function Financials({
  a,
  language,
  locale,
  mode,
}: {
  a: Analysis;
  language: Language;
  locale: string;
  mode: string;
}) {
  const zh = language === "zh-TW";
  const revenue = a.case.financials.revenue as Money;
  const prior = a.case.financials.prior_revenue as Money;
  return (
    <>
      <FinancialSpreadingPanel
        analysis={a}
        language={language}
        locale={locale}
        mode={mode}
      />
      <div className="trend-strip">
        <div>
          <span>{zh ? "前期營收" : "Prior revenue"}</span>
          <strong>{money(prior, locale, true)}</strong>
        </div>
        <i />
        <div>
          <span>{zh ? "LTM 營收" : "LTM revenue"}</span>
          <strong>{money(revenue, locale, true)}</strong>
        </div>
      </div>
      <div className="stats-grid">
        {Object.values(a.metrics)
          .slice(0, 8)
          .map((value) => (
            <Stat
              key={value.metric_id}
              label={zh ? value.plain_label : value.label}
              value={ratio(value.value, value.status, zh)}
              note={value.status === "valid" ? undefined : value.reason_code}
              meaning={
                mode === "guided"
                  ? zh
                    ? "此比率由標準化財務輸入計算。"
                    : "Calculated from normalized borrower financials."
                  : undefined
              }
            />
          ))}
      </div>
      {mode === "analyst" && (
        <article className="panel table-panel" tabIndex={0}>
          <h3>{zh ? "完整計算溯源" : "Calculation lineage"}</h3>
          <table>
            <thead>
              <tr>
                <th>{zh ? "指標" : "Metric"}</th>
                <th>{zh ? "狀態" : "State"}</th>
                <th>{zh ? "公式" : "Formula"}</th>
                <th>{zh ? "政策" : "Policy"}</th>
                <th>{zh ? "模型" : "Model"}</th>
              </tr>
            </thead>
            <tbody>
              {Object.values(a.metrics).map((value) => (
                <tr key={value.metric_id}>
                  <td>
                    {metricName[value.metric_id]?.[zh ? 1 : 0] ??
                      (zh ? "財務指標" : value.label)}
                  </td>
                  <td>{uiStatus(value.status, zh)}</td>
                  <td>{value.formula_id ?? "—"}</td>
                  <td>{value.policy_ref ?? "—"}</td>
                  <td>{value.model_version}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </article>
      )}
    </>
  );
}

function Capacity({
  a,
  language,
  locale,
}: {
  a: Analysis;
  language: Language;
  locale: string;
}) {
  const zh = language === "zh-TW";
  return (
    <>
      <div className="capacity-answer">
        <MoneyStat
          label={zh ? "申請額" : "Request"}
          value={a.capacity.requested}
          locale={locale}
        />
        <span>→</span>
        <MoneyStat
          label={zh ? "可支援額度" : "Recommended"}
          value={a.capacity.recommended}
          locale={locale}
          note={a.capacity.binding_constraints.join(", ")}
        />
      </div>
      <article className="panel table-panel" tabIndex={0}>
        <h3>
          {zh ? "容量限制與適用性" : "Capacity constraints and applicability"}
        </h3>
        <table>
          <thead>
            <tr>
              <th>{zh ? "方法" : "Method"}</th>
              <th>{zh ? "適用" : "Applicable"}</th>
              <th>{zh ? "容量" : "Capacity"}</th>
              <th>{zh ? "狀態" : "State"}</th>
              <th>{zh ? "說明" : "Reason"}</th>
            </tr>
          </thead>
          <tbody>
            {a.capacity.constraints.map((item) => (
              <tr key={item.key} className={item.binding ? "binding-row" : ""}>
                <td>{zh ? bindingLabel(item.key, true) : item.label}</td>
                <td>
                  {item.applicable ? (zh ? "是" : "Yes") : zh ? "不適用" : "No"}
                </td>
                <td>
                  {item.amount
                    ? money(item.amount, locale, true)
                    : zh
                      ? "不適用"
                      : "Not applicable"}
                </td>
                <td>
                  {item.binding
                    ? zh
                      ? "具約束力"
                      : "Binding"
                    : uiStatus(item.status, zh)}
                </td>
                <td>{zh ? "依案件輸入與版本化政策計算。" : item.reason}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </article>
    </>
  );
}

function Risk({
  a,
  language,
  mode,
}: {
  a: Analysis;
  language: Language;
  mode: string;
}) {
  const zh = language === "zh-TW";
  return (
    <>
      <div className="score-hero">
        <div>
          <p>{zh ? "加權債務人分數" : "Weighted obligor score"}</p>
          <strong>{a.scorecard.score ?? "—"}</strong>
          <span>/ 100</span>
        </div>
        <div>
          <p>{zh ? "內部評等" : "Internal grade"}</p>
          <strong>{a.scorecard.grade ?? "—"}</strong>
          <span>{a.scorecard.grade_label}</span>
        </div>
        <div>
          <p>{zh ? "信心程度" : "Confidence"}</p>
          <strong className="word">
            {uiStatus(a.scorecard.confidence, zh)}
          </strong>
          <span>{a.scorecard.confidence_score}/100</span>
        </div>
      </div>
      <p className="synthetic-notice">
        {zh
          ? "合成示範資料，不代表真實資料品質評估。"
          : a.scorecard.synthetic_notice}
      </p>
      <article className="panel table-panel" tabIndex={0}>
        <h3>{zh ? "評分組成" : "Score components"}</h3>
        <table>
          <thead>
            <tr>
              <th>{zh ? "因素" : "Factor"}</th>
              <th>{zh ? "狀態" : "State"}</th>
              <th>{zh ? "分數" : "Score"}</th>
              <th>{zh ? "權重" : "Weight"}</th>
              <th>{zh ? "貢獻" : "Contribution"}</th>
              {mode === "analyst" && (
                <th>{zh ? "區間／證據" : "Band / evidence"}</th>
              )}
            </tr>
          </thead>
          <tbody>
            {a.scorecard.components.map((c) => (
              <tr key={c.key}>
                <td>{riskFactorLabel(c.key, zh)}</td>
                <td>{uiStatus(c.status, zh)}</td>
                <td>{c.score}</td>
                <td>{c.weight}%</td>
                <td>{c.contribution}</td>
                {mode === "analyst" && (
                  <td>
                    {uiStatus(c.band, zh)}
                    <br />
                    <small>
                      {zh ? "證據與來源已保留於案件輸入。" : c.evidence}
                    </small>
                  </td>
                )}
              </tr>
            ))}
          </tbody>
        </table>
      </article>
      <div className="two-column">
        <article className="panel">
          <h3>{zh ? "信心驅動因素" : "Confidence drivers"}</h3>
          <ul>
            {a.scorecard.confidence_drivers.map((x) => (
              <li key={x}>{confidenceText(x, zh)}</li>
            ))}
          </ul>
        </article>
        <article className="panel">
          <h3>{zh ? "改善方式" : "Improve confidence"}</h3>
          <ul>
            {a.scorecard.improvement_actions.map((x) => (
              <li key={x}>{confidenceText(x, zh)}</li>
            ))}
          </ul>
        </article>
      </div>
    </>
  );
}

function ScenarioLineChart({
  title,
  labels: chartLabels,
  series,
}: {
  title: string;
  labels: string[];
  series: Array<{ label: string; values: number[] }>;
}) {
  const values = series.flatMap((item) => item.values);
  const maximum = Math.max(...values, 1);
  const minimum = Math.min(...values, 0);
  const range = Math.max(1, maximum - minimum);
  const x = (index: number) => 34 + index * 128;
  const y = (value: number) => 128 - ((value - minimum) / range) * 96;
  const description = series
    .map((item) => `${item.label}: ${item.values.join(", ")}`)
    .join("; ");
  return (
    <figure className="line-chart">
      <figcaption>{title}</figcaption>
      <svg
        viewBox="0 0 330 165"
        role="img"
        aria-label={`${title}. ${description}`}
      >
        <line x1="34" y1="128" x2="310" y2="128" className="chart-axis" />
        {series.map((item, seriesIndex) => {
          const points = item.values
            .map((value, index) => `${x(index)},${y(value)}`)
            .join(" ");
          return (
            <g
              key={item.label}
              className={`chart-series series-${seriesIndex}`}
            >
              <polyline points={points} />
              {item.values.map((value, index) => (
                <circle
                  key={`${item.label}-${index}`}
                  cx={x(index)}
                  cy={y(value)}
                  r="3"
                />
              ))}
            </g>
          );
        })}
        {chartLabels.map((label, index) => (
          <text key={label} x={x(index)} y="150" textAnchor="middle">
            {label}
          </text>
        ))}
      </svg>
      <div className="chart-legend">
        {series.map((item, index) => (
          <span key={item.label} className={`legend-${index}`}>
            {item.label}
          </span>
        ))}
      </div>
    </figure>
  );
}

function Stress({
  a,
  language,
  locale,
  onSave,
}: {
  a: Analysis;
  language: Language;
  locale: string;
  onSave: (value: CaseInput) => Promise<void>;
}) {
  const zh = language === "zh-TW";
  const [draft, setDraft] = useState(() => structuredClone(a.case));
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const firstYears = a.scenarios.map((s) => ({
    ...s.years[0],
    name: s.name,
    first: s.first_breach_year,
  }));
  function change(
    name: keyof CaseInput["scenarios"],
    key: keyof ScenarioInput,
    value: string,
  ) {
    setDraft((current) => ({
      ...current,
      scenarios: {
        ...current.scenarios,
        [name]: { ...current.scenarios[name], [key]: value },
      },
    }));
  }
  async function save() {
    setBusy(true);
    setError("");
    try {
      await onSave(draft);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : String(cause));
    } finally {
      setBusy(false);
    }
  }
  return (
    <>
      <div className="scenario-grid">
        {firstYears.map(
          (y: ScenarioYear & { name: string; first: number | null }) => (
            <article
              className={`scenario-card ${y.covenant_status}`}
              key={y.name}
            >
              <p>{scenarioName(y.name, zh)}</p>
              <h3>{zh ? "第一年" : "Year 1"}</h3>
              <dl>
                <div>
                  <dt>{zh ? "營收" : "Revenue"}</dt>
                  <dd>{money(y.revenue, locale, true)}</dd>
                </div>
                <div>
                  <dt>EBITDA</dt>
                  <dd>{money(y.adjusted_ebitda, locale, true)}</dd>
                </div>
                <div>
                  <dt>{zh ? "槓桿" : "Leverage"}</dt>
                  <dd>{ratio(y.leverage, y.leverage_status, zh)}</dd>
                </div>
                <div>
                  <dt>DSCR</dt>
                  <dd>{ratio(y.dscr, y.dscr_status, zh)}</dd>
                </div>
                <div>
                  <dt>{zh ? "現金缺口" : "Cash shortfall"}</dt>
                  <dd>{money(y.cash_shortfall, locale, true)}</dd>
                </div>
                <div>
                  <dt>{zh ? "再融資需求" : "Refinancing"}</dt>
                  <dd>{money(y.refinancing_need, locale, true)}</dd>
                </div>
              </dl>
              <span className="status">{uiStatus(y.covenant_status, zh)}</span>
            </article>
          ),
        )}
      </div>
      <article className="panel scenario-edit">
        <h3>{zh ? "編輯情境假設" : "Edit scenario assumptions"}</h3>
        <div className="scenario-editor">
          {(["base", "downside", "severe"] as const).map((name) => (
            <fieldset key={name}>
              <legend>{scenarioName(name, zh)}</legend>
              {(
                [
                  "revenue_growth",
                  "subsequent_growth",
                  "ebitda_margin_change",
                  "rate_shock",
                  "working_capital_pct_revenue",
                  "maintenance_capex_pct_revenue",
                ] as const
              ).map((key) => (
                <label key={key}>
                  {scenarioFieldName[key][zh ? 1 : 0]}
                  <input
                    value={draft.scenarios[name][key]}
                    onChange={(e) => change(name, key, e.target.value)}
                  />
                </label>
              ))}
            </fieldset>
          ))}
        </div>
        {error && (
          <p className="error" role="alert">
            {error}
          </p>
        )}
        <button className="button primary" onClick={save} disabled={busy}>
          {busy ? (
            <LoaderCircle className="spin" size={16} />
          ) : (
            <RefreshCw size={16} />
          )}{" "}
          {zh ? "儲存情境並重新計算" : "Save scenarios and recalculate"}
        </button>
      </article>
      <div className="reverse-strip">
        <Gauge size={22} />
        <div>
          <strong>{zh ? "反向壓力測試" : "Reverse stress"}</strong>
          <span>
            {a.reverse_stress.dscr_minimum_revenue_decline === null
              ? zh
                ? `無法求得收斂結果：${a.reverse_stress.failure_reason ?? "未提供原因"}`
                : `No converged result: ${a.reverse_stress.failure_reason ?? "No reason provided"}`
              : zh
                ? `營收下降 ${a.reverse_stress.dscr_minimum_revenue_decline}% 時，DSCR 抵達最低門檻。`
                : `Revenue decline to minimum DSCR: ${a.reverse_stress.dscr_minimum_revenue_decline}%`}
          </span>
          <small>
            {zh ? "有界二分法" : a.reverse_stress.method} ·{" "}
            {a.reverse_stress.iterations} {zh ? "次迭代" : "iterations"} ·{" "}
            {a.reverse_stress.converged
              ? zh
                ? "已收斂"
                : "converged"
              : zh
                ? "未收斂"
                : "not converged"}
          </small>
        </div>
      </div>
      <div className="stress-charts">
        <ScenarioLineChart
          title={
            zh ? "下行情境：營收與 EBITDA" : "Downside: revenue and EBITDA"
          }
          labels={a.scenarios
            .find((item) => item.name === "downside")!
            .years.map(
              (item) => `${zh ? "第" : "Y"}${item.year}${zh ? "年" : ""}`,
            )}
          series={[
            {
              label: zh ? "營收" : "Revenue",
              values: a.scenarios
                .find((item) => item.name === "downside")!
                .years.map((item) => item.revenue.amount_minor),
            },
            {
              label: "EBITDA",
              values: a.scenarios
                .find((item) => item.name === "downside")!
                .years.map((item) => item.adjusted_ebitda.amount_minor),
            },
          ]}
        />
        <ScenarioLineChart
          title={
            zh ? "下行情境：期末現金與債務" : "Downside: ending cash and debt"
          }
          labels={a.scenarios
            .find((item) => item.name === "downside")!
            .years.map(
              (item) => `${zh ? "第" : "Y"}${item.year}${zh ? "年" : ""}`,
            )}
          series={[
            {
              label: zh ? "期末現金" : "Ending cash",
              values: a.scenarios
                .find((item) => item.name === "downside")!
                .years.map((item) => item.ending_cash.amount_minor),
            },
            {
              label: zh ? "期末債務" : "Ending debt",
              values: a.scenarios
                .find((item) => item.name === "downside")!
                .years.map((item) => item.ending_debt.amount_minor),
            },
          ]}
        />
      </div>
      <details className="panel solver-details">
        <summary>
          {zh
            ? "顯示六個反向壓力求解器"
            : "Show all six reverse-stress solvers"}
        </summary>
        <div className="solver-grid">
          {a.reverse_stress.solvers.map((solver) => (
            <article key={solver.key}>
              <span className={`pill ${solver.converged ? "pass" : "breach"}`}>
                {solver.converged
                  ? zh
                    ? "已收斂"
                    : "Converged"
                  : zh
                    ? "未收斂"
                    : "Not converged"}
              </span>
              <h4>
                {zh
                  ? (
                      {
                        revenue_dscr: "營收跌幅與最低 DSCR",
                        margin_leverage: "EBITDA 利潤率與最高槓桿",
                        rate_coverage: "利率衝擊與最低保障",
                        working_capital_liquidity: "營運資金使用與流動性",
                        maximum_downside_loan: "下行情境最高貸款",
                        maximum_severe_liquidity_loan: "嚴重情境流動性最高貸款",
                      } as Record<string, string>
                    )[solver.key]
                  : solver.variable_solved}
              </h4>
              <strong>
                {solver.result_money
                  ? money(solver.result_money, locale, true)
                  : (solver.result ?? "—")}
              </strong>
              <p>
                {zh
                  ? "以完整三年預測及版本化政策進行有界二分求解。"
                  : solver.interpretation}
              </p>
              <small>
                {solver.iterations} {zh ? "次迭代" : "iterations"} ·{" "}
                {zh ? "殘差" : "residual"} {solver.residual ?? "—"}
              </small>
              {!solver.converged && (
                <p className="solver-failure">
                  {zh ? "在政策界限內無收斂解。" : solver.failure_reason}
                </p>
              )}
            </article>
          ))}
        </div>
      </details>
      <details className="panel covenant-details">
        <summary>
          {zh ? "顯示完整財務契約表" : "Show full covenant table"}
        </summary>
        <table>
          <thead>
            <tr>
              <th>{zh ? "情境／年度" : "Scenario / year"}</th>
              <th>{zh ? "契約" : "Covenant"}</th>
              <th>{zh ? "實際" : "Actual"}</th>
              <th>{zh ? "門檻" : "Threshold"}</th>
              <th>{zh ? "狀態" : "Status"}</th>
            </tr>
          </thead>
          <tbody>
            {a.covenants.map((c, i) => (
              <tr key={`${c.scenario}-${c.year}-${i}`}>
                <td>
                  {scenarioName(c.scenario, zh)} / {c.year}
                </td>
                <td>{covenantLabel(c.name, zh)}</td>
                <td>
                  {zh && /[A-Za-z]{4,}/.test(c.actual)
                    ? "依 API 計算"
                    : c.actual}
                </td>
                <td>
                  {zh && /[A-Za-z]{4,}/.test(c.threshold)
                    ? "依政策設定"
                    : c.threshold}
                </td>
                <td>{uiStatus(c.status, zh)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </details>
    </>
  );
}

function Decision({
  a,
  language,
  locale,
}: {
  a: Analysis;
  language: Language;
  locale: string;
}) {
  const zh = language === "zh-TW";
  const rationale = zh
    ? [
        `債務人分數 ${a.scorecard.score ?? "已阻擋"}，對應${a.scorecard.grade === null ? "無最終評等" : `第 ${a.scorecard.grade} 級`}。`,
        `建議曝險受 ${a.capacity.binding_constraints.map((x) => bindingLabel(x, true)).join("、")} 約束。`,
        `下行情境償債能力與財務契約餘裕決定核准條件。`,
      ]
    : a.decision.rationale;
  return (
    <>
      <div className="decision-banner">
        <div>
          <p>{zh ? "最終授信建議" : "Final credit recommendation"}</p>
          <h2>{outcome(a.decision.outcome, zh)}</h2>
          <span>
            {zh
              ? "由政策、容量、壓力與決策優先規則共同決定。"
              : "Determined by policy, capacity, stress, and explicit decision priority."}
          </span>
        </div>
        <MoneyStat
          label={zh ? "建議額度" : "Recommended amount"}
          value={a.capacity.recommended}
          locale={locale}
        />
      </div>
      <div className="terms-grid">
        <dl>
          <div>
            <dt>{zh ? "額度類型" : "Facility"}</dt>
            <dd>{facilityType(a.decision.facility_type, zh)}</dd>
          </div>
          <div>
            <dt>{zh ? "到期／攤還" : "Maturity / amortization"}</dt>
            <dd>
              {a.decision.maturity_years} / {a.decision.amortization_years}{" "}
              {zh ? "年" : "years"}
            </dd>
          </div>
          <div>
            <dt>{zh ? "擔保" : "Collateral"}</dt>
            <dd>{structureText(a.decision.collateral, zh)}</dd>
          </div>
          <div>
            <dt>{zh ? "保證" : "Guarantee"}</dt>
            <dd>{structureText(a.decision.guarantee, zh)}</dd>
          </div>
          <div>
            <dt>{zh ? "利率類型／基準利率" : "Rate type / base rate"}</dt>
            <dd>
              {zh
                ? a.case.request.rate_type === "fixed"
                  ? "固定"
                  : "浮動"
                : a.case.request.rate_type}{" "}
              · {(Number(a.pricing.reference_base_rate) * 100).toFixed(2)}%
            </dd>
          </div>
          <div>
            <dt>{zh ? "風險利差" : "Risk-grade spread"}</dt>
            <dd>{a.pricing.risk_grade_spread_bps} bps</dd>
          </div>
          <div>
            <dt>{zh ? "示意全包利率" : "Indicative all-in rate"}</dt>
            <dd>
              {(Number(a.pricing.indicative_all_in_rate) * 100).toFixed(2)}%
            </dd>
          </div>
          <div>
            <dt>{zh ? "承諾費／前端費" : "Commitment / upfront fee"}</dt>
            <dd>
              {a.pricing.commitment_fee_bps ?? "—"} /{" "}
              {a.pricing.upfront_fee_bps ?? "—"} bps
            </dd>
          </div>
        </dl>
      </div>
      <p className="synthetic-notice">
        {zh
          ? "僅供教育用途的示意定價；不代表即時市場報價、銀行承諾或授信建議。"
          : a.pricing.disclaimer}
      </p>
      <div className="two-column">
        <article className="panel">
          <h3>{zh ? "決策理由" : "Decision rationale"}</h3>
          <ol>
            {rationale.map((x) => (
              <li key={x}>{x}</li>
            ))}
          </ol>
          <h3>{zh ? "還款來源" : "Repayment sources"}</h3>
          <p>
            {zh
              ? `主要：${a.decision.primary_repayment_source === "Operating cash flow" ? "營運現金流" : a.decision.primary_repayment_source}`
              : `Primary: ${a.decision.primary_repayment_source}`}
          </p>
        </article>
        <article className="panel copper">
          <h3>{zh ? "核准條件與監控" : "Conditions and monitoring"}</h3>
          <ul>
            {a.decision.conditions.map((x) => (
              <li key={x}>{conditionText(x, zh)}</li>
            ))}
          </ul>
        </article>
      </div>
      <article className="panel table-panel" tabIndex={0}>
        <h3>{zh ? "政策檢查" : "Policy checks"}</h3>
        <table>
          <thead>
            <tr>
              <th>{zh ? "規則" : "Rule"}</th>
              <th>{zh ? "實際" : "Actual"}</th>
              <th>{zh ? "門檻" : "Threshold"}</th>
              <th>{zh ? "結果" : "Result"}</th>
              <th>{zh ? "例外" : "Exception"}</th>
            </tr>
          </thead>
          <tbody>
            {a.policy_checks.map((item) => (
              <tr key={item.key}>
                <td>{policyCheckLabel(item.key, zh)}</td>
                <td>
                  {zh && /[A-Za-z]{4,}/.test(item.actual)
                    ? "依案件輸入"
                    : item.actual}
                </td>
                <td>
                  {zh && /[A-Za-z]{4,}/.test(item.threshold)
                    ? "依版本化政策"
                    : item.threshold}
                </td>
                <td>{uiStatus(item.status, zh)}</td>
                <td>
                  {item.exception_allowed
                    ? zh
                      ? "可申請"
                      : "Allowed"
                    : zh
                      ? "不允許"
                      : "No"}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </article>
    </>
  );
}

function Memo({
  a,
  language,
  onDownload,
}: {
  a: Analysis;
  language: Language;
  onDownload: (detailed: boolean) => Promise<void>;
}) {
  const zh = language === "zh-TW";
  const [busy, setBusy] = useState<"executive" | "detailed" | null>(null);
  const [error, setError] = useState("");
  async function download(detailed: boolean) {
    setBusy(detailed ? "detailed" : "executive");
    setError("");
    try {
      await onDownload(detailed);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : String(cause));
    } finally {
      setBusy(null);
    }
  }
  const sections = zh ? zhMemoSections(a) : a.memo_sections;
  return (
    <article className="memo-paper">
      <header>
        <p>{zh ? "NORTHSTAR 授信備忘錄" : "NORTHSTAR CREDIT MEMORANDUM"}</p>
        <h2>{a.case.borrower.legal_name}</h2>
        <span>{a.case.data_as_of}</span>
      </header>
      {Object.entries(sections).map(([title, paragraphs]) => (
        <section key={title}>
          <h3>{memoTitle(title, zh)}</h3>
          {paragraphs.map((p, paragraphIndex) => (
            <p key={`${title}-${paragraphIndex}`}>{memoParagraph(p, zh)}</p>
          ))}
        </section>
      ))}
      <footer>
        <small>Input hash: {a.input_hash}</small>
      </footer>
      {error && (
        <p className="error" role="alert">
          {error}
        </p>
      )}
      <div className="memo-actions">
        <button
          className="button secondary"
          onClick={() => download(false)}
          disabled={busy !== null}
        >
          {busy === "executive" ? (
            <LoaderCircle className="spin" size={17} />
          ) : (
            <Download size={17} />
          )}{" "}
          {zh ? "一頁式 PDF" : "One-page PDF"}
        </button>
        <button
          className="button primary"
          onClick={() => download(true)}
          disabled={busy !== null}
        >
          {busy === "detailed" ? (
            <LoaderCircle className="spin" size={17} />
          ) : (
            <Download size={17} />
          )}{" "}
          {zh ? "詳細 PDF" : "Detailed PDF"}
        </button>
      </div>
    </article>
  );
}

export function CaseWorkspace({
  caseId,
  section,
  language,
}: {
  caseId: string;
  section: string;
  language: Language;
}) {
  const root = prefix(language);
  const locale = language === "en" ? "en-US" : "zh-TW";
  const zh = language === "zh-TW";
  const [data, setData] = useState<CaseEnvelope | null>(null);
  const [error, setError] = useState("");
  const [mode, setMode] = useState("guided");
  const [drawer, setDrawer] = useState(false);
  const [running, setRunning] = useState(false);
  const drawerRef = useRef<HTMLElement>(null);
  const idx = Math.max(
    0,
    workspaceSections.indexOf(section as (typeof workspaceSections)[number]),
  );
  useEffect(() => {
    api
      .getCase(caseId)
      .then(setData)
      .catch((cause) =>
        setError(cause instanceof Error ? cause.message : String(cause)),
      );
  }, [caseId]);
  useEffect(() => {
    const stored = window.localStorage.getItem("northstar-workspace-mode");
    if (stored === "analyst") setMode(stored);
  }, []);
  useEffect(() => {
    window.localStorage.setItem("northstar-workspace-mode", mode);
  }, [mode]);
  useEffect(() => {
    if (!drawer) return;
    document.body.style.overflow = "hidden";
    drawerRef.current?.querySelector<HTMLElement>("a,button")?.focus();
    function key(event: KeyboardEvent) {
      if (event.key === "Escape") setDrawer(false);
      if (event.key === "Tab" && drawerRef.current) {
        const focusable = Array.from(
          drawerRef.current.querySelectorAll<HTMLElement>(
            "a,button:not([disabled])",
          ),
        );
        if (focusable.length === 0) return;
        const first = focusable[0],
          last = focusable[focusable.length - 1];
        if (event.shiftKey && document.activeElement === first) {
          event.preventDefault();
          last.focus();
        } else if (!event.shiftKey && document.activeElement === last) {
          event.preventDefault();
          first.focus();
        }
      }
    }
    window.addEventListener("keydown", key);
    return () => {
      document.body.style.overflow = "";
      window.removeEventListener("keydown", key);
    };
  }, [drawer]);
  async function save(value: CaseInput, rerun = false) {
    const updated = await api.updateCase(caseId, value);
    setData(updated);
    if (rerun) {
      setRunning(true);
      try {
        await api.analyze(caseId);
        setData(await api.getCase(caseId));
      } finally {
        setRunning(false);
      }
    }
  }
  async function run() {
    setRunning(true);
    setError("");
    try {
      await api.analyze(caseId);
      setData(await api.getCase(caseId));
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : String(cause));
    } finally {
      setRunning(false);
    }
  }
  const nav = useMemo(() => {
    if (!data) return null;
    return (
      <>
        <Link className="back" href={`${root}/app/cases`}>
          <ArrowLeft size={16} />
          {zh ? "所有案件" : "All cases"}
        </Link>
        <div className="borrower-mark">
          <span>
            {data.input.borrower.legal_name.slice(0, 2).toUpperCase()}
          </span>
          <div>
            <strong>{data.input.borrower.legal_name}</strong>
            <small>
              {uiStatus(data.status, zh)} · v{data.version}
            </small>
          </div>
        </div>
        <nav aria-label={zh ? "授信工作流程" : "Underwriting workflow"}>
          {workspaceSections.map((item, i) => (
            <Link
              key={item}
              className={i === idx ? "active" : ""}
              href={`${root}/app/cases/${caseId}/${item}`}
              onClick={() => setDrawer(false)}
            >
              <span>{String(i + 1).padStart(2, "0")}</span>
              {labels[language][i]}
            </Link>
          ))}
        </nav>
        <div className="mode-switch">
          <p>
            <SlidersHorizontal size={15} />
            {zh ? "工作區模式" : "Workspace mode"}
          </p>
          <div>
            <button
              className={mode === "guided" ? "active" : ""}
              onClick={() => setMode("guided")}
            >
              {zh ? "引導" : "Guided"}
            </button>
            <button
              className={mode === "analyst" ? "active" : ""}
              onClick={() => setMode("analyst")}
            >
              {zh ? "分析師" : "Analyst"}
            </button>
          </div>
        </div>
      </>
    );
  }, [caseId, data, idx, language, mode, root, zh]);
  if (error)
    return (
      <>
        <Header language={language} />
        <main className="center-state">
          <CircleAlert />
          <h2>{zh ? "無法載入此案件" : "This case could not be loaded"}</h2>
          <p>{error}</p>
          <Link href={`${root}/app/cases`}>
            {zh ? "返回案件列表" : "Return to cases"}
          </Link>
        </main>
      </>
    );
  if (!data)
    return (
      <main className="center-state">
        <LoaderCircle className="spin" />
        <p>{zh ? "載入案件…" : "Loading case…"}</p>
      </main>
    );
  if (!data.analysis)
    return (
      <>
        <Header language={language} />
        <main className="center-state stale-state">
          <RefreshCw />
          <h2>
            {data.status === "stale"
              ? zh
                ? "輸入已變更，分析已過期"
                : "Inputs changed; analysis is stale"
              : zh
                ? "草稿尚未分析"
                : "Draft has not been analyzed"}
          </h2>
          <p>
            {zh
              ? "重新執行模型後，評等、容量、情境、契約與備忘錄才會更新。"
              : "Rerun the model to update grade, capacity, scenarios, covenants, and memo."}
          </p>
          <button className="button primary" onClick={run} disabled={running}>
            {running ? (
              <LoaderCircle className="spin" size={16} />
            ) : (
              <RefreshCw size={16} />
            )}{" "}
            {zh ? "重新執行授信分析" : "Run credit analysis"}
          </button>
          <Link href={`${root}/app/cases`}>
            {zh ? "返回案件列表" : "Back to cases"}
          </Link>
        </main>
      </>
    );
  const a = data.analysis;
  return (
    <>
      <Header language={language} />
      <div className="workspace-shell">
        <aside>{nav}</aside>
        {drawer && (
          <>
            <button
              className="drawer-backdrop"
              aria-label={zh ? "關閉選單" : "Close menu"}
              onClick={() => setDrawer(false)}
            />
            <aside
              className="mobile-drawer"
              ref={drawerRef}
              role="dialog"
              aria-modal="true"
              aria-label={zh ? "授信工作流程" : "Underwriting workflow"}
            >
              <button className="drawer-close" onClick={() => setDrawer(false)}>
                <X size={19} />
                <span className="sr-only">{zh ? "關閉" : "Close"}</span>
              </button>
              {nav}
            </aside>
          </>
        )}
        <main className="workspace">
          <div className="workspace-top">
            <div>
              <p className="section-name">{labels[language][idx]}</p>
              <h1>{questions[language][idx]}</h1>
            </div>
            <div className="top-meta">
              <span>
                {zh ? "計算日期" : "Calculated"}
                <strong>
                  {new Date(a.calculated_at).toLocaleDateString(locale)}
                </strong>
              </span>
              <button
                className="mobile-menu-button"
                aria-expanded={drawer}
                aria-label={
                  zh ? "開啟工作流程選單" : "Open workflow navigation"
                }
                onClick={() => setDrawer(true)}
              >
                <Menu size={18} />
              </button>
            </div>
          </div>
          {workspaceSections[idx] === "overview" && (
            <Overview a={a} language={language} locale={locale} />
          )}{" "}
          {workspaceSections[idx] === "inputs" && (
            <Inputs
              key={data.version}
              input={data.input}
              language={language}
              locale={locale}
              mode={mode}
              onSave={(value) => save(value)}
            />
          )}{" "}
          {workspaceSections[idx] === "financials" && (
            <Financials a={a} language={language} locale={locale} mode={mode} />
          )}{" "}
          {workspaceSections[idx] === "capacity" && (
            <Capacity a={a} language={language} locale={locale} />
          )}{" "}
          {workspaceSections[idx] === "facility" && (
            <FacilityProtectionPage
              analysis={a}
              language={language}
              locale={locale}
            />
          )}{" "}
          {workspaceSections[idx] === "risk" && (
            <Risk a={a} language={language} mode={mode} />
          )}{" "}
          {workspaceSections[idx] === "stress" && (
            <Stress
              a={a}
              language={language}
              locale={locale}
              onSave={(value) => save(value, true)}
            />
          )}{" "}
          {workspaceSections[idx] === "decision" && (
            <Decision a={a} language={language} locale={locale} />
          )}{" "}
          {workspaceSections[idx] === "memo" && (
            <Memo
              a={a}
              language={language}
              onDownload={(detailed) =>
                downloadMemo(caseId, language, detailed)
              }
            />
          )}
          <GlossaryDrawer language={language} />
          <AuditHistory
            caseId={caseId}
            currentVersion={data.version}
            language={language}
            onRestored={async () => setData(await api.getCase(caseId))}
          />
        </main>
      </div>
    </>
  );
}
