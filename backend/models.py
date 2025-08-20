from typing import Optional, List, Literal, Dict, Any
from datetime import datetime
from sqlmodel import SQLModel, Field, Column, JSON

Effect = Literal["allow", "block"]

class TimeWindow(SQLModel):
    start: str  # "09:00"
    end: str    # "18:00"
    tz: str     # "America/Los_Angeles"

class Conditions(SQLModel):
    users: Optional[List[str]] = None
    locations: Optional[List[str]] = None
    apps: Optional[List[str]] = None
    timeWindow: Optional[TimeWindow] = None
    deviceCompliance: Optional[Literal["compliant","non_compliant","any"]] = "any"
    signInRisk: Optional[Literal["none","low","medium","high","low_or_none"]] = "low_or_none"

class Actions(SQLModel):
    effect: Effect = "allow"
    mfa: bool = False
    passwordReset: bool = False

class Policy(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    enabled: bool = True
    version: int = 1
    conditions: Dict[str, Any] = Field(sa_column=Column(JSON))
    actions: Dict[str, Any] = Field(sa_column=Column(JSON))
    updatedBy: str = "admin"
    updatedAt: datetime = Field(default_factory=datetime.utcnow)

class EvaluationInput(SQLModel):
    user: str
    groups: List[str] = []
    geo: Optional[str] = None
    time: str  # ISO 时间，例如 "2025-08-20T10:35:00-07:00"
    device: Dict[str, Any] = {}
    risk: Dict[str, Any] = {}
    app: Optional[str] = None

class EvaluationOutput(SQLModel):
    decision: Effect
    requirements: Dict[str, Any]
    matchedPolicies: List[str]
    explanations: List[str]

class DraftRequest(SQLModel):
    prompt: str

class DraftResponse(SQLModel):
    policy: Dict[str, Any]
