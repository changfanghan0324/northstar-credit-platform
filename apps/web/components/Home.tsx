"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { ArrowRight, Building2, ChartNoAxesCombined, FileCheck2, LoaderCircle, ShieldCheck } from "lucide-react";
import { useEffect, useState } from "react";
import { Header } from "./Header";
import { api, money } from "@/lib/api";
import { type Language, prefix, t } from "@/lib/i18n";
import type { DemoCase } from "@/lib/types";

const demoZh: Record<string, { name: string; industry: string; description: string }> = {
  "stable-manufacturer": { name: "穩健製造公司", industry: "工業製造", description: "具穩定現金流、適度槓桿與可預測資本支出的合成製造商。" },
  "cyclical-distributor": { name: "週期性經銷公司", industry: "工業經銷", description: "受景氣循環、營運資金需求與較薄財務契約餘裕影響的合成經銷商。" },
  "software-services": { name: "軟體服務公司", industry: "軟體服務", description: "具高續約收入、低資本密集度與有限擔保品支援的合成服務公司。" },
};

function localizedOutcome(value: string, zh: boolean): string {
  if (!zh) return value;
  return ({ "Approve": "核准", "Approve with conditions": "附條件核准", "Reduce requested amount": "降低申請額度", "Refer to credit committee": "提交信審會", "Decline": "婉拒" } as Record<string, string>)[value] ?? value;
}

export function Home({ language }: { language: Language }) {
  const text = t(language); const root = prefix(language); const locale = language === "en" ? "en-US" : "zh-TW";
  const [cases, setCases] = useState<DemoCase[]>([]); const [loading, setLoading] = useState(""); const [error, setError] = useState(""); const router = useRouter();
  useEffect(() => { api.demos().then(setCases).catch(() => setError(language === "en" ? "The live analysis service is temporarily unavailable." : "即時分析服務暫時無法使用。")); }, [language]);
  async function open(slug: string) { setLoading(slug); setError(""); try { const result = await api.openDemo(slug); router.push(`${root}/app/cases/${result.id}/overview`); } catch { setError(language === "en" ? "Unable to open this case." : "無法開啟此案件。"); } finally { setLoading(""); } }
  return <><Header language={language}/><main>
    <section className="hero"><h1>{text.hero}</h1><p className="hero-copy">{text.subhero}</p><p className="privacy-inline">{language==="en"?"Synthetic demonstration only. Do not enter confidential information.":"僅供合成資料示範。請勿輸入機密資訊。"}</p><div className="actions"><Link className="button primary" href={`${root}/app/cases/new`}>{text.start}<ArrowRight size={17}/></Link><button className="button secondary" disabled={cases.length===0||Boolean(loading)} onClick={() => open(cases[0].slug)}>{cases.length===0?(language==="en"?"Loading sample…":"載入範例中…"):text.explore}</button><Link className="button ghost" href={`${root}/app/cases`}>{language==="en"?"View my cases":"查看我的案件"}</Link></div><div className="question-strip"><span><ShieldCheck size={17}/>{language==="en"?"Credit grade":"信用評等"}</span><span><ChartNoAxesCombined size={17}/>{language==="en"?"Debt capacity":"債務容量"}</span><span><FileCheck2 size={17}/>{language==="en"?"Decision & terms":"決策與條件"}</span></div></section>
    <section className="section"><div className="section-heading"><p className="eyebrow">{language==="en"?"Live demonstration":"即時示範"}</p><h2>{text.samples}</h2><p>{text.sampleIntro}</p></div>{error && <p className="error">{error}</p>}<div className="case-grid">{cases.length === 0 && !error ? [0,1,2].map(i => <div className="case-card skeleton" key={i}/>) : cases.map(item => {const localized=demoZh[item.slug];return <article className="case-card" key={item.slug}><div className="case-icon"><Building2 size={20}/></div><p className="case-industry">{language==="zh-TW"&&localized?localized.industry:item.borrower.industry}</p><h3>{language==="zh-TW"&&localized?localized.name:item.borrower.legal_name}</h3><p>{language==="zh-TW"&&localized?localized.description:item.borrower.description}</p><dl><div><dt>{language === "en" ? "Request" : "申請額"}</dt><dd>{money(item.request.amount, locale, true)}</dd></div><div><dt>{language === "en" ? "Grade" : "評等"}</dt><dd>{item.grade??"—"}</dd></div><div><dt>{language === "en" ? "Recommended" : "建議額度"}</dt><dd>{money(item.recommended, locale, true)}</dd></div></dl><p className="decision-label">{localizedOutcome(item.decision.outcome,language==="zh-TW")}</p><button className="text-action" onClick={() => open(item.slug)} disabled={Boolean(loading)}>{loading === item.slug ? <LoaderCircle className="spin" size={17}/> : null}{text.workspace}<ArrowRight size={16}/></button></article>;})}</div></section>
    <section className="process"><div><p className="eyebrow">{language==="en"?"Underwriting flow":"授信流程"}</p><h2>{text.how}</h2></div><ol><li><strong>01</strong><span>{language === "en" ? "Normalize borrower and facility inputs" : "標準化借款人與授信條件"}</span></li><li><strong>02</strong><span>{language === "en" ? "Calculate risk, capacity, and stress" : "計算風險、容量與壓力結果"}</span></li><li><strong>03</strong><span>{language === "en" ? "Set terms and export the memo" : "設定條件並輸出授信備忘錄"}</span></li></ol></section>
  </main><footer><span>Northstar Credit Platform</span><span>{language === "en" ? "Educational analysis · Synthetic data only" : "教育用途分析 · 僅使用合成資料"}</span></footer></>;
}
