from fastapi import APIRouter, HTTPException
import os
import json

router = APIRouter(prefix="/api/admin", tags=["Admin Dashboard"])

LOGS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../logs'))
LOG_FILE = os.path.join(LOGS_DIR, 'interaction_log.jsonl')

@router.get("/logs")
async def get_audit_logs():
    """
    Returns all logged AI interactions for the Admin Dashboard.
    Provides visibility into exactly what data was accessed (tool calls) for SOX compliance.
    """
    if not os.path.exists(LOG_FILE):
        return []
        
    logs = []
    try:
        with open(LOG_FILE, 'r') as f:
            for line in f:
                if line.strip():
                    logs.append(json.loads(line))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
        
    # Return reversed so newest are first
    return logs[::-1]
