"use client";

import { BookOpen, X } from "lucide-react";
import { useEffect, useRef, useState } from "react";

const terms: Array<[string, string, string]> = [
  [
    "EBITDA",
    "Operating profit before interest, tax, depreciation and amortization.",
    "息稅折舊攤銷前利益。",
  ],
  [
    "Adjusted EBITDA",
    "EBITDA after approved, evidenced normalization items.",
    "納入已核准且有證據的正常化項目後之 EBITDA。",
  ],
  ["CFADS", "Cash flow available for debt service.", "可供償還本息的現金流。"],
  [
    "DSCR",
    "CFADS divided by required interest and principal service.",
    "可供償債現金流除以應付利息與本金。",
  ],
  [
    "Leverage",
    "Debt relative to earnings capacity.",
    "債務相對於獲利能力的倍數。",
  ],
  [
    "Interest coverage",
    "Earnings available to pay cash interest.",
    "可用盈餘支付現金利息的倍數。",
  ],
  [
    "Covenant",
    "A contractual financial or reporting requirement.",
    "貸款合約中的財務或報告義務。",
  ],
  [
    "Headroom",
    "Distance between actual performance and a limit.",
    "實際表現與限制門檻之間的餘裕。",
  ],
  [
    "Debt capacity",
    "Additional debt supportable under policy and forecast cash flow.",
    "依政策與預測現金流可支援的新增債務。",
  ],
  [
    "Borrowing base",
    "Eligible collateral after advance rates, reserves, and prior liens.",
    "合格擔保品扣除預支率、準備與優先權後的可借額。",
  ],
  [
    "Facility",
    "The proposed lending instrument and its terms.",
    "擬議授信工具及其條件。",
  ],
  [
    "Amortization",
    "Scheduled repayment of principal before maturity.",
    "到期日前依排程償還本金。",
  ],
  [
    "Revolver",
    "A facility that can be drawn, repaid, and redrawn within limits.",
    "在額度內可動用、償還並再次動用的循環信用。",
  ],
  [
    "Collateral",
    "Assets pledged to support a facility.",
    "為授信提供保障而設定擔保的資產。",
  ],
  [
    "Guarantee",
    "A third party's promise to support repayment.",
    "第三方對還款責任提供的保證。",
  ],
  [
    "Refinancing risk",
    "Risk that maturing debt cannot be replaced on acceptable terms.",
    "到期債務無法以可接受條件再融資的風險。",
  ],
];

export function GlossaryDrawer({ language }: { language: "en" | "zh-TW" }) {
  const zh = language === "zh-TW";
  const [open, setOpen] = useState(false);
  const dialog = useRef<HTMLDivElement>(null);
  const trigger = useRef<HTMLButtonElement>(null);
  useEffect(() => {
    if (!open) return;
    dialog.current?.querySelector<HTMLElement>("button")?.focus();
    const close = (event: KeyboardEvent) =>
      event.key === "Escape" && setOpen(false);
    window.addEventListener("keydown", close);
    return () => window.removeEventListener("keydown", close);
  }, [open]);
  return (
    <>
      <button
        ref={trigger}
        className="glossary-trigger"
        onClick={() => setOpen(true)}
      >
        <BookOpen size={16} />
        {zh ? "名詞表" : "Glossary"}
      </button>
      {open && (
        <>
          <button
            className="drawer-backdrop glossary-backdrop"
            aria-label={zh ? "關閉名詞表" : "Close glossary"}
            onClick={() => setOpen(false)}
          />
          <div
            ref={dialog}
            className="glossary-drawer"
            role="dialog"
            aria-modal="true"
            aria-labelledby="glossary-title"
          >
            <button
              className="drawer-close"
              onClick={() => {
                setOpen(false);
                trigger.current?.focus();
              }}
            >
              <X size={18} />
              <span className="sr-only">{zh ? "關閉" : "Close"}</span>
            </button>
            <h2 id="glossary-title">{zh ? "授信名詞表" : "Credit glossary"}</h2>
            <dl>
              {terms.map(([term, en, traditional]) => (
                <div key={term}>
                  <dt>{term}</dt>
                  <dd>{zh ? traditional : en}</dd>
                </div>
              ))}
            </dl>
          </div>
        </>
      )}
    </>
  );
}
