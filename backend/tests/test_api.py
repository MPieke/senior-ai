from httpx import ASGITransport, AsyncClient
from app.main import create_app
from app.services.llm import FixtureProvider


async def test_scam_sms_is_stored_with_safe_actions(tmp_path):
    app = create_app(database_path=tmp_path / "test.db", provider=FixtureProvider())
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/v1/analyses", json={"text": "Your bank account is locked. Click http://bad.example now."})
        assert response.status_code == 201
        result = response.json()
        assert result["riskLevel"] == "red"
        assert result["actionRequirement"] == "verify_before_acting"
        assert "draft_reply" not in [action["type"] for action in result["recommendedActions"]]
        assert len(result["recommendedActions"]) <= 3
        history = await client.get("/v1/analyses")
        assert history.json()[0]["analysisId"] == result["analysisId"]


async def test_action_requires_confirmation(tmp_path):
    app = create_app(database_path=tmp_path / "test.db", provider=FixtureProvider())
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        analysis = (await client.post("/v1/analyses", json={"text": "bank link http://bad.example"})).json()
        response = await client.post(f"/v1/analyses/{analysis['analysisId']}/actions", json={"actionType": "save_item", "confirmed": False})
        assert response.status_code == 400
