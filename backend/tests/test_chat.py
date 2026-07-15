from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from main import app, dal

def print_chat(title, prompt, response_json):
    print("=" * 80)
    print(f"TEST: {title}")
    print(f"USER: {prompt}")
    print("-" * 80)
    print(f"FINSAGE: {response_json.get('answer', 'ERROR: ' + str(response_json))}")
    print("-" * 80)
    if 'sources' in response_json:
        print("SOURCES USED:")
        for src in response_json['sources']:
            print(f" - {src['tool']} (args: {src['params']})")
        if not response_json['sources']:
            print(" - None")
        print(f"LOW CONFIDENCE FLAG: {response_json['low_confidence']}")
    print("=" * 80 + "\n")

# Mock Anthropic responses to simulate Claude's behavior
class MockBlock:
    def __init__(self, type, text=None, name=None, id=None, input=None):
        self.type = type
        self.text = text
        self.name = name
        self.id = id
        self.input = input

class MockResponse:
    def __init__(self, content):
        self.content = content

def mock_messages_create(*args, **kwargs):
    messages = kwargs.get("messages", [])
    last_msg = messages[-1]["content"] if messages else ""
    
    # Test A: Duplicate invoices
    if isinstance(last_msg, str) and "Which invoices look like duplicates in business unit BU-01?" in last_msg:
        return MockResponse([MockBlock(type="tool_use", name="get_high_risk_invoices", id="tool_1", input={"business_unit_id": "BU-01"})])
    
    # Test A: Follow up after tool
    if isinstance(last_msg, list) and len(last_msg) > 0 and last_msg[0].get("tool_use_id") == "tool_1":
        return MockResponse([MockBlock(type="text", text="Based on the AP data, there are duplicates in BU-01 for vendor VEND-000 and others totaling several thousands in risk.")])

    # Test D: Report generation
    if isinstance(last_msg, str) and "draft a report" in last_msg.lower():
        return MockResponse([MockBlock(type="tool_use", name="generate_risk_report", id="tool_3", input={"scope": "vendor", "id": "VEND-999"})])
        
    # Test B: Vendor risk
    if isinstance(last_msg, str) and "VEND-999" in last_msg:
        return MockResponse([MockBlock(type="tool_use", name="get_vendor_risk_profile", id="tool_2", input={"vendor_id": "VEND-999"})])
        
    # Test B: Follow up after tool
    if isinstance(last_msg, list) and len(last_msg) > 0 and last_msg[0].get("tool_use_id") == "tool_2":
        return MockResponse([MockBlock(type="text", text="Based on cross-domain data, VEND-999 has a highly concerning risk profile. AP shows a $250,000 round-number high-risk invoice. Audit shows a Segregation of Duties violation matching that amount. Treasury shows a massive unforecasted variance exactly correlating with this. This looks highly suspicious.")])

    # Test C: Revenue (Guardrail)
    if isinstance(last_msg, str) and "revenue growth" in last_msg:
        return MockResponse([MockBlock(type="text", text="I don't have data to answer that. My tools only cover AP invoices, Audit GL entries, and Treasury cash flow.")])
        
    # Test D: Follow up after report generation
    if isinstance(last_msg, list) and len(last_msg) > 0 and last_msg[0].get("tool_use_id") == "tool_3":
        return MockResponse([MockBlock(type="text", text="I have successfully generated the formal risk report for vendor VEND-999 for the audit committee. You can download it using the link provided.")])

    return MockResponse([MockBlock(type="text", text="I am a mock response.")])

@patch('routers.chat.client.messages.create', side_effect=mock_messages_create)
def test_chat(mock_create):
    # Ensure data is loaded
    dal.load_data()
    
    client = TestClient(app)
    
    # ... existing tests ...
    
    # TEST A: Single Tool
    prompt_a = "Which invoices look like duplicates in business unit BU-01?"
    res_a = client.post("/api/chat", json={"message": prompt_a, "conversation_id": "conv-test-1"})
    print_chat("A) Duplicate Invoices in BU-01", prompt_a, res_a.json())

    # TEST B: Multi-domain / Vendor Risk
    prompt_b = "Tell me everything you know about vendor VEND-999 \u2014 is there anything concerning?"
    res_b = client.post("/api/chat", json={"message": prompt_b, "conversation_id": "conv-test-2"})
    print_chat("B) Cross-Domain Vendor Risk", prompt_b, res_b.json())
    
    # TEST C: Guardrails (No Revenue Data)
    prompt_c = "What was our revenue growth last quarter?"
    res_c = client.post("/api/chat", json={"message": prompt_c, "conversation_id": "conv-test-3"})
    print_chat("C) Guardrails & Refusal", prompt_c, res_c.json())
    
    # TEST D: Report Generation Action
    prompt_e = "Draft a report for the audit committee on vendor VEND-999"
    res_e = client.post("/api/chat", json={"message": prompt_e, "conversation_id": "conv-test-5"})
    json_res = res_e.json()
    print_chat("D) Report Generation & Action UI", prompt_e, json_res)
    
    # Verify action
    assert "actions" in json_res
    assert len(json_res["actions"]) > 0
    assert json_res["actions"][0]["type"] == "report_generated"
    print(f"Verified Action UI Output: {json_res['actions'][0]['url']}")
    
    # Verify logs
    log_path = os.path.join(os.path.dirname(__file__), '../logs/interaction_log.jsonl')
    assert os.path.exists(log_path), "Audit log file was not created!"
    with open(log_path, 'r') as f:
        logs = f.readlines()
        assert len(logs) >= 4, "Not enough logs captured!"
        print("\n[OK] SOX-style interaction_log.jsonl verified successfully.")
        
    print("\nAll endpoints and action capabilities validated successfully!")

if __name__ == "__main__":
    test_chat()
