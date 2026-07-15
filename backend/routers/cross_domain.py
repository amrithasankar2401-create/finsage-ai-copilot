from fastapi import APIRouter, HTTPException
from data_access import dal
from routers.invoices import get_high_risk_invoices
from routers.audit import get_audit_exceptions
from routers.treasury import get_treasury_variance

router = APIRouter(tags=["Cross Domain"])

@router.get("/api/vendors/{vendor_id}/risk-profile")
async def get_vendor_risk_profile(vendor_id: str):
    # Lookup vendor
    vendor_df = dal.vendors_df[dal.vendors_df['vendor_id'] == vendor_id]
    if vendor_df.empty:
        raise HTTPException(status_code=404, detail="Vendor not found")
        
    vendor_info = vendor_df.iloc[0].to_dict()
    bu_id = vendor_info['business_unit_id']
    
    # Get high risk invoices for this BU
    all_high_risk_invoices = await get_high_risk_invoices(business_unit_id=bu_id)
    # Filter to this specific vendor
    vendor_high_risk_invoices = [inv for inv in all_high_risk_invoices if inv['vendor_id'] == vendor_id]
    
    # Get GL exceptions for this BU
    gl_exceptions = await get_audit_exceptions(business_unit_id=bu_id, exception_type=None)
    
    # Get Treasury variance for this entity
    # First, find entity for this BU
    entity_id = None
    entity_df = dal.treasury_df[dal.treasury_df['business_unit_id'] == bu_id]
    if not entity_df.empty:
        entity_id = entity_df.iloc[0]['entity_id']
        
    treasury_variance = []
    if entity_id:
        treasury_variance = await get_treasury_variance(entity_id=entity_id)

    return {
        "vendor_info": vendor_info,
        "high_risk_invoices": vendor_high_risk_invoices,
        "related_gl_exceptions": gl_exceptions,
        "related_treasury_variance": treasury_variance
    }

@router.get("/api/business-units/{bu_id}/summary")
async def get_bu_summary(bu_id: str):
    # Total high-risk invoice $
    all_high_risk_invoices = await get_high_risk_invoices(business_unit_id=bu_id)
    total_high_risk_amount = sum(inv['invoice_amount'] for inv in all_high_risk_invoices)
    
    # Count of audit exceptions
    gl_exceptions = await get_audit_exceptions(business_unit_id=bu_id, exception_type=None)
    audit_exceptions_count = len(gl_exceptions)
    
    # Treasury variance trend
    entity_id = None
    entity_df = dal.treasury_df[dal.treasury_df['business_unit_id'] == bu_id]
    if not entity_df.empty:
        entity_id = entity_df.iloc[0]['entity_id']
        
    treasury_variance = []
    if entity_id:
        treasury_variance = await get_treasury_variance(entity_id=entity_id)
    
    return {
        "business_unit_id": bu_id,
        "total_high_risk_invoice_amount": round(total_high_risk_amount, 2),
        "audit_exceptions_count": audit_exceptions_count,
        "treasury_variance_incidents": len(treasury_variance)
    }
