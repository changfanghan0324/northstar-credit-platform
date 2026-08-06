import Link from "next/link";
import { Compass, Menu } from "lucide-react";
import { type Language, prefix, t } from "@/lib/i18n";

export function Header({ language }: { language: Language }) {
  const text = t(language);
  const root = prefix(language);
  const links = (
    <>
      <Link href={`${root}/app/cases`}>
        {language === "en" ? "Cases" : "案件"}
      </Link>
      <Link href={`${root}/methodology`}>{text.nav[0]}</Link>
      <Link href={`${root}/technical-validation`}>{text.nav[1]}</Link>
      <Link href={`${root}/about`}>{text.nav[2]}</Link>
    </>
  );
  return (
    <header className="site-header">
      <Link className="brand" href={`${root}/`}>
        <Compass size={22} />
        <span>{text.product}</span>
      </Link>
      <nav>{links}</nav>
      <details className="mobile-site-menu">
        <summary
          aria-label={
            language === "en" ? "Open site navigation" : "開啟網站導覽"
          }
        >
          <Menu size={19} />
        </summary>
        <nav>{links}</nav>
      </details>
      <Link className="language" href={language === "en" ? "/zh-TW/" : "/"}>
        {text.language}
      </Link>
    </header>
  );
}
