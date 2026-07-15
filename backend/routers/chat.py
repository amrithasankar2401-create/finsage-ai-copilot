from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict
import os
import json
import datetime
from agents.orchestrator import process_chat_request

LOGS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../logs'))

router = APIRouter(prefix="/api", tags=["Chat"])

# In-memory storage for conversations
conversations: Dict[str, List[Dict]] = {}

class ChatRequest(BaseModel):
    message: str
    conversation_id: str

def append_to_audit_log(cid, user_msg, used_tools, final_text, low_confidence, actions, specialists_used):
    log_file = os.path.join(LOGS_DIR, 'interaction_log.jsonl')
    log_entry = {
        "timestamp": datetime.datetime.now().isoformat(),
        "conversation_id": cid,
        "user_message": user_msg,
        "tools_called": used_tools,
        "assistant_response": final_text,
        "low_confidence": low_confidence,
        "actions": actions,
        "specialists_used": specialists_used
    }
    with open(log_file, "a") as f:
        f.write(json.dumps(log_entry) + "\n")

@router.post("/chat")
async def chat_endpoint(req: ChatRequest):
    cid = req.conversation_id
    if cid not in conversations:
        conversations[cid] = []
        
    try:
        # Process through orchestrator (passes history without current msg)
        result = await process_chat_request(req.message, conversations[cid])
    except Exception as e:
        print(f"Orchestrator failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
        
    # Append to memory
    conversations[cid].append({"role": "user", "content": req.message})
    conversations[cid].append({"role": "assistant", "content": result["answer"]})

    # Audit Logging
    append_to_audit_log(
        cid, 
        req.message, 
        result["sources"], 
        result["answer"], 
        result["low_confidence"], 
        result["actions"],
        result["specialists_used"]
    )

    return {
        "answer": result["answer"],
        "sources": result["sources"],
        "low_confidence": result["low_confidence"],
        "actions": result["actions"],
        "specialists_used": result["specialists_used"]
    }
