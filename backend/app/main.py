from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

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

# Register v1 routes
app.include_router(api_v1_router)

@app.get("/", tags=["Health"])
def root():
    return {
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "online",
        "documentation": "/docs",
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
