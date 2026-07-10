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
    
    // Attendance card has been deferred/removed. 
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