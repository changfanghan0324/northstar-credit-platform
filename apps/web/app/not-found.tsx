import { headers } from "next/headers";
import Link from "next/link";

export default async function NotFound() {
  const zh = (await headers()).get("x-northstar-locale") === "zh-Hant-TW";
  return (
    <main className="center-state">
      <h1>404</h1>
      <h2>{zh ? "找不到頁面" : "Page not found"}</h2>
      <p>
        {zh
          ? "要求的頁面或案件工作區不存在。"
          : "The requested route or case workspace page does not exist."}
      </p>
      <Link className="button primary" href={zh ? "/zh-TW/" : "/"}>
        {zh ? "返回首頁" : "Return home"}
      </Link>
    </main>
  );
}
