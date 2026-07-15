import json
import os
import asyncio
from datetime import datetime
import anthropic

from routers.invoices import get_high_risk_invoices
from routers.audit import get_audit_exceptions
from routers.treasury import get_treasury_variance

MONITORING_DIR = os.path.dirname(os.path.abspath(__file__))
LAST_SCAN_FILE = os.path.join(MONITORING_DIR, 'last_scan.json')
HISTORY_FILE = os.path.join(MONITORING_DIR, 'briefing_history.json')
LOG_FILE = os.path.abspath(os.path.join(MONITORING_DIR, '../logs/interaction_log.jsonl'))

def load_json(filepath, default_val):
    if os.path.exists(filepath):
        try:
            with open(filepath, 'r') as f:
                return json.load(f)
        except:
            return default_val
    return default_val

def save_json(filepath, data):
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2)

async def generate_summary_with_claude(new_invs, new_audits, new_treasury, new_compound, active_invs, active_audits, active_treasury, active_compound):
    client = anthropic.AsyncAnthropic()
    
    prompt = f"""
You are FinSage's autonomous monitoring agent. Generate a short, executive-style paragraph summarizing the following morning briefing findings. 
Be concise, professional, and use plain language.
- Active High Risk Invoices: {len(active_invs)} ({len(new_invs)} new)
- Active Audit Exceptions: {len(active_audits)} ({len(new_audits)} new)
- Active Treasury Variances: {len(active_treasury)} ({len(new_treasury)} new)
- Active Compound Risk Alerts (multi-domain): {len(active_compound)} ({len(new_compound)} new)

Ensure you accurately reflect the CURRENT ACTIVE STATE. If there are active risks, explicitly state them (e.g. "{len(active_compound)} compound risk alerts remain active"). Do not claim the environment is stable if active findings are non-zero.
"""
    try:
        response = await client.messages.create(
            model="claude-3-5-sonnet-20240620",
            max_tokens=150,
            system="You are an expert enterprise finance risk analyst.",
            messages=[{"role": "user", "content": prompt}]
        )
        return response.content[0].text
    except Exception as e:
        total_active = len(active_invs) + len(active_audits) + len(active_treasury)
        if total_active == 0 and len(active_compound) == 0:
            return "No risk anomalies detected across AP, Audit, or Treasury domains. The enterprise environment remains stable."
        
        return f"Proactive monitoring reports {len(active_compound)} compound risk alerts and {total_active} isolated anomalies remain active. There were {len(new_invs)+len(new_audits)+len(new_treasury)} new findings since the last scan."

def compute_multi_domain_alerts(invs, audits, treasury):
    audit_bus = {a.get('business_unit_id') for a in audits if a.get('business_unit_id')}
    treasury_bus = {t.get('business_unit_id') for t in treasury if t.get('business_unit_id')}
    
    vendor_to_bu = {}
    for i in invs:
        vid = i.get('vendor_id')
        bu = i.get('business_unit_id')
        if vid and bu and i.get('risk_score', 0) >= 90:
            vendor_to_bu[vid] = bu
            
    alerts = []
    for vid, bu in vendor_to_bu.items():
        domains = ['AP']
        if bu in audit_bus:
            domains.append('Audit')
        if bu in treasury_bus:
            domains.append('Treasury')
            
        if len(domains) >= 2:
            domains_str = "/".join(domains)
            alerts.append({
                "id_key": f"{vid}_{bu}",
                "business_unit_id": f"{vid} ({bu})",
                "message": f"Flagged across multiple domains ({domains_str})"
            })
    return alerts

async def run_risk_scan():
    # 0. Reload data
    from data_access import dal
    dal.load_data()
    
    # 1. Fetch current state
    invs = await get_high_risk_invoices()
    audits = await get_audit_exceptions(exception_type=None)
    treasury = await get_treasury_variance()

    # 2. Load previous state
    last_scan = load_json(LAST_SCAN_FILE, {"invs": [], "audits": [], "treasury": []})
    prev_invs = last_scan.get("invs", [])
    prev_audits = last_scan.get("audits", [])
    prev_treasury = last_scan.get("treasury", [])

    # 3. Diff (New since last scan)
    prev_inv_ids = {i['invoice_id'] for i in prev_invs if 'invoice_id' in i}
    new_invs = [i for i in invs if i.get('invoice_id') not in prev_inv_ids]

    prev_audit_ids = {a['entry_id'] for a in prev_audits if 'entry_id' in a}
    new_audits = [a for a in audits if a.get('entry_id') not in prev_audit_ids]

    prev_treasury_ids = {f"{t.get('entity_id')}_{t.get('week_start_date')}" for t in prev_treasury}
    new_treasury = [t for t in treasury if f"{t.get('entity_id')}_{t.get('week_start_date')}" not in prev_treasury_ids]

    from actions.proposer import propose_action
    # 4. Compound Risk Logic
    current_alerts = compute_multi_domain_alerts(invs, audits, treasury)
    prev_alerts = compute_multi_domain_alerts(prev_invs, prev_audits, prev_treasury)
    
    current_alert_ids = {a['id_key'] for a in current_alerts}
    prev_alert_ids = {a['id_key'] for a in prev_alerts}
    new_alert_ids = current_alert_ids - prev_alert_ids
    
    new_compound_alerts = [a for a in current_alerts if a['id_key'] in new_alert_ids]
    active_compound_alerts = current_alerts
    
    for a in new_compound_alerts:
        # vendor_id is available in the ID key or we can parse it from business_unit_id, 
        # but earlier we set id_key = "{vid}_{bu}". 
        vid = a['id_key'].split('_')[0]
        if vid and vid != 'Unknown':
            propose_action(
                action_type="escalate_to_audit_committee",
                target_entity_id=vid,
                target_type="vendor",
                description=f"Autonomous detection: Vendor {vid} flagged across multiple domains.",
                proposed_by="autonomous_scan"
            )

    # 5. Generate Summary Text
    summary_text = await generate_summary_with_claude(
        new_invs, new_audits, new_treasury, new_compound_alerts,
        invs, audits, treasury, active_compound_alerts
    )

    new_findings = []
    for i in new_invs:
        new_findings.append(f"AP Risk: {i.get('risk_reason')} (BU: {i.get('business_unit_id')}, Amt: ${i.get('invoice_amount')})")
    for a in new_audits:
        new_findings.append(f"Audit Exception: {a.get('exception_reason')} (BU: {a.get('business_unit_id')})")
    for t in new_treasury:
        new_findings.append(f"Treasury Variance: {t.get('variance_pct')}% deviation (Entity: {t.get('entity_id')})")

    active_findings = []
    for i in invs:
        active_findings.append(f"AP Risk: {i.get('risk_reason')} (BU: {i.get('business_unit_id')}, Amt: ${i.get('invoice_amount')})")
    for a in audits:
        active_findings.append(f"Audit Exception: {a.get('exception_reason')} (BU: {a.get('business_unit_id')})")
    for t in treasury:
        active_findings.append(f"Treasury Variance: {t.get('variance_pct')}% deviation (Entity: {t.get('entity_id')})")



    # 6. Save State
    current_state = {
        "invs": invs,
        "audits": audits,
        "treasury": treasury
    }
    save_json(LAST_SCAN_FILE, current_state)

    # 7. Construct Briefing
    timestamp = datetime.utcnow().isoformat() + "Z"
    briefing = {
        "scan_timestamp": timestamp,
        "summary_text": summary_text,
        "new_findings": new_findings,
        "compound_risk_alerts": new_compound_alerts, # these are new compound alerts
        "active_findings": active_findings,
        "active_compound_alerts": active_compound_alerts
    }

    history = load_json(HISTORY_FILE, [])
    history.insert(0, briefing)
    history = history[:10]
    save_json(HISTORY_FILE, history)

    # 8. Audit Logging
    log_entry = {
        "timestamp": timestamp,
        "event_type": "autonomous_scan",
        "user_message": "SYSTEM: Proactive Morning Scan",
        "assistant_response": summary_text,
        "tools_called": [{"tool": "run_risk_scan", "params": {}}],
        "low_confidence": False,
        "actions": [
            {"type": "autonomous_scan_completed", "new_findings_count": len(new_findings), "compound_alerts_count": len(new_compound_alerts)}
        ]
    }
    
    with open(LOG_FILE, 'a') as f:
        f.write(json.dumps(log_entry) + '\n')

    return briefing

async def background_scanner_loop():
    # Wait a few seconds on startup to let datasets load
    await asyncio.sleep(5)
    while True:
        try:
            print("Running autonomous risk scan...")
            await run_risk_scan()
            print("Autonomous scan complete.")
        except Exception as e:
            print(f"Autonomous scan failed: {e}")
        # Run every 5 minutes
        await asyncio.sleep(300)
