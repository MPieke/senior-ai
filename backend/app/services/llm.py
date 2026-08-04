from typing import Protocol


class AnalysisProvider(Protocol):
    async def analyze(self, text: str) -> dict: ...


class FixtureProvider:
    async def analyze(self, text: str) -> dict:
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
