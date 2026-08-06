import AxeBuilder from "@axe-core/playwright";
import { expect, test } from "@playwright/test";

async function assertNoSeriousA11yViolations(
  page: import("@playwright/test").Page,
) {
  const results = await new AxeBuilder({ page })
    .withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa", "wcag22aa"])
    .analyze();
  expect(
    results.violations.filter((item) =>
      ["critical", "serious"].includes(item.impact ?? ""),
    ),
  ).toEqual([]);
}

test("English and Traditional Chinese home pages are accessible", async ({
  page,
}) => {
  await page.goto("/");
  await expect(page.locator("h1")).toContainText("Should we lend");
  await assertNoSeriousA11yViolations(page);
  await page.goto("/zh-TW/");
  await expect(page.locator("html")).toHaveAttribute("lang", "zh-Hant-TW");
  await expect(page.locator("h1")).toContainText("銀行該不該借錢");
  await assertNoSeriousA11yViolations(page);
});

test("demo lifecycle exposes professional workspace pages and both modes", async ({
  page,
  isMobile,
}) => {
  async function navigateWorkspace(name: RegExp) {
    if (isMobile) {
      await page
        .getByRole("button", { name: "Open workflow navigation" })
        .click();
    }
    await page.getByRole("link", { name }).click();
  }
  await page.goto("/");
  await page.getByRole("button", { name: "Open workspace" }).first().click();
  await expect(page).toHaveURL(/\/app\/cases\/[^/]+\/overview/);
  await expect(page.getByRole("heading", { level: 1 })).toContainText(
    "credit recommendation",
  );
  await navigateWorkspace(/Facility protection/);
  await expect(page.getByRole("heading", { level: 1 })).toContainText(
    "lender protected",
  );
  await expect(page.getByText("Facility protection score")).toBeVisible();
  await assertNoSeriousA11yViolations(page);
  await navigateWorkspace(/Inputs/);
  await expect(page.getByText("Editable case inputs")).toBeVisible();
  if (isMobile) {
    await page
      .getByRole("button", { name: "Open workflow navigation" })
      .click();
  }
  await page.getByRole("button", { name: "Analyst" }).click();
  if (isMobile) await page.keyboard.press("Escape");
  await expect(page.getByText("Analyst multi-period spread")).toBeVisible();
  await page.getByRole("button", { name: "Add 3-year history" }).click();
  await expect(page.locator(".period-cards fieldset")).toHaveCount(3);
  await navigateWorkspace(/Stress & covenants/);
  await expect(page.locator(".line-chart")).toHaveCount(2);
  await page.getByText("Show all six reverse-stress solvers").click();
  await expect(page.locator(".solver-grid article")).toHaveCount(6);
});

test("keyboard skip link, glossary dialog, mobile navigation, and localized 404 work", async ({
  page,
  isMobile,
}) => {
  await page.goto("/zh-TW/");
  await page.keyboard.press("Tab");
  await expect(page.getByRole("link", { name: "跳至主要內容" })).toBeFocused();
  await page.goto("/zh-TW/不存在的頁面");
  await expect(page.getByRole("heading", { name: "找不到頁面" })).toBeVisible();
  if (!isMobile) return;
  await page.goto("/");
  await page.getByRole("button", { name: "Open workspace" }).first().click();
  await page.getByRole("button", { name: "Open workflow navigation" }).click();
  await expect(
    page.getByRole("dialog", { name: "Underwriting workflow" }),
  ).toBeVisible();
  await page.keyboard.press("Escape");
  await expect(
    page.getByRole("dialog", { name: "Underwriting workflow" }),
  ).toBeHidden();
  await page.getByRole("button", { name: "Glossary" }).click();
  await expect(
    page.getByRole("dialog", { name: "Credit glossary" }),
  ).toBeVisible();
  await page.keyboard.press("Escape");
});

test("Traditional Chinese business routes avoid unapproved English interface labels", async ({
  page,
}) => {
  await page.goto("/zh-TW/");
  await page.getByRole("button", { name: "開啟工作區" }).first().click();
  await expect(page).toHaveURL(/\/zh-TW\/app\/cases\/[^/]+\/overview/);
  const caseId = page.url().match(/\/cases\/([^/]+)\//)?.[1];
  expect(caseId).toBeTruthy();
  await page.evaluate(() =>
    window.localStorage.setItem("northstar-workspace-mode", "analyst"),
  );
  const forbidden = [
    "Methodology",
    "Technical validation",
    "Start a credit case",
    "Open workspace",
    "Page not found",
    "Return home",
    "Facility protection score",
    "Protection category",
    "Expected recovery",
    "Editable case inputs",
    "Borrower and request",
    "Company name",
    "Requested amount",
    "Maturity years",
    "Analyst multi-period spread",
    "Add 3-year history",
    "Normalization adjustment log",
    "Indicative pricing inputs",
    "Financials and debt",
    "Calculation lineage",
    "Capacity constraints and applicability",
    "Score components",
    "Confidence drivers",
    "Improve confidence",
    "Edit scenario assumptions",
    "Show all six reverse-stress solvers",
    "Show full covenant table",
    "Final credit recommendation",
    "Decision rationale",
    "Conditions and monitoring",
    "Policy checks",
    "Credit memorandum",
    "Version and audit history",
    "Refresh history",
  ];
  for (const section of [
    "overview",
    "inputs",
    "financials",
    "capacity",
    "facility",
    "risk",
    "stress",
    "decision",
    "memo",
  ]) {
    await page.goto(`/zh-TW/app/cases/${caseId}/${section}`);
    await expect(page.getByRole("heading", { level: 1 })).toBeVisible();
    if (section === "inputs") {
      await page.getByRole("button", { name: "加入三年歷史" }).click();
      await page.getByRole("button", { name: "新增調整" }).click();
    }
    const body = await page.locator("body").innerText();
    for (const text of forbidden) expect(body).not.toContain(text);
  }
});
