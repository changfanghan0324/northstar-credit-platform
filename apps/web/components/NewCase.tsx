"use client";

import {
  ArrowLeft,
  ArrowRight,
  Check,
  LoaderCircle,
  Save,
  ShieldAlert,
} from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useRef, useState } from "react";
import { Header } from "./Header";
import { api, money } from "@/lib/api";
import { type Language, prefix } from "@/lib/i18n";
import { formatMoneyInput, parseMoneyInput } from "@/lib/money";
import type {
  CaseInput,
  DebtInstrument,
  Money,
  ScenarioInput,
} from "@/lib/types";

type ValidationPreview = {
  valid: boolean;
  missing: string[];
  warnings: string[];
  estimated_confidence: number;
};

const steps = [
  "Borrower",
  "Facility",
  "Financials",
  "Debt",
  "Business risk",
  "Scenarios",
  "Review",
];
const moneyFields = [
  "revenue",
  "prior_revenue",
  "ebit",
  "depreciation_amortization",
  "positive_ebitda_adjustments",
  "negative_ebitda_adjustments",
  "prior_adjusted_ebitda",
  "cfo",
  "capex",
  "maintenance_capex",
  "cash_taxes",
  "working_capital_increase",
  "mandatory_pension",
  "cash_interest",
  "scheduled_principal",
  "short_term_borrowings",
  "current_maturities",
  "long_term_debt",
  "finance_leases",
  "unrestricted_cash",
  "current_assets",
  "current_liabilities",
  "accounts_receivable",
  "inventory",
  "other_current_assets",
  "undrawn_revolver",
  "minimum_operating_cash",
  "monthly_stressed_cash_burn",
  "equity",
  "total_liabilities",
  "total_assets",
  "secured_debt",
  "contractual_rent",
  "net_income",
  "collateral_capacity",
] as const;

const fieldLabels: Record<string, [string, string]> = {
  revenue: ["Revenue", "營收"],
  prior_revenue: ["Prior-year revenue", "前期營收"],
  ebit: ["Operating profit (EBIT)", "營業利益（EBIT）"],
  depreciation_amortization: ["Depreciation and amortization", "折舊與攤銷"],
  cfo: ["Cash from operations", "營業現金流"],
  maintenance_capex: ["Maintenance capital spending", "維持性資本支出"],
  cash_taxes: ["Cash taxes", "現金稅負"],
  working_capital_increase: ["Working-capital investment", "營運資金增加"],
  cash_interest: ["Annual cash interest", "年度現金利息"],
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
  positive_ebitda_adjustments: [
    "Positive EBITDA adjustments",
    "正向 EBITDA 調整",
  ],
  negative_ebitda_adjustments: [
    "Negative EBITDA adjustments",
    "負向 EBITDA 調整",
  ],
  prior_adjusted_ebitda: ["Prior adjusted EBITDA", "前期調整後 EBITDA"],
  capex: ["Total capital spending", "總資本支出"],
  mandatory_pension: ["Mandatory pension contributions", "必要退休金提撥"],
  other_current_assets: ["Other current assets", "其他流動資產"],
  monthly_stressed_cash_burn: [
    "Monthly stressed cash burn",
    "每月壓力現金消耗",
  ],
  equity: ["Equity", "權益"],
  total_liabilities: ["Total liabilities", "總負債"],
  total_assets: ["Total assets", "總資產"],
  secured_debt: ["Secured debt", "有擔保債務"],
  contractual_rent: ["Contractual rent", "合約租金"],
  net_income: ["Net income", "淨利"],
};

function scenarioNameForWizard(value: string, zh: boolean) {
  return zh
    ? (
        { base: "基準", downside: "下行情境", severe: "嚴重壓力" } as Record<
          string,
          string
        >
      )[value]
    : value[0].toUpperCase() + value.slice(1);
}
function scenarioFieldLabel(value: string, zh: boolean) {
  const labels = zh
    ? {
        revenue_growth: "第一年營收衝擊",
        subsequent_growth: "後續年度成長",
        ebitda_margin_change: "EBITDA 利潤率變化",
        rate_shock: "利率衝擊",
        working_capital_pct_revenue: "營運資金占營收",
        maintenance_capex_pct_revenue: "維持性資本支出占營收",
      }
    : {
        revenue_growth: "Year 1 revenue shock",
        subsequent_growth: "Subsequent annual growth",
        ebitda_margin_change: "EBITDA margin change",
        rate_shock: "Interest-rate shock",
        working_capital_pct_revenue: "Working capital as % of revenue",
        maintenance_capex_pct_revenue: "Maintenance capex as % of revenue",
      };
  return (labels as Record<string, string>)[value] ?? value;
}
function riskFieldLabel(value: string, zh: boolean) {
  const labels = zh
    ? {
        industry: "產業在景氣壓力下的韌性如何？",
        competitive_position: "公司的競爭地位有多穩固？",
        customer_concentration: "客戶集中度風險管理得如何？",
        diversification: "收入與產品是否充分多元？",
        management_policy: "管理團隊與財務政策是否可靠？",
        governance_event: "治理與重大事件風險是否受控？",
      }
    : {
        industry: "How resilient is the industry under stress?",
        competitive_position: "How durable is the competitive position?",
        customer_concentration: "How well managed is customer concentration?",
        diversification: "How diversified are revenue and products?",
        management_policy: "How reliable are management and financial policy?",
        governance_event: "How controlled are governance and event risks?",
      };
  return (labels as Record<string, string>)[value] ?? value;
}

export function NewCase({ language }: { language: Language }) {
  const zh = language === "zh-TW";
  const root = prefix(language);
  const router = useRouter();
  const [input, setInput] = useState<CaseInput | null>(null);
  const [step, setStep] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [review, setReview] = useState<ValidationPreview | null>(null);
  const [template, setTemplate] = useState("stable-manufacturer");
  const [entryMode, setEntryMode] = useState<"guided" | "analyst">("guided");
  const initialized = useRef(false);
  const draftKey = `northstar-case-draft-${language}`;

  useEffect(() => {
    if (!initialized.current) {
      initialized.current = true;
      const saved = window.sessionStorage.getItem(draftKey);
      if (saved) {
        try {
          const parsed = JSON.parse(saved) as CaseInput;
          Promise.resolve(parsed).then(setInput);
          return;
        } catch {
          window.sessionStorage.removeItem(draftKey);
        }
      }
    }
    api
      .demoTemplate(template)
      .then((value) => setInput(structuredClone(value)))
      .catch((e) => setError(String(e)));
  }, [draftKey, template]);
  useEffect(() => {
    if (input) window.sessionStorage.setItem(draftKey, JSON.stringify(input));
  }, [draftKey, input]);
  useEffect(() => {
    if (step === 6 && input) {
      api
        .validateInput(input)
        .then(setReview)
        .catch((cause) =>
          setError(cause instanceof Error ? cause.message : String(cause)),
        );
    }
  }, [input, step]);
  function patchInput(update: Partial<CaseInput>) {
    setInput((current) => (current ? { ...current, ...update } : current));
  }
  function patchBorrower(key: keyof CaseInput["borrower"], value: string) {
    if (input) patchInput({ borrower: { ...input.borrower, [key]: value } });
  }
  function patchRequest(key: keyof CaseInput["request"], value: unknown) {
    if (input) patchInput({ request: { ...input.request, [key]: value } });
  }
  function percentDisplay(value: string | number): string {
    if (entryMode === "analyst") return String(value);
    const numeric = Number(value);
    return Number.isFinite(numeric)
      ? `${(numeric * 100).toFixed(2).replace(/\.00$/, "")}%`
      : `${value}%`;
  }
  function percentValue(value: string): string {
    if (entryMode === "analyst") return value;
    const numeric = Number(value.trim().replace(/%$/, ""));
    return Number.isFinite(numeric) ? String(numeric / 100) : value;
  }
  function parsedAmount(value: string, current: Money): number | null {
    const parsed = parseMoneyInput(
      value,
      current.minor_unit_exponent,
      language,
    );
    if (!parsed.ok) {
      setError(parsed.message);
      return null;
    }
    setError("");
    return parsed.amountMinor;
  }
  function patchMoney(key: string, value: string) {
    if (!input) return;
    const current = input.financials[key] as Money;
    const amountMinor = parsedAmount(value, current);
    if (amountMinor === null) return;
    patchInput({
      financials: {
        ...input.financials,
        [key]: {
          ...current,
          amount_minor: amountMinor,
        },
      },
    });
  }
  function patchRisk(key: string, value: string | string[]) {
    if (!input) return;
    const existing = input.business_risk.factor_evidence?.[key];
    patchInput({
      business_risk: {
        ...input.business_risk,
        [key]: value,
        ...(typeof value === "string" && existing
          ? {
              factor_evidence: {
                ...input.business_risk.factor_evidence,
                [key]: { ...existing, score: value },
              },
            }
          : {}),
      },
    });
  }
  function patchRiskEvidence(key: string, update: Record<string, string>) {
    if (!input) return;
    const current = input.business_risk.factor_evidence?.[key];
    if (!current) return;
    const next = {
      ...current,
      ...update,
      last_updated: new Date().toISOString(),
    };
    patchInput({
      business_risk: {
        ...input.business_risk,
        ...(update.score ? { [key]: update.score } : {}),
        factor_evidence: {
          ...input.business_risk.factor_evidence,
          [key]: next,
        },
      },
    });
  }
  function patchScenario(
    name: keyof CaseInput["scenarios"],
    key: keyof ScenarioInput,
    value: string,
  ) {
    if (!input) return;
    patchInput({
      scenarios: {
        ...input.scenarios,
        [name]: { ...input.scenarios[name], [key]: value },
      },
    });
  }
  function addDebt() {
    if (!input) return;
    const blank: DebtInstrument = {
      name: zh ? "現有債務" : "Existing debt",
      principal: { ...input.request.amount, amount_minor: 0 },
      annual_rate: "0.06",
      rate_type: "fixed",
      spread: "0",
      rate_floor: "0",
      scheduled_amortization: { ...input.request.amount, amount_minor: 0 },
      maturity_year: 3,
      secured: false,
      seniority: "Senior",
      collateral: "None",
      schedule_completeness: "unspecified",
    };
    patchInput({ debt_instruments: [...input.debt_instruments, blank] });
  }
  function patchDebt(index: number, update: Partial<DebtInstrument>) {
    if (!input) return;
    patchInput({
      debt_instruments: input.debt_instruments.map((item, i) =>
        i === index ? { ...item, ...update } : item,
      ),
    });
  }

  async function run() {
    if (!input) return;
    setLoading(true);
    setError("");
    try {
      const preview = await api.validateInput(input);
      if (!preview.valid)
        throw new Error(
          `${zh ? "缺少或無效的關鍵輸入" : "Missing or invalid critical inputs"}: ${preview.missing.join(", ")}`,
        );
      const payload = {
        ...input,
        slug: `custom-${crypto.randomUUID().slice(0, 8)}`,
      };
      const created = await api.createCase(payload);
      await api.analyze(created.id);
      window.sessionStorage.removeItem(draftKey);
      router.push(`${root}/app/cases/${created.id}/overview`);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : String(cause));
      setLoading(false);
    }
  }
  if (!input)
    return (
      <>
        <Header language={language} />
        <main className="center-state">
          <LoaderCircle className="spin" />
          <p>
            {zh
              ? "載入安全的合成範本…"
              : "Loading a safe synthetic starting point…"}
          </p>
        </main>
      </>
    );

  const locale = zh ? "zh-TW" : "en-US";
  const requiredChecks = [
    Boolean(input.borrower.legal_name.trim()),
    Boolean(input.borrower.description.trim()),
    input.request.amount.amount_minor > 0,
    Boolean(input.request.purpose.trim()),
    Number(input.request.annual_rate) > 0,
    input.request.maturity_years > 0,
    (input.financials.revenue as Money).amount_minor > 0,
    (input.financials.cfo as Money).amount_minor !== 0,
    (input.financials.cash_interest as Money).amount_minor >= 0,
    (input.financials.scheduled_principal as Money).amount_minor >= 0,
    input.business_risk.strengths.length > 0,
    input.business_risk.risks.length > 0,
  ];
  const requiredCompleted = requiredChecks.filter(Boolean).length;
  const completion = Math.round(
    (requiredCompleted / requiredChecks.length) * 100,
  );
  return (
    <>
      <Header language={language} />
      <main className="new-case wizard">
        <Link className="back" href={`${root}/app/cases`}>
          <ArrowLeft size={16} />
          {zh ? "返回案件列表" : "Back to cases"}
        </Link>
        <div className="privacy-warning">
          <ShieldAlert size={20} />
          <div>
            <strong>
              {zh
                ? "請勿輸入機密資訊"
                : "Do not enter confidential information"}
            </strong>
            <span>
              {zh
                ? "此公開工具僅供合成資料與教育示範。案件在匿名工作階段中最多保留七天。"
                : "This public tool is for synthetic educational data only. Anonymous cases are retained for up to seven days."}
            </span>
          </div>
        </div>
        <div className="wizard-head">
          <div>
            <h1>{zh ? "建立自訂授信案件" : "Create a custom credit case"}</h1>
            <p>
              {zh
                ? "逐步建立完整、可編輯且可重新計算的分析。"
                : "Build a complete, editable analysis and review it before calculation."}
            </p>
          </div>
          <div className="wizard-controls">
            <label>
              {zh ? "輸入模式" : "Entry mode"}
              <select
                value={entryMode}
                onChange={(event) =>
                  setEntryMode(event.target.value as "guided" | "analyst")
                }
              >
                <option value="guided">
                  {zh ? "引導模式（基本欄位）" : "Guided (essential fields)"}
                </option>
                <option value="analyst">
                  {zh ? "分析師模式（完整明細）" : "Analyst (full detail)"}
                </option>
              </select>
            </label>
            <label>
              {zh ? "合成起始範本" : "Synthetic starting template"}
              <select
                value={template}
                onChange={(event) => setTemplate(event.target.value)}
              >
                <option value="stable-manufacturer">
                  {zh ? "穩健製造商" : "Stable manufacturer"}
                </option>
                <option value="cyclical-distributor">
                  {zh ? "週期性經銷商" : "Cyclical distributor"}
                </option>
                <option value="software-services">
                  {zh ? "軟體服務公司" : "Software services"}
                </option>
              </select>
            </label>
          </div>
        </div>
        <div className="wizard-progress">
          <span>
            {zh
              ? `必要欄位 ${requiredCompleted}/${requiredChecks.length}（${completion}%）`
              : `${requiredCompleted}/${requiredChecks.length} required fields (${completion}%)`}
          </span>
          <span>
            {zh
              ? "草稿已自動儲存於此瀏覽器工作階段"
              : "Draft autosaved in this browser session"}
          </span>
        </div>
        <ol
          className="stepper"
          aria-label={zh ? "建案進度" : "Case setup progress"}
        >
          {steps.map((name, index) => (
            <li
              key={name}
              className={index === step ? "active" : index < step ? "done" : ""}
            >
              <button type="button" onClick={() => setStep(index)}>
                <span>{index < step ? <Check size={14} /> : index + 1}</span>
                {zh
                  ? [
                      "借款人",
                      "授信結構",
                      "財務資料",
                      "債務",
                      "營運風險",
                      "情境",
                      "檢查",
                    ][index]
                  : name}
              </button>
            </li>
          ))}
        </ol>
        <div className="wizard-status" aria-live="polite" role="status">
          {review
            ? review.valid
              ? zh
                ? "輸入驗證通過"
                : "Input validation passed"
              : zh
                ? `尚缺 ${review.missing.length} 項必要資料`
                : `${review.missing.length} required items remain`
            : zh
              ? "完成必要欄位後進行驗證"
              : "Complete required fields before validation"}
        </div>
        <section className="wizard-panel">
          {step === 0 && (
            <>
              <h2>{zh ? "借款人是誰？" : "Who is the borrower?"}</h2>
              <div className="input-grid">
                <label>
                  {zh ? "公司名稱" : "Legal company name"}
                  <input
                    required
                    value={input.borrower.legal_name}
                    onChange={(e) =>
                      patchBorrower("legal_name", e.target.value)
                    }
                  />
                </label>
                <label>
                  {zh ? "產業" : "Industry"}
                  <input
                    value={input.borrower.industry}
                    onChange={(e) => patchBorrower("industry", e.target.value)}
                  />
                </label>
                <label>
                  {zh ? "總部" : "Headquarters"}
                  <input
                    value={input.borrower.headquarters}
                    onChange={(e) =>
                      patchBorrower("headquarters", e.target.value)
                    }
                  />
                </label>
                <label>
                  {zh ? "資料基準日" : "Data as of"}
                  <input
                    type="date"
                    value={input.data_as_of}
                    onChange={(e) => patchInput({ data_as_of: e.target.value })}
                  />
                </label>
                <label className="wide">
                  {zh ? "業務說明" : "Business description"}
                  <textarea
                    value={input.borrower.description}
                    onChange={(e) =>
                      patchBorrower("description", e.target.value)
                    }
                  />
                </label>
              </div>
            </>
          )}
          {step === 1 && (
            <>
              <h2>
                {zh
                  ? "借款人申請什麼授信？"
                  : "What facility is being requested?"}
              </h2>
              <div className="input-grid">
                <label>
                  {zh ? "申請額（美元）" : "Requested amount (USD)"}
                  <input
                    inputMode="decimal"
                    value={formatMoneyInput(input.request.amount)}
                    onChange={(e) => {
                      const amountMinor = parsedAmount(
                        e.target.value,
                        input.request.amount,
                      );
                      if (amountMinor === null) return;
                      patchRequest("amount", {
                        ...input.request.amount,
                        amount_minor: amountMinor,
                      });
                    }}
                  />
                </label>
                <label>
                  {zh ? "用途" : "Purpose"}
                  <input
                    value={input.request.purpose}
                    onChange={(e) => patchRequest("purpose", e.target.value)}
                  />
                </label>
                <label>
                  {zh ? "額度類型" : "Facility type"}
                  <select
                    value={input.request.facility_type}
                    onChange={(e) =>
                      patchRequest("facility_type", e.target.value)
                    }
                  >
                    <option value="term_loan">
                      {zh ? "定期貸款" : "Term loan"}
                    </option>
                    <option value="revolver">
                      {zh ? "循環信用額度" : "Revolver"}
                    </option>
                    <option value="asset_based">
                      {zh ? "資產基礎融資" : "Asset-based"}
                    </option>
                  </select>
                </label>
                <label>
                  {zh ? "擔保結構" : "Security"}
                  <select
                    value={input.request.security_type}
                    onChange={(e) =>
                      patchRequest("security_type", e.target.value)
                    }
                  >
                    <option value="secured">{zh ? "有擔保" : "Secured"}</option>
                    <option value="unsecured">
                      {zh ? "無擔保" : "Unsecured"}
                    </option>
                    <option value="asset_based">
                      {zh ? "資產基礎" : "Asset-based"}
                    </option>
                  </select>
                </label>
                <label>
                  {zh ? "利率類型" : "Rate type"}
                  <select
                    value={input.request.rate_type}
                    onChange={(e) => patchRequest("rate_type", e.target.value)}
                  >
                    <option value="fixed">{zh ? "固定" : "Fixed"}</option>
                    <option value="floating">{zh ? "浮動" : "Floating"}</option>
                  </select>
                </label>
                <label>
                  {zh
                    ? entryMode === "guided"
                      ? "年利率（百分比）"
                      : "年利率（小數）"
                    : entryMode === "guided"
                      ? "Annual rate (%)"
                      : "Annual rate (decimal)"}
                  <input
                    inputMode="decimal"
                    value={percentDisplay(input.request.annual_rate)}
                    onChange={(e) =>
                      patchRequest("annual_rate", percentValue(e.target.value))
                    }
                  />
                </label>
                <label>
                  {zh ? "到期年數" : "Maturity years"}
                  <input
                    type="number"
                    min="1"
                    max="30"
                    value={input.request.maturity_years}
                    onChange={(e) =>
                      patchRequest(
                        "maturity_years",
                        Number.parseInt(e.target.value, 10),
                      )
                    }
                  />
                </label>
                <label>
                  {zh ? "攤還年數" : "Amortization years"}
                  <input
                    type="number"
                    min="1"
                    max="30"
                    value={
                      input.request.amortization_years ??
                      input.request.maturity_years
                    }
                    onChange={(e) =>
                      patchRequest(
                        "amortization_years",
                        Number.parseInt(e.target.value, 10),
                      )
                    }
                  />
                </label>
                <label>
                  {zh ? "保證" : "Guarantee"}
                  <input
                    value={input.request.guarantee}
                    onChange={(e) => patchRequest("guarantee", e.target.value)}
                  />
                </label>
                <label>
                  {zh ? "主要還款來源" : "Primary repayment source"}
                  <input
                    value={input.request.primary_repayment_source}
                    onChange={(e) =>
                      patchRequest("primary_repayment_source", e.target.value)
                    }
                  />
                </label>
              </div>
            </>
          )}
          {step === 2 && (
            <>
              <h2>
                {zh
                  ? "借款人如何營運並產生現金？"
                  : "How has the borrower performed and generated cash?"}
              </h2>
              <p className="question-help">
                {zh
                  ? "輸入 LTM 與比較期的核心損益、現金流及資產負債表資料。所有金額均為美元。"
                  : "Enter the core LTM and comparative income statement, cash-flow, and balance-sheet values. All amounts are USD."}
              </p>
              <div className="input-grid">
                {moneyFields
                  .slice(0, 9)
                  .filter((key) =>
                    entryMode === "analyst"
                      ? true
                      : [
                          "revenue",
                          "prior_revenue",
                          "ebit",
                          "depreciation_amortization",
                          "cfo",
                          "maintenance_capex",
                        ].includes(key),
                  )
                  .map((key) => (
                    <label key={key}>
                      {zh ? fieldLabels[key][1] : fieldLabels[key][0]}
                      <input
                        inputMode="decimal"
                        value={formatMoneyInput(input.financials[key] as Money)}
                        onChange={(e) => patchMoney(key, e.target.value)}
                      />
                    </label>
                  ))}
                <label>
                  {zh
                    ? entryMode === "guided"
                      ? "可用現金比例（百分比）"
                      : "可用現金比例（小數）"
                    : entryMode === "guided"
                      ? "Cash availability (%)"
                      : "Cash availability factor (decimal)"}
                  <input
                    inputMode="decimal"
                    value={percentDisplay(
                      String(input.financials.cash_availability_factor),
                    )}
                    onChange={(e) =>
                      patchInput({
                        financials: {
                          ...input.financials,
                          cash_availability_factor: percentValue(e.target.value),
                        },
                      })
                    }
                  />
                </label>
                <label>
                  {zh
                    ? entryMode === "guided"
                      ? "現金稅率（百分比）"
                      : "現金稅率（小數）"
                    : entryMode === "guided"
                      ? "Cash tax rate (%)"
                      : "Cash tax rate (decimal)"}
                  <input
                    inputMode="decimal"
                    value={percentDisplay(String(input.financials.tax_rate))}
                    onChange={(e) =>
                      patchInput({
                        financials: {
                          ...input.financials,
                          tax_rate: percentValue(e.target.value),
                        },
                      })
                    }
                  />
                </label>
              </div>
            </>
          )}
          {step === 3 && (
            <>
              <h2>
                {zh
                  ? "現有及新增債務如何償還？"
                  : "How will existing and new debt be repaid?"}
              </h2>
              <p className="question-help">
                {zh
                  ? "先核對資產負債表與現金流的債務總額，再加入每項債務工具供利息、攤還與到期分析使用。"
                  : "Reconcile aggregate debt first, then add each instrument used for interest, amortization, and maturity analysis."}
              </p>
              <div className="input-grid">
                {moneyFields
                  .slice(9)
                  .filter((key) =>
                    entryMode === "analyst"
                      ? true
                      : [
                          "cash_interest",
                          "scheduled_principal",
                          "long_term_debt",
                          "unrestricted_cash",
                          "current_assets",
                          "current_liabilities",
                          "minimum_operating_cash",
                        ].includes(key),
                  )
                  .map((key) => (
                    <label key={key}>
                      {zh ? fieldLabels[key][1] : fieldLabels[key][0]}
                      <input
                        inputMode="decimal"
                        value={formatMoneyInput(input.financials[key] as Money)}
                        onChange={(e) => patchMoney(key, e.target.value)}
                      />
                    </label>
                  ))}
              </div>
              <h3>{zh ? "債務工具" : "Debt instruments"}</h3>
              {input.debt_instruments.map((item, index) => (
                <fieldset key={`${item.name}-${index}`}>
                  <legend>
                    {zh ? `工具 ${index + 1}` : `Instrument ${index + 1}`}
                  </legend>
                  <div className="input-grid">
                    <label>
                      {zh ? "名稱" : "Name"}
                      <input
                        value={item.name}
                        onChange={(e) =>
                          patchDebt(index, { name: e.target.value })
                        }
                      />
                    </label>
                    <label>
                      {zh ? "本金餘額" : "Principal balance"}
                      <input
                        value={formatMoneyInput(item.principal)}
                        onChange={(e) => {
                          const amountMinor = parsedAmount(
                            e.target.value,
                            item.principal,
                          );
                          if (amountMinor === null) return;
                          patchDebt(index, {
                            principal: {
                              ...item.principal,
                              amount_minor: amountMinor,
                            },
                          });
                        }}
                      />
                    </label>
                    <label>
                      {zh ? "固定／浮動" : "Fixed / floating"}
                      <select
                        value={item.rate_type}
                        onChange={(e) =>
                          patchDebt(index, {
                            rate_type: e.target
                              .value as DebtInstrument["rate_type"],
                          })
                        }
                      >
                        <option value="fixed">{zh ? "固定" : "Fixed"}</option>
                        <option value="floating">
                          {zh ? "浮動" : "Floating"}
                        </option>
                      </select>
                    </label>
                    <label>
                      {zh ? "年利率" : "Annual rate"}
                      <input
                        value={item.annual_rate}
                        onChange={(e) =>
                          patchDebt(index, { annual_rate: e.target.value })
                        }
                      />
                    </label>
                    <label>
                      {zh ? "利差" : "Spread"}
                      <input
                        value={item.spread}
                        onChange={(e) =>
                          patchDebt(index, { spread: e.target.value })
                        }
                      />
                    </label>
                    <label>
                      {zh ? "利率下限" : "Rate floor"}
                      <input
                        value={item.rate_floor}
                        onChange={(e) =>
                          patchDebt(index, { rate_floor: e.target.value })
                        }
                      />
                    </label>
                    <label>
                      {zh ? "年度攤還" : "Annual amortization"}
                      <input
                        value={formatMoneyInput(item.scheduled_amortization)}
                        onChange={(e) => {
                          const amountMinor = parsedAmount(
                            e.target.value,
                            item.scheduled_amortization,
                          );
                          if (amountMinor === null) return;
                          patchDebt(index, {
                            scheduled_amortization: {
                              ...item.scheduled_amortization,
                              amount_minor: amountMinor,
                            },
                          });
                        }}
                      />
                    </label>
                    <label>
                      {zh ? "到期年度" : "Maturity year"}
                      <input
                        type="number"
                        min="1"
                        max="30"
                        value={item.maturity_year}
                        onChange={(e) =>
                          patchDebt(index, {
                            maturity_year: Number.parseInt(e.target.value, 10),
                          })
                        }
                      />
                    </label>
                    <label>
                      {zh ? "排程完整性" : "Schedule completeness"}
                      <select
                        value={item.schedule_completeness}
                        onChange={(e) =>
                          patchDebt(index, {
                            schedule_completeness: e.target
                              .value as DebtInstrument["schedule_completeness"],
                          })
                        }
                      >
                        <option value="unspecified">
                          {zh ? "未聲明（會阻擋）" : "Unspecified (blocks)"}
                        </option>
                        <option value="complete">
                          {zh ? "完整排程" : "Complete schedule"}
                        </option>
                        <option value="partial">
                          {zh ? "部分排程（需殘餘處理）" : "Partial schedule (residual)"}
                        </option>
                      </select>
                    </label>
                    <label>
                      {zh ? "順位" : "Seniority"}
                      <input
                        value={item.seniority}
                        onChange={(e) =>
                          patchDebt(index, { seniority: e.target.value })
                        }
                      />
                    </label>
                    <label>
                      {zh ? "擔保品" : "Collateral"}
                      <input
                        value={item.collateral}
                        onChange={(e) =>
                          patchDebt(index, { collateral: e.target.value })
                        }
                      />
                    </label>
                    <label>
                      <input
                        type="checkbox"
                        checked={item.secured}
                        onChange={(e) =>
                          patchDebt(index, { secured: e.target.checked })
                        }
                      />
                      {zh ? "有擔保" : "Secured"}
                    </label>
                  </div>
                  <button
                    className="button ghost"
                    type="button"
                    onClick={() =>
                      patchInput({
                        debt_instruments: input.debt_instruments.filter(
                          (_, i) => i !== index,
                        ),
                      })
                    }
                  >
                    {zh ? "移除工具" : "Remove instrument"}
                  </button>
                </fieldset>
              ))}
              <button
                className="button secondary"
                type="button"
                onClick={addDebt}
              >
                {zh ? "新增債務工具" : "Add debt instrument"}
              </button>
            </>
          )}
          {step === 4 && (
            <>
              <h2>
                {zh
                  ? "哪些非財務因素可能改變還款能力？"
                  : "Which business risks could change repayment capacity?"}
              </h2>
              <p className="question-help">
                {zh
                  ? "每題以 0–100 評估；分數越高代表風險管理越強。請在優勢與風險欄記錄判斷依據。"
                  : "Assess each question from 0–100; higher means stronger risk management. Record rationale and evidence in strengths and risks."}
              </p>
              <div className="input-grid">
                {[
                  "industry",
                  "competitive_position",
                  "customer_concentration",
                  "diversification",
                  "management_policy",
                  "governance_event",
                ].map((key) => {
                  const evidence = input.business_risk.factor_evidence?.[key];
                  const bandScores: Record<string, string> = {
                    strong: "90",
                    adequate: "75",
                    moderate_concern: "55",
                    weak: "35",
                    severe_concern: "15",
                  };
                  return (
                    <fieldset className="risk-evidence-card" key={key}>
                      <legend>{riskFieldLabel(key, zh)}</legend>
                      <label>
                        {zh ? "評估區間" : "Assessment band"}
                        <select
                          value={evidence?.band ?? "adequate"}
                          onChange={(event) =>
                            patchRiskEvidence(key, {
                              band: event.target.value,
                              score: bandScores[event.target.value],
                            })
                          }
                        >
                          <option value="strong">{zh ? "強" : "Strong"}</option>
                          <option value="adequate">
                            {zh ? "良好" : "Adequate"}
                          </option>
                          <option value="moderate_concern">
                            {zh ? "中度疑慮" : "Moderate concern"}
                          </option>
                          <option value="weak">{zh ? "偏弱" : "Weak"}</option>
                          <option value="severe_concern">
                            {zh ? "嚴重疑慮" : "Severe concern"}
                          </option>
                        </select>
                      </label>
                      {entryMode === "analyst" && (
                        <label>
                          {zh ? "數值分數" : "Numeric score"}
                          <input
                            type="number"
                            min="0"
                            max="100"
                            value={String(input.business_risk[key])}
                            onChange={(event) =>
                              patchRisk(key, event.target.value)
                            }
                          />
                        </label>
                      )}
                      <label className="wide">
                        {zh ? "證據陳述" : "Evidence statement"}
                        <textarea
                          value={evidence?.evidence ?? ""}
                          onChange={(event) =>
                            patchRiskEvidence(key, {
                              evidence: event.target.value,
                            })
                          }
                        />
                      </label>
                      <label>
                        {zh ? "來源" : "Source"}
                        <input
                          value={evidence?.source ?? ""}
                          onChange={(event) =>
                            patchRiskEvidence(key, {
                              source: event.target.value,
                            })
                          }
                        />
                      </label>
                      <label>
                        {zh ? "信心" : "Confidence"}
                        <select
                          value={evidence?.confidence ?? "medium"}
                          onChange={(event) =>
                            patchRiskEvidence(key, {
                              confidence: event.target.value,
                            })
                          }
                        >
                          <option value="high">{zh ? "高" : "High"}</option>
                          <option value="medium">{zh ? "中" : "Medium"}</option>
                          <option value="low">{zh ? "低" : "Low"}</option>
                        </select>
                      </label>
                      <label className="wide">
                        {zh ? "分析師理由" : "Analyst rationale"}
                        <textarea
                          value={evidence?.analyst_rationale ?? ""}
                          onChange={(event) =>
                            patchRiskEvidence(key, {
                              analyst_rationale: event.target.value,
                            })
                          }
                        />
                      </label>
                    </fieldset>
                  );
                })}
                <label className="wide">
                  {zh
                    ? "主要優勢與支持證據（每行一項）"
                    : "Key strengths and supporting evidence (one per line)"}
                  <textarea
                    value={input.business_risk.strengths.join("\n")}
                    onChange={(e) =>
                      patchRisk(
                        "strengths",
                        e.target.value.split("\n").filter(Boolean),
                      )
                    }
                  />
                </label>
                <label className="wide">
                  {zh
                    ? "主要風險與判斷理由（每行一項）"
                    : "Key risks and rationale (one per line)"}
                  <textarea
                    value={input.business_risk.risks.join("\n")}
                    onChange={(e) =>
                      patchRisk(
                        "risks",
                        e.target.value.split("\n").filter(Boolean),
                      )
                    }
                  />
                </label>
              </div>
            </>
          )}
          {step === 5 && (
            <>
              <h2>
                {zh ? "壓力下哪些條件會失效？" : "What breaks under stress?"}
              </h2>
              <div className="scenario-editor">
                {(["base", "downside", "severe"] as const).map((name) => (
                  <fieldset key={name}>
                    <legend>{scenarioNameForWizard(name, zh)}</legend>
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
                        {scenarioFieldLabel(key, zh)}
                        <input
                          inputMode="decimal"
                          value={percentDisplay(input.scenarios[name][key])}
                          onChange={(e) =>
                            patchScenario(name, key, percentValue(e.target.value))
                          }
                        />
                      </label>
                    ))}
                  </fieldset>
                ))}
              </div>
            </>
          )}
          {step === 6 && (
            <>
              <h2>
                {zh
                  ? "準備好執行授信分析了嗎？"
                  : "Ready to run the credit analysis?"}
              </h2>
              <div className="review-provenance" role="note">
                <p>
                  {zh
                    ? `目前範本：${template}；已編輯借款人與授信資料後，請確認其餘財務與情境仍屬此範本。`
                    : `Current template: ${template}. Confirm that unchanged financials and scenarios still belong to this borrower.`}
                </p>
                <div className="button-row">
                  <button
                    type="button"
                    className="button secondary"
                    onClick={() =>
                      setInput((current) =>
                        current
                          ? {
                              ...current,
                              borrower: {
                                ...current.borrower,
                                legal_name: "",
                              },
                            }
                          : current,
                      )
                    }
                  >
                    {zh ? "清除借款人名稱" : "Clear borrower name"}
                  </button>
                  <button
                    type="button"
                    className="button secondary"
                    onClick={() => {
                      setInput(null);
                      setStep(0);
                    }}
                  >
                    {zh ? "重設為範本" : "Reset to template"}
                  </button>
                </div>
              </div>
              <div className="review-summary">
                <dl>
                  <div>
                    <dt>{zh ? "借款人" : "Borrower"}</dt>
                    <dd>{input.borrower.legal_name}</dd>
                  </div>
                  <div>
                    <dt>{zh ? "申請額" : "Request"}</dt>
                    <dd>{money(input.request.amount, locale)}</dd>
                  </div>
                  <div>
                    <dt>{zh ? "結構" : "Structure"}</dt>
                    <dd>
                      {input.request.facility_type} ·{" "}
                      {input.request.security_type}
                    </dd>
                  </div>
                  <div>
                    <dt>{zh ? "情境" : "Scenarios"}</dt>
                    <dd>
                      {zh
                        ? "基準 · 下行 · 嚴重壓力"
                        : "Base · Downside · Severe"}
                    </dd>
                  </div>
                  <div>
                    <dt>{zh ? "輸入驗證" : "Input validation"}</dt>
                    <dd>
                      {review
                        ? review.valid
                          ? zh
                            ? "通過"
                            : "Passed"
                          : zh
                            ? `缺少：${review.missing.join("、")}`
                            : `Missing: ${review.missing.join(", ")}`
                        : zh
                          ? "驗證中…"
                          : "Validating…"}
                    </dd>
                  </div>
                  <div>
                    <dt>{zh ? "預估信心" : "Estimated confidence"}</dt>
                    <dd>
                      {review ? `${review.estimated_confidence}/100` : "—"}
                    </dd>
                  </div>
                </dl>
                {review && review.warnings.length > 0 && (
                  <ul>
                    {review.warnings.map((item) => (
                      <li key={item}>{item}</li>
                    ))}
                  </ul>
                )}
                <p>
                  <ShieldAlert size={18} />
                  {zh
                    ? "此分析僅使用合成資料。驗證通過後才會建立案件並執行模型。"
                    : "Synthetic data only. A case is created only after validation passes."}
                </p>
              </div>
            </>
          )}
          {error && (
            <p className="error" role="alert">
              {error}
            </p>
          )}
          <div className="wizard-actions">
            <button
              className="button secondary"
              type="button"
              disabled={step === 0 || loading}
              onClick={() => setStep((value) => value - 1)}
            >
              <ArrowLeft size={16} />
              {zh ? "上一步" : "Back"}
            </button>
            {step < 6 ? (
              <button
                className="button primary"
                type="button"
                onClick={() => setStep((value) => value + 1)}
              >
                {zh ? "繼續" : "Continue"}
                <ArrowRight size={16} />
              </button>
            ) : (
              <button
                className="button primary"
                type="button"
                onClick={run}
                disabled={loading}
              >
                {loading ? (
                  <LoaderCircle className="spin" size={17} />
                ) : (
                  <Save size={17} />
                )}{" "}
                {zh
                  ? "儲存草稿並執行授信分析"
                  : "Save draft and run credit analysis"}
              </button>
            )}
          </div>
        </section>
      </main>
    </>
  );
}
