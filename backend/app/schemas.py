from typing import Literal
from pydantic import BaseModel, ConfigDict, Field


class RecommendedAction(BaseModel):
    model_config = ConfigDict(extra="forbid")
    type: Literal["create_reminder", "draft_reply", "share_with_trusted_contact", "call_trusted_contact", "save_item", "report_suspicious", "verify_with_organization", "take_no_action"]
    priority: Literal[1, 2, 3]
    label: str = Field(max_length=100)
    reason: str = Field(max_length=240)
    enabled: bool
    implementation: Literal["live", "stub", "informational"]


class ExtractedFacts(BaseModel):
    model_config = ConfigDict(extra="forbid")
    sender: str | None
    organization: str | None
    amount: str | None
    deadline: str | None
    appointmentDate: str | None
    phoneNumber: str | None
    website: str | None


class AnalysisPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")
    status: Literal["complete", "partially_readable", "insufficient_information", "failed"]
    inputType: Literal["official_document", "bill_or_payment", "appointment", "message", "medical", "unknown"]
    specificType: str | None
    title: str = Field(max_length=140)
    summary: str = Field(max_length=500)
    actionRequirement: Literal["no_action", "optional_action", "action_required", "verify_before_acting", "unknown"]
    urgency: Literal["none", "low", "medium", "high", "unknown"]
    riskLevel: Literal["green", "yellow", "red", "unknown"]
    consequenceLevel: Literal["low", "moderate", "high", "unknown"]
    confidence: Literal["high", "medium", "low"]
    riskCategories: list[str]
    riskReasons: list[str]
    extractedFacts: ExtractedFacts
    recommendedActions: list[RecommendedAction]
    uncertaintyReasons: list[str]


class AnalysisInput(BaseModel):
    text: str | None = None
    filename: str | None = None
    media_type: str | None = None
    content: bytes | None = None
