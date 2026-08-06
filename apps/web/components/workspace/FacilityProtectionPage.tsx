import { ShieldCheck, TriangleAlert } from "lucide-react";

import { money } from "@/lib/api";
import type { Analysis } from "@/lib/types";

const factorLabels: Record<string, [string, string]> = {
  seniority: ["Seniority", "受償順位"],
  collateral: ["Collateral quality and coverage", "擔保品品質與覆蓋"],
  guarantee: ["Guarantee strength", "保證強度"],
  amortization: ["Amortization", "攤還結構"],
  maturity: ["Maturity and refinancing", "到期與再融資"],
  covenants: ["Covenant protection", "財務契約保障"],
  reporting: ["Reporting requirements", "報告要求"],
  purpose_alignment: [
    "Purpose and repayment alignment",
    "用途與還款來源一致性",
  ],
};

function status(value: string, zh: boolean) {
  const copy: Record<string, string> = {
    strong: "強",
    adequate: "良好",
    moderate: "中等",
    weak: "偏弱",
    severe: "嚴重不足",
    high: "高",
    limited: "有限",
    low: "低",
    calculated: "已計算",
    blocked: "已阻擋",
    not_applicable: "不適用",
  };
  return zh ? (copy[value] ?? value) : value.replaceAll("_", " ");
}
function facilityText(value: string, zh: boolean) {
  if (!zh) return value;
  return (
    (
      {
        "Senior claim": "優先受償權",
        "Quarterly covenant testing": "按季檢驗財務契約",
        "Financial reporting": "定期財務報告",
        "Collateral security package": "擔保品權利組合",
        "No collateral support": "無擔保品支援",
        "Bullet-style repayment concentration": "到期一次還本集中風險",
        "Collateral coverage below requested exposure": "擔保覆蓋低於申請曝險",
        "Maintain tighter leverage and liquidity covenants":
          "維持較嚴格的槓桿與流動性契約",
        "Add scheduled amortization": "加入預定本金攤還",
        "Reduce exposure or add eligible collateral":
          "降低曝險或增加合格擔保品",
        "No material structural weakness identified in the synthetic inputs":
          "合成輸入未識別重大結構弱點",
        "Maintain proposed structure and reporting": "維持擬議結構與報告要求",
      } as Record<string, string>
    )[value] ?? "依案件結構與政策評估。"
  );
}

export function FacilityProtectionPage({
  analysis,
  language,
  locale,
}: {
  analysis: Analysis;
  language: "en" | "zh-TW";
  locale: string;
}) {
  const zh = language === "zh-TW";
  const facility = analysis.facility_protection;
  const base = analysis.borrowing_base;
  return (
    <>
      <div className="score-hero facility-score">
        <div>
          <p>{zh ? "設施保障分數" : "Facility protection score"}</p>
          <strong>{facility.score}</strong>
          <span>/ 100</span>
        </div>
        <div>
          <p>{zh ? "保障類別" : "Protection category"}</p>
          <strong className="word">{status(facility.category, zh)}</strong>
        </div>
        <div>
          <p>{zh ? "預期回收類別" : "Expected recovery"}</p>
          <strong className="word">
            {status(facility.expected_recovery_category, zh)}
          </strong>
        </div>
      </div>
      <p className="synthetic-notice">
        {zh
          ? "設施保障與債務人評等分開計算；較強的擔保不會提高債務人評等。"
          : "Facility protection is separate from the obligor grade; stronger collateral does not improve borrower credit quality."}
      </p>
      <article className="panel table-panel" tabIndex={0}>
        <h3>{zh ? "保障因素" : "Protection factors"}</h3>
        <table>
          <caption className="sr-only">
            {zh
              ? "設施保障因素與分數"
              : "Facility protection factors and scores"}
          </caption>
          <thead>
            <tr>
              <th>{zh ? "因素" : "Factor"}</th>
              <th>{zh ? "分數" : "Score"}</th>
              <th>{zh ? "解讀" : "Interpretation"}</th>
            </tr>
          </thead>
          <tbody>
            {Object.entries(facility.factors).map(([key, value]) => (
              <tr key={key}>
                <td>{factorLabels[key]?.[zh ? 1 : 0] ?? key}</td>
                <td>{value}</td>
                <td>
                  {Number(value) >= 80
                    ? zh
                      ? "強"
                      : "Strong"
                    : Number(value) >= 60
                      ? zh
                        ? "良好"
                        : "Adequate"
                      : zh
                        ? "需改善"
                        : "Needs improvement"}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </article>
      <div className="two-column facility-lists">
        <article className="panel">
          <h3>
            <ShieldCheck size={19} /> {zh ? "主要保障" : "Main protections"}
          </h3>
          <ul>
            {facility.main_protections.map((item) => (
              <li key={item}>{facilityText(item, zh)}</li>
            ))}
          </ul>
        </article>
        <article className="panel copper">
          <h3>
            <TriangleAlert size={19} />{" "}
            {zh ? "結構弱點" : "Structural weaknesses"}
          </h3>
          <ul>
            {facility.main_structural_weaknesses.map((item) => (
              <li key={item}>{facilityText(item, zh)}</li>
            ))}
          </ul>
        </article>
      </div>
      <article className="panel borrowing-base-panel">
        <div className="panel-head">
          <div>
            <h3>{zh ? "借款基礎" : "Borrowing base"}</h3>
            <p>
              {zh
                ? "僅適用於資產基礎融資。"
                : "Applicable only to asset-based facilities."}
            </p>
          </div>
          <span className="pill">{status(base.status, zh)}</span>
        </div>
        {base.borrowing_base ? (
          <div className="stats-grid">
            <div className="stat">
              <span>{zh ? "應收帳款可用額" : "AR availability"}</span>
              <strong>
                {money(base.receivables_availability!, locale, true)}
              </strong>
            </div>
            <div className="stat">
              <span>{zh ? "存貨可用額" : "Inventory availability"}</span>
              <strong>
                {money(base.inventory_availability!, locale, true)}
              </strong>
            </div>
            <div className="stat">
              <span>{zh ? "準備與優先權" : "Reserves and liens"}</span>
              <strong>
                {money(
                  {
                    ...base.reserves!,
                    amount_minor:
                      base.reserves!.amount_minor +
                      base.prior_liens!.amount_minor,
                  },
                  locale,
                  true,
                )}
              </strong>
            </div>
            <div className="stat">
              <span>{zh ? "最終借款基礎" : "Final borrowing base"}</span>
              <strong>{money(base.borrowing_base, locale, true)}</strong>
            </div>
          </div>
        ) : (
          <p>
            {zh
              ? "此額度不適用借款基礎，或尚缺少合格擔保品輸入。"
              : "Borrowing base is not applicable or eligible-collateral inputs are incomplete."}
          </p>
        )}
        <small>
          {zh ? "示意政策預支率；不構成授信承諾。" : base.policy_notice}
        </small>
      </article>
    </>
  );
}
