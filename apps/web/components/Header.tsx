import Link from "next/link";
import { Compass } from "lucide-react";
import { type Language, prefix, t } from "@/lib/i18n";

export function Header({ language }: { language: Language }) {
  const text = t(language); const root = prefix(language);
  return <header className="site-header"><Link className="brand" href={`${root}/`}><Compass size={22}/><span>{text.product}</span></Link><nav><Link href={`${root}/methodology`}>{text.nav[0]}</Link><Link href={`${root}/technical-validation`}>{text.nav[1]}</Link><Link href={`${root}/about`}>{text.nav[2]}</Link></nav><Link className="language" href={language === "en" ? "/zh-TW/" : "/"}>{text.language}</Link></header>;
}
