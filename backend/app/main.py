from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.api.v1 import api_v1_router

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="DataPilot AI-Powered Analytical Engine - Backend Foundation",
)

# Enable CORS for local hackathon development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static directory for Frontend UI
STATIC_DIR = Path(__file__).resolve().parent / "static"
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# Register v1 routes
app.include_router(api_v1_router)

@app.get("/ui", include_in_schema=False)
def serve_ui():
    """Serves the DataPilot Questionless Discovery Web Interface."""
    index_file = STATIC_DIR / "index.html"
    if index_file.exists():
        return FileResponse(index_file)
    return {"message": "UI assets not found"}

@app.get("/", tags=["Health"])
def root(request: Request):
    accept = request.headers.get("accept", "")
    if "text/html" in accept:
        index_file = STATIC_DIR / "index.html"
        if index_file.exists():
            return FileResponse(index_file)

    return {
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "online",
        "documentation": "/docs",
        "ui": "/ui",
        "gemini_model": settings.GEMINI_MODEL,
        "gemini_key_configured": settings.has_gemini_key,
    }

@app.get("/health", tags=["Health"])
def health_check():
    return {
        "status": "healthy",
        "gemini_model": settings.GEMINI_MODEL,
        "gemini_key_configured": settings.has_gemini_key,
    }

