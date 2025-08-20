from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import select, Session
from typing import List, Dict, Any
from datetime import datetime
from dotenv import load_dotenv

from db import init_db, get_session
from models import Policy, DraftRequest, DraftResponse, EvaluationInput, EvaluationOutput
from policy_engine import evaluate_against_policies

load_dotenv()
app = FastAPI(title="AI Policy Platform (MVP)")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"]
)

@app.on_event("startup")
def on_startup():
    init_db()

@app.get("/health")
def health():
    return {"status": "ok", "time": datetime.utcnow().isoformat() + "Z"}

# --- AI Draft（先用规则模板模拟；后续可接 LLM） ---
@app.post("/ai/draft", response_model=DraftResponse)
def ai_draft(req: DraftRequest):
    text = req.prompt.lower()
    # 简化映射：识别几个关键词并生成一个策略草案
    policy = {
        "name": "Draft Policy",
        "enabled": True,
        "conditions": {
            "users": ["group:employees"],
            "locations": ["US-CA"],
            "apps": ["crm"],
            "timeWindow": {"start": "09:00", "end": "18:00", "tz": "America/Los_Angeles"},
            "deviceCompliance": "any",
            "signInRisk": "low_or_none"
        },
        "actions": {"effect": "allow", "mfa": False, "passwordReset": False},
    }
    if "mfa" in text or "非合规" in text or "二次验证" in text:
        policy["actions"]["mfa"] = True
    if "阻止" in text or "block" in text or "高风险" in text:
        policy["actions"]["effect"] = "block"
        policy["conditions"]["signInRisk"] = "high"
    if "外包" in text or "contractor" in text:
        policy["conditions"]["users"] = ["group:contractors"]
    if "时间" in text and "8" in text:
        policy["conditions"]["timeWindow"]["start"] = "08:00"

    return {"policy": policy}

# --- Policies CRUD ---
@app.get("/policies", response_model=List[Policy])
def list_policies(session: Session = Depends(get_session)):
    return session.exec(select(Policy)).all()

@app.post("/policies", response_model=Policy)
def create_policy(payload: Dict[str, Any], session: Session = Depends(get_session)):
    p = Policy(
        name=payload.get("name", "New Policy"),
        enabled=payload.get("enabled", True),
        version=1,
        conditions=payload.get("conditions", {}),
        actions=payload.get("actions", {}),
        updatedBy=payload.get("updatedBy", "admin"),
    )
    session.add(p)
    session.commit()
    session.refresh(p)
    return p

@app.get("/policies/{pid}", response_model=Policy)
def get_policy(pid: int, session: Session = Depends(get_session)):
    p = session.get(Policy, pid)
    if not p:
        raise HTTPException(404, "Policy not found")
    return p

@app.put("/policies/{pid}", response_model=Policy)
def update_policy(pid: int, payload: Dict[str, Any], session: Session = Depends(get_session)):
    p = session.get(Policy, pid)
    if not p:
        raise HTTPException(404, "Policy not found")
    # 简单版本控制：每次更新 +1
    p.name = payload.get("name", p.name)
    p.enabled = payload.get("enabled", p.enabled)
    p.conditions = payload.get("conditions", p.conditions)
    p.actions = payload.get("actions", p.actions)
    p.version += 1
    p.updatedBy = payload.get("updatedBy", "admin")
    p.updatedAt = datetime.utcnow()
    session.add(p)
    session.commit()
    session.refresh(p)
    return p

# --- Evaluate ---
@app.post("/evaluate", response_model=EvaluationOutput)
def evaluate(login: EvaluationInput, session: Session = Depends(get_session)):
    policies = session.exec(select(Policy).where(Policy.enabled == True)).all()
    result = evaluate_against_policies([{
        "name": p.name,
        "enabled": p.enabled,
        "conditions": p.conditions,
        "actions": p.actions
    } for p in policies], login.model_dump())
    return result
