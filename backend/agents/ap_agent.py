import os
import json
from anthropic import AsyncAnthropic
from routers.invoices import get_high_risk_invoices

client = AsyncAnthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

AP_SYSTEM_PROMPT = """You are FinSage's AP Fraud & Invoice Specialist.
You ONLY handle questions about Accounts Payable, invoices, duplicate payments, and AP vendors.
If asked something outside your scope (like GL audit controls, treasury, or general non-finance questions), politely refuse and state you do not have data for that.
ALWAYS use the provided tools to fetch data before answering. Do not guess financial numbers.
If you identify a clear, specific risk (e.g., a high-risk invoice that should not be paid), you MUST proactively suggest a relevant action using the `propose_system_action` tool, rather than only describing the problem. Use action_type "hold_payment" for invoices.
Be concise.
"""

AP_TOOLS = [
    {
        "name": "get_high_risk_invoices",
        "description": "Get a list of high-risk invoices (likely duplicates or unusually large round amounts).",
        "input_schema": {
            "type": "object",
            "properties": {
                "business_unit_id": {"type": "string"},
                "min_amount": {"type": "number"}
            }
        }
    },
    {
        "name": "propose_system_action",
        "description": "Propose an action to remediate a risk, which will be sent to a human for approval.",
        "input_schema": {
            "type": "object",
            "properties": {
                "action_type": {"type": "string", "enum": ["hold_payment", "flag_for_review"]},
                "target_entity_id": {"type": "string", "description": "The specific ID of the invoice or vendor"},
                "target_type": {"type": "string", "enum": ["invoice", "vendor"]},
                "description": {"type": "string", "description": "A short reason for the action"}
            },
            "required": ["action_type", "target_entity_id", "target_type", "description"]
        }
    }
]

from actions.proposer import propose_action

async def execute_ap_tool(tool_name: str, args: dict):
    if tool_name == "get_high_risk_invoices":
        return await get_high_risk_invoices(**args)
    elif tool_name == "propose_system_action":
        proposal_id = propose_action(
            action_type=args['action_type'],
            target_entity_id=args['target_entity_id'],
            target_type=args['target_type'],
            description=args['description'],
            proposed_by="chat"
        )
        return {"status": "success", "proposal_id": proposal_id, "message": "Action proposed successfully"}
    raise ValueError(f"Unknown tool: {tool_name}")

async def run_ap_specialist(user_question: str, conversation_context: list):
    messages = conversation_context.copy()
    messages.append({"role": "user", "content": user_question})
    
    tools_called = []
    actions_to_return = []
    
    while True:
        response = await client.messages.create(
            model="claude-3-5-sonnet-20240620",
            max_tokens=1000,
            system=AP_SYSTEM_PROMPT,
            messages=messages,
            tools=AP_TOOLS
        )
        
        messages.append({"role": "assistant", "content": response.content})
        
        tool_calls = [block for block in response.content if block.type == "tool_use"]
        
        if not tool_calls:
            break
            
        tool_results_blocks = []
        for tc in tool_calls:
            tools_called.append({"tool": tc.name, "params": tc.input})
            try:
                result = await execute_ap_tool(tc.name, tc.input)
                result_str = json.dumps(result)
                
                if tc.name == "propose_system_action" and isinstance(result, dict) and "proposal_id" in result:
                    actions_to_return.append({
                        "type": "proposed_action",
                        "proposal_id": result["proposal_id"],
                        "action_type": tc.input["action_type"],
                        "target_entity_id": tc.input["target_entity_id"],
                        "target_type": tc.input["target_type"],
                        "description": tc.input["description"]
                    })
            except Exception as e:
                result_str = json.dumps({"error": str(e)})
                
            tool_results_blocks.append({
                "type": "tool_result",
                "tool_use_id": tc.id,
                "content": result_str
            })
            
        messages.append({
            "role": "user",
            "content": tool_results_blocks
        })
        
    final_text = "".join(b.text for b in response.content if b.type == "text")
    
    low_confidence = False
    if not tools_called and any(kw in user_question.lower() for kw in ['invoice', 'vendor', 'duplicate', 'ap']):
        low_confidence = True

    return {
        "agent_name": "AP Specialist",
        "answer_text": final_text,
        "tools_called": tools_called,
        "low_confidence": low_confidence,
        "actions": actions_to_return
    }
