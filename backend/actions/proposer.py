import os
import json
import uuid
from datetime import datetime
from data_access import dal

ACTIONS_DIR = os.path.dirname(os.path.abspath(__file__))
PROPOSALS_FILE = os.path.join(ACTIONS_DIR, 'proposals.json')
LOG_FILE = os.path.abspath(os.path.join(ACTIONS_DIR, '../logs/interaction_log.jsonl'))

def load_proposals():
    if os.path.exists(PROPOSALS_FILE):
        with open(PROPOSALS_FILE, 'r') as f:
            return json.load(f)
    return []

def save_proposals(data):
    os.makedirs(ACTIONS_DIR, exist_ok=True)
    with open(PROPOSALS_FILE, 'w') as f:
        json.dump(data, f, indent=2)

def log_action_event(event_type, proposal, current_user="controller@finsage-demo.com"):
    log_entry = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "event_type": event_type,
        "user_message": f"SYSTEM: Action {event_type.upper()}",
        "assistant_response": f"Proposal {proposal['proposal_id']}: {proposal['description']}",
        "tools_called": [],
        "low_confidence": False,
        "actions": [
            {
                "type": event_type,
                "proposal_id": proposal['proposal_id'],
                "action_type": proposal['action_type'],
                "target_entity_id": proposal['target_entity_id'],
                "target_type": proposal['target_type'],
                "approved_by": current_user if event_type in ["action_approved_executed", "action_rejected"] else None
            }
        ]
    }
    
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    with open(LOG_FILE, 'a') as f:
        f.write(json.dumps(log_entry) + '\n')

def propose_action(action_type: str, target_entity_id: str, target_type: str, description: str, proposed_by: str = "chat"):
    proposals = load_proposals()
    
    # Check if a pending proposal already exists for this action & entity
    for p in proposals:
        if p['status'] == 'pending' and p['action_type'] == action_type and p['target_entity_id'] == target_entity_id:
            return p['proposal_id']
            
    proposal_id = f"ACT-{str(uuid.uuid4())[:8].upper()}"
    
    proposal = {
        "proposal_id": proposal_id,
        "action_type": action_type,
        "target_entity_id": target_entity_id,
        "target_type": target_type,
        "description": description,
        "proposed_by": proposed_by,
        "status": "pending",
        "created_at": datetime.utcnow().isoformat() + "Z"
    }
    
    proposals.append(proposal)
    save_proposals(proposals)
    log_action_event("action_proposed", proposal)
    
    return proposal_id

def execute_action(proposal_id: str, current_user: str = "controller@finsage-demo.com"):
    proposals = load_proposals()
    for p in proposals:
        if p['proposal_id'] == proposal_id and p['status'] == 'pending':
            # Perform actual data change
            if p['action_type'] == 'hold_payment' and p['target_type'] == 'invoice':
                idx = dal.invoices_df.index[dal.invoices_df['invoice_id'] == p['target_entity_id']]
                if not idx.empty:
                    dal.invoices_df.loc[idx, 'payment_status'] = 'on_hold'
                    dal.save_invoices()
            elif p['action_type'] == 'flag_for_review' and p['target_type'] == 'vendor':
                idx = dal.vendors_df.index[dal.vendors_df['vendor_id'] == p['target_entity_id']]
                if not idx.empty:
                    dal.vendors_df.loc[idx, 'risk_rating'] = 'High (Under Review)'
                    dal.save_vendors()
            elif p['action_type'] == 'flag_for_review' and p['target_type'] == 'journal_entry':
                # For demo purposes, we might not have a status column in GL, but let's assume we update a flag
                idx = dal.gl_entries_df.index[dal.gl_entries_df['entry_id'] == p['target_entity_id']]
                if not idx.empty:
                    dal.gl_entries_df.loc[idx, 'entry_type'] = 'Under Review'
                    dal.save_gl_entries()
            elif p['action_type'] == 'escalate_to_audit_committee' and p['target_type'] == 'vendor':
                idx = dal.vendors_df.index[dal.vendors_df['vendor_id'] == p['target_entity_id']]
                if not idx.empty:
                    dal.vendors_df.loc[idx, 'risk_rating'] = 'Escalated to Audit Committee'
                    dal.save_vendors()

            p['status'] = 'approved_and_executed'
            p['executed_at'] = datetime.utcnow().isoformat() + "Z"
            p['executed_by'] = current_user
            save_proposals(proposals)
            log_action_event("action_approved_executed", p, current_user)
            return p
            
    return None

def reject_action(proposal_id: str, current_user: str = "controller@finsage-demo.com"):
    proposals = load_proposals()
    for p in proposals:
        if p['proposal_id'] == proposal_id and p['status'] == 'pending':
            p['status'] = 'rejected'
            p['rejected_at'] = datetime.utcnow().isoformat() + "Z"
            p['rejected_by'] = current_user
            save_proposals(proposals)
            log_action_event("action_rejected", p, current_user)
            return p
            
    return None

def get_pending_actions():
    proposals = load_proposals()
    return [p for p in proposals if p['status'] == 'pending']
