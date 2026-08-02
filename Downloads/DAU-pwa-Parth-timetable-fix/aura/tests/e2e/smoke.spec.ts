import { test, expect } from "@playwright/test";

test.describe("AURA PWA - Smoke Tests", () => {
  // Test 1: Unauthenticated user flow
  test("unauthenticated user is gated from chat and redirected/shown login prompt", async ({ page }) => {
    await page.goto("/");

    // The middleware gates unauthenticated users and redirects them to /login or disables input.
    await page.waitForTimeout(1000);
    const url = page.url();

    if (url.includes("/login")) {
      const googleBtn = page.locator("button:has-text('Continue with Google Workspace')");
      await expect(googleBtn).toBeVisible();
    } else {
      // If on chat page but input is blocked/disabled for guest
      const input = page.locator("textarea[placeholder*='Sign in']");
      const isInputDisabled = await input.isDisabled().catch(() => true);
      expect(isInputDisabled).toBe(true);
    }
  });

  test("is redirected to /login when visiting a protected route", async ({ page }) => {
    await page.goto("/dashboard");
    await expect(page).toHaveURL(/\/login/);
  });

  // NOTE: PR #145's rewrite of this file dropped the two tests below
  // (protected-API-401 and manifest-serving) in favour of the new
  // login/dashboard/offline tests. Both are kept here — they cover
  // distinct regressions (an unauthenticated API call that silently
  // succeeds, and a broken/missing PWA manifest) that none of the new
  // tests exercise.
  test("hitting a protected API route returns 401, not a crash page", async ({ request }) => {
    const res = await request.get("/api/erp/fees");
    expect(res.status()).toBe(401);
  });

  test("manifest.json is served and installable-shaped", async ({ request }) => {
    const res = await request.get("/manifest.json");
    expect(res.ok()).toBeTruthy();
    const manifest = await res.json();
    expect(manifest.name).toContain("AURA");
    expect(manifest.display).toBe("standalone");
    expect(manifest.icons.length).toBeGreaterThan(0);
  });

  // Test 2: Login page and elements
  test("login page renders all sign-in options", async ({ page }) => {
    await page.goto("/login");

    const googleBtn = page.locator("button:has-text('Continue with Google Workspace')");
    await expect(googleBtn).toBeVisible();

    await expect(page.locator("text=AURA")).toBeVisible();
    await expect(page.locator("text=DAU AI Assistant")).toBeVisible();
  });

  // Test 3: Dashboard - Verify no attendance card
  test("dashboard does not display attendance card", async ({ page }) => {
    await page.goto("/dashboard");

    // Attendance card has been removed per v7 policy (no DB table access granted).
    // We check that no element contains the word 'attendance' in the UI.
    const attendanceCard = page.locator("text=attendance").or(page.locator("text=Attendance"));
    const count = await attendanceCard.count();
    expect(count).toBe(0);
  });

  // Test 4: Offline fallback route check
  test("offline route renders correct offline messages", async ({ page }) => {
    await page.goto("/offline");

    // Verify offline message elements
    await expect(page.locator("h1")).toHaveText("You are offline");
    await expect(page.locator("text=retry").or(page.locator("text=Retry"))).toBeVisible();
    await expect(page.locator("text=Go to Home")).toBeVisible();
  });
});
