# DermaTwin — AI Skin Digital Twin + Predictive Skin Simulator

AI-powered skin health intelligence web application that transforms a single face photograph
into a complete, personalized skin health report with annotated overlays, severity grading,
a predictive engine, treatment simulation, and an AI-generated skincare routine.

## Architecture

- **Backend**: Python / FastAPI — hybrid CV pipeline with YOLOv8 + HuggingFace Transformers
- **Frontend**: React 18 + TypeScript + Vite
- **AI Models**: `imfarzanansari/skintelligent-acne` (HuggingFace), MediaPipe Face Mesh, OpenCV
- **Routine Generation**: Google Gemini API (`gemini-2.0-flash`)

## Quick Start

### Prerequisites

- Python 3.10+
- Node.js 18+
- Git

### 1. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS/Linux

# Install dependencies
pip install -r requirements.txt

# Configure environment
copy .env.example .env
# Edit .env and add your GEMINI_API_KEY

# Start backend server
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

> **First run note**: The HuggingFace model (~300MB) downloads automatically on first API call.
> This takes 1-3 minutes depending on your connection.

### 2. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start dev server
npm run dev
```

The frontend runs at `http://localhost:5173` and the backend at `http://localhost:8000`.

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/analyze` | Upload face image + lifestyle data → full analysis |
| POST | `/api/simulate` | Skin profile + interventions → projected outcomes |
| POST | `/api/routine` | Skin profile → AI-generated skincare routine |
| GET | `/api/history/{uid}` | Retrieve past scan history |
| POST | `/api/history` | Save current scan to history |
| GET | `/api/interventions` | List available treatment interventions |
| GET | `/api/status` | Check system status and model availability |

## CV Pipeline

1. **Image Preprocessing** — EXIF correction, resize, normalize
2. **Face Mesh Detection** — MediaPipe 468 landmarks → 5 zone polygons
3. **Lesion Detection** — OpenCV (default) or YOLOv8 (if acne-specific weights available)
4. **Crop Lesion Regions** — Extract individual lesion patches
5. **Global Severity Classification** — HuggingFace Transformer model (primary)
6. **Hybrid Fusion** — Model prediction + spatial density guard rails
7. **Pigmentation Analysis** — OpenCV LAB color space + ITA melanin estimation
8. **Score Computation** — Weighted 0-100 composite (35% acne, 25% lesion, 20% pigment, 20% zone)
9. **Overlay Rendering** — Pillow server-side composition of all layers
10. **Prediction Engine** — 7-day and 30-day projections with lifestyle modifiers

## Optional: YOLOv8 Acne Model

Place acne-specific YOLOv8 weights at `backend/models/acne_yolov8.pt` for improved
detection. Without this, the system uses OpenCV-based detection which works reliably.

## Environment Variables

```env
# backend/.env
GEMINI_API_KEY=your_gemini_api_key_here
```

## Disclaimer

DermaTwin is an educational AI tool. It provides evidence-based projections, not medical
diagnoses. Always consult a qualified dermatologist for medical advice.
