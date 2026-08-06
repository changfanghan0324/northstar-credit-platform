# Northstar 企業授信平台

**語言：** [English](README.md) | [繁體中文](README.zh-TW.md)

> 銀行該不該借錢給這家公司？如果要借，該借多少、設定什麼條件？

Northstar 是一套完整的教育用途企業授信工作區。它會把標準化的借款人與授信
條件連結到財務比率、透明的信用分數與評等、負債能力、三年壓力情境、財務契約
餘裕、規則式授信建議、擬議條件，以及確定性生成的授信備忘錄 PDF。

## 公開產品

- 網站：https://northstar-credit-platform.vercel.app
- 英文：`/`
- 繁體中文：`/zh-TW/`
- 三個合成案例：穩健製造商、週期性經銷商、軟體服務公司
- 工作區：總覽、輸入、財務分析、債務容量、風險、壓力測試與契約、決策與條件、授信備忘錄
- 模式：Guided 與 Analyst 只是同一組持久化輸入與計算輸出的兩種呈現方式

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

正式環境透過 `DATABASE_URL` 接受 PostgreSQL 連線；本機與暫時性展示環境會回退
使用 `/tmp` 內的 SQLite。公開案件採匿名、session 隔離；`/runtime` API 與案件
列表會如實顯示目前是持久或暫時模式。所有貨幣跨邊界時皆以整數最小貨幣單位
傳送，比率則序列化為十進位字串。

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

目前交付通過 79 項 Python 測試，信用引擎分支感知覆蓋率為 99.54%，並通過
Ruff lint／格式、Strict Mypy、Strict TypeScript、ESLint 與 Next.js production
build。瀏覽器 QA 另涵蓋英／繁中首頁、390px 手機版、開啟範例、自訂案件建立、
session 隔離、Guided／Analyst 數值一致、壓力與契約呈現，以及備忘錄 PDF。

## 文件

- [方法論](docs/methodology.md)
- [修正稽核](docs/architecture/recovery-audit.md)
- [資料模型](docs/architecture/data-model.md)
- [設計系統與概念忠實度](docs/product/design-system.md)
- [修正決策紀錄](docs/collaboration/decision-log.md)
- [Claude Opus 5 High 設定證據](docs/collaboration/model-config.md)
- [Claude 獨立審查](docs/collaboration/corrective-debate-claude.md)
- [v3 修正前稽核](docs/audits/pre-correction-audit.md)
- [v3 Claude 審查與 Codex 回應](docs/collaboration/v3-claude-opus-5-review.md)

跨模型協作紀錄僅作為 repository 證據，不會在產品介面中當作行銷宣稱。
