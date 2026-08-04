from app.evaluation import evaluate_fixture


async def test_fixture_evaluation_reports_expected_safety_result():
    report = await evaluate_fixture("scam-bank-link", provider="fixture")
    assert report["passed"] is True
    assert report["actual"]["riskLevel"] == "red"
    assert "draft_reply" not in report["actual"]["actions"]
