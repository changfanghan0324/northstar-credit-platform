"use client";

import { Copy, Download, Plus, Trash2 } from "lucide-react";
import { useState } from "react";

import { formatMoneyInput, parseMoneyInput } from "@/lib/money";
import type { CaseInput, FinancialPeriod, Money } from "@/lib/types";

type Spread = NonNullable<CaseInput["financial_spread"]>;
type Statement = "income_statement" | "balance_sheet" | "cash_flow";
const fields: Record<Statement, string[]> = {
  income_statement: [
    "revenue",
    "cogs",
    "gross_profit",
    "operating_expenses",
    "ebitda",
    "depreciation_amortization",
    "ebit",
    "cash_interest",
    "pretax_income",
    "cash_taxes",
    "net_income",
  ],
  balance_sheet: [
    "cash",
    "restricted_cash",
    "accounts_receivable",
    "inventory",
    "current_assets",
    "ppe",
    "goodwill",
    "intangible_assets",
    "total_assets",
    "accounts_payable",
    "current_liabilities",
    "short_term_debt",
    "current_maturities",
    "long_term_debt",
    "lease_liabilities",
    "total_liabilities",
    "equity",
  ],
  cash_flow: [
    "operating_cash_flow",
    "working_capital_change",
    "capital_expenditures",
    "maintenance_capex",
    "acquisitions",
    "asset_sales",
    "dividends",
    "share_repurchases",
    "debt_issued",
    "debt_repaid",
    "free_cash_flow",
  ],
};
const statementNames: Record<Statement, [string, string]> = {
  income_statement: ["Income statement", "損益表"],
  balance_sheet: ["Balance sheet", "資產負債表"],
  cash_flow: ["Cash flow", "現金流量表"],
};
const zhLineItems: Record<string, string> = {
  revenue: "營收",
  cogs: "銷貨成本",
  gross_profit: "毛利",
  operating_expenses: "營業費用",
  ebitda: "EBITDA",
  depreciation_amortization: "折舊與攤銷",
  ebit: "EBIT",
  cash_interest: "現金利息",
  pretax_income: "稅前淨利",
  cash_taxes: "現金稅負",
  net_income: "淨利",
  cash: "現金",
  restricted_cash: "受限現金",
  accounts_receivable: "應收帳款",
  inventory: "存貨",
  current_assets: "流動資產",
  ppe: "不動產、廠房及設備",
  goodwill: "商譽",
  intangible_assets: "無形資產",
  total_assets: "總資產",
  accounts_payable: "應付帳款",
  current_liabilities: "流動負債",
  short_term_debt: "短期債務",
  current_maturities: "一年內到期債務",
  long_term_debt: "長期債務",
  lease_liabilities: "租賃負債",
  total_liabilities: "總負債",
  equity: "權益",
  operating_cash_flow: "營業現金流",
  working_capital_change: "營運資金變動",
  capital_expenditures: "資本支出",
  maintenance_capex: "維持性資本支出",
  acquisitions: "併購支出",
  asset_sales: "資產出售",
  dividends: "股利",
  share_repurchases: "股份回購",
  debt_issued: "新增債務",
  debt_repaid: "償還債務",
  free_cash_flow: "自由現金流",
};
function lineItem(field: string, zh: boolean): string {
  return zh ? (zhLineItems[field] ?? field) : field.replaceAll("_", " ");
}
function scaleLabel(scale: FinancialPeriod["scale"], zh: boolean): string {
  if (!zh) return scale;
  return { whole: "元", thousands: "千", millions: "百萬" }[scale];
}
function scaleFactor(scale: FinancialPeriod["scale"]): number {
  return scale === "millions" ? 1_000_000 : scale === "thousands" ? 1_000 : 1;
}
function displayMoney(value: Money, scale: FinancialPeriod["scale"]): string {
  const factor = scaleFactor(scale);
  return formatMoneyInput({
    ...value,
    amount_minor: value.amount_minor / factor,
  });
}

function blankPeriod(
  kind: "historical_fiscal_year" | "quarter" | "forecast",
  index: number,
  zh: boolean,
): FinancialPeriod {
  const currentYear = new Date().getFullYear();
  let year =
    kind === "historical_fiscal_year"
      ? currentYear - index
      : kind === "forecast"
        ? currentYear + index
        : currentYear;
  let quarter: number | null = null;
  let startDate = `${year}-01-01`;
  let endDate = `${year}-12-31`;
  if (kind === "quarter") {
    const completedQuarter = Math.floor(new Date().getMonth() / 3);
    const absoluteQuarter = currentYear * 4 + completedQuarter - index;
    year = Math.floor(absoluteQuarter / 4);
    quarter = (((absoluteQuarter % 4) + 4) % 4) + 1;
    const startMonth = (quarter - 1) * 3 + 1;
    const endMonth = quarter * 3;
    const endDay = new Date(Date.UTC(year, endMonth, 0)).getUTCDate();
    startDate = `${year}-${String(startMonth).padStart(2, "0")}-01`;
    endDate = `${year}-${String(endMonth).padStart(2, "0")}-${String(endDay).padStart(2, "0")}`;
  }
  return {
    id: `${kind}-${year}-${quarter ?? "annual"}-${Date.now()}`,
    label: zh
      ? kind === "forecast"
        ? `預測第 ${index} 年`
        : kind === "quarter"
          ? `${year} 年第 ${quarter} 季`
          : `${year} 會計年度`
      : kind === "forecast"
        ? `Forecast ${index}`
        : kind === "quarter"
          ? `${year} Q${quarter}`
          : `FY ${year}`,
    period_type: kind,
    start_date: startDate,
    end_date: endDate,
    fiscal_year: year,
    fiscal_quarter: quarter,
    audited: false,
    source_type: kind === "forecast" ? "forecast" : "management",
    source_reference: zh
      ? "合成分析資料來源"
      : "Synthetic analyst-provided source",
    currency: "USD",
    scale: "whole",
    flow_type: "discrete",
    entity_scope: "borrower_consolidated",
    accounting_basis: "management",
    fiscal_calendar: "calendar",
    mapping_version: "default",
    restated: false,
    pro_forma: false,
    income_statement: {},
    balance_sheet: {},
    cash_flow: {},
  };
}

export function FinancialSpreadEditor({
  value,
  language,
  onChange,
}: {
  value: Spread | undefined;
  language: "en" | "zh-TW";
  onChange: (value: Spread) => void;
}) {
  const zh = language === "zh-TW";
  const spread: Spread = value ?? { periods: [], selected_ltm_method: null };
  const [error, setError] = useState("");
  const [paste, setPaste] = useState("");
  function periods(next: FinancialPeriod[]) {
    onChange({ ...spread, periods: next });
  }
  function updatePeriod(id: string, update: Partial<FinancialPeriod>) {
    periods(
      spread.periods.map((item) =>
        item.id === id ? { ...item, ...update } : item,
      ),
    );
  }
  function setMoney(
    id: string,
    statement: Statement,
    field: string,
    text: string,
  ) {
    const parsed = parseMoneyInput(text, 2, language);
    if (!parsed.ok) {
      setError(parsed.message);
      return;
    }
    const period = spread.periods.find((item) => item.id === id);
    const scaled = parsed.amountMinor * scaleFactor(period?.scale ?? "whole");
    if (!Number.isSafeInteger(scaled)) {
      setError(
        zh
          ? "依所選單位換算後，金額超過安全上限。"
          : "The scaled amount exceeds the exact supported range.",
      );
      return;
    }
    setError("");
    periods(
      spread.periods.map((item) =>
        item.id === id
          ? {
              ...item,
              [statement]: {
                ...item[statement],
                [field]: {
                  amount_minor: scaled,
                  currency: item.currency,
                  minor_unit_exponent: 2,
                },
              },
            }
          : item,
      ),
    );
  }
  function add(kind: "historical_fiscal_year" | "quarter" | "forecast") {
    const existing = spread.periods.filter((item) =>
      kind === "historical_fiscal_year"
        ? item.period_type === "historical_fiscal_year"
        : item.period_type === kind,
    ).length;
    periods([...spread.periods, blankPeriod(kind, existing + 1, zh)]);
  }
  function seedHistory() {
    periods([
      blankPeriod("historical_fiscal_year", 3, zh),
      blankPeriod("historical_fiscal_year", 2, zh),
      blankPeriod("historical_fiscal_year", 1, zh),
      ...spread.periods,
    ]);
  }
  function copyPeriod(period: FinancialPeriod) {
    periods([
      ...spread.periods,
      {
        ...structuredClone(period),
        id: `${period.id}-copy-${Date.now()}`,
        label: `${period.label}${zh ? " 副本" : " copy"}`,
        audited: false,
      },
    ]);
  }
  function downloadTemplate() {
    const header = [
      "label",
      "period_type",
      "start_date",
      "end_date",
      "fiscal_year",
      "currency",
      "scale",
      ...fields.income_statement,
      ...fields.balance_sheet,
      ...fields.cash_flow,
    ].join(",");
    const url = URL.createObjectURL(
      new Blob([`${header}\n`], { type: "text/csv;charset=utf-8" }),
    );
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = "northstar-financial-spread-template.csv";
    anchor.click();
    URL.revokeObjectURL(url);
  }
  function applyPaste() {
    const rows = paste
      .trim()
      .split(/\r?\n/)
      .map((row) => row.split("\t"));
    if (!rows.length || spread.periods.length === 0) {
      setError(zh ? "請先新增期間。" : "Add periods before pasting values.");
      return;
    }
    const pasteFields: Array<[Statement, string]> = [
      ["income_statement", "revenue"],
      ["income_statement", "ebitda"],
      ["balance_sheet", "cash"],
      ["balance_sheet", "total_assets"],
      ["balance_sheet", "total_liabilities"],
      ["balance_sheet", "equity"],
      ["cash_flow", "operating_cash_flow"],
      ["cash_flow", "capital_expenditures"],
    ];
    const next = structuredClone(spread.periods);
    rows.slice(0, next.length).forEach((row, rowIndex) =>
      row.slice(0, pasteFields.length).forEach((cell, columnIndex) => {
        const parsed = parseMoneyInput(cell, 2, language);
        const scaled = parsed.ok
          ? parsed.amountMinor * scaleFactor(next[rowIndex].scale)
          : 0;
        if (parsed.ok && Number.isSafeInteger(scaled)) {
          const [statement, field] = pasteFields[columnIndex];
          next[rowIndex][statement][field] = {
            amount_minor: scaled,
            currency: next[rowIndex].currency,
            minor_unit_exponent: 2,
          };
        }
      }),
    );
    periods(next);
    setPaste("");
    setError("");
  }
  return (
    <section className="spread-editor" aria-labelledby="spread-editor-title">
      <div className="panel-head">
        <div>
          <h4 id="spread-editor-title">
            {zh ? "分析師多期財務展開" : "Analyst multi-period spread"}
          </h4>
          <p>
            {zh
              ? "金額以選定幣別輸入；括號或負號代表現金流出。"
              : "Enter values in the selected currency; use a minus sign for cash outflows."}
          </p>
        </div>
        <button
          type="button"
          className="button secondary"
          onClick={downloadTemplate}
        >
          <Download size={15} />
          {zh ? "CSV 範本" : "CSV template"}
        </button>
      </div>
      <div className="spread-actions">
        <button type="button" onClick={seedHistory}>
          <Plus size={14} />
          {zh ? "加入三年歷史" : "Add 3-year history"}
        </button>
        <button type="button" onClick={() => add("quarter")}>
          <Plus size={14} />
          {zh ? "加入最新季" : "Add latest quarter"}
        </button>
        <button type="button" onClick={() => add("forecast")}>
          <Plus size={14} />
          {zh ? "加入預測年" : "Add forecast year"}
        </button>
      </div>
      <label className="ltm-select">
        {zh ? "LTM 方法" : "LTM method"}
        <select
          value={spread.selected_ltm_method ?? ""}
          onChange={(event) =>
            onChange({
              ...spread,
              selected_ltm_method: event.target.value || null,
            })
          }
        >
          <option value="">{zh ? "選擇方法" : "Select method"}</option>
          <option value="reported_ltm">
            {zh ? "報告 LTM" : "Reported LTM"}
          </option>
          <option value="latest_four_quarters">
            {zh ? "最近四個不重疊季度" : "Latest four nonoverlapping quarters"}
          </option>
          <option value="fiscal_year_plus_current_ytd_minus_prior_ytd">
            {zh
              ? "會計年度＋本期 YTD－前期可比 YTD"
              : "FY + current YTD - prior comparable YTD"}
          </option>
        </select>
      </label>
      <div className="period-cards">
        {spread.periods.map((period) => (
          <fieldset key={period.id}>
            <legend>{period.label}</legend>
            <div className="period-meta">
              <label>
                {zh ? "標籤" : "Label"}
                <input
                  value={period.label}
                  onChange={(event) =>
                    updatePeriod(period.id, { label: event.target.value })
                  }
                />
              </label>
              <label>
                {zh ? "類型" : "Type"}
                <select
                  value={period.period_type}
                  onChange={(event) =>
                    updatePeriod(period.id, { period_type: event.target.value })
                  }
                >
                  <option value="historical_fiscal_year">
                    {zh ? "歷史年度" : "Historical FY"}
                  </option>
                  <option value="quarter">{zh ? "季度" : "Quarter"}</option>
                  <option value="ytd">YTD</option>
                  <option value="ltm">LTM</option>
                  <option value="forecast">{zh ? "預測" : "Forecast"}</option>
                </select>
              </label>
              <label>
                {zh ? "開始" : "Start"}
                <input
                  type="date"
                  value={period.start_date}
                  onChange={(event) =>
                    updatePeriod(period.id, { start_date: event.target.value })
                  }
                />
              </label>
              <label>
                {zh ? "結束" : "End"}
                <input
                  type="date"
                  value={period.end_date}
                  onChange={(event) =>
                    updatePeriod(period.id, { end_date: event.target.value })
                  }
                />
              </label>
              <label>
                {zh ? "幣別" : "Currency"}
                <select
                  value={period.currency}
                  onChange={(event) =>
                    updatePeriod(period.id, { currency: event.target.value })
                  }
                >
                  <option>USD</option>
                  <option>EUR</option>
                  <option>GBP</option>
                  <option>CAD</option>
                </select>
              </label>
              <label>
                {zh ? "單位" : "Scale"}
                <select
                  value={period.scale}
                  onChange={(event) =>
                    updatePeriod(period.id, {
                      scale: event.target.value as FinancialPeriod["scale"],
                    })
                  }
                >
                  <option value="whole">{zh ? "元" : "Whole"}</option>
                  <option value="thousands">{zh ? "千" : "Thousands"}</option>
                  <option value="millions">{zh ? "百萬" : "Millions"}</option>
                </select>
              </label>
              <label className="wide">
                {zh ? "來源" : "Source reference"}
                <input
                  value={period.source_reference}
                  onChange={(event) =>
                    updatePeriod(period.id, {
                      source_reference: event.target.value,
                    })
                  }
                />
              </label>
            </div>
            <div className="period-tools">
              <button type="button" onClick={() => copyPeriod(period)}>
                <Copy size={14} />
                {zh ? "複製" : "Copy"}
              </button>
              <button
                type="button"
                onClick={() =>
                  periods(
                    spread.periods.filter((item) => item.id !== period.id),
                  )
                }
              >
                <Trash2 size={14} />
                {zh ? "移除" : "Remove"}
              </button>
            </div>
          </fieldset>
        ))}
      </div>
      {spread.periods.length > 0 &&
        (Object.keys(fields) as Statement[]).map((statement) => (
          <details key={statement} className="statement-table">
            <summary>{statementNames[statement][zh ? 1 : 0]}</summary>
            <div>
              <table>
                <caption className="sr-only">
                  {statementNames[statement][zh ? 1 : 0]}
                </caption>
                <thead>
                  <tr>
                    <th>{zh ? "科目" : "Line item"}</th>
                    {spread.periods.map((period) => (
                      <th key={period.id}>
                        {period.label}
                        <small>
                          {period.currency} · {scaleLabel(period.scale, zh)}
                        </small>
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {fields[statement].map((field) => (
                    <tr key={field}>
                      <td>{lineItem(field, zh)}</td>
                      {spread.periods.map((period) => {
                        const current = period[statement][field] as
                          Money | null | undefined;
                        return (
                          <td key={period.id}>
                            <input
                              aria-label={`${period.label} ${lineItem(field, zh)}`}
                              inputMode="decimal"
                              value={
                                current
                                  ? displayMoney(current, period.scale)
                                  : ""
                              }
                              placeholder="—"
                              onChange={(event) =>
                                setMoney(
                                  period.id,
                                  statement,
                                  field,
                                  event.target.value,
                                )
                              }
                            />
                          </td>
                        );
                      })}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </details>
        ))}
      <details className="bulk-paste">
        <summary>
          {zh ? "從 Excel 貼上主要欄位" : "Paste key fields from Excel"}
        </summary>
        <p>
          {zh
            ? "每列對應一個期間；欄位依序為營收、EBITDA、現金、總資產、總負債、權益、營業現金流、資本支出。"
            : "One row per period: revenue, EBITDA, cash, total assets, total liabilities, equity, operating cash flow, capex."}
        </p>
        <textarea
          value={paste}
          onChange={(event) => setPaste(event.target.value)}
        />
        <button type="button" className="button secondary" onClick={applyPaste}>
          {zh ? "套用貼上資料" : "Apply pasted data"}
        </button>
      </details>
      {error && (
        <p className="error" role="alert">
          {error}
        </p>
      )}
    </section>
  );
}
