import os
import json
import asyncio
from anthropic import AsyncAnthropic

from agents.ap_agent import run_ap_specialist
from agents.audit_agent import run_audit_specialist
from agents.treasury_agent import run_treasury_specialist
from routers.reports import generate_risk_report_action

client = AsyncAnthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

ORCHESTRATOR_TOOLS = [
    {
        "name": "generate_risk_report",
        "description": "Generates a structured PDF report for a vendor or business unit, returning a download URL.",
        "input_schema": {
            "type": "object",
            "properties": {
                "scope": {"type": "string", "description": "'vendor' or 'business_unit'"},
                "id": {"type": "string", "description": "The vendor_id or business_unit_id"}
            },
            "required": ["scope", "id"]
        }
    }
]

async def classify_intent(message: str) -> list:
    prompt = f"""
    You are the Orchestrator for FinSage. 
    Analyze the user's message and determine which specialist agents are required to answer it.
    Options: 'AP', 'Audit', 'Treasury'.
    Output a JSON array of the required agents. 
    If the question is out of scope for finance (e.g., revenue, HR, general chat), output an empty array [].
    If the user asks about a vendor across all domains, or asks a compound question, output all three.
    User Message: "{message}"
    Output strictly JSON, e.g. ["AP", "Treasury"]. No other text.
    """
    try:
        response = await client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=50,
            messages=[{"role": "user", "content": prompt}]
        )
        content = response.content[0].text.strip()
        # Clean markdown if present
        if content.startswith('```'):
            content = content.split('\n')[1:-1]
            content = '\n'.join(content)
        return json.loads(content)
    except Exception as e:
        print(f"Classification failed: {e}")
        return []

async def process_chat_request(message: str, conversation_history: list):
    required_agents = await classify_intent(message)
    
    if not required_agents:
        return {
            "answer": "I don't have data to answer that. My scope is restricted to AP, Audit, and Treasury domains.",
            "sources": [],
            "low_confidence": True,
            "actions": [],
            "specialists_used": []
        }
        
    tasks = []
    if "AP" in required_agents:
        tasks.append(run_ap_specialist(message, conversation_history))
    if "Audit" in required_agents:
        tasks.append(run_audit_specialist(message, conversation_history))
    if "Treasury" in required_agents:
        tasks.append(run_treasury_specialist(message, conversation_history))
        
    results = await asyncio.gather(*tasks)
    
    specialists_used = [r['agent_name'] for r in results]
    all_tools_called = []
    for r in results:
        all_tools_called.extend(r['tools_called'])
        
    low_confidence = any(r['low_confidence'] for r in results)
    
    needs_synthesis = len(results) > 1 or "report" in message.lower()
    actions = []
    
    if not needs_synthesis:
        final_answer = results[0]['answer_text']
    else:
        # Synthesize
        combined_context = "Here are the findings from the specialists:\n"
        for r in results:
            combined_context += f"\n--- {r['agent_name']} ---\n{r['answer_text']}\n"
            
        sys_prompt = """You are the Orchestrator for FinSage.
        Synthesize the following reports from your specialist agents into a single, coherent, executive-ready response.
        If multiple specialists flagged risks for the same entity, explicitly note this as a 'Compound Risk' in your summary.
        If the user asked to generate a formal risk report, use the generate_risk_report tool and mention that the report is ready.
        """
        
        synth_messages = conversation_history.copy()
        synth_messages.append({"role": "user", "content": f"User Question: {message}\n\n{combined_context}"})
        
        response = await client.messages.create(
            model="claude-3-5-sonnet-20240620",
            max_tokens=1000,
            system=sys_prompt,
            messages=synth_messages,
            tools=ORCHESTRATOR_TOOLS
        )
        
        tool_calls = [b for b in response.content if b.type == "tool_use"]
        final_answer = "".join(b.text for b in response.content if b.type == "text")
        
        # Add a note if synthesis omitted text but generated a tool call
        if not final_answer and tool_calls:
            final_answer = "I have generated the requested report."

        for tc in tool_calls:
            if tc.name == "generate_risk_report":
                url = await generate_risk_report_action(**tc.input)
                actions.append({"type": "report_generated", "url": url})
                all_tools_called.append({"tool": tc.name, "params": tc.input})
                
        specialists_used.append("Orchestrator Synthesizer")

    return {
        "answer": final_answer,
        "sources": all_tools_called,
        "low_confidence": low_confidence,
        "actions": actions,
        "specialists_used": specialists_used
    }
