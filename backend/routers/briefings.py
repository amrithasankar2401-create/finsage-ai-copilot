from fastapi import APIRouter, HTTPException
import json
import os
from monitoring.scanner import run_risk_scan, HISTORY_FILE, load_json

router = APIRouter(prefix="/api/briefings", tags=["Proactive Monitoring"])

@router.get("/latest")
async def get_latest_briefing():
    history = load_json(HISTORY_FILE, [])
    if not history:
        return {}
    return history[0]

@router.get("/history")
async def get_briefing_history():
    return load_json(HISTORY_FILE, [])

@router.post("/trigger")
async def trigger_scan():
    try:
        briefing = await run_risk_scan()
        return {"status": "success", "briefing": briefing}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
