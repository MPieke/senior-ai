import { test, expect } from "@playwright/test";

const scamResult = {
  analysisId: "test-analysis",
  riskLevel: "red",
  title: "This looks like a scam text message.",
  summary: "Someone may be pretending to be your bank.",
  actionRequirement: "verify_before_acting",
  recommendedActions: [],
  originalText: "Your bank is locked. Click http://bad.example now.",
};

test("scam flow keeps original content collapsed", async ({ page }) => {
  await page.route("**/v1/analyses", async (route) => {
    if (route.request().method() === "POST") {
      await route.fulfill({ json: scamResult });
    } else {
      await route.continue();
    }
  });
  await page.goto("/");
  await page.getByRole("button", { name: "Paste a message" }).click();
  await page
    .getByLabel("Message")
    .fill("Your bank is locked. Click http://bad.example now.");
  await page.getByRole("button", { name: "Continue" }).click();
  await expect(
    page.getByText("Stop and verify before responding."),
  ).toBeVisible();
  await expect(page.getByText("Your bank is locked.")).toBeHidden();
  await page.getByRole("button", { name: "Show original message" }).click();
  await expect(page.getByText("Your bank is locked.")).toBeVisible();
});

test("document upload shows a review screen", async ({ page }) => {
  await page.goto("/");
  await page.getByRole("button", { name: "Upload a document" }).click();
  await page.getByLabel("Choose a document").setInputFiles({
    name: "notice.pdf",
    mimeType: "application/pdf",
    buffer: Buffer.from("%PDF-1.4"),
  });
  await expect(page.getByText("notice.pdf")).toBeVisible();
  await page.getByRole("button", { name: "Remove document" }).click();
  await expect(page.getByText("notice.pdf")).toBeHidden();
});
