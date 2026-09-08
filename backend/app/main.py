import os
import sys
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware

# Ensure root is in sys.path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from backend.app.api.routes import router as api_router
from backend.app.core.config import settings
from backend.app.db.session import engine, Base

# Create tables on startup
Base.metadata.create_all(bind=engine)

# Auto-seed if database is freshly created or empty (ensures 100% demo readiness on Render / cloud)
try:
    from backend.app.db.session import SessionLocal
    from backend.app.models.entities import Project
    from scripts.seed_demo import run_seed
    with SessionLocal() as _db:
        if _db.query(Project).count() == 0:
            print("INFO: Database is empty. Running initial demo seed...")
            run_seed(_db)
            print("INFO: Initial demo seed completed successfully.")
except Exception as e:
    print(f"INFO: Auto-seed check completed or skipped: {e}")


app = FastAPI(
    title="PRAGATI AI",
    description="AI-Powered Planning-to-Execution Intelligence Layer (SIH26122 - Oil India Limited)",
    version="1.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Router
app.include_router(api_router, prefix=settings.API_V1_STR)

# System Health Check
@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "PRAGATI AI Backend",
        "version": "1.0.0",
        "ai_provider": settings.AI_PROVIDER,
        "database": "sqlite/postgresql",
        "mode": "demo_ready"
    }

# Static Files & UI Serving
STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
os.makedirs(STATIC_DIR, exist_ok=True)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

@app.get("/")
def serve_ui():
    index_path = os.path.join(STATIC_DIR, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return JSONResponse({"message": "PRAGATI AI API is running. Visit /docs for Swagger UI or /api/dashboard/summary."})
