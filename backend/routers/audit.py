from fastapi import APIRouter, Query
from typing import Optional
from data_access import dal
import pandas as pd

router = APIRouter(prefix="/api/audit", tags=["Audit"])

@router.get("/exceptions")
async def get_audit_exceptions(
    business_unit_id: Optional[str] = None,
    exception_type: Optional[str] = Query(None, description="'sod', 'round_dollar', 'after_hours'")
):
    df = dal.gl_entries_df.copy()
    
    if business_unit_id:
        df = df[df['business_unit_id'] == business_unit_id]
        
    if df.empty:
        return []

    df['posting_timestamp'] = pd.to_datetime(df['posting_timestamp'])
    exceptions = []
    
    for _, row in df.iterrows():
        reasons = []
        
        # Segregation of Duties
        is_sod = row['posting_user'] == row['approving_user']
        if is_sod and (exception_type in [None, 'sod']):
            reasons.append("Segregation of Duties violation: poster is approver")
            
        # Round Dollar
        is_round = (row['amount'] >= 10000) and (row['amount'] % 1000 == 0)
        if is_round and (exception_type in [None, 'round_dollar']):
            reasons.append("Unusual round-dollar posting")
            
        # After Hours / Weekend
        hour = row['posting_timestamp'].hour
        weekday = row['posting_timestamp'].weekday()
        is_after_hours = hour < 7 or hour > 20 or weekday >= 5
        if is_after_hours and (exception_type in [None, 'after_hours']):
            reasons.append("Posting outside business hours or on weekend")
            
        if reasons:
            entry_dict = row.to_dict()
            entry_dict['posting_timestamp'] = entry_dict['posting_timestamp'].strftime('%Y-%m-%d %H:%M:%S')
            entry_dict['exception_reason'] = " | ".join(reasons)
            
            # If the user requested a specific type and we didn't find it for this row, skip
            # (Handled by the condition checks above, if reasons is populated, it matched the filter)
            exceptions.append(entry_dict)
            
    return exceptions
