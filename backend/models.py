from pydantic import BaseModel
from typing import Optional

class Vendor(BaseModel):
    vendor_id: str
    vendor_name: str
    business_unit_id: str
    category: str
    risk_rating: str
    country: str

class Invoice(BaseModel):
    invoice_id: str
    vendor_id: str
    vendor_name: str
    business_unit_id: str
    po_number: str
    grn_number: str
    invoice_amount: float
    invoice_date: str
    due_date: str
    payment_status: str
    currency: str

class JournalEntry(BaseModel):
    entry_id: str
    business_unit_id: str
    account_code: str
    account_name: str
    amount: float
    posting_user: str
    approving_user: str
    posting_timestamp: str
    entry_type: str

class TreasuryWeek(BaseModel):
    entity_id: str
    business_unit_id: str
    currency: str
    week_start_date: str
    opening_balance: float
    ar_collections: float
    ap_payments: float
    closing_balance: float
    forecast_closing_balance: float
