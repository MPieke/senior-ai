import json
import os
import sqlite3
import uuid
from pathlib import Path
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from .schemas import AnalysisInput, AnalysisPayload
from .services.llm import AnalysisProvider, FixtureProvider, OpenAIProvider

MAX_FILE_BYTES = 10 * 1024 * 1024
SUPPORTED_TYPES = {"application/pdf", "image/jpeg", "image/png", "image/webp"}

class ActionRequest(BaseModel):
    actionType: str
    confirmed: bool
    parameters: dict = {}

async def normalize(request: Request) -> AnalysisInput:
    if request.headers.get("content-type", "").startswith("application/json"):
        body = await request.json(); text = body.get("text", "")
        if not isinstance(text, str) or not text.strip(): raise HTTPException(422, "Please paste a message to continue.")
        return AnalysisInput(text=text)
    form = await request.form(); upload = form.get("file")
    if upload is None or not hasattr(upload, "read"): raise HTTPException(422, "Choose a message, photo, PDF, or document.")
    media_type = upload.content_type or ""
    if media_type not in SUPPORTED_TYPES: raise HTTPException(415, "Please choose a photo, PDF, or supported document.")
    content = await upload.read()
    if not content: raise HTTPException(422, "That file is empty. Please choose another one.")
    if len(content) > MAX_FILE_BYTES: raise HTTPException(413, "That file is too large. Please choose one smaller than 10 MB.")
    return AnalysisInput(filename=upload.filename, media_type=media_type, content=content)

def create_app(database_path: Path | str = "./data/senior_ai.db", provider: AnalysisProvider | None = None) -> FastAPI:
    app = FastAPI(title="Senior AI API")
    app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:4173", "http://127.0.0.1:4173"], allow_methods=["*"], allow_headers=["*"])
    db_path = Path(database_path); db_path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(db_path) as db: db.execute("create table if not exists analyses (id text primary key, result text not null)")
    service = provider or (OpenAIProvider() if os.getenv("OPENAI_API_KEY") else FixtureProvider())
    @app.get("/health")
    async def health(): return {"status":"ok"}
    @app.post("/v1/analyses", status_code=201)
    async def create(request: Request):
        input = await normalize(request)
        try: result = AnalysisPayload.model_validate(await service.analyze(input))
        except Exception as exc: raise HTTPException(502, "I could not safely read this. Please try again.") from exc
        actions = {a.type: a for a in result.recommendedActions}
        if result.riskLevel == "red": actions.pop("draft_reply", None)
        result.recommendedActions = sorted(actions.values(), key=lambda a: a.priority)[:3]
        output = result.model_dump() | {"schemaVersion":"1.0", "analysisId":str(uuid.uuid4()), "createdAt":"2026-08-04T00:00:00Z", "originalText":input.text}
        with sqlite3.connect(db_path) as db: db.execute("insert into analyses values (?,?)", (output["analysisId"], json.dumps(output)))
        return output
    @app.get("/v1/analyses")
    async def history():
        with sqlite3.connect(db_path) as db: return [json.loads(row[0]) for row in db.execute("select result from analyses order by rowid desc")]
    @app.post("/v1/analyses/{analysis_id}/actions")
    async def action(analysis_id: str, request: ActionRequest):
        if not request.confirmed: raise HTTPException(400, "Please confirm this action first.")
        return {"actionAttemptId":str(uuid.uuid4()), "status":"stubbed", "message":"This was saved as a practice action. Nothing was sent outside this app."}
    return app

app = create_app()
