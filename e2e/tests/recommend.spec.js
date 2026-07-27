import { test, expect } from "@playwright/test";

test.describe("Recommendation Flow", () => {
  test("app loads and shows map", async ({ page }) => {
    await page.goto("/");
    await expect(page.locator(".leaflet-container")).toBeVisible({ timeout: 10000 });
  });

  test("shows carpark cards when API responds", async ({ page }) => {
    await page.goto("/");
    const cards = page.locator(".carpark-card");
    await expect(cards.first()).toBeVisible({ timeout: 15000 });
  });

  test("search bar is visible", async ({ page }) => {
    await page.goto("/");
    const searchInput = page.locator('input[placeholder*="search" i], input[placeholder*="Search" i]');
    await expect(searchInput.first()).toBeVisible();
  });

  test("clicking carpark card selects it", async ({ page }) => {
    await page.goto("/");
    const card = page.locator(".carpark-card").first();
    await card.click();
    await expect(card).toHaveClass(/selected/);
  });
});
