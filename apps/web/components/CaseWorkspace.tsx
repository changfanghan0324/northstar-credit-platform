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
import type {
  Analysis,
  CaseEnvelope,
  CaseInput,
  Money,
  ScenarioInput,
  ScenarioYear,
} from "@/lib/types";
import { workspaceSections } from "@/lib/workspace";

const labels = {
  en: [
    "Overview",
    "Inputs",
    "Financials",
    "Debt capacity",
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
        executive_summary: "執行摘要",
        borrower_overview: "借款人概況",
        request_and_structure: "申請與結構",
        historical_financial_performance: "歷史財務表現",
        capacity: "債務容量",
        scenario_and_reverse_stress: "情境與反向壓力",
        analysis: "分析",
        strengths: "優勢",
        risks: "風險",
        recommendation_and_terms: "建議與條件",
        policy_exceptions: "政策例外",
        monitoring: "監控",
        limitations: "限制",
        sign_off: "簽核",
      } as Record<string, string>
    )[value] ?? value
  );
}
function isMoney(value: unknown): value is Money {
  return Boolean(value && typeof value === "object" && "amount_minor" in value);
}
function dollars(value: Money) {
  const minor = BigInt(value.amount_minor);
  const scale = 10n ** BigInt(value.minor_unit_exponent);
  const negative = minor < 0n;
  const absolute = negative ? -minor : minor;
  const whole = absolute / scale;
  const fraction = (absolute % scale)
    .toString()
    .padStart(value.minor_unit_exponent, "0");
  return `${negative ? "-" : ""}${whole}.${fraction}`;
}
function toMinor(value: string, exponent: number) {
  const clean = value.trim().replaceAll(",", "");
  if (clean === "") return 0;
  if (!/^-?\d+(\.\d{0,2})?$/.test(clean))
    throw new Error("Enter a valid amount");
  const negative = clean.startsWith("-");
  const [whole, fraction = ""] = clean.replace("-", "").split(".");
  const parsed = Number.parseInt(
    `${whole}${fraction.padEnd(exponent, "0").slice(0, exponent)}`,
    10,
  );
  return negative ? -parsed : parsed;
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
    setDraft((value) => ({
      ...value,
      financials: {
        ...value.financials,
        [key]: {
          ...current,
          amount_minor: toMinor(text, current.minor_unit_exponent),
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
            value={dollars(draft.request.amount)}
            onChange={(e) =>
              setDraft((v) => ({
                ...v,
                request: {
                  ...v.request,
                  amount: {
                    ...v.request.amount,
                    amount_minor: toMinor(
                      e.target.value,
                      v.request.amount.minor_unit_exponent,
                    ),
                  },
                },
              }))
            }
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
      <h4>{zh ? "財務與債務" : "Financials and debt"}</h4>
      <div className="input-grid">
        {shown.map(([key, value]) => (
          <label key={key}>
            {fieldName[key]?.[zh ? 1 : 0] ?? key.replaceAll("_", " ")}
            <input
              inputMode="decimal"
              value={dollars(value as Money)}
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
        <article className="panel table-panel">
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
                  <td>{value.label}</td>
                  <td>{value.status}</td>
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
      <article className="panel table-panel">
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
                <td>{item.label}</td>
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
                  {item.binding ? (zh ? "具約束力" : "Binding") : item.status}
                </td>
                <td>{item.reason}</td>
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
          <strong className="word">{a.scorecard.confidence}</strong>
          <span>{a.scorecard.confidence_score}/100</span>
        </div>
      </div>
      <p className="synthetic-notice">
        {zh
          ? "合成示範資料，不代表真實資料品質評估。"
          : a.scorecard.synthetic_notice}
      </p>
      <article className="panel table-panel">
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
                <td>{c.key.replaceAll("_", " ")}</td>
                <td>{c.status}</td>
                <td>{c.score}</td>
                <td>{c.weight}%</td>
                <td>{c.contribution}</td>
                {mode === "analyst" && (
                  <td>
                    {c.band}
                    <br />
                    <small>{c.evidence}</small>
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
              <li key={x}>{x}</li>
            ))}
          </ul>
        </article>
        <article className="panel">
          <h3>{zh ? "改善方式" : "Improve confidence"}</h3>
          <ul>
            {a.scorecard.improvement_actions.map((x) => (
              <li key={x}>{x}</li>
            ))}
          </ul>
        </article>
      </div>
    </>
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
                  <dd>{ratio(y.leverage)}</dd>
                </div>
                <div>
                  <dt>DSCR</dt>
                  <dd>{ratio(y.dscr)}</dd>
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
              <span className="status">{y.covenant_status}</span>
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
                  {key.replaceAll("_", " ")}
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
            {zh
              ? `營收下降 ${a.reverse_stress.dscr_minimum_revenue_decline}% 時，DSCR 抵達最低門檻。`
              : `Revenue decline to minimum DSCR: ${a.reverse_stress.dscr_minimum_revenue_decline}%`}
          </span>
          <small>
            {a.reverse_stress.method} · {a.reverse_stress.iterations} iterations
            · {a.reverse_stress.converged ? "converged" : "not converged"}
          </small>
        </div>
      </div>
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
                <td>{c.name}</td>
                <td>{c.actual}</td>
                <td>{c.threshold}</td>
                <td>{c.status}</td>
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
            <dd>{a.decision.facility_type}</dd>
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
            <dd>{a.decision.collateral}</dd>
          </div>
          <div>
            <dt>{zh ? "保證" : "Guarantee"}</dt>
            <dd>{a.decision.guarantee}</dd>
          </div>
        </dl>
      </div>
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
      <article className="panel table-panel">
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
                <td>{item.label}</td>
                <td>{item.actual}</td>
                <td>{item.threshold}</td>
                <td>{item.status}</td>
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
  return (
    <article className="memo-paper">
      <header>
        <p>{zh ? "NORTHSTAR 授信備忘錄" : "NORTHSTAR CREDIT MEMORANDUM"}</p>
        <h2>{a.case.borrower.legal_name}</h2>
        <span>{a.case.data_as_of}</span>
      </header>
      {Object.entries(a.memo_sections).map(([title, paragraphs]) => (
        <section key={title}>
          <h3>{memoTitle(title, zh)}</h3>
          {paragraphs.map((p) => (
            <p key={p}>{memoParagraph(p, zh)}</p>
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
              {data.status} · v{data.version}
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
        </main>
      </div>
    </>
  );
}
