# FinSage

FinSage is an Agentic GenAI Copilot tailored for enterprise finance operations. It provides a robust, LLM-powered layer that connects directly to Accounts Payable (AP), Audit (GL), and Treasury Cashflow data.

## SOX-Style Audit Logging & LLM Governance

A crucial differentiator for FinSage in a regulated finance context is its comprehensive audit trail. Every interaction with the copilot is securely appended to `backend/logs/interaction_log.jsonl`. 

Why this matters for LLM Governance:
1. **Traceability**: In a Sarbanes-Oxley (SOX) regulated environment, if an AI is providing insights that influence financial reporting or risk management, the organization must be able to prove *exactly* what data the AI accessed.
2. **Reproducibility**: The interaction log captures the user's prompt, the specific tool calls and parameters (the exact queries made to the underlying systems), and the final synthesized response.
3. **Guardrails**: The log captures a `low_confidence` flag if the model attempts to answer a financial data question without grounding itself in a tool execution, enabling compliance officers to monitor hallucination attempts or out-of-scope usage via an admin dashboard.

## Project Structure
- `/backend`: FastAPI service exposing the Data Intelligence endpoints, the Claude Agentic Chat router, and the PDF generation service.
- `/frontend`: Vite + React + Tailwind frontend providing the UI for the copilot.
- `/data`: Synthetic CSV datasets acting as the enterprise data warehouse.
- `/docs`: Architecture details and Data Dictionary.
