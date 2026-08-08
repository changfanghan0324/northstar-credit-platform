# Northstar 企業授信平台

**語言：** [English](README.md) | [繁體中文](README.zh-TW.md)

> 銀行該不該借錢給這家公司？如果要借，該借多少、設定什麼條件？

Northstar 是一套完整的教育用途企業授信工作區。它會把標準化的借款人與授信
條件連結到財務比率、透明的信用分數與評等、債務容量、獨立設施保障、選配借款
基礎、三年壓力情境、六個數值反向壓力求解器、透明示意定價、擬議條件，以及
本地化授信備忘錄 PDF。

## 公開產品

- 網站：https://northstar-credit-platform.vercel.app
- 英文：`/`
- 繁體中文：`/zh-TW/`
- 三個合成案例：穩健製造商、週期性經銷商、軟體服務公司
- 工作區：總覽、輸入、財務分析、債務容量、設施保障、風險、壓力測試與契約、決策與條件、授信備忘錄
- 模式：引導與分析師模式是同一組輸入與計算輸出的兩種漸進式呈現
- 分析師輸入支援多期損益表、資產負債表、現金流量表、CSV 範本、Excel 貼上、期間複製／移除、調節與明確 LTM 方法
- 正常化調整與定性營運風險因素必須有理由、證據、來源及覆核狀態，才能支持最終評等
- 財務解析器會保留一個不可變的已報告／推導 LTM 財務快照；非空但無法驗證的多期資料會阻擋最終評等與定價，不會靜默沿用過期舊數字。壓力情境明確區分定期攤還、到期還本、部分攤還與循環額度機制。

所有借款人資料均為合成資料。Northstar 是教育與作品集展示，不是銀行、評等
機構、信用意見或放款承諾。

## 架構

```text
Next.js 16 + Strict TypeScript
            │
            ▼
FastAPI + Pydantic 契約
            │
            ▼
credit_app 編排層 ── 版本化 YAML 政策
            │
            ▼
Decimal-safe credit_engine
            │
            ▼
SQLAlchemy 儲存層 + Alembic migrations
```

Northstar 明確採用**作品集展示模式（Mode A）**。可透過 `DATABASE_URL` 使用
PostgreSQL；本機與暫時性展示環境則使用 `/tmp` 內的 SQLite。公開案件僅限合成
資料，採匿名工作階段隔離、配額限制，並於七天後到期；`/runtime` API 會如實
揭露限制。貨幣採精確整數最小貨幣單位；契約與瀏覽器解析器會拒絕超出
JavaScript 安全整數範圍、錯誤千分位、科學記號或超出幣別精度的輸入。比率則
序列化為十進位字串。

## 本機執行

Python API：

```sh
PYTHONPATH=packages/credit_engine:packages/credit_app:packages/policy:apps/api \
  .venv-rebuilt/bin/uvicorn northstar_api.main:app --reload
```

網站：

```sh
cd apps/web
pnpm install
pnpm dev
```

開發環境由 `apps/web/.env.development` 連線到 `http://127.0.0.1:8000`；正式環境
使用同網域 API rewrite。

## 驗證

```sh
PYTHON_BIN=.venv-rebuilt/bin/python ./scripts/verify
```

驗證涵蓋 Python 單元／整合測試、分支感知應用程式覆蓋率、Ruff lint／格式、
Strict Mypy、Strict TypeScript、ESLint、Next.js production build、Playwright
桌面／手機流程與 axe WCAG 檢查。瀏覽器 QA 包含英／繁中、引導／分析師流程、
多期財務展開、設施保障、求解器中繼資料、鍵盤操作、本地化錯誤頁，以及一頁式／
詳細 PDF。PDF 每頁均渲染檢查；繁中使用內嵌開源 Noto Sans TC 字型。

## 文件

- [目前發布狀態](docs/release-status.md)
- [v6 模型一致性強化規格](docs/prompts/Northstar_v6_Final_Credit_Model_Consistency_Prompt.md)
- [金額尺度契約](docs/architecture/money-scale-contract.md)
- [v6 Claude Opus 5 High 審查](docs/collaboration/v6-claude-opus-5-review.md)
- [v6 決策紀錄](docs/collaboration/v6-decision-log.md)
- [方法論](docs/methodology.md)
- [目前模型限制](docs/release-status.md#current-limitations)
- [測試證據](docs/release-status.md#verification-at-release-authoring)
- [展示案例](data/demo_cases/)
- [修正稽核](docs/architecture/recovery-audit.md)
- [資料模型](docs/architecture/data-model.md)
- [設計系統與概念忠實度](docs/product/design-system.md)
- [修正決策紀錄](docs/collaboration/decision-log.md)
- [Claude Opus 5 High 設定證據](docs/collaboration/model-config.md)
- [Claude 獨立審查](docs/collaboration/corrective-debate-claude.md)
- [v3 修正前稽核](docs/audits/pre-correction-audit.md)
- [v3 Claude 審查與 Codex 回應](docs/collaboration/v3-claude-opus-5-review.md)
- [最終產品稽核](docs/audits/final-product-audit.md)
- [最終模型稽核](docs/audits/final-model-audit.md)
- [最終 UX 稽核](docs/audits/final-ux-audit.md)
- [正式環境部署驗證](docs/audits/final-deployment-verification.md)
- [最終 Claude Opus 5 High 審查](docs/collaboration/final-review-claude-opus-5.md)
- [v4 獨立稽核](docs/audits/final-independent-audit-v4.md)
- [v4 修正任務板](docs/implementation-task-board-v4.md)
- [v4 Claude Opus 5 High 挑戰紀錄](docs/collaboration/v4-claude-opus-5-review.md)

### 歷史審查紀錄

上列 v3／v4 稽核、任務板與辯論紀錄均保留作為歷史證據。現行產品宣稱、測試數、
部署與限制，唯一以[目前發布狀態](docs/release-status.md)為準。

跨模型協作紀錄僅作為 repository 證據，不會在產品介面中當作行銷宣稱。
