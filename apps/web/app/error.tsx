"use client";

import { usePathname } from "next/navigation";
import { useEffect } from "react";

export default function ErrorPage({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  const zh = usePathname().startsWith("/zh-TW");
  useEffect(() => {
    console.error(error);
  }, [error]);
  return (
    <main className="center-state">
      <h1>{zh ? "無法載入 Northstar" : "Unable to load Northstar"}</h1>
      <p>
        {zh
          ? "服務可能暫時無法使用；瀏覽器中的未儲存輸入可能仍然保留。"
          : "The service may be temporarily unavailable. Your unsaved browser input may still be present."}
      </p>
      <button className="button primary" onClick={reset}>
        {zh ? "重試" : "Retry"}
      </button>
    </main>
  );
}
