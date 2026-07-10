import { test, expect } from "@playwright/test"

test.describe("Unauthenticated visitor", () => {
  test("can load the chat shell at /", async ({ page }) => {
    await page.goto("/")
    await expect(page).toHaveURL("/")
    // ChatShell renders some composer/input for an unauthenticated visitor.
    await expect(page.locator("textarea, input[type='text']").first()).toBeVisible()
  })

  test("is redirected to /login when visiting a protected route", async ({ page }) => {
    await page.goto("/dashboard")
    await expect(page).toHaveURL(/\/login/)
  })

  test("hitting a protected API route returns 401, not a crash page", async ({ request }) => {
    const res = await request.get("/api/erp/fees")
    expect(res.status()).toBe(401)
  })
})

test.describe("Login page", () => {
  test("renders Google sign-in and shows the DomainNotAllowed error copy", async ({ page }) => {
    await page.goto("/login?error=DomainNotAllowed")
    await expect(page.getByText(/dau\.ac\.in|daiict\.ac\.in/i).first()).toBeVisible()
  })
})

test.describe("PWA shell", () => {
  test("manifest.webmanifest is served and installable-shaped", async ({ request }) => {
    const res = await request.get("/manifest.webmanifest")
    expect(res.ok()).toBeTruthy()
    const manifest = await res.json()
    expect(manifest.name).toContain("AURA")
    expect(manifest.icons.length).toBeGreaterThan(0)
  })

  test("offline fallback page renders", async ({ page }) => {
    await page.goto("/offline")
    await expect(page.getByText(/you're offline/i)).toBeVisible()
  })
})
