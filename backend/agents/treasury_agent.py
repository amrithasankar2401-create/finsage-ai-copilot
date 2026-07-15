import os
import json
from anthropic import AsyncAnthropic
from routers.treasury import get_treasury_variance, get_forecast_summary

client = AsyncAnthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

TREASURY_SYSTEM_PROMPT = """You are FinSage's Treasury & Liquidity Specialist.
You ONLY handle questions about cash flow, closing balance forecasts, and treasury variance.
If asked something outside your scope (like AP invoices, audit GL, or general non-finance questions), politely refuse and state you do not have data for that.
ALWAYS use the provided tools to fetch data before answering. Do not guess financial numbers.
Be concise.
"""

TREASURY_TOOLS = [
    {
        "name": "get_treasury_variance",
        "description": "Get weeks where the actual vs forecast treasury closing balance variance exceeds a threshold.",
        "input_schema": {
            "type": "object",
            "properties": {
                "entity_id": {"type": "string"},
                "min_variance_pct": {"type": "number", "description": "Minimum variance percentage. Defaults to 15.0"}
            }
        }
    },
    {
        "name": "get_treasury_forecast_summary",
        "description": "Get a rolling summary of average weekly closing balance trend and current liquidity position.",
        "input_schema": {
            "type": "object",
            "properties": {
                "entity_id": {"type": "string"}
            }
        }
    }
]

async def execute_treasury_tool(tool_name: str, args: dict):
    if tool_name == "get_treasury_variance":
        if 'min_variance_pct' not in args:
            args['min_variance_pct'] = 15.0
        return await get_treasury_variance(**args)
    elif tool_name == "get_treasury_forecast_summary":
        return await get_forecast_summary(**args)
    raise ValueError(f"Unknown tool: {tool_name}")

async def run_treasury_specialist(user_question: str, conversation_context: list):
    messages = conversation_context.copy()
    messages.append({"role": "user", "content": user_question})
    
    tools_called = []
    
    while True:
        response = await client.messages.create(
            model="claude-3-5-sonnet-20240620",
            max_tokens=1000,
            system=TREASURY_SYSTEM_PROMPT,
            messages=messages,
            tools=TREASURY_TOOLS
        )
        
        messages.append({"role": "assistant", "content": response.content})
        
        tool_calls = [block for block in response.content if block.type == "tool_use"]
        
        if not tool_calls:
            break
            
        tool_results_blocks = []
        for tc in tool_calls:
            tools_called.append({"tool": tc.name, "params": tc.input})
            try:
                result = await execute_treasury_tool(tc.name, tc.input)
                result_str = json.dumps(result)
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
    if not tools_called and any(kw in user_question.lower() for kw in ['treasury', 'cash', 'variance', 'forecast', 'liquidity']):
        low_confidence = True
        
    return {
        "agent_name": "Treasury Specialist",
        "answer_text": final_text,
        "tools_called": tools_called,
        "low_confidence": low_confidence,
        "actions": []
    }
