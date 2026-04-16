"""
GET/POST /api/history — Scan history storage and retrieval.
Uses JSON file-based storage for simplicity.
"""

import os
import json
import uuid
import threading
from datetime import datetime
from fastapi import APIRouter
from schemas.models import HistorySaveRequest

router = APIRouter()

HISTORY_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "history")
os.makedirs(HISTORY_DIR, exist_ok=True)
_history_lock = threading.Lock()


@router.get("/history/{uid}")
async def get_history(uid: str):
    """Retrieve all past scans for a user."""
    user_file = os.path.join(HISTORY_DIR, f"{uid}.json")

    if not os.path.exists(user_file):
        return {"uid": uid, "scans": []}

    with open(user_file, "r") as f:
        data = json.load(f)

    return {"uid": uid, "scans": data}


@router.post("/history")
async def save_history(request: HistorySaveRequest):
    """Save current scan to history."""
    user_file = os.path.join(HISTORY_DIR, f"{request.uid}.json")

    with _history_lock:
        # Load existing history
        if os.path.exists(user_file):
            with open(user_file, "r") as f:
                data = json.load(f)
        else:
            data = []

        # Create scan entry
        scan_id = str(uuid.uuid4())[:8]
        entry = {
            "scan_id": scan_id,
            "timestamp": datetime.now().isoformat(),
            "skin_health_score": request.scan_data.get("skin_health_score", 0),
            "acne_severity": request.scan_data.get("acne_severity", "Unknown"),
            "lesion_count": request.scan_data.get("lesion_count", 0),
            "hyperpigmentation_pct": request.scan_data.get("hyperpigmentation_pct", 0),
            "score_breakdown": request.scan_data.get("score_breakdown", {}),
        }

        data.append(entry)

        # Save — keep last 50 scans
        data = data[-50:]
        with open(user_file, "w") as f:
            json.dump(data, f, indent=2)

    return {"status": "saved", "scan_id": scan_id}
