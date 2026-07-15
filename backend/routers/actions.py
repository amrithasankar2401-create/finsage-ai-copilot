from fastapi import APIRouter, HTTPException
from actions.proposer import get_pending_actions, execute_action, reject_action

router = APIRouter(prefix="/api/actions", tags=["Actions"])

@router.get("/pending")
async def get_pending():
    return get_pending_actions()

@router.post("/{proposal_id}/approve")
async def approve_action(proposal_id: str):
    result = execute_action(proposal_id)
    if not result:
        raise HTTPException(status_code=404, detail="Proposal not found or not pending")
    return {"status": "success", "proposal": result}

@router.post("/{proposal_id}/reject")
async def reject_proposal(proposal_id: str):
    result = reject_action(proposal_id)
    if not result:
        raise HTTPException(status_code=404, detail="Proposal not found or not pending")
    return {"status": "success", "proposal": result}
