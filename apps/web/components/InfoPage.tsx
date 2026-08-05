import Link from "next/link";
import { Header } from "./Header";
import { type Language, prefix } from "@/lib/i18n";

const pages = {
  methodology: {
    en: ["Methodology", "How Northstar turns company facts into a lending recommendation.", ["Exact money and typed metric states", "Transparent score weights and policy bands", "Leverage, DSCR, collateral, and policy capacity", "Three deterministic scenarios and covenant headroom", "Rule-based decision and memo provenance"]],
    "zh-TW": ["方法論", "Northstar 如何將公司資料轉換成授信建議。", ["精確貨幣與具型別的指標狀態", "透明的評分權重與政策區間", "槓桿、DSCR、擔保品與政策容量", "三種確定性情境與財務契約餘裕", "規則式決策與備忘錄溯源"]],
  },
  "technical-validation": {
    en: ["Technical validation", "One calculation contract from inputs through API, interface, and PDF.", ["Integer minor-unit money; no binary floating point", "Four-decimal ratio display with exact covenant comparisons", "Versioned policy hash and input hash", "Strict Python and TypeScript checks", "Synthetic cases and reproducible deterministic outputs"]],
    "zh-TW": ["技術驗證", "從輸入、API、介面到 PDF，使用同一份計算契約。", ["貨幣以整數最小單位儲存，不使用二進位浮點數", "比率顯示至四位小數，契約比較採精確值", "版本化政策雜湊與輸入雜湊", "嚴格 Python 與 TypeScript 檢查", "合成案例與可重現的確定性輸出"]],
  },
  about: {
    en: ["About Northstar", "An educational, transparent corporate-credit underwriting workspace.", ["Built for learning and portfolio demonstration", "Uses synthetic borrower data only", "Does not represent a bank, rating agency, or lending commitment", "Makes policy limits and binding constraints visible", "Designed for both guided learners and analyst review"]],
    "zh-TW": ["關於 Northstar", "一套教育用途、透明的企業授信分析工作區。", ["用於學習與作品集展示", "僅使用合成借款人資料", "不代表銀行、評等機構或授信承諾", "清楚呈現政策限制與具約束力的條件", "同時支援引導學習與分析師檢視"]],
  },
} as const;

export function InfoPage({ language, page }: { language: Language; page: string }) { const selected=pages[page as keyof typeof pages] ?? pages.about; const [title,intro,items]=selected[language]; const root=prefix(language); return <><Header language={language}/><main className="info-page"><p className="eyebrow">Northstar reference</p><h1>{title}</h1><p className="lead">{intro}</p><div className="info-list">{items.map((item,i)=><article key={item}><span>{String(i+1).padStart(2,"0")}</span><h2>{item}</h2></article>)}</div><Link className="button primary" href={`${root}/app/cases/new`}>{language==="en"?"Start a calculated case":"建立可計算案件"}</Link></main></>; }
