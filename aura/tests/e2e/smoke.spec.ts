import { test, expect } from "@playwright/test";

test.describe("AURA PWA - Smoke Tests", () => {
  // Test 1: Unauthenticated user flow
  test("guest user sees limited chat access and a sign-in action", async ({ page }) => {
    await page.goto("/");

    await expect(page.getByRole("textbox", { name: "Message AURA" })).toBeVisible();
    await expect(page.getByText("10 messages left")).toBeVisible();
    await expect(page.getByRole("button", { name: "Sign in", exact: true })).toBeVisible();
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
    const res = await request.get("/api/auth/history");
    expect(res.status()).toBe(401);
  });

  test("@pwa manifest.json is served and installable-shaped", async ({ request }) => {
    const res = await request.get("/manifest.json");
    expect(res.ok()).toBeTruthy();
    const manifest = await res.json();
    expect(manifest.name).toContain("AURA");
    expect(manifest.display).toBe("standalone");
    expect(manifest.icons.length).toBeGreaterThan(0);

    for (const icon of manifest.icons) {
      const iconResponse = await request.get(icon.src);
      expect(iconResponse.ok()).toBeTruthy();
    }
  });

  test("@pwa production service worker is served", async ({ request }) => {
    const res = await request.get("/sw.js");
    expect(res.ok()).toBeTruthy();
    expect(res.headers()["content-type"]).toContain("javascript");
    expect(await res.text()).toContain("/offline");
  });

  // Test 2: Login page and elements
  test("login page renders all sign-in options", async ({ page }) => {
    await page.goto("/login");

    const googleBtn = page.locator("button:has-text('Continue with Google Workspace')");
    await expect(googleBtn).toBeVisible();

    await expect(page.locator("text=AURA")).toBeVisible();
    await expect(page.locator("text=DAU AI Assistant")).toBeVisible();
  });

  // Test 3: Offline fallback route check
  test("@pwa offline route renders correct offline messages", async ({ page }) => {
    await page.goto("/offline");

    // Verify offline message elements
    await expect(page.locator("h1")).toHaveText("You are offline");
    await expect(page.locator("text=retry").or(page.locator("text=Retry"))).toBeVisible();
    await expect(page.locator("text=Go to Home")).toBeVisible();
  });
});
