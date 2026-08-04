import json
import os
import base64
from typing import Protocol
from openai import AsyncOpenAI
from ..schemas import AnalysisInput, AnalysisPayload


class AnalysisProvider(Protocol):
    async def analyze(self, input: AnalysisInput) -> dict: ...


class FixtureProvider:
    async def analyze(self, input: AnalysisInput) -> dict:
        text = input.text or input.filename or "document"
        is_scam = any(word in text.lower() for word in ("http", "bank", "locked", "urgent"))
        return {
            "status": "complete", "inputType": "message", "specificType": "scam_text" if is_scam else None,
            "title": "This looks like a scam text message." if is_scam else "This is a personal message.",
            "summary": "Someone may be pretending to be your bank and asking you to click a link." if is_scam else "This looks like an ordinary message.",
            "actionRequirement": "verify_before_acting" if is_scam else "no_action",
            "urgency": "high" if is_scam else "none", "riskLevel": "red" if is_scam else "green",
            "consequenceLevel": "high" if is_scam else "low", "confidence": "high",
            "riskCategories": ["scam", "suspicious_link"] if is_scam else ["none"],
            "riskReasons": ["It asks you to use an unfamiliar link."] if is_scam else [],
            "extractedFacts": {"sender": None, "organization": "Bank" if is_scam else None, "amount": None, "deadline": None, "appointmentDate": None, "phoneNumber": None, "website": None},
            "recommendedActions": ([
                {"type":"verify_with_organization","priority":1,"label":"Verify with your bank","reason":"Use a number you find yourself.","enabled":True,"implementation":"stub"},
                {"type":"report_suspicious","priority":2,"label":"Report as suspicious","reason":"You can record this message.","enabled":True,"implementation":"stub"},
                {"type":"save_item","priority":3,"label":"Save this","reason":"Keep it for later.","enabled":True,"implementation":"stub"}
            ] if is_scam else [{"type":"take_no_action","priority":1,"label":"No action needed","reason":"There are no obvious warning signs.","enabled":True,"implementation":"informational"}]),
            "uncertaintyReasons": []
        }


class OpenAIProvider:
    """Keeps vendor-specific structured-output details outside application services."""
    async def analyze(self, input: AnalysisInput) -> dict:
        content = [{"type":"input_text", "text": input.text or "Please read this document carefully."}]
        if input.content and input.media_type:
            data = base64.b64encode(input.content).decode()
            if input.media_type.startswith("image/"):
                content.append({"type":"input_image", "image_url":f"data:{input.media_type};base64,{data}", "detail":"high"})
            else:
                content.append({"type":"input_file", "filename":input.filename or "document.pdf", "file_data":data})
        response = await AsyncOpenAI().responses.create(
            model=os.getenv("OPENAI_MODEL", "gpt-4.1-mini"),
            instructions="You explain everyday messages calmly for older adults. Return only the requested JSON. Never recommend replying to suspicious senders.",
            input=[{"role":"user", "content":content}],
            text={"format":{"type":"json_schema", "name":"analysis", "strict":True,
              "schema":AnalysisPayload.model_json_schema()}},
        )
        return json.loads(response.output_text)
