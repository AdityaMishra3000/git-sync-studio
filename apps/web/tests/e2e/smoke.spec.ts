import { expect, test } from "@playwright/test";

/**
 * PHASE 0 end-to-end proof: a real browser reaches Next.js, Next.js reaches
 * FastAPI over the container network, and FastAPI reports on PostgreSQL, Redis
 * and the Celery worker. Requires the full stack to be up.
 */

test("the landing page loads and links to the dashboard", async ({ page }) => {
  await page.goto("/");

  await expect(page.getByRole("heading", { level: 1 })).toContainText("Repository intelligence");
  await page.getByRole("link", { name: "Open the dashboard" }).click();

  await expect(page).toHaveURL(/\/dashboard$/);
});

test("the dashboard reports every dependency as operational", async ({ page }) => {
  await page.goto("/dashboard");

  await expect(page.getByRole("heading", { name: "Platform status" })).toBeVisible();

  // If this assertion fails with "Backend unreachable", the api service is down -
  // that is the test doing its job, not a flaky selector.
  await expect(page.getByText("Backend unreachable")).toHaveCount(0);

  for (const component of ["PostgreSQL", "Redis", "Celery worker"]) {
    await expect(page.getByText(component, { exact: true })).toBeVisible();
  }

  // Three dependencies plus the service verdict, all reading "Operational".
  await expect(page.getByText("Operational")).toHaveCount(4);
});
