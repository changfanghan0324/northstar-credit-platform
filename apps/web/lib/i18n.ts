export type Language = "en" | "zh-TW";

const copy = {
  en: {
    product: "Northstar Credit Platform",
    nav: ["Methodology", "Technical validation", "About"],
    hero: "Should we lend to this company? If yes, how much—and under what terms?",
    subhero:
      "A transparent underwriting workspace that connects borrower inputs to credit grade, debt capacity, stress performance, covenants, and a committee-ready memo.",
    start: "Start a credit case",
    explore: "Explore a sample case",
    samples: "Three computed borrower profiles",
    sampleIntro:
      "Each profile is synthetic. Every grade, capacity limit, scenario, and decision is calculated through the same API used by the analyst workspace.",
    how: "From borrower facts to a lending decision",
    workspace: "Open workspace",
    language: "繁體中文",
  },
  "zh-TW": {
    product: "Northstar 企業授信平台",
    nav: ["方法論", "技術驗證", "關於"],
    hero: "銀行該不該借錢給這家公司？如果要借，該借多少、設定什麼條件？",
    subhero:
      "一套透明的企業授信工作區，將借款人資料連結到信用評等、負債能力、壓力測試、財務契約與可提交信審會的備忘錄。",
    start: "建立授信案件",
    explore: "查看範例案件",
    samples: "三個即時計算的借款人輪廓",
    sampleIntro:
      "所有公司均為合成案例；評等、授信容量、情境與決策皆由分析工作區使用的同一 API 即時計算。",
    how: "從公司資料到授信決策",
    workspace: "開啟工作區",
    language: "English",
  },
} as const;

export function t(language: Language) {
  return copy[language];
}
export function prefix(language: Language) {
  return language === "zh-TW" ? "/zh-TW" : "";
}
