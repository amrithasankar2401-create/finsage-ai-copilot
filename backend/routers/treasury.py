from fastapi import APIRouter, Query
from typing import Optional
from data_access import dal
import pandas as pd

router = APIRouter(prefix="/api/treasury", tags=["Treasury"])

@router.get("/variance")
async def get_treasury_variance(
    entity_id: Optional[str] = None,
    min_variance_pct: float = 15.0
):
    df = dal.treasury_df.copy()
    
    if entity_id:
        df = df[df['entity_id'] == entity_id]
        
    if df.empty:
        return []

    variances = []
    
    for _, row in df.iterrows():
        actual = row['closing_balance']
        forecast = row['forecast_closing_balance']
        
        if forecast == 0:
            continue
            
        variance_amount = actual - forecast
        variance_pct = abs(variance_amount / forecast) * 100
        
        if variance_pct > min_variance_pct:
            var_dict = row.to_dict()
            var_dict['variance_amount'] = round(variance_amount, 2)
            var_dict['variance_pct'] = round(variance_pct, 2)
            variances.append(var_dict)
            
    return variances

@router.get("/forecast-summary")
async def get_forecast_summary(
    entity_id: Optional[str] = None
):
    df = dal.treasury_df.copy()
    
    if entity_id:
        df = df[df['entity_id'] == entity_id]
        
    if df.empty:
        return {}

    # Average weekly closing balance trend
    avg_closing = df.groupby('entity_id')['closing_balance'].mean().round(2).to_dict()
    
    # Current liquidity position (latest week)
    df['week_start_date'] = pd.to_datetime(df['week_start_date'])
    latest_date = df['week_start_date'].max()
    latest_df = df[df['week_start_date'] == latest_date]
    
    current_liquidity = latest_df.set_index('entity_id')['closing_balance'].to_dict()
    
    return {
        "average_weekly_closing_balances": avg_closing,
        "current_liquidity_position": current_liquidity,
        "latest_week": latest_date.strftime('%Y-%m-%d')
    }
