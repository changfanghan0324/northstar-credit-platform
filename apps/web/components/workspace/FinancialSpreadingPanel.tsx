import { CircleAlert } from "lucide-react";

import { money } from "@/lib/api";
import type { Analysis, Money } from "@/lib/types";

function periodMoney(value: unknown, locale: string) {
  return value && typeof value === "object" && "amount_minor" in value
    ? money(value as Money, locale, true)
    : "—";
}
function scaleLabel(value: string, zh: boolean): string {
  if (!zh) return value;
  return (
    (
      { whole: "元", thousands: "千", millions: "百萬" } as Record<
        string,
        string
      >
    )[value] ?? value
  );
}
function adjustmentCategory(value: string, zh: boolean): string {
  if (!zh) return value.replaceAll("_", " ");
  return (
    (
      {
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
      } as Record<string, string>
    )[value] ?? "其他"
  );
}
function approvalStatus(value: string, zh: boolean): string {
  if (!zh) return value.replaceAll("_", " ");
  return (
    (
      {
        draft: "草稿",
        pending: "待覆核",
        approved: "已核准",
        rejected: "已拒絕",
      } as Record<string, string>
    )[value] ?? "已記錄"
  );
}

export function FinancialSpreadingPanel({
  analysis,
  language,
  locale,
  mode,
}: {
  analysis: Analysis;
  language: "en" | "zh-TW";
  locale: string;
  mode: string;
}) {
  const zh = language === "zh-TW";
  const spreading = analysis.financial_spreading;
  const adjustments = analysis.adjustments;
  return (
    <>
      <div className="spread-status" role="status">
        <div>
          <span>{zh ? "LTM 方法" : "LTM method"}</span>
          <strong>
            {zh
              ? ((
                  {
                    reported_ltm: "報告 LTM",
                    latest_four_quarters: "最近四個不重疊季度",
                    fiscal_year_plus_current_ytd_minus_prior_ytd:
                      "會計年度加本期 YTD 減前期可比 YTD",
                  } as Record<string, string>
                )[spreading.selected_ltm_method ?? ""] ?? "未選擇")
              : (spreading.selected_ltm_method?.replaceAll("_", " ") ??
                "Not selected")}
          </strong>
        </div>
        <div>
          <span>{zh ? "狀態" : "Status"}</span>
          <strong>
            {spreading.ltm_status === "available"
              ? zh
                ? "可使用"
                : "Available"
              : spreading.ltm_status === "blocked"
                ? zh
                  ? "已阻擋"
                  : "Blocked"
                : zh
                  ? "舊版單期快照"
                  : "Legacy snapshot"}
          </strong>
        </div>
        <div>
          <span>{zh ? "歷史／預測期數" : "Historical / forecast"}</span>
          <strong>
            {spreading.historical_years} / {spreading.forecast_years}
          </strong>
        </div>
      </div>
      {spreading.resolved_snapshot && (
        <div className="source-lineage-note">
          <strong>{zh ? "權威來源" : "Authoritative source"}</strong>
          <span>
            {zh
              ? `流量：${spreading.resolved_snapshot.flow_source_period_ids.join("、") || "舊版快照"}；資產負債表：${spreading.resolved_snapshot.balance_sheet_source_period_id ?? "舊版快照"}`
              : `Flows: ${spreading.resolved_snapshot.flow_source_period_ids.join(", ") || "legacy snapshot"}; balance sheet: ${spreading.resolved_snapshot.balance_sheet_source_period_id ?? "legacy snapshot"}`}
          </span>
          <code>{spreading.resolved_snapshot.snapshot_hash.slice(0, 16)}</code>
        </div>
      )}
      {spreading.reconciliation_warnings.length > 0 && (
        <div className="reconciliation-warning">
          <CircleAlert size={18} />
          <ul>
            {spreading.reconciliation_warnings.map((item) => (
              <li key={item}>
                {zh
                  ? "財務期間或調節資料尚不完整；LTM 與趨勢限制已保留於 API。"
                  : item}
              </li>
            ))}
          </ul>
        </div>
      )}
      {spreading.periods.length > 0 && (
        <article className="panel table-panel spread-table" tabIndex={0}>
          <h3>{zh ? "多期財務展開" : "Multi-period financial spread"}</h3>
          <table>
            <caption className="sr-only">
              {zh ? "依期間列示的財務資料" : "Financial data by period"}
            </caption>
            <thead>
              <tr>
                <th>{zh ? "項目" : "Line item"}</th>
                {spreading.periods.map((period) => (
                  <th key={period.id}>
                    {period.label}
                    <small>
                      {scaleLabel(period.scale, zh)} · {period.currency}
                    </small>
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {[
                ["revenue", zh ? "營收" : "Revenue", "income_statement"],
                ["ebitda", "EBITDA", "income_statement"],
                ["cash", zh ? "現金" : "Cash", "balance_sheet"],
                [
                  "total_assets",
                  zh ? "總資產" : "Total assets",
                  "balance_sheet",
                ],
                [
                  "total_liabilities",
                  zh ? "總負債" : "Total liabilities",
                  "balance_sheet",
                ],
                [
                  "operating_cash_flow",
                  zh ? "營業現金流" : "Operating cash flow",
                  "cash_flow",
                ],
                [
                  "free_cash_flow",
                  zh ? "自由現金流" : "Free cash flow",
                  "cash_flow",
                ],
              ].map(([field, label, statement]) => (
                <tr key={field}>
                  <td>{label}</td>
                  {spreading.periods.map((period) => (
                    <td key={period.id}>
                      {periodMoney(
                        period[statement as keyof typeof period] &&
                          (
                            period[statement as "income_statement"] as Record<
                              string,
                              unknown
                            >
                          )[field],
                        locale,
                      )}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </article>
      )}
      <article className="panel adjustment-bridge">
        <div className="panel-head">
          <div>
            <h3>{zh ? "EBITDA 正常化橋接" : "EBITDA normalization bridge"}</h3>
            <p>
              {zh
                ? "只有已核准且有證據的調整才納入。"
                : "Only approved, evidenced adjustments are included."}
            </p>
          </div>
          {adjustments.warning && (
            <span className="pill breach">
              {zh ? "超過政策警示值" : "Policy warning"}
            </span>
          )}
        </div>
        <div className="bridge-grid">
          <div>
            <span>{zh ? "報告 EBITDA" : "Reported EBITDA"}</span>
            <strong>{money(adjustments.reported_ebitda, locale, true)}</strong>
          </div>
          <b>+</b>
          <div>
            <span>{zh ? "已核准調整" : "Approved adjustment"}</span>
            <strong>
              {money(adjustments.approved_adjustment, locale, true)}
            </strong>
          </div>
          <b>=</b>
          <div>
            <span>{zh ? "調整後 EBITDA" : "Adjusted EBITDA"}</span>
            <strong>{money(adjustments.adjusted_ebitda, locale, true)}</strong>
          </div>
        </div>
        <dl className="impact-row">
          <div>
            <dt>{zh ? "槓桿（前／後）" : "Leverage (before / after)"}</dt>
            <dd>
              {adjustments.leverage_before ?? "—"}x /{" "}
              {adjustments.leverage_after ?? "—"}x
            </dd>
          </div>
          <div>
            <dt>DSCR ({zh ? "前／後" : "before / after"})</dt>
            <dd>
              {adjustments.dscr_before ?? "—"}x /{" "}
              {adjustments.dscr_after ?? "—"}x
            </dd>
          </div>
        </dl>
        {mode === "analyst" && adjustments.entries.length > 0 && (
          <details>
            <summary>
              {zh ? "顯示完整調整紀錄" : "Show complete adjustment log"}
            </summary>
            <ul>
              {adjustments.entries.map((item) => (
                <li key={item.id}>
                  <strong>{item.name}</strong> ·{" "}
                  {adjustmentCategory(item.category, zh)} ·{" "}
                  {approvalStatus(item.approval_status, zh)}
                  <br />
                  <small>
                    {zh
                      ? "理由、證據與來源已保留於案件輸入。"
                      : `${item.analyst_rationale} · ${item.source_reference}`}
                  </small>
                </li>
              ))}
            </ul>
          </details>
        )}
      </article>
    </>
  );
}
