import Link from "next/link";
import { Header } from "./Header";
import { type Language, prefix } from "@/lib/i18n";

type Entry = { title: string; body: string };
type PageCopy = { title: string; intro: string; entries: Entry[] };

const pages: Record<string, Record<Language, PageCopy>> = {
  methodology: {
    en: { title: "Methodology", intro: "A transparent path from supplied company facts to a lending recommendation.", entries: [
      { title: "Normalize the case", body: "Borrower, facility, financial, debt, business-risk, and scenario inputs are validated before calculation. Money remains integer minor units in one reporting currency." },
      { title: "Calculate operating performance", body: "Reported EBITDA is reconciled to adjusted EBITDA. Cash flow available for debt service deducts cash taxes, working-capital investment, maintenance capital spending, and other mandatory uses." },
      { title: "Measure credit risk", body: "Leverage, coverage, liquidity, cash-flow, and business-risk factors use typed states. Missing or invalid critical measures block the grade; they never become zero." },
      { title: "Size debt capacity", body: "The recommendation is the minimum valid, applicable constraint: leverage, DSCR, collateral when applicable, and policy. A zero supported amount always results in decline." },
      { title: "Stress three years", body: "Base, downside, and severe cases roll beginning debt, interest on average debt, amortization, cash shortfall, revolver draws, ending cash, and refinancing needs forward." },
      { title: "Solve reverse stress", body: "A bounded bisection solver estimates the revenue decline that reaches minimum DSCR and reports bounds, tolerance, iterations, residual, and convergence." },
      { title: "Apply policy and terms", body: "Active leverage, coverage, maturity, liquidity, currency, exposure, covenant, and monitoring rules are evaluated before the decision priority is applied." },
      { title: "Record provenance", body: "Each result includes engine and policy versions, a policy hash, a case-and-model input hash, calculation time, memo sections, and an immutable audit event." },
      { title: "Ratio definitions", body: "Each ratio exposes its numerator, denominator, direction, source period, formula identifier, typed state, and active policy reference." },
      { title: "EBITDA adjustments", body: "Positive and negative adjustments remain visible. Material add-backs reduce confidence and are tested against an explicit policy ceiling." },
      { title: "CFADS and DSCR", body: "CFADS deducts cash taxes, maintenance capital expenditure, working-capital investment, and mandatory pension uses. DSCR divides CFADS by cash interest plus scheduled principal." },
      { title: "Score weights", body: "Financial, liquidity, cash-flow, and qualitative components retain their configured weights. A blocked critical component prevents a numeric grade." },
      { title: "Grade mapping", body: "The weighted obligor score maps to an internal grade only after all critical measures are scoreable and minimum data-confidence policy is met." },
      { title: "Covenant design", body: "Maintenance, reporting, and liquidity covenants respond to facility type, collateral reliance, downside headroom, and borrower risk." },
      { title: "Confidence", body: "Confidence is separate from credit quality. It falls for synthetic evidence, missing debt schedules, material adjustments, weak qualitative evidence, or blocked calculations." },
      { title: "Overrides and exceptions", body: "Hard stops cannot be silently overridden. Eligible warnings identify the required approval, remediation, and decision impact." },
      { title: "Applicability", body: "Not-applicable constraints remain distinct from zero and blocked values; only valid applicable constraints can determine supported exposure." },
      { title: "Currency integrity", body: "Every monetary input in a case must use one reporting currency. Mixed-currency requests fail validation before analysis." },
      { title: "Model limitations", body: "This educational model does not replace borrower verification, legal review, sanctions screening, fraud controls, collateral appraisal, or authorized credit judgment." },
      { title: "Audit and reproducibility", body: "Versioned inputs, immutable analyses, audit events, policy hashes, tests, and public review evidence support independent reproduction of each conclusion." },
    ]},
    "zh-TW": { title: "方法論", intro: "從公司輸入資料到授信建議，提供透明且可追溯的完整路徑。", entries: [
      { title: "標準化案件", body: "計算前會驗證借款人、授信結構、財務、債務、營運風險與情境資料。貨幣全程以單一報導幣別的整數最小單位處理。" },
      { title: "計算營運表現", body: "系統會將報導 EBITDA 調節為調整後 EBITDA；可供償債現金流扣除現金稅、營運資金投入、維持性資本支出與其他必要用途。" },
      { title: "衡量信用風險", body: "槓桿、償債、流動性、現金流與營運風險使用具型別狀態。缺少或無效的關鍵指標會阻擋評等，絕不自動當成零。" },
      { title: "決定債務容量", body: "建議額度取所有有效且適用限制中的最低值，包括槓桿、DSCR、適用時的擔保品及政策上限。可支援額度為零時必須婉拒。" },
      { title: "執行三年壓力測試", body: "基準、下行與嚴重壓力情境會逐年推演期初債務、平均債務利息、攤還、現金缺口、循環額度動用、期末現金與再融資需求。" },
      { title: "求解反向壓力", body: "有界二分法求解到達最低 DSCR 的營收跌幅，並揭露上下界、容許誤差、迭代次數、殘差與是否收斂。" },
      { title: "套用政策與條件", body: "在決策優先規則之前，系統檢查槓桿、覆蓋率、到期日、流動性、幣別、曝險、財務契約與監控規則。" },
      { title: "保留溯源", body: "每次結果包含引擎與政策版本、政策雜湊、案件與模型輸入雜湊、計算時間、備忘錄內容及不可變更的稽核事件。" },
      { title: "比率定義", body: "每個比率均揭露分子、分母、方向、資料期間、公式識別碼、具型別狀態及適用政策。" },
      { title: "EBITDA 調整", body: "正向與負向調整均保持可見；重大加回會降低資料信心，並接受明確的政策上限檢查。" },
      { title: "CFADS 與 DSCR", body: "CFADS 扣除現金稅、維持性資本支出、營運資金投入及必要退休金用途；DSCR 以 CFADS 除以現金利息與預定本金。" },
      { title: "評分權重", body: "財務、流動性、現金流與質化因素保留政策設定權重；任何關鍵項目遭阻擋時，不會產生數字評等。" },
      { title: "評等對應", body: "只有在所有關鍵指標可評分，且符合最低資料信心政策後，加權債務人分數才會對應內部評等。" },
      { title: "財務契約設計", body: "維持性、報告與流動性契約會依額度類型、擔保依賴、下行餘裕及借款人風險動態調整。" },
      { title: "資料信心", body: "信心與信用品質分開衡量；合成證據、缺少債務明細、重大調整、質化證據不足或計算遭阻擋都會降低信心。" },
      { title: "覆核與例外", body: "硬性停止不得靜默覆寫；可申請例外的警示會列出所需核准層級、補救方式及決策影響。" },
      { title: "適用性", body: "不適用限制與零值、阻擋值保持區分；只有有效且適用的限制可以決定可支援曝險。" },
      { title: "幣別完整性", body: "同一案件的所有貨幣輸入必須使用單一報導幣別；混合幣別會在分析前驗證失敗。" },
      { title: "模型限制", body: "本教育模型不能取代借款人驗證、法律審查、制裁篩檢、詐欺控制、擔保品鑑價或具授權授信判斷。" },
      { title: "稽核與重現", body: "版本化輸入、不可變分析、稽核事件、政策雜湊、測試與公開審查證據，可供獨立重現每項結論。" },
    ]},
  },
  "technical-validation": {
    en: { title: "Technical validation", intro: "One deterministic calculation contract from request to API, interface, and PDF.", entries: [
      { title: "Exact numeric boundary", body: "Money uses integer minor units; ratios and rates use Python Decimal and serialized decimal strings. The browser formats values but does not calculate credit conclusions." },
      { title: "Typed failure states", body: "Valid, missing-input, invalid-denominator, not-meaningful, blocked, and policy-not-applicable states remain distinct through scoring and display." },
      { title: "Deterministic outputs", body: "Identical case, engine, and policy inputs produce the same input hash and financial result. Calculation time is metadata, not a model input." },
      { title: "Verification gates", body: "The repository gate runs Ruff, formatting, strict Mypy, unit/invariant/integration tests, branch-aware coverage, ESLint, strict TypeScript, and a production Next.js build." },
      { title: "Session isolation", body: "The server issues a cryptographic HttpOnly cookie, stores only its hash, enforces ownership on every case route, and applies anonymous quotas and payload/PDF limits." },
      { title: "Deployment truthfulness", body: "The runtime endpoint reports durable PostgreSQL or temporary-session mode. The interface never claims persistence when a production database is absent." },
    ]},
    "zh-TW": { title: "技術驗證", intro: "從請求、API、介面到 PDF，共用同一套確定性計算契約。", entries: [
      { title: "精確數值邊界", body: "貨幣使用整數最小單位；比率與利率使用 Python Decimal 並序列化為十進位字串。瀏覽器只負責格式化，不計算授信結論。" },
      { title: "具型別失敗狀態", body: "有效、缺少輸入、分母無效、不具意義、已阻擋與政策不適用等狀態，從評分到畫面都保持區分。" },
      { title: "確定性輸出", body: "相同案件、引擎與政策輸入會產生相同輸入雜湊及財務結果；計算時間只是中繼資料，不是模型輸入。" },
      { title: "驗證關卡", body: "Repository 閘門執行 Ruff、格式、Strict Mypy、單元／不變量／整合測試、分支覆蓋率、ESLint、Strict TypeScript 與 Next.js production build。" },
      { title: "工作階段隔離", body: "伺服器發出密碼學隨機 HttpOnly Cookie，只儲存其雜湊；所有案件路由都驗證擁有權，並套用匿名配額與內容／PDF 限制。" },
      { title: "如實揭露部署狀態", body: "Runtime API 會回報 PostgreSQL 持久模式或暫時工作階段；沒有正式資料庫時，介面不會聲稱資料能持久保存。" },
    ]},
  },
  about: {
    en: { title: "About Northstar", intro: "An educational corporate-credit workspace built for transparent reasoning, not automated lending.", entries: [
      { title: "Purpose", body: "Northstar helps learners and evaluators follow how a corporate lending case moves from facts to ratios, capacity, stress, terms, and a credit memo." },
      { title: "Audience", body: "Plain-language conclusions support first-time reviewers; the same values gain lineage, formula, policy, and confidence context in Analyst mode." },
      { title: "Data", body: "The three demonstrations are synthetic. Custom public cases must also use synthetic information; confidential, personal, or regulated data must not be entered." },
      { title: "Limits", body: "Northstar is not a bank, rating agency, credit opinion, investment product, accounting service, legal service, or lending commitment." },
      { title: "Privacy", body: "There is no user account. Anonymous cases are session-scoped, quota-limited, and designed to expire after seven days when durable storage is configured." },
      { title: "Open evidence", body: "The public repository contains methodology, policy, architecture, audit, cross-model review, tests, and deployment documentation." },
    ]},
    "zh-TW": { title: "關於 Northstar", intro: "一套重視透明推理的教育用企業授信工作區，不是自動放款系統。", entries: [
      { title: "目的", body: "Northstar 協助學習者與評估者理解企業授信如何從事實，走到比率、容量、壓力、條件與授信備忘錄。" },
      { title: "使用者", body: "初次檢視者可先看白話結論；分析師模式則在完全相同的數值上加入來源、公式、政策與信心資訊。" },
      { title: "資料", body: "三個示範案例都是合成資料。公開自訂案件也只能使用合成資訊，請勿輸入機密、個人或受監管資料。" },
      { title: "限制", body: "Northstar 不是銀行、評等機構、信用意見、投資產品、會計或法律服務，也不構成授信承諾。" },
      { title: "隱私", body: "本站沒有使用者帳號。匿名案件以工作階段隔離、受配額限制；設定持久儲存時，設計保留期最長為七天。" },
      { title: "公開證據", body: "公開 repository 包含方法論、政策、架構、稽核、跨模型審查、測試與部署文件。" },
    ]},
  },
};

export function InfoPage({ language, page }: { language: Language; page: string }) {
  const selected = pages[page]?.[language] ?? pages.about[language];
  const root = prefix(language);
  return <><Header language={language}/><main className="info-page"><p className="eyebrow">{language==="en"?"Northstar reference":"Northstar 參考資料"}</p><h1>{selected.title}</h1><p className="lead">{selected.intro}</p><div className="reference-grid">{selected.entries.map((entry,index)=><article key={entry.title}><span>{String(index+1).padStart(2,"0")}</span><div><h2>{entry.title}</h2><p>{entry.body}</p></div></article>)}</div><div className="reference-actions"><Link className="button primary" href={`${root}/app/cases/new`}>{language==="en"?"Start a calculated case":"建立可計算案件"}</Link><Link className="button secondary" href={`${root}/app/cases`}>{language==="en"?"View my cases":"查看我的案件"}</Link></div></main></>;
}
