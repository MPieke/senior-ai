import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { App } from "./App";

test("guides a pasted scam message through a safe result", async () => {
  const user = userEvent.setup();
  render(
    <App
      api={{
        analyze: async () => ({
          analysisId: "a1",
          riskLevel: "red",
          title: "This looks like a scam text message.",
          summary: "Someone is pretending to be your bank.",
          actionRequirement: "verify_before_acting",
          recommendedActions: [
            {
              type: "verify_with_organization",
              label: "Verify with your bank",
            },
          ],
          originalText: "Click bad link",
        }),
      }}
    />,
  );
  await user.click(screen.getByRole("button", { name: "Paste a message" }));
  await user.type(screen.getByLabelText("Message"), "Click bad link");
  await user.click(screen.getByRole("button", { name: "Continue" }));
  expect(
    await screen.findByText("Stop and verify before responding."),
  ).toBeInTheDocument();
  expect(screen.queryByText("Click bad link")).not.toBeInTheDocument();
  await user.click(
    screen.getByRole("button", { name: "Show original message" }),
  );
  expect(screen.getByText("Click bad link")).toBeInTheDocument();
});

test("reviews a selected document before upload", async () => {
  const user = userEvent.setup();
  const file = new File(["sample"], "insurance-letter.pdf", {
    type: "application/pdf",
  });
  render(
    <App
      api={{
        analyze: async () => ({
          analysisId: "a2",
          riskLevel: "green",
          title: "This is an insurance letter.",
          summary: "No action needed.",
          actionRequirement: "no_action",
          recommendedActions: [],
        }),
      }}
    />,
  );
  await user.click(screen.getByRole("button", { name: "Upload a document" }));
  await user.upload(screen.getByLabelText("Choose a document"), file);
  expect(screen.getByText("insurance-letter.pdf")).toBeInTheDocument();
  await user.click(screen.getByRole("button", { name: "Remove document" }));
  expect(screen.queryByText("insurance-letter.pdf")).not.toBeInTheDocument();
});

test("shows safety guidance as text and keeps only operations clickable", async () => {
  const user = userEvent.setup();
  render(
    <App
      api={{
        analyze: async () => ({
          analysisId: "a-guidance",
          riskLevel: "red",
          title: "This may be a scam.",
          summary: "Someone is asking for money.",
          actionRequirement: "verify_before_acting",
          safetyGuidance: ["Do not send money or gift card codes"],
          recommendedActions: [
            {
              type: "verify_with_organization",
              label: "Verify with a trusted family member",
            },
          ],
        }),
      }}
    />,
  );
  await user.click(screen.getByRole("button", { name: "Paste a message" }));
  await user.type(screen.getByLabelText("Message"), "Please send money.");
  await user.click(screen.getByRole("button", { name: "Continue" }));

  expect(
    await screen.findByText("Do not send money or gift card codes"),
  ).toBeInTheDocument();
  expect(
    screen.queryByRole("button", { name: "Do not send money or gift card codes" }),
  ).not.toBeInTheDocument();
  await user.click(
    screen.getByRole("button", { name: "Verify with a trusted family member" }),
  );
  expect(screen.getByRole("dialog", { name: "Confirm action" })).toBeInTheDocument();
});

test("camera is marked coming soon and back clears a pending file", async () => {
  const user = userEvent.setup();
  const file = new File(["sample"], "letter.pdf", { type: "application/pdf" });
  render(
    <App
      api={{
        analyze: async () => ({
          analysisId: "a3",
          riskLevel: "green",
          title: "Letter",
          summary: "",
          actionRequirement: "no_action",
          recommendedActions: [],
        }),
      }}
    />,
  );
  expect(
    screen.getByRole("button", { name: /Take a picture.*Coming soon/ }),
  ).toBeDisabled();
  await user.click(screen.getByRole("button", { name: "Upload a document" }));
  await user.upload(screen.getByLabelText("Choose a document"), file);
  await user.click(screen.getByRole("button", { name: "Go back" }));
  await user.click(screen.getByRole("button", { name: "Upload a document" }));
  expect(screen.queryByText("letter.pdf")).not.toBeInTheDocument();
});
