import json, sqlite3, uuid
from pathlib import Path
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from .services.llm import AnalysisProvider, FixtureProvider, OpenAIProvider

class CreateAnalysis(BaseModel): text: str = Field(min_length=1, max_length=20000)
class ActionRequest(BaseModel): actionType: str; confirmed: bool; parameters: dict = {}

def create_app(database_path: Path | str = "./data/senior_ai.db", provider: AnalysisProvider | None = None) -> FastAPI:
    app = FastAPI(title="Senior AI API")
    db_path = Path(database_path); db_path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(db_path) as db: db.execute("create table if not exists analyses (id text primary key, result text not null)")
    service = provider or (OpenAIProvider() if __import__("os").getenv("OPENAI_API_KEY") else FixtureProvider())
    def save(identifier, result):
        with sqlite3.connect(db_path) as db: db.execute("insert into analyses values (?,?)", (identifier, json.dumps(result)))
    @app.get("/health")
    async def health(): return {"status":"ok"}
    @app.post("/v1/analyses", status_code=201)
    async def create(request: CreateAnalysis):
        result = await service.analyze(request.text)
        if result["riskLevel"] == "red": result["recommendedActions"] = [a for a in result["recommendedActions"] if a["type"] != "draft_reply"]
        result["recommendedActions"] = sorted(result["recommendedActions"], key=lambda a:a["priority"])[:3]
        result.update({"schemaVersion":"1.0", "analysisId":str(uuid.uuid4()), "createdAt":"2026-08-04T00:00:00Z", "originalText":request.text})
        save(result["analysisId"], result); return result
    @app.get("/v1/analyses")
    async def history():
        with sqlite3.connect(db_path) as db: return [json.loads(row[0]) for row in db.execute("select result from analyses order by rowid desc")]
    @app.post("/v1/analyses/{analysis_id}/actions")
    async def action(analysis_id: str, request: ActionRequest):
        if not request.confirmed: raise HTTPException(400, "Please confirm this action first.")
        return {"actionAttemptId":str(uuid.uuid4()), "status":"stubbed", "message":"This was saved as a practice action. Nothing was sent outside this app."}
    return app

app = create_app()
