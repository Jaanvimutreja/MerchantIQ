from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database import engine, Base
from routes import products, bargains, offers, payments, audit

# Create all tables on startup
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


# Register routers
app.include_router(products.router)
app.include_router(bargains.router)
app.include_router(offers.router)
app.include_router(payments.router)
app.include_router(audit.router)
