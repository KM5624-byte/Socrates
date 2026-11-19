import { expect, test } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";

test("filters a real series and exports the same months", async ({ page, request }) => {
  await page.goto("/");
  await expect(page.getByRole("heading", { name: "Unemployment rate" })).toBeVisible();
  await expect(page.getByRole("heading", { name: "NYC Local Law 144" })).toBeVisible();
  await expect(page.locator(".chart svg").first()).toBeVisible();
  await page.getByLabel("Indicator").selectOption("jolts");
  await page.getByLabel("From", { exact: true }).fill("2024-01");
  await page.getByLabel("To", { exact: true }).fill("2024-02");
  await page.getByRole("button", { name: "Apply filters" }).click();
  await expect(page.getByRole("heading", { name: "Job openings" })).toBeVisible();
  await page.getByText("View monthly values and source notes").click();
  await expect(page.getByRole("rowheader", { name: "2024-01" })).toBeVisible();
  const exportPath = await page.getByRole("link", { name: "CSV" }).getAttribute("href");
  const response = await request.get(exportPath!);
  expect(response.ok()).toBeTruthy();
  const rows = (await response.text()).trim().split(/\r?\n/);
  expect(rows.length).toBe(3);
  expect(rows[1]).toMatch(/^2024-01,[\d.]+,thousands,[0-9a-f]{64},/);
  expect(rows[2]).toMatch(/^2024-02,[\d.]+,thousands,[0-9a-f]{64},/);
});

test("mobile layout fits horizontally and passes automated accessibility checks", async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("/");
  await expect(page.getByRole("heading", { name: "Unemployment rate" })).toBeVisible();
  expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(390);
  const { violations } = await new AxeBuilder({ page }).withTags(["wcag2a", "wcag2aa", "wcag21aa", "wcag22aa"]).analyze();
  expect(violations.map(({id, nodes}) => ({id, targets: nodes.map((node) => node.target)}))).toEqual([]);
});

test("switches to the EU timeline and hides incompatible policy overlays", async ({ page }) => {
  await page.goto("/");
  await page.getByLabel("Jurisdiction").selectOption("eu");
  await page.getByRole("button", { name: "Show timeline" }).click();
  await expect(page.getByRole("heading", { name: "EU AI Act" })).toBeVisible();
  await expect(page.getByText("Consolidated text date")).toBeVisible();
  await expect(page.getByText("Dashed lines indicate months")).toHaveCount(0);
});
