from fastapi import APIRouter, Query
from typing import Optional
from data_access import dal
import pandas as pd
import numpy as np

router = APIRouter(prefix="/api/invoices", tags=["Invoices"])

@router.get("/high-risk")
async def get_high_risk_invoices(
    business_unit_id: Optional[str] = None,
    min_amount: Optional[float] = None
):
    df = dal.invoices_df.copy()
    
    if business_unit_id:
        df = df[df['business_unit_id'] == business_unit_id]
    if min_amount:
        df = df[df['invoice_amount'] >= min_amount]
        
    if df.empty:
        return []

    # Ensure date parsing
    df['invoice_date'] = pd.to_datetime(df['invoice_date'])
    
    # Sort for shift operations
    df = df.sort_values(by=['vendor_id', 'invoice_amount', 'invoice_date'])
    
    high_risk_results = []
    
    # Find likely duplicates (same vendor, amount diff < $1, date within 5 days)
    # Using simple shift comparison for near duplicates
    df['prev_vendor'] = df['vendor_id'].shift(1)
    df['prev_amount'] = df['invoice_amount'].shift(1)
    df['prev_date'] = df['invoice_date'].shift(1)
    
    # Identify duplicates
    duplicates = df[
        (df['vendor_id'] == df['prev_vendor']) &
        (abs(df['invoice_amount'] - df['prev_amount']) < 1.0) &
        ((df['invoice_date'] - df['prev_date']).dt.days <= 5)
    ]
    
    for _, row in duplicates.iterrows():
        inv_dict = row.drop(['prev_vendor', 'prev_amount', 'prev_date']).to_dict()
        inv_dict['invoice_date'] = inv_dict['invoice_date'].strftime('%Y-%m-%d')
        inv_dict['risk_score'] = 85
        inv_dict['risk_reason'] = "Likely duplicate: Same vendor and amount within 5 days"
        high_risk_results.append(inv_dict)
        
    # Identify excessively large round-number invoices (e.g., amount % 1000 == 0 and > 100k)
    round_numbers = df[
        (df['invoice_amount'] >= 100000) & 
        (df['invoice_amount'] % 1000 == 0)
    ]
    
    for _, row in round_numbers.iterrows():
        # Avoid duplicate entries if already flagged
        if not any(x['invoice_id'] == row['invoice_id'] for x in high_risk_results):
            inv_dict = row.drop(['prev_vendor', 'prev_amount', 'prev_date']).to_dict()
            inv_dict['invoice_date'] = inv_dict['invoice_date'].strftime('%Y-%m-%d')
            inv_dict['risk_score'] = 90
            inv_dict['risk_reason'] = "High risk: Large round-number amount"
            high_risk_results.append(inv_dict)
            
    return high_risk_results
