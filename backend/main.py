"""
DermaTwin Backend — FastAPI Application
AI-powered skin health intelligence system.
"""

import os
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

load_dotenv()

# Configure logging — show INFO level for our modules
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    datefmt="%H:%M:%S",
)
# Suppress noisy third-party loggers
logging.getLogger("httpcore").setLevel(logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("PIL").setLevel(logging.WARNING)

from routes.analyze import router as analyze_router
from routes.simulate import router as simulate_router
from routes.routine import router as routine_router
from routes.history import router as history_router

app = FastAPI(
    title="DermaTwin API",
    description="AI Skin Digital Twin + Predictive Skin Simulator",
    version="1.0.0",
)

# CORS — allow all for local development
cors_origins = os.getenv("CORS_ORIGINS", "*").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(analyze_router, prefix="/api")
app.include_router(simulate_router, prefix="/api")
app.include_router(routine_router, prefix="/api")
app.include_router(history_router, prefix="/api")


@app.on_event("startup")
async def warm_models():
    import logging

    logger = logging.getLogger("startup")
    logger.info("Warming up ML models...")

    from cv_modules.face_mesh import get_face_mesh_analyzer
    from cv_modules.lesion_detector import get_lesion_detector
    from cv_modules.hybrid_model import get_hybrid_model

    get_face_mesh_analyzer()
    get_lesion_detector()
    get_hybrid_model()

    logger.info("ML models ready.")


@app.get("/")
async def health_check():
    return {
        "status": "healthy",
        "service": "DermaTwin API",
        "version": "1.0.0",
    }


@app.get("/api/status")
async def api_status():
    """Check which ML models are available."""
    import torch

    gpu_available = torch.cuda.is_available()
    gpu_name = torch.cuda.get_device_name(0) if gpu_available else None

    acne_yolo_path = os.path.join(os.path.dirname(__file__), "models", "acne_yolov8.pt")
    has_acne_yolo = os.path.exists(acne_yolo_path)

    return {
        "gpu_available": gpu_available,
        "gpu_name": gpu_name,
        "acne_yolo_model": has_acne_yolo,
        "hf_model": "imfarzanansari/skintelligent-acne",
        "gemini_configured": bool(os.getenv("GEMINI_API_KEY")),
    }
