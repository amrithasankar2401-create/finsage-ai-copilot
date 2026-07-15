import pandas as pd
import numpy as np
from faker import Faker
import random
from datetime import datetime, timedelta
import os

fake = Faker()
Faker.seed(42)
np.random.seed(42)
random.seed(42)

# Ensure data directory exists
os.makedirs(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../data')), exist_ok=True)
data_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../data'))

# -------------------------------------------------------------------------
# 1. Vendor Master
# -------------------------------------------------------------------------
business_units = ['BU-01', 'BU-02', 'BU-03', 'BU-04', 'BU-05']
entities = {'BU-01': 'ENT-01', 'BU-02': 'ENT-02', 'BU-03': 'ENT-03', 'BU-04': 'ENT-04', 'BU-05': 'ENT-05'}
categories = ['IT Services', 'Office Supplies', 'Marketing', 'Consulting', 'Logistics']
countries = ['US', 'UK', 'CA', 'DE', 'FR']

vendors = []
# Deliberately correlated high-risk vendors
correlated_vendors = [
    {'vendor_id': 'VEND-999', 'vendor_name': 'Acme Shadow Corp', 'business_unit_id': 'BU-01', 'category': 'Consulting', 'risk_rating': 'High', 'country': 'US'},
    {'vendor_id': 'VEND-888', 'vendor_name': 'Global Logistics Shell', 'business_unit_id': 'BU-02', 'category': 'Logistics', 'risk_rating': 'High', 'country': 'CA'}
]
vendors.extend(correlated_vendors)

for i in range(150):
    vendors.append({
        'vendor_id': f'VEND-{i:03d}',
        'vendor_name': fake.company(),
        'business_unit_id': random.choice(business_units),
        'category': random.choice(categories),
        'risk_rating': random.choices(['Low', 'Medium', 'High'], weights=[0.7, 0.2, 0.1])[0],
        'country': random.choice(countries)
    })

df_vendors = pd.DataFrame(vendors)
df_vendors.to_csv(os.path.join(data_dir, 'vendor_master.csv'), index=False)

# -------------------------------------------------------------------------
# 2. Invoices
# -------------------------------------------------------------------------
invoices = []
start_date = datetime(2023, 1, 1)

for i in range(2500):
    vendor = random.choice(vendors)
    inv_date = fake.date_between(start_date=start_date, end_date=datetime(2023, 12, 31))
    amount = round(random.uniform(500, 50000), 2)
    
    invoices.append({
        'invoice_id': f'INV-{i:05d}',
        'vendor_id': vendor['vendor_id'],
        'vendor_name': vendor['vendor_name'],
        'business_unit_id': vendor['business_unit_id'],
        'po_number': f'PO-{random.randint(10000, 99999)}',
        'grn_number': f'GRN-{random.randint(10000, 99999)}',
        'invoice_amount': amount,
        'invoice_date': inv_date.strftime('%Y-%m-%d'),
        'due_date': (inv_date + timedelta(days=30)).strftime('%Y-%m-%d'),
        'payment_status': random.choices(['Paid', 'Pending', 'Overdue'], weights=[0.8, 0.1, 0.1])[0],
        'currency': 'USD'
    })

# Plant duplicates/near-duplicates
for i in range(100):
    base_inv = random.choice(invoices)
    invoices.append({
        'invoice_id': f'INV-DUP-{i:03d}',
        'vendor_id': base_inv['vendor_id'],
        'vendor_name': base_inv['vendor_name'],
        'business_unit_id': base_inv['business_unit_id'],
        'po_number': base_inv['po_number'],
        'grn_number': base_inv['grn_number'],
        'invoice_amount': base_inv['invoice_amount'],
        'invoice_date': (datetime.strptime(base_inv['invoice_date'], '%Y-%m-%d') + timedelta(days=random.randint(1,3))).strftime('%Y-%m-%d'),
        'due_date': base_inv['due_date'],
        'payment_status': 'Pending',
        'currency': 'USD'
    })

# Plant high-risk patterns for correlated vendors (round numbers, unusually high)
for i, v in enumerate(correlated_vendors):
    inv_date = datetime(2023, 6, 15) + timedelta(days=i*10)
    invoices.append({
        'invoice_id': f'INV-HR-{i:03d}',
        'vendor_id': v['vendor_id'],
        'vendor_name': v['vendor_name'],
        'business_unit_id': v['business_unit_id'],
        'po_number': f'PO-HR-{i}',
        'grn_number': f'GRN-HR-{i}',
        'invoice_amount': 250000.00, # Round number, very high
        'invoice_date': inv_date.strftime('%Y-%m-%d'),
        'due_date': (inv_date + timedelta(days=15)).strftime('%Y-%m-%d'), # Short terms
        'payment_status': 'Paid',
        'currency': 'USD'
    })

df_invoices = pd.DataFrame(invoices)
df_invoices.to_csv(os.path.join(data_dir, 'invoices.csv'), index=False)


# -------------------------------------------------------------------------
# 3. GL Journal Entries
# -------------------------------------------------------------------------
gl_entries = []
accounts = [
    ('1000', 'Cash'),
    ('2000', 'Accounts Payable'),
    ('5000', 'Professional Fees'),
    ('5100', 'Travel & Entertainment'),
    ('5200', 'Office Supplies')
]
users = ['user1@corp.com', 'user2@corp.com', 'user3@corp.com', 'manager1@corp.com', 'manager2@corp.com']

for i in range(5000):
    acc = random.choice(accounts)
    post_time = fake.date_time_between(start_date=start_date, end_date=datetime(2023, 12, 31))
    # Make sure it's a weekday for normal entries
    if post_time.weekday() >= 5:
        post_time -= timedelta(days=2)
    # Make sure it's during business hours
    post_time = post_time.replace(hour=random.randint(9, 17))
    
    amount = round(random.uniform(100, 10000), 2)
    poster = random.choice(users[:3])
    approver = random.choice(users[3:])
    
    gl_entries.append({
        'entry_id': f'GL-{i:05d}',
        'business_unit_id': random.choice(business_units),
        'account_code': acc[0],
        'account_name': acc[1],
        'amount': amount,
        'posting_user': poster,
        'approving_user': approver,
        'posting_timestamp': post_time.strftime('%Y-%m-%d %H:%M:%S'),
        'entry_type': 'Manual' if random.random() > 0.8 else 'Automated'
    })

# Plant anomalies: round-dollar, weekend/after-hours, SoD violations
for i, v in enumerate(correlated_vendors):
    # Segregation of duties violation & round dollar
    post_time = datetime(2023, 11, 25, 23, 45, 0) # Saturday night
    gl_entries.append({
        'entry_id': f'GL-ANOM-{i:03d}',
        'business_unit_id': v['business_unit_id'],
        'account_code': '5000',
        'account_name': 'Professional Fees',
        'amount': 250000.00, # Round number, matches the invoice
        'posting_user': 'manager1@corp.com',
        'approving_user': 'manager1@corp.com', # SoD violation
        'posting_timestamp': post_time.strftime('%Y-%m-%d %H:%M:%S'),
        'entry_type': 'Manual'
    })

df_gl = pd.DataFrame(gl_entries)
df_gl.to_csv(os.path.join(data_dir, 'gl_journal_entries.csv'), index=False)


# -------------------------------------------------------------------------
# 4. Treasury Cashflow
# -------------------------------------------------------------------------
treasury = []
current_date = start_date

# Generate 52 weeks of data
for week in range(52):
    for bu in business_units:
        opening = round(random.uniform(200000, 800000), 2)
        collections = round(random.uniform(50000, 200000), 2)
        payments = round(random.uniform(40000, 150000), 2)
        
        # Calculate actuals
        actual_closing = opening + collections - payments
        
        # Forecast is usually close
        forecast_closing = actual_closing * random.uniform(0.95, 1.05)
        
        # Plant deviation for correlated vendor BUs on a specific week (e.g. week 46, roughly mid-Nov)
        if week == 46 and bu in [v['business_unit_id'] for v in correlated_vendors]:
            actual_closing = actual_closing - 250000.00 # large unforecasted payment
            # forecast remains high, creating >15% deviation
        
        treasury.append({
            'entity_id': entities[bu],
            'business_unit_id': bu,
            'currency': 'USD',
            'week_start_date': current_date.strftime('%Y-%m-%d'),
            'opening_balance': opening,
            'ar_collections': collections,
            'ap_payments': payments,
            'closing_balance': actual_closing,
            'forecast_closing_balance': round(forecast_closing, 2)
        })
    current_date += timedelta(days=7)

df_treasury = pd.DataFrame(treasury)
df_treasury.to_csv(os.path.join(data_dir, 'treasury_cashflow.csv'), index=False)

print("Data generation complete. Files saved to data directory.")
