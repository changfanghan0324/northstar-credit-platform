"use client";

import { Plus, Trash2 } from "lucide-react";

import { formatMoneyInput, parseMoneyInput } from "@/lib/money";
import type {
  Adjustment,
  BorrowingBaseInput,
  CaseInput,
  Money,
} from "@/lib/types";

function blankMoney(template: Money): Money {
  return { ...template, amount_minor: 0 };
}

const zhAdjustmentCategories: Record<string, string> = {
  restructuring: "重組",
  litigation: "訴訟",
  impairment: "減損",
  acquisition_related: "併購相關成本",
  asset_sale_gain: "資產出售利益",
  one_time_compensation: "一次性薪酬",
  government_support: "非經常性政府補助",
  related_party: "關係人交易",
  owner_compensation: "業主薪酬調整",
  other: "其他",
};
const zhCollateralLabels: Record<string, string> = {
  accounts_receivable: "應收帳款",
  inventory: "存貨",
  other_collateral: "其他擔保品",
  gross_receivables: "應收帳款總額",
  ineligible_receivables: "不合格應收帳款",
  past_due_receivables: "逾期應收帳款",
  cross_aged_receivables: "交叉帳齡應收帳款",
  foreign_receivables: "國外應收帳款",
  concentration_reserve: "集中度準備",
  dilution_reserve: "稀釋準備",
  advance_rate: "預支率",
  gross_inventory: "存貨總額",
  ineligible_inventory: "不合格存貨",
  obsolete_inventory: "過時存貨",
  inventory_cap: "存貨上限",
  equipment: "設備",
  real_estate: "不動產",
  cash: "現金",
  other: "其他",
  additional_reserves: "其他準備",
  prior_liens: "優先留置權",
};
function fieldLabel(value: string, zh: boolean): string {
  return zh ? (zhCollateralLabels[value] ?? value) : value.replaceAll("_", " ");
}

export function AdjustmentLogEditor({
  input,
  language,
  onChange,
  onError,
}: {
  input: CaseInput;
  language: "en" | "zh-TW";
  onChange: (value: Adjustment[]) => void;
  onError: (value: string) => void;
}) {
  const zh = language === "zh-TW";
  const entries = input.normalization_adjustments ?? [];
  const template = input.request.amount;
  function add() {
    const now = new Date().toISOString();
    onChange([
      ...entries,
      {
        id: crypto.randomUUID(),
        name: zh ? "新調整" : "New adjustment",
        period_id: input.financial_spread?.periods[0]?.id ?? "legacy-snapshot",
        category: "other",
        amount: blankMoney(template),
        direction: "positive",
        cash_classification: "cash",
        recurrence: "nonrecurring",
        ebitda_impact: blankMoney(template),
        ebit_impact: blankMoney(template),
        cfads_impact: blankMoney(template),
        supporting_evidence: "",
        source_reference: "",
        analyst_rationale: "",
        approval_status: "draft",
        reviewer: null,
        created_at: now,
        updated_at: now,
      },
    ]);
  }
  function patch(index: number, update: Partial<Adjustment>) {
    onChange(
      entries.map((item, itemIndex) =>
        itemIndex === index
          ? { ...item, ...update, updated_at: new Date().toISOString() }
          : item,
      ),
    );
  }
  function patchMoney(
    index: number,
    key: "amount" | "ebitda_impact" | "ebit_impact" | "cfads_impact",
    text: string,
  ) {
    const current = entries[index][key];
    const parsed = parseMoneyInput(text, current.minor_unit_exponent, language);
    if (!parsed.ok) {
      onError(parsed.message);
      return;
    }
    onError("");
    patch(index, { [key]: { ...current, amount_minor: parsed.amountMinor } });
  }
  return (
    <section className="adjustment-editor">
      <div className="panel-head">
        <div>
          <h4>{zh ? "正常化調整紀錄" : "Normalization adjustment log"}</h4>
          <p>
            {zh
              ? "核准項目必須包含證據、來源、理由與覆核資訊。"
              : "Approved items require evidence, source, rationale, and review details."}
          </p>
        </div>
        <button type="button" className="button secondary" onClick={add}>
          <Plus size={15} />
          {zh ? "新增調整" : "Add adjustment"}
        </button>
      </div>
      {entries.map((item, index) => (
        <fieldset key={item.id}>
          <legend>{item.name}</legend>
          <div className="input-grid">
            <label>
              {zh ? "名稱" : "Name"}
              <input
                value={item.name}
                onChange={(event) => patch(index, { name: event.target.value })}
              />
            </label>
            <label>
              {zh ? "期間" : "Period"}
              <select
                value={item.period_id}
                onChange={(event) =>
                  patch(index, { period_id: event.target.value })
                }
              >
                <option value="legacy-snapshot">
                  {zh ? "舊版快照" : "Legacy snapshot"}
                </option>
                {input.financial_spread?.periods.map((period) => (
                  <option key={period.id} value={period.id}>
                    {period.label}
                  </option>
                ))}
              </select>
            </label>
            <label>
              {zh ? "類別" : "Category"}
              <select
                value={item.category}
                onChange={(event) =>
                  patch(index, { category: event.target.value })
                }
              >
                {[
                  "restructuring",
                  "litigation",
                  "impairment",
                  "acquisition_related",
                  "asset_sale_gain",
                  "one_time_compensation",
                  "government_support",
                  "related_party",
                  "owner_compensation",
                  "other",
                ].map((value) => (
                  <option key={value} value={value}>
                    {zh
                      ? zhAdjustmentCategories[value]
                      : value.replaceAll("_", " ")}
                  </option>
                ))}
              </select>
            </label>
            <label>
              {zh ? "金額" : "Amount"}
              <input
                inputMode="decimal"
                value={formatMoneyInput(item.amount)}
                onChange={(event) =>
                  patchMoney(index, "amount", event.target.value)
                }
              />
            </label>
            <label>
              {zh ? "方向" : "Direction"}
              <select
                value={item.direction}
                onChange={(event) =>
                  patch(index, {
                    direction: event.target.value as Adjustment["direction"],
                  })
                }
              >
                <option value="positive">{zh ? "正向" : "Positive"}</option>
                <option value="negative">{zh ? "負向" : "Negative"}</option>
              </select>
            </label>
            <label>
              {zh ? "現金分類" : "Cash classification"}
              <select
                value={item.cash_classification}
                onChange={(event) =>
                  patch(index, {
                    cash_classification: event.target
                      .value as Adjustment["cash_classification"],
                  })
                }
              >
                <option value="cash">{zh ? "現金" : "Cash"}</option>
                <option value="noncash">{zh ? "非現金" : "Noncash"}</option>
              </select>
            </label>
            <label>
              {zh ? "重複性" : "Recurrence"}
              <select
                value={item.recurrence}
                onChange={(event) =>
                  patch(index, {
                    recurrence: event.target.value as Adjustment["recurrence"],
                  })
                }
              >
                <option value="nonrecurring">
                  {zh ? "非經常" : "Nonrecurring"}
                </option>
                <option value="recurring">{zh ? "經常" : "Recurring"}</option>
              </select>
            </label>
            {(["ebitda_impact", "ebit_impact", "cfads_impact"] as const).map(
              (key) => (
                <label key={key}>
                  {key === "ebitda_impact"
                    ? zh
                      ? "EBITDA 影響"
                      : "EBITDA impact"
                    : key === "ebit_impact"
                      ? zh
                        ? "EBIT 影響"
                        : "EBIT impact"
                      : zh
                        ? "CFADS 影響"
                        : "CFADS impact"}
                  <input
                    inputMode="decimal"
                    value={formatMoneyInput(item[key])}
                    onChange={(event) =>
                      patchMoney(index, key, event.target.value)
                    }
                  />
                </label>
              ),
            )}
            <label className="wide">
              {zh ? "支持證據" : "Supporting evidence"}
              <textarea
                value={item.supporting_evidence}
                onChange={(event) =>
                  patch(index, { supporting_evidence: event.target.value })
                }
              />
            </label>
            <label>
              {zh ? "來源參考" : "Source reference"}
              <input
                value={item.source_reference}
                onChange={(event) =>
                  patch(index, { source_reference: event.target.value })
                }
              />
            </label>
            <label>
              {zh ? "覆核人" : "Reviewer"}
              <input
                value={item.reviewer ?? ""}
                onChange={(event) =>
                  patch(index, { reviewer: event.target.value || null })
                }
              />
            </label>
            <label className="wide">
              {zh ? "分析師理由" : "Analyst rationale"}
              <textarea
                value={item.analyst_rationale}
                onChange={(event) =>
                  patch(index, { analyst_rationale: event.target.value })
                }
              />
            </label>
            <label>
              {zh ? "核准狀態" : "Approval status"}
              <select
                value={item.approval_status}
                onChange={(event) =>
                  patch(index, { approval_status: event.target.value })
                }
              >
                <option value="draft">{zh ? "草稿" : "Draft"}</option>
                <option value="pending">{zh ? "待覆核" : "Pending"}</option>
                <option value="approved">{zh ? "已核准" : "Approved"}</option>
                <option value="rejected">{zh ? "已拒絕" : "Rejected"}</option>
              </select>
            </label>
          </div>
          <button
            type="button"
            className="button ghost"
            onClick={() =>
              onChange(entries.filter((_, itemIndex) => itemIndex !== index))
            }
          >
            <Trash2 size={15} />
            {zh ? "移除此調整" : "Remove adjustment"}
          </button>
        </fieldset>
      ))}
    </section>
  );
}

export function BorrowingBaseEditor({
  input,
  language,
  onChange,
  onError,
}: {
  input: CaseInput;
  language: "en" | "zh-TW";
  onChange: (value: BorrowingBaseInput) => void;
  onError: (value: string) => void;
}) {
  const zh = language === "zh-TW";
  if (input.request.facility_type !== "asset_based") return null;
  const template = input.request.amount;
  const value = input.borrowing_base ?? {
    accounts_receivable: {
      gross_receivables: blankMoney(template),
      ineligible_receivables: blankMoney(template),
      past_due_receivables: blankMoney(template),
      cross_aged_receivables: blankMoney(template),
      foreign_receivables: blankMoney(template),
      concentration_reserve: blankMoney(template),
      dilution_reserve: blankMoney(template),
      advance_rate: "0.85",
    },
    inventory: {
      gross_inventory: blankMoney(template),
      ineligible_inventory: blankMoney(template),
      obsolete_inventory: blankMoney(template),
      advance_rate: "0.50",
      inventory_cap: blankMoney(template),
    },
    other_collateral: {
      equipment: blankMoney(template),
      real_estate: blankMoney(template),
      cash: blankMoney(template),
      other: blankMoney(template),
    },
    additional_reserves: blankMoney(template),
    prior_liens: blankMoney(template),
  };
  function groupMoney(
    group: "accounts_receivable" | "inventory" | "other_collateral",
    key: string,
    text: string,
  ) {
    const current = value[group][key] as Money;
    const parsed = parseMoneyInput(text, current.minor_unit_exponent, language);
    if (!parsed.ok) {
      onError(parsed.message);
      return;
    }
    onError("");
    onChange({
      ...value,
      [group]: {
        ...value[group],
        [key]: { ...current, amount_minor: parsed.amountMinor },
      },
    });
  }
  function topMoney(key: "additional_reserves" | "prior_liens", text: string) {
    const current = value[key];
    const parsed = parseMoneyInput(text, current.minor_unit_exponent, language);
    if (!parsed.ok) {
      onError(parsed.message);
      return;
    }
    onError("");
    onChange({
      ...value,
      [key]: { ...current, amount_minor: parsed.amountMinor },
    });
  }
  return (
    <section className="borrowing-editor">
      <h4>{zh ? "資產基礎融資借款基礎" : "Asset-based borrowing base"}</h4>
      <p>
        {zh
          ? "預支率將受版本化政策上限約束。"
          : "Advance rates are capped by versioned policy."}
      </p>
      {(["accounts_receivable", "inventory", "other_collateral"] as const).map(
        (group) => (
          <fieldset key={group}>
            <legend>{fieldLabel(group, zh)}</legend>
            <div className="input-grid">
              {Object.entries(value[group]).map(([key, current]) =>
                typeof current === "string" ? (
                  <label key={key}>
                    {fieldLabel(key, zh)}
                    <input
                      value={current}
                      onChange={(event) =>
                        onChange({
                          ...value,
                          [group]: {
                            ...value[group],
                            [key]: event.target.value,
                          },
                        })
                      }
                    />
                  </label>
                ) : (
                  <label key={key}>
                    {fieldLabel(key, zh)}
                    <input
                      inputMode="decimal"
                      value={formatMoneyInput(current)}
                      onChange={(event) =>
                        groupMoney(group, key, event.target.value)
                      }
                    />
                  </label>
                ),
              )}
            </div>
          </fieldset>
        ),
      )}
      <div className="input-grid">
        {(["additional_reserves", "prior_liens"] as const).map((key) => (
          <label key={key}>
            {fieldLabel(key, zh)}
            <input
              inputMode="decimal"
              value={formatMoneyInput(value[key])}
              onChange={(event) => topMoney(key, event.target.value)}
            />
          </label>
        ))}
      </div>
    </section>
  );
}
