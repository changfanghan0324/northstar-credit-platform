import AxeBuilder from "@axe-core/playwright";
import { expect, test } from "@playwright/test";

import vectors from "../../../../tests/fixtures/money_scale_vectors.json";
import {
  formatMoneyAtScale,
  normalizeMoneyInput,
  type MoneyDisplayScale,
} from "../../lib/money";

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

test("money scale golden vectors stay canonical in TypeScript", () => {
  for (const vector of vectors) {
    const scale = vector.scale as MoneyDisplayScale;
    const parsed = normalizeMoneyInput(vector.input, scale, 2);
    expect(parsed).toEqual({
      ok: true,
      amountMinor: vector.expected_amount_minor,
    });
    expect(
      formatMoneyAtScale(
        {
          amount_minor: vector.expected_amount_minor,
          currency: "USD",
          minor_unit_exponent: 2,
        },
        scale,
      ),
    ).toBe(vector.expected_display);
  }

  expect(normalizeMoneyInput("90071992.54740991", "millions", 2)).toEqual({
    ok: true,
    amountMinor: Number.MAX_SAFE_INTEGER,
  });
  expect(normalizeMoneyInput("90071992.54740992", "millions", 2)).toMatchObject(
    { ok: false, code: "unsafe_amount" },
  );
});

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
  await navigateWorkspace(/Financials/);
  await expect(
    page.getByText("Show decision-field source authority"),
  ).toBeVisible();
  await expect(page.getByText("Debt reconciliation source")).toBeVisible();
  await expect(page.getByText("Resolved facility mechanics")).toBeVisible();
  await navigateWorkspace(/Stress & covenants/);
  await expect(page.locator(".line-chart")).toHaveCount(2);
  await page.getByText("Show all six reverse-stress solvers").click();
  await expect(page.locator(".solver-grid article")).toHaveCount(6);
});

test("analyst money scales preserve canonical cents across entry and paste", async ({
  page,
  isMobile,
}) => {
  test.skip(isMobile, "The scale contract flow is covered on desktop only.");
  await page.goto("/");
  await page.getByRole("button", { name: "Open workspace" }).first().click();
  await page.getByRole("link", { name: /Inputs/ }).click();
  await page.getByRole("button", { name: "Analyst" }).click();
  await page.getByRole("button", { name: "Add 3-year history" }).click();
  await page
    .locator("details.statement-table")
    .first()
    .locator("summary")
    .click();

  const periods = page.locator(".period-cards fieldset");
  const directPeriod = periods.nth(0);
  const pastedPeriod = periods.nth(1);
  const revenues = page.locator('input[aria-label$="revenue"]');
  const directRevenue = revenues.nth(0);
  const pastedRevenue = revenues.nth(1);

  await directPeriod.getByLabel("Scale").selectOption("millions");
  await directRevenue.fill("100.00");
  await expect(directRevenue).toHaveValue("100.00");
  await directPeriod.getByLabel("Scale").selectOption("whole");
  await expect(directRevenue).toHaveValue("100000000.00");

  await directPeriod.getByLabel("Scale").selectOption("thousands");
  await directRevenue.fill("100.01");
  await directPeriod.getByLabel("Scale").selectOption("whole");
  const directCanonicalDisplay = await directRevenue.inputValue();
  await directPeriod.getByLabel("Scale").selectOption("millions");
  await expect(directRevenue).toHaveValue("0.10001");
  await directPeriod.getByLabel("Scale").selectOption("whole");
  await expect(directRevenue).toHaveValue(directCanonicalDisplay);

  await pastedPeriod.getByLabel("Scale").selectOption("thousands");
  await page.locator("details.bulk-paste").locator("summary").click();
  await page
    .locator("details.bulk-paste textarea")
    .fill("0\t0\t0\t0\t0\t0\t0\t0\n100.01\t0\t0\t0\t0\t0\t0\t0");
  await page.getByRole("button", { name: "Apply pasted data" }).click();
  await pastedPeriod.getByLabel("Scale").selectOption("whole");
  await expect(pastedRevenue).toHaveValue(directCanonicalDisplay);

  await directPeriod.getByLabel("Scale").selectOption("millions");
  await directRevenue.fill("90071992.54740992");
  await expect(page.locator("p.error[role=alert]")).toContainText(
    "exact range supported",
  );
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
