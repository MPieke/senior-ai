from httpx import ASGITransport, AsyncClient
import app.main as main
from app.main import create_app
from app.services.llm import FixtureProvider


class InvalidProvider:
    async def analyze(self, input):
        return {"title": "Missing the required analysis fields"}


class GuidanceProvider:
    async def analyze(self, input):
        result = await FixtureProvider().analyze(input)
        result["recommendedActions"] = [
            {
                "type": "verify_with_organization",
                "priority": 1,
                "label": "Verify with a trusted family member",
                "reason": "Ask someone you trust for help.",
                "enabled": True,
                "implementation": "stub",
            },
            {
                "type": "take_no_action",
                "priority": 2,
                "label": "Do not send money or gift card codes",
                "reason": "Do not respond to the sender.",
                "enabled": True,
                "implementation": "informational",
            },
        ]
        return result


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


async def test_analysis_and_action_events_exclude_message_content(tmp_path, monkeypatch):
    events = []

    class EventLogger:
        def info(self, message, *values):
            events.append(message.format(*values))

    monkeypatch.setattr(main, "logger", EventLogger())
    app = main.create_app(database_path=tmp_path / "test.db", provider=FixtureProvider())
    secret_message = "private message content must never appear in logs"
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        analysis = (await client.post("/v1/analyses", json={"text": secret_message})).json()
        await client.post(
            f"/v1/analyses/{analysis['analysisId']}/actions",
            json={"actionType": "save_item", "confirmed": True},
        )

    assert any(event.startswith("analysis.received") for event in events)
    assert any(event.startswith("analysis.completed") for event in events)
    assert any(event.startswith("action.attempted") for event in events)
    assert secret_message not in "\n".join(events)


async def test_safety_guidance_is_not_a_clickable_action(tmp_path):
    app = create_app(database_path=tmp_path / "test.db", provider=GuidanceProvider())
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/v1/analyses", json={"text": "A worrying message"})
    assert response.status_code == 201
    result = response.json()
    assert result["safetyGuidance"] == ["Do not send money or gift card codes"]
    assert [action["type"] for action in result["recommendedActions"]] == [
        "verify_with_organization"
    ]


async def test_invalid_provider_output_is_rejected(tmp_path):
    app = create_app(database_path=tmp_path / "test.db", provider=InvalidProvider())
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/v1/analyses", json={"text": "A message"})
    assert response.status_code == 502
    assert "could not safely read" in response.json()["detail"].lower()


async def test_pdf_upload_is_normalized_and_stored(tmp_path):
    app = create_app(database_path=tmp_path / "test.db", provider=FixtureProvider())
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            "/v1/analyses",
            files={"file": ("notice.pdf", b"%PDF-1.4 sample", "application/pdf")},
        )
    assert response.status_code == 201
    assert response.json()["inputType"] == "message"


async def test_unsupported_upload_has_a_clear_recovery_message(tmp_path):
    app = create_app(database_path=tmp_path / "test.db", provider=FixtureProvider())
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/v1/analyses", files={"file": ("script.exe", b"no", "application/octet-stream")})
    assert response.status_code == 415
    assert "photo, PDF" in response.json()["detail"]


async def test_uploaded_original_can_be_viewed_and_is_deleted_with_analysis(tmp_path):
    app = create_app(database_path=tmp_path / "test.db", provider=FixtureProvider())
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        created = await client.post("/v1/analyses", files={"file": ("notice.pdf", b"%PDF-1.4 sample", "application/pdf")})
        analysis_id = created.json()["analysisId"]
        original = await client.get(f"/v1/analyses/{analysis_id}/original")
        assert original.status_code == 200
        assert original.headers["content-type"] == "application/pdf"
        assert original.content == b"%PDF-1.4 sample"
        deleted = await client.delete(f"/v1/analyses/{analysis_id}")
        assert deleted.status_code == 204
        assert (await client.get(f"/v1/analyses/{analysis_id}/original")).status_code == 404
