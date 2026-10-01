# MindScreen

**A Late-Fusion Depression Screening Prototype with a Rule-Based Safety Override**

MindScreen is a web-based research prototype that combines the Patient Health Questionnaire-9 (PHQ-9), an off-the-shelf text emotion classifier, and browser-extracted acoustic descriptors through weighted late fusion to produce a preliminary depression risk tier. It is not a diagnostic tool and has not undergone clinical validation.

Developed by Savitha G, Ruchita Saraf, Shravya Sanikere, Chandrika Lamani, and Apoorva K at RV Institute of Technology and Management, Bengaluru (RVITM Major Project BCS685).

---

## Overview

The system takes three inputs from a user in a single assessment session:

1. Nine PHQ-9 items, each scored 0 to 3, producing a total of 0 to 27.
2. A free-text journal entry of any length, analysed by the Hartmann DistilRoBERTa emotion classifier mapped to a four-class depression risk distribution.
3. An optional voice recording of 10 to 30 seconds, from which six acoustic descriptors are extracted in the browser using the Web Audio API: RMS energy mean and standard deviation, zero-crossing rate mean, spectral centroid, 85-percent spectral rolloff, and speaking ratio.

The three probability vectors are combined through weighted late fusion (text 0.50, audio 0.30, PHQ-9 0.20), renormalised over the modalities actually present, and passed through monotone temperature scaling (T = 1.20). A rule-based safety layer then applies three overrides:

- R0: PHQ-9 tier floor. The fused tier may escalate but never falls below the severity band implied by the PHQ-9 total score.
- R1: PHQ-9 Item 9. Any score above zero on the self-harm item forces a severe classification and sets the crisis flag.
- R2: Crisis language. Affirmative, self-directed suicidal or self-harm language detected by the v2.1 clause-scoped filter forces the same escalation.

An evaluation of the crisis-language filter on two public corpora (SDCNL test split, n = 379; a tweet corpus, n = 8 785) found that the original fixed-window filter (v1) achieved sensitivity of 22.8 and 24.2 percent respectively. The clause-scoped revision (v2 and v2.1) raised sensitivity to 55.4 and 51.3 percent (McNemar p less than 10^-10), with specificity of 75.8 and 91.7 percent. The filter remains a supplementary trigger and not a safety guarantee.

A design-space analysis showed that, without overrides, the fused tier fell below the PHQ-9 severity band in 37.0, 55.3, and 85.2 percent of text-audio input configurations for PHQ-9 totals of 5-9, 10-14, and 15-19 respectively. The PHQ-9 tier floor removes this under-triage by construction.

---

## Repository Structure

```
mindscreen/
├── backend/
│   ├── main.py                    FastAPI application entry point
│   ├── config.py                  Environment settings, resolves .env from backend directory
│   ├── database.py                SQLAlchemy setup; falls back to SQLite if PostgreSQL is unavailable
│   ├── models/                    ORM models: User, Assessment, MoodLog
│   ├── schemas/                   Pydantic request and response schemas
│   ├── routers/
│   │   ├── auth.py                Registration, login, JWT refresh
│   │   ├── predict.py             /api/predict/text and /api/predict/fused endpoints
│   │   ├── phq.py                 PHQ-9 submission and history
│   │   ├── mood.py                Mood logging and trend
│   │   ├── chat.py                Saathi companion endpoint
│   │   └── health.py              /api/health
│   └── services/
│       ├── fusion_service.py      Weighted late fusion with R0/R1/R2 safety layer
│       ├── negation_service.py    Crisis-language filter v2.1 (clause-scoped, ConText-style)
│       ├── ml_service.py          HuggingFace emotion API call and keyword fallback
│       ├── audio_service.py       Six-descriptor acoustic scoring from Web Audio API features
│       ├── phq_service.py         PHQ-9 score-to-probability vector mapping
│       └── calibration_service.py Temperature scaling, ECE, and Brier score utilities
│
├── frontend/
│   └── src/
│       ├── App.tsx                Route definitions
│       ├── pages/
│       │   ├── Landing.tsx        Public landing page
│       │   ├── Login.tsx          Authentication
│       │   ├── Register.tsx       Account creation
│       │   ├── Dashboard.tsx      Post-login home
│       │   ├── Assessment.tsx     PHQ-9, journal, voice recording (AGC/noise suppression disabled)
│       │   ├── Results.tsx        Risk output with SHAP word attribution
│       │   ├── History.tsx        Past assessment timeline
│       │   ├── MoodTracker.tsx    Daily mood logging and trend chart
│       │   ├── SaathiChat.tsx     Saathi wellbeing companion
│       │   └── CounselorDashboard.tsx  Counselor view
│       ├── utils/
│       │   └── audioFeatures.ts   Web Audio API feature extractor; returns null for recordings under 5 frames
│       └── api/
│           └── client.ts          Axios instance with JWT auto-refresh interceptor
│
├── mindscreen_code_and_evaluation/
│   ├── evaluation/                Evaluation scripts reproducing all paper tables and figures
│   │   ├── crisis_v1.py           Verbatim copy of the deployed v1 filter
│   │   ├── crisis_v2.py           Evaluated clause-scoped revision
│   │   ├── crisis_v2_1.py         v2 plus self-harm triggers (the released version)
│   │   ├── eval_crisis.py         Table VI main rows, constructed suite, McNemar tests
│   │   ├── eval_posthoc.py        Ablation, v2.1, v1 miss breakdown, lexicon ceiling
│   │   ├── fusion_analysis.py     Tables IV and V, modality ablation, design-space scan
│   │   ├── latency.py             Table VII server-side compute latency
│   │   ├── suite.py               26-item constructed test suite
│   │   ├── results_crisis.json    Raw evaluation results: SDCNL and Twitter corpora
│   │   ├── results_fusion.json    Raw fusion and design-space results
│   │   ├── results_latency.json   Raw latency measurements
│   │   ├── results_posthoc.json   Post-hoc ablation results
│   │   ├── results_v1_miss_breakdown.json  v1 miss categories
│   │   └── FROZEN_SHA256.txt      SHA-256 hashes of v1, v2, and suite.py at evaluation time
│   └── patches/                   Drop-in replacements applied to the repository at revision
│
├── benchmarks/                    Earlier constructed suite and evidence audit files
├── docker-compose.yml             PostgreSQL + backend containerised setup
├── render.yaml                    Render deployment configuration
└── README.md
```

---

## Technology Stack

**Backend**

- Python 3.11, FastAPI 0.111, Uvicorn
- SQLAlchemy 2.0 with PostgreSQL (automatic SQLite fallback)
- Alembic for schema migrations
- JWT authentication via python-jose and passlib/bcrypt
- slowapi for per-route rate limiting

**Frontend**

- React 19, TypeScript, Vite 8
- Tailwind CSS v4 with dark glassmorphism design tokens
- Framer Motion for page and card animations
- Recharts for mood trend visualisation
- TanStack React Query and Axios for data fetching

**Machine Learning and Signal Processing**

- j-hartmann/emotion-english-distilroberta-base via HuggingFace Inference API (emotion-to-risk mapping)
- Keyword heuristic fallback when the API is unavailable
- Web Audio API (browser-side) for acoustic feature extraction; no server-side audio library required
- SHAP-style keyword attribution displayed on the results page

**Companion (Saathi)**

- Google Gemini 2.5 Flash via REST API (thinkingBudget: 0, maxOutputTokens: 800)
- Mistral-7B-Instruct-v0.2 via HuggingFace as secondary fallback
- Rule-based topic-matched responses as tertiary fallback

---

## API Reference

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | /api/health | None | Health check |
| POST | /api/auth/register | None | Create user account |
| POST | /api/auth/login | None | Obtain access and refresh tokens |
| POST | /api/auth/refresh | Refresh token | Rotate access token |
| POST | /api/predict/text | Bearer | Text-only risk prediction |
| POST | /api/predict/fused | Bearer | Full multimodal assessment |
| GET | /api/phq/history | Bearer | Past assessment records |
| POST | /api/mood/log | Bearer | Log daily mood entry |
| GET | /api/mood/trend | Bearer | Mood trend for charting |
| POST | /api/chat/companion | None | Saathi conversation turn |

The interactive API documentation is served at `/docs` when the backend is running.

---

## Local Setup

### Prerequisites

- Python 3.11
- Node.js 18 or later
- A HuggingFace account token (optional; keyword fallback is used when absent)
- A Google Gemini API key (optional; rule-based fallback is used when absent)

### Backend

```bash
cd backend
python -m venv venv

# Windows
.\venv\Scripts\Activate.ps1

# macOS / Linux
source venv/bin/activate

pip install -r requirements.txt

# Create backend/.env with at minimum:
# GEMINI_API_KEY=your_key_here
# HF_TOKEN=your_token_here
# SECRET_KEY=a_long_random_string

uvicorn main:app --reload --port 8000
```

The server starts at `http://localhost:8000`. Swagger UI is at `http://localhost:8000/docs`.

### Frontend

```bash
cd frontend
npm install
npm run dev
```

The development server starts at `http://localhost:5173`.

---

## Deployment

The live frontend is served from Vercel at `https://mindscreen.vercel.app`. The backend is hosted on Render at `https://mindscreen-rhe3.onrender.com`. The production API base URL is configured in `frontend/.env.production` and is not committed to this repository.

---

## Running the Evaluation

The `mindscreen_code_and_evaluation/evaluation/` directory reproduces all numbers in the accompanying paper. The SDCNL and Twitter corpora are not redistributed here and must be downloaded separately.

```bash
cd mindscreen_code_and_evaluation

# Download corpora (not included)
mkdir ../data
git clone --depth 1 https://github.com/ayaanzhaque/SDCNL.git ../data/SDCNL
git clone --depth 1 https://github.com/laxmimerit/twitter-suicidal-intention-dataset.git ../data/twitter

cd evaluation
pip install pandas numpy scipy scikit-learn

python eval_crisis.py        # Table VI, Figure 2, constructed suite
python eval_posthoc.py       # Ablation, v2.1, v1 miss breakdown, lexicon ceiling
python fusion_analysis.py    # Tables IV and V, modality ablation

# Verify frozen hashes
sha256sum -c FROZEN_SHA256.txt
```

---

## Limitations

- No component has been evaluated against clinician-administered depression diagnoses. No diagnostic accuracy figures are claimed.
- The emotion classifier and acoustic index were not validated against depression labels. Fusion weights are design choices, not learned from labeled data.
- Three of the six acoustic descriptors (ZCR, spectral centroid, spectral rolloff) lack direct literature support for depression screening.
- The crisis-language filter and emotion model are English-only. Hinglish and regional-language input are out of scope.
- Saathi's conversational responses have not undergone safety red-teaming.
- The SDCNL corpus uses subreddit membership as a proxy label. The Twitter corpus label provenance is undocumented.

---

## Helplines

If you or someone you know is in distress:

- Tele-MANAS (Government of India): 14416 or 1-800-891-4416 (free, 24/7)
- iCall (Tata Institute of Social Sciences): 9152987821 (Monday to Saturday, 8 am to 10 pm)
- NIMHANS Helpline: 080-46110007

---

## Disclaimer

MindScreen is a research prototype developed for academic purposes. It is not a certified diagnostic instrument and does not replace professional medical advice, diagnosis, or treatment. All example inputs and outputs in this repository were generated by the authors for testing purposes; no real user data is included.
