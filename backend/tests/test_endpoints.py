from fastapi.testclient import TestClient
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from main import app, dal

def test_endpoints():
    # Ensure data is loaded
    dal.load_data()
    
    client = TestClient(app)
    
    print("Testing 1. GET /api/invoices/high-risk")
    response = client.get("/api/invoices/high-risk")
    assert response.status_code == 200
    invoices = response.json()
    assert len(invoices) > 0
    # Check if our planted HR invoices are found
    hr_ids = [inv['invoice_id'] for inv in invoices]
    assert 'INV-HR-000' in hr_ids, "Failed to detect INV-HR-000"
    assert 'INV-HR-001' in hr_ids, "Failed to detect INV-HR-001"
    assert any('INV-DUP' in i_id for i_id in hr_ids), "Failed to detect duplicate invoices"
    print("[PASS] Invoices endpoint works correctly")
    
    print("Testing 2. GET /api/audit/exceptions")
    response = client.get("/api/audit/exceptions")
    assert response.status_code == 200
    exceptions = response.json()
    assert len(exceptions) > 0
    # Check if planted GL anomalies are found
    anom_ids = [ex['entry_id'] for ex in exceptions]
    assert 'GL-ANOM-000' in anom_ids, "Failed to detect GL-ANOM-000"
    assert 'GL-ANOM-001' in anom_ids, "Failed to detect GL-ANOM-001"
    print("[PASS] Audit exceptions endpoint works correctly")

    print("Testing 3. GET /api/treasury/variance")
    response = client.get("/api/treasury/variance")
    assert response.status_code == 200
    variances = response.json()
    assert len(variances) > 0
    print("[PASS] Treasury variance endpoint works correctly")
    
    print("Testing 4. GET /api/treasury/forecast-summary")
    response = client.get("/api/treasury/forecast-summary")
    assert response.status_code == 200
    summary = response.json()
    assert "average_weekly_closing_balances" in summary
    assert "current_liquidity_position" in summary
    print("[PASS] Treasury forecast summary endpoint works correctly")
    
    print("Testing 5. GET /api/vendors/{vendor_id}/risk-profile (Cross Domain)")
    # Test our correlated vendor VEND-999
    response = client.get("/api/vendors/VEND-999/risk-profile")
    assert response.status_code == 200
    profile = response.json()
    
    assert profile['vendor_info']['vendor_id'] == 'VEND-999'
    
    # Must have the HR invoice
    assert any(inv['invoice_id'] == 'INV-HR-000' for inv in profile['high_risk_invoices'])
    # Must have the GL anomaly for that BU
    assert any(ex['entry_id'] == 'GL-ANOM-000' for ex in profile['related_gl_exceptions'])
    # Must have treasury variance for that BU/Entity
    assert len(profile['related_treasury_variance']) > 0
    print("[PASS] Cross-domain endpoint works correctly and detects VEND-999 footprint across all datasets!")
    
    print("Testing 6. GET /api/business-units/{bu_id}/summary")
    response = client.get("/api/business-units/BU-01/summary")
    assert response.status_code == 200
    bu_summary = response.json()
    assert bu_summary['business_unit_id'] == 'BU-01'
    assert bu_summary['total_high_risk_invoice_amount'] > 0
    assert bu_summary['audit_exceptions_count'] > 0
    assert bu_summary['treasury_variance_incidents'] > 0
    print("[PASS] BU summary endpoint works correctly")
    
    print("\nAll 6 endpoints validated successfully against synthetic ground truth!")

if __name__ == "__main__":
    test_endpoints()
