"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { ArrowLeft, Check, CircleAlert, Download, Gauge, LoaderCircle, PanelLeft, SlidersHorizontal } from "lucide-react";
import { useEffect, useState } from "react";
import { Header } from "./Header";
import { api, downloadMemo, money } from "@/lib/api";
import { type Language, prefix } from "@/lib/i18n";
import type { Analysis, CaseEnvelope, Money, ScenarioYear } from "@/lib/types";

const sections = ["overview", "inputs", "financials", "risk", "stress", "decision", "memo"] as const;
const labels = {
  en: ["Overview", "Inputs", "Financials", "Risk", "Stress & covenants", "Decision", "Credit memo"],
  "zh-TW": ["總覽", "輸入", "財務分析", "風險", "壓力測試與契約", "決策", "授信備忘錄"],
};

function ratio(value: string | null) { return value === null ? "N/M" : `${Number(value).toFixed(2)}x`; }
function Stat({ label, value, note }: { label: string; value: string; note?: string }) { return <div className="stat"><span>{label}</span><strong>{value}</strong>{note && <small>{note}</small>}</div>; }
function MoneyStat({ label, value, locale, note }: { label: string; value: Money; locale: string; note?: string }) { return <Stat label={label} value={money(value, locale, true)} note={note}/>; }

function Overview({ a, language, locale }: { a: Analysis; language: Language; locale: string }) {
  const zh = language === "zh-TW";
  return <><div className="decision-banner"><div><p>{zh ? "授信建議" : "Credit recommendation"}</p><h2>{a.decision.outcome}</h2><span>{a.decision.rationale[1]}</span></div><div className="grade-seal"><span>{zh ? "內部評等" : "Internal grade"}</span><strong>{a.scorecard.grade}</strong><small>{a.scorecard.grade_label}</small></div></div><div className="stats-grid"><MoneyStat label={zh ? "申請額" : "Requested"} value={a.capacity.requested} locale={locale}/><MoneyStat label={zh ? "建議額度" : "Recommended"} value={a.capacity.recommended} locale={locale} note={a.capacity.binding_constraints.join(", ")}/><Stat label={zh ? "總槓桿" : "Gross leverage"} value={ratio(a.metrics.gross_leverage.value)}/><Stat label="DSCR" value={ratio(a.metrics.dscr.value)}/></div><div className="two-column"><article className="panel"><h3>{zh ? "主要優勢" : "Key strengths"}</h3><ul className="clean-list">{a.case.business_risk.strengths.map(x => <li key={x}><Check size={17}/>{x}</li>)}</ul></article><article className="panel"><h3>{zh ? "主要風險" : "Key risks"}</h3><ul className="clean-list risks">{a.case.business_risk.risks.map(x => <li key={x}><CircleAlert size={17}/>{x}</li>)}</ul></article></div></>;
}

function Inputs({ a, language, locale, mode }: { a: Analysis; language: Language; locale: string; mode: string }) {
  const zh = language === "zh-TW"; const f = a.case.financials;
  const keys = ["revenue", "ebit", "depreciation_amortization", "cfo", "capex", "cash_interest", "scheduled_principal", "unrestricted_cash", "current_assets", "current_liabilities"];
  return <div className="panel"><div className="panel-head"><div><h3>{zh ? "標準化案件輸入" : "Normalized case inputs"}</h3><p>{mode === "guided" ? (zh ? "引導模式會將欄位依授信問題分組。" : "Guided mode groups fields by the lending question they answer.") : (zh ? "分析師模式顯示來源欄位名稱；底層值完全相同。" : "Analyst mode exposes source field names; underlying values are identical.")}</p></div><span className="as-of">{a.case.data_as_of}</span></div><div className="input-grid">{keys.map(key => { const value = f[key] as Money; return <label key={key}><span>{key.replaceAll("_", " ")}</span><input readOnly value={money(value, locale)}/></label>; })}</div></div>;
}

function Financials({ a, language, locale }: { a: Analysis; language: Language; locale: string }) {
  const zh = language === "zh-TW";
  return <><div className="stats-grid">{Object.entries(a.metrics).slice(0,8).map(([key, value]) => <Stat key={key} label={value.label} value={ratio(value.value)} note={value.status === "ok" ? undefined : value.reason_code}/>)}</div><article className="panel"><h3>{zh ? "授信容量與約束" : "Debt capacity and constraints"}</h3><div className="capacity-bars">{(["leverage", "dscr", "collateral", "policy"] as const).map(key => <div key={key}><span>{key}</span><div><i style={{width: `${Math.min(100, a.capacity[key].amount_minor / Math.max(a.capacity.requested.amount_minor, 1) * 100)}%`}}/></div><strong>{money(a.capacity[key], locale, true)}</strong></div>)}</div></article></>;
}

function Risk({ a, language }: { a: Analysis; language: Language }) {
  const zh = language === "zh-TW";
  return <><div className="score-hero"><div><p>{zh ? "加權債務人分數" : "Weighted obligor score"}</p><strong>{a.scorecard.score}</strong><span>/ 100</span></div><div><p>{zh ? "內部評等" : "Internal grade"}</p><strong>{a.scorecard.grade}</strong><span>{a.scorecard.grade_label}</span></div><div><p>{zh ? "信心程度" : "Confidence"}</p><strong className="word">{a.scorecard.confidence}</strong><span>{zh ? "合成資料" : "synthetic data"}</span></div></div><article className="panel table-panel"><h3>{zh ? "評分組成" : "Score components"}</h3><table><thead><tr><th>{zh ? "因素" : "Factor"}</th><th>{zh ? "分數" : "Score"}</th><th>{zh ? "權重" : "Weight"}</th><th>{zh ? "貢獻" : "Contribution"}</th><th>{zh ? "依據" : "Band / basis"}</th></tr></thead><tbody>{a.scorecard.components.map(c => <tr key={c.key}><td>{c.key.replaceAll("_", " ")}</td><td>{c.score}</td><td>{c.weight}%</td><td>{c.contribution}</td><td>{c.band}</td></tr>)}</tbody></table></article></>;
}

function Stress({ a, language, locale }: { a: Analysis; language: Language; locale: string }) {
  const zh = language === "zh-TW"; const firstYears = a.scenarios.map(s => ({...s.years[0], name:s.name}));
  return <><div className="scenario-grid">{firstYears.map((y: ScenarioYear & {name:string}) => <article className={`scenario-card ${y.covenant_status}`} key={y.name}><p>{y.name}</p><h3>{zh ? "第一年" : "Year 1"}</h3><dl><div><dt>Revenue</dt><dd>{money(y.revenue, locale, true)}</dd></div><div><dt>EBITDA</dt><dd>{money(y.adjusted_ebitda, locale, true)}</dd></div><div><dt>Leverage</dt><dd>{ratio(y.leverage)}</dd></div><div><dt>DSCR</dt><dd>{ratio(y.dscr)}</dd></div></dl><span className="status">{y.covenant_status}</span></article>)}</div><article className="panel table-panel"><h3>{zh ? "財務契約檢驗" : "Covenant testing"}</h3><table><thead><tr><th>{zh ? "情境 / 年度" : "Scenario / year"}</th><th>{zh ? "契約" : "Covenant"}</th><th>{zh ? "實際" : "Actual"}</th><th>{zh ? "門檻" : "Threshold"}</th><th>{zh ? "餘裕" : "Headroom"}</th><th>{zh ? "狀態" : "Status"}</th></tr></thead><tbody>{a.covenants.map((c,i) => <tr key={`${c.scenario}-${c.year}-${c.name}-${i}`}><td>{c.scenario} / {c.year}</td><td>{c.name}</td><td>{c.actual}x</td><td>{c.threshold}x</td><td>{c.headroom}x</td><td><span className={`pill ${c.status}`}>{c.status}</span></td></tr>)}</tbody></table></article><div className="reverse-strip"><Gauge size={22}/><div><strong>{zh ? "反向壓力測試" : "Reverse stress"}</strong><span>{zh ? `DSCR 降至最低門檻的營收下降幅度：${a.reverse_stress.dscr_minimum_revenue_decline}%` : `Revenue decline to minimum DSCR: ${a.reverse_stress.dscr_minimum_revenue_decline}%`}</span></div></div></>;
}

function Decision({ a, language, locale }: { a: Analysis; language: Language; locale: string }) { const zh = language === "zh-TW"; return <><div className="decision-banner"><div><p>{zh ? "最終授信建議" : "Final credit recommendation"}</p><h2>{a.decision.outcome}</h2><span>{zh ? "由政策、容量與壓力結果決定" : "Determined by policy, capacity, and stress results"}</span></div><MoneyStat label={zh ? "建議額度" : "Recommended amount"} value={a.capacity.recommended} locale={locale}/></div><div className="two-column"><article className="panel"><h3>{zh ? "決策理由" : "Decision rationale"}</h3><ol>{a.decision.rationale.map(x => <li key={x}>{x}</li>)}</ol><h3>{zh ? "還款來源" : "Repayment sources"}</h3><p><strong>{zh ? "主要：" : "Primary: "}</strong>{a.decision.primary_repayment_source}</p><p><strong>{zh ? "次要：" : "Secondary: "}</strong>{a.decision.secondary_repayment_source}</p></article><article className="panel copper"><h3>{zh ? "核准條件" : "Proposed conditions"}</h3><ul>{a.decision.conditions.map(x => <li key={x}>{x}</li>)}</ul></article></div></>; }

function Memo({ a, language, onDownload }: { a: Analysis; language: Language; onDownload: () => void }) { const zh = language === "zh-TW"; return <article className="memo-paper"><header><p>NORTHSTAR CREDIT MEMORANDUM</p><h2>{a.case.borrower.legal_name}</h2><span>{a.case.data_as_of}</span></header>{Object.entries(a.memo_sections).map(([title, paragraphs]) => <section key={title}><h3>{title.replaceAll("_", " ")}</h3>{paragraphs.map((p,i) => <p key={i}>{p}</p>)}</section>)}<footer><small>Input hash: {a.input_hash}</small></footer><button className="button primary memo-download" onClick={onDownload}><Download size={17}/>{zh ? "下載 PDF" : "Download PDF"}</button></article>; }

export function CaseWorkspace({ caseId, section, language }: { caseId: string; section: string; language: Language }) {
  const root = prefix(language); const locale = language === "en" ? "en-US" : "zh-TW"; const [data,setData] = useState<CaseEnvelope|null>(null); const [error,setError] = useState(""); const [mode,setMode] = useState("guided"); const router=useRouter();
  useEffect(() => { api.getCase(caseId).then(setData).catch(e => setError(String(e))); }, [caseId]);
  if (error) return <><Header language={language}/><main className="center-state"><CircleAlert/><h2>{language === "en" ? "This case could not be loaded" : "無法載入此案件"}</h2><p>{error}</p><Link href={`${root}/`}>{language === "en" ? "Return home" : "返回首頁"}</Link></main></>;
  if (!data?.analysis) return <main className="center-state"><LoaderCircle className="spin"/><p>{language === "en" ? "Loading calculated case…" : "載入計算結果…"}</p></main>;
  const a=data.analysis; const idx=Math.max(0,sections.indexOf(section as typeof sections[number]));
  return <><Header language={language}/><div className="workspace-shell"><aside><Link className="back" href={`${root}/`}><ArrowLeft size={16}/>{language === "en" ? "All cases" : "所有案件"}</Link><div className="borrower-mark"><span>{a.case.borrower.legal_name.slice(0,2).toUpperCase()}</span><div><strong>{a.case.borrower.legal_name}</strong><small>{a.case.borrower.industry}</small></div></div><nav>{sections.map((item,i)=><Link key={item} className={i===idx ? "active" : ""} href={`${root}/app/cases/${caseId}/${item}`}><span>{String(i+1).padStart(2,"0")}</span>{labels[language][i]}</Link>)}</nav><div className="mode-switch"><p><SlidersHorizontal size={15}/>{language === "en" ? "Workspace mode" : "工作區模式"}</p><div><button className={mode==="guided"?"active":""} onClick={()=>setMode("guided")}>{language === "en"?"Guided":"引導"}</button><button className={mode==="analyst"?"active":""} onClick={()=>setMode("analyst")}>{language === "en"?"Analyst":"分析師"}</button></div></div></aside><main className="workspace"><div className="workspace-top"><div><p className="eyebrow">{labels[language][idx]}</p><h1>{idx===0 ? a.case.borrower.legal_name : labels[language][idx]}</h1></div><div className="top-meta"><span>{language === "en" ? "Calculated" : "計算時間"}<strong>{new Date(a.calculated_at).toLocaleDateString(locale)}</strong></span><button title="Toggle navigation" onClick={()=>router.refresh()}><PanelLeft size={18}/></button></div></div>
  {sections[idx]==="overview"&&<Overview a={a} language={language} locale={locale}/>} {sections[idx]==="inputs"&&<Inputs a={a} language={language} locale={locale} mode={mode}/>} {sections[idx]==="financials"&&<Financials a={a} language={language} locale={locale}/>} {sections[idx]==="risk"&&<Risk a={a} language={language}/>} {sections[idx]==="stress"&&<Stress a={a} language={language} locale={locale}/>} {sections[idx]==="decision"&&<Decision a={a} language={language} locale={locale}/>} {sections[idx]==="memo"&&<Memo a={a} language={language} onDownload={()=>downloadMemo(caseId)}/>}</main></div></>;
}
