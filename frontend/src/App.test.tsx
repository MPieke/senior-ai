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
