from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database import engine, Base
from routes import products, bargains, offers, payments, audit

# Phase 4: import Resolution model BEFORE create_all so the table is registered
import ai.outcome_tracker  # noqa: F401 — registers Resolution with Base.metadata

# Create all tables on startup (existing + Resolution added in Phase 4)
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="BargainAI2 API",
    description="AI-powered merchant bargaining system — backend API",
    version="0.1.0",
)

# CORS — allow Next.js frontend during local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", tags=["Health"])
def health_check():
    return {"status": "ok", "message": "BargainAI2 backend is running"}


# Register routers — existing BargainAI routes
app.include_router(products.router)
app.include_router(bargains.router)
app.include_router(offers.router)
app.include_router(payments.router)
app.include_router(audit.router)

# Phase 2 — ML Discovery
from routes.ai_discoveries import router as ai_discoveries_router
app.include_router(ai_discoveries_router)

# Phase 3 — AI Investigation
from routes.ai_investigations import router as ai_investigations_router
app.include_router(ai_investigations_router)

# Phase 4 — Autonomous Resolution + Feedback Loop
from routes.ai_resolutions import router as ai_resolutions_router
app.include_router(ai_resolutions_router)
