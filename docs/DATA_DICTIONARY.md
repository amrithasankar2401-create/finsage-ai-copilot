# FinSage Data Dictionary

This document details the synthetic datasets generated for the FinSage project, the schema for each dataset, and specifically highlights the anomalies planted for testing the GenAI copilot's detection capabilities.

## 1. Vendor Master (`vendor_master.csv`)
**Purpose:** Dimension table listing approved vendors and risk ratings.

**Columns:**
- `vendor_id`: Unique identifier for the vendor.
- `vendor_name`: Name of the vendor.
- `business_unit_id`: The business unit this vendor is primarily associated with.
- `category`: Category of services/goods (e.g., IT Services, Logistics).
- `risk_rating`: Low, Medium, or High.
- `country`: Vendor location.

**Planted Anomalies / Key Vendors:**
- `VEND-999` (Acme Shadow Corp) - Correlated high-risk vendor in `BU-01`.
- `VEND-888` (Global Logistics Shell) - Correlated high-risk vendor in `BU-02`.

## 2. Invoices (`invoices.csv`)
**Purpose:** Fact table of AP invoices.

**Columns:**
- `invoice_id`: Unique invoice identifier.
- `vendor_id`: Foreign key to `vendor_master`.
- `vendor_name`: Denormalized vendor name.
- `business_unit_id`: BU responsible for the invoice.
- `po_number`: Purchase Order number.
- `grn_number`: Goods Receipt Note number.
- `invoice_amount`: Amount billed.
- `invoice_date`: Date of invoice.
- `due_date`: Expected payment date.
- `payment_status`: Paid, Pending, or Overdue.
- `currency`: Transaction currency.

**Planted Anomalies:**
1. **Duplicate Invoices**: 100 near-duplicate invoices generated with IDs formatted as `INV-DUP-xxx` (e.g., `INV-DUP-000` to `INV-DUP-099`). They share the same vendor, amount, PO, GRN but have a slightly different invoice date and are marked "Pending".
2. **High-Risk Invoices**: Specific unusually high, round-number invoices for our correlated vendors:
   - `INV-HR-000`: $250,000 for `VEND-999` in `BU-01` on 2023-06-15.
   - `INV-HR-001`: $250,000 for `VEND-888` in `BU-02` on 2023-06-25.

## 3. GL Journal Entries (`gl_journal_entries.csv`)
**Purpose:** General Ledger postings to track accounting transactions.

**Columns:**
- `entry_id`: Unique journal entry ID.
- `business_unit_id`: BU where the entry is posted.
- `account_code`: GL account code.
- `account_name`: GL account name (e.g., Professional Fees).
- `amount`: Posted amount.
- `posting_user`: User who created the entry.
- `approving_user`: User who approved the entry.
- `posting_timestamp`: Datetime of the posting.
- `entry_type`: Manual or Automated.

**Planted Anomalies:**
1. **Segregation of Duties (SoD) Violations**: Entries where `posting_user` equals `approving_user` (`manager1@corp.com`), posted on a Saturday night (weekend/after-hours), and for a round $250,000 amount (matching the suspicious invoices).
   - `GL-ANOM-000`: `BU-01` (correlates with `VEND-999`)
   - `GL-ANOM-001`: `BU-02` (correlates with `VEND-888`)

## 4. Treasury Cashflow (`treasury_cashflow.csv`)
**Purpose:** Weekly cashflow tracking and forecasting.

**Columns:**
- `entity_id`: Entity tracking the cash.
- `business_unit_id`: Associated BU.
- `currency`: Base currency.
- `week_start_date`: First day of the week.
- `opening_balance`: Starting cash balance.
- `ar_collections`: AR collected in the week.
- `ap_payments`: AP paid out in the week.
- `closing_balance`: Actual end-of-week balance.
- `forecast_closing_balance`: Forecasted balance.

**Planted Anomalies:**
1. **Significant Forecast Deviation (>15%)**: For week 46 (mid-Nov 2023), `BU-01` and `BU-02` experience a sudden, unforecasted AP payment of $250,000, causing the actual closing balance to deviate materially from the forecast. This correlates to the high-risk invoices and SoD GL entries for `VEND-999` and `VEND-888`.
