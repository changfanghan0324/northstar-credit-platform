"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { ArrowRight, Building2, ChartNoAxesCombined, FileCheck2, Landmark, LoaderCircle, ShieldCheck } from "lucide-react";
import { useEffect, useState } from "react";
import { Header } from "./Header";
import { api, money } from "@/lib/api";
import { type Language, prefix, t } from "@/lib/i18n";
import type { DemoCase } from "@/lib/types";

export function Home({ language }: { language: Language }) {
  const text = t(language); const root = prefix(language); const locale = language === "en" ? "en-US" : "zh-TW";
  const [cases, setCases] = useState<DemoCase[]>([]); const [loading, setLoading] = useState(""); const [error, setError] = useState(""); const router = useRouter();
  useEffect(() => { api.demos().then(setCases).catch(() => setError(language === "en" ? "The live analysis service is temporarily unavailable." : "即時分析服務暫時無法使用。")); }, [language]);
  async function open(slug: string) { setLoading(slug); setError(""); try { const result = await api.openDemo(slug); router.push(`${root}/app/cases/${result.id}/overview`); } catch { setError(language === "en" ? "Unable to open this case." : "無法開啟此案件。"); } finally { setLoading(""); } }
  return <><Header language={language}/><main>
    <section className="hero"><p className="eyebrow"><Landmark size={16}/> Corporate credit underwriting</p><h1>{text.hero}</h1><p className="hero-copy">{text.subhero}</p><div className="actions"><Link className="button primary" href={`${root}/app/cases/new`}>{text.start}<ArrowRight size={17}/></Link><button className="button secondary" onClick={() => cases[0] && open(cases[0].slug)}>{text.explore}</button></div><div className="question-strip"><span><ShieldCheck size={17}/> Credit grade</span><span><ChartNoAxesCombined size={17}/> Debt capacity</span><span><FileCheck2 size={17}/> Decision & terms</span></div></section>
    <section className="section"><div className="section-heading"><p className="eyebrow">Live demonstration</p><h2>{text.samples}</h2><p>{text.sampleIntro}</p></div>{error && <p className="error">{error}</p>}<div className="case-grid">{cases.length === 0 && !error ? [0,1,2].map(i => <div className="case-card skeleton" key={i}/>) : cases.map(item => <article className="case-card" key={item.slug}><div className="case-icon"><Building2 size={20}/></div><p className="case-industry">{item.borrower.industry}</p><h3>{item.borrower.legal_name}</h3><p>{item.borrower.description}</p><dl><div><dt>{language === "en" ? "Request" : "申請額"}</dt><dd>{money(item.request.amount, locale, true)}</dd></div><div><dt>{language === "en" ? "Grade" : "評等"}</dt><dd>{item.grade}</dd></div><div><dt>{language === "en" ? "Recommended" : "建議額度"}</dt><dd>{money(item.recommended, locale, true)}</dd></div></dl><p className="decision-label">{item.decision.outcome}</p><button className="text-action" onClick={() => open(item.slug)} disabled={Boolean(loading)}>{loading === item.slug ? <LoaderCircle className="spin" size={17}/> : null}{text.workspace}<ArrowRight size={16}/></button></article>)}</div></section>
    <section className="process"><div><p className="eyebrow">Underwriting flow</p><h2>{text.how}</h2></div><ol><li><strong>01</strong><span>{language === "en" ? "Normalize borrower and facility inputs" : "標準化借款人與授信條件"}</span></li><li><strong>02</strong><span>{language === "en" ? "Calculate risk, capacity, and stress" : "計算風險、容量與壓力結果"}</span></li><li><strong>03</strong><span>{language === "en" ? "Set terms and export the memo" : "設定條件並輸出授信備忘錄"}</span></li></ol></section>
  </main><footer><span>Northstar Credit Platform</span><span>{language === "en" ? "Educational analysis · Synthetic data only" : "教育用途分析 · 僅使用合成資料"}</span></footer></>;
}
