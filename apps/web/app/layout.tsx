import type { Metadata } from "next";
import { headers } from "next/headers";
import "./globals.css";

export const metadata: Metadata = {
  title: "Northstar | Corporate Credit Underwriting",
  description:
    "A transparent, educational corporate-credit underwriting workspace.",
  metadataBase: new URL("https://northstar-credit-platform.vercel.app"),
  alternates: {
    canonical: "/",
    languages: { en: "/", "zh-Hant-TW": "/zh-TW/" },
  },
  openGraph: {
    title: "Northstar Credit Platform",
    description:
      "From borrower facts to grade, capacity, stress, and lending terms.",
    locale: "en_US",
    alternateLocale: ["zh_TW"],
  },
};

export default async function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  const language = (await headers()).get("x-northstar-locale") ?? "en";
  return (
    <html lang={language} data-scroll-behavior="smooth">
      <body>
        <a className="skip-link" href="#main-content">
          {language === "zh-Hant-TW" ? "跳至主要內容" : "Skip to main content"}
        </a>
        <div id="main-content">{children}</div>
      </body>
    </html>
  );
}
