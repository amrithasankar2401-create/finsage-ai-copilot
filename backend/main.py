from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import asyncio
from contextlib import asynccontextmanager
from data_access import dal
from routers.invoices import router as invoices_router
from routers.audit import router as audit_router
from routers.treasury import router as treasury_router
from routers.cross_domain import router as cross_domain_router
from routers.chat import router as chat_router
from routers.reports import router as reports_router
from routers.admin import router as admin_router
from routers.briefings import router as briefings_router
from routers.actions import router as actions_router
from monitoring.scanner import background_scanner_loop

app = FastAPI(title="FinSage API", description="Agentic GenAI Copilot for Finance Operations")

# Configure CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(invoices_router)
app.include_router(audit_router)
app.include_router(treasury_router)
app.include_router(cross_domain_router)
app.include_router(chat_router)
app.include_router(reports_router)
app.include_router(admin_router)
app.include_router(briefings_router)
app.include_router(actions_router)

@app.on_event("startup")
async def startup_event():
    # Load data once on startup
    dal.load_data()
    # Start the proactive monitoring background scanner
    asyncio.create_task(background_scanner_loop())

@app.get("/health")
async def health_check():
    return {
        "status": "ok",
        "datasets_loaded": {
            "vendors": len(dal.vendors_df),
            "invoices": len(dal.invoices_df),
            "gl_entries": len(dal.gl_entries_df),
            "treasury_weeks": len(dal.treasury_df)
        }
    }

