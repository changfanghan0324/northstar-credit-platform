# Northstar 信用分析平台

**語言：** [English](README.md) | [繁體中文](README.zh-TW.md)

一套具備 Decimal 精確金額運算、型別化原因代碼、幣別防護、明確信心度處理，
並經獨立重現驗證的確定性信用分析引擎。

## 公開交付

- 網站：https://northstar-credit-platform.vercel.app
- 原始碼：`packages/credit_engine/credit_engine/`
- 方法論：`docs/methodology.md`
- 獨立驗收紀錄：
  `docs/collaboration/task1-rereview-claude-opus-5-round2.md`

## 驗證

```sh
PYTHON_BIN=.venv-rebuilt/bin/python ./scripts/verify
```

Task 1 的驗收版本通過 54 項測試，分支感知覆蓋率達 99.53%，Ruff lint 與格式
檢查皆無錯誤，Strict Mypy 檢查亦全部通過。Claude Opus 5 已獨立重現完整驗證
流程並核准此實作。

## 網站

公開專案頁面是一個零相依的靜態網站。網站頁首可切換英文與繁體中文版本
（`/` 與 `/zh-TW/`）。可使用任何靜態 HTTP 伺服器在本機執行：

```sh
python3 -m http.server 4173
```
