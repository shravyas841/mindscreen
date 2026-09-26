# 🧠 MindScreen: AI-Powered Multimodal Mental Health Screening Platform

> **RVITM Major Project (BCS685)**  
> *An intelligent, multimodal mental health assessment web platform combining clinical questionnaires, transformer-based NLP, and acoustic voice analysis for early depression detection and risk triaging.*

---

## 📌 Executive Summary

**MindScreen** is a mental-health screening-support prototype designed for preliminary screening and wellness tracking. Its **multimodal late-fusion decision architecture** integrates three independent input streams:

1. 📋 **PHQ-9 Clinical Questionnaire** (Standardized medical assessment baseline)
2. 🧠 **Hosted Emotion Classification** (DistilRoBERTa affect labels mapped heuristically to screening tiers)
3. 🎙️ **Browser Acoustic Descriptors** (RMS, ZCR, spectral centroid/rolloff, and speaking ratio)

---

## ✨ Key Features

- **Multimodal Risk Prediction Engine**: Fuses questionnaire, affective-text, and heuristic acoustic scores to generate a triaged screening tier (`Minimal`, `Mild`, `Moderate`, `High Priority`).
- **Lexical Indicators**: Displays hand-written keyword contributions used by the fallback/display layer. These are not SHAP values or causal model explanations.
- **Safety First & Crisis Overrides**: Instant detection of high-risk indicators or self-harm signals (PHQ-9 Q9) automatically triggers emergency helpline banners (iCall, NIMHANS).
- **Daily Mood Tracker & CBT Exercises**: Interactive daily mood logging with trend visualization (`Recharts`) and dynamic Cognitive Behavioral Therapy (CBT) activity recommendations based on user emotional state.
- **Assessment History & Longitudinal Tracking**: Complete historical logs allowing users to view risk progression over time with detailed probability distribution breakdowns.
- **Modern Glassmorphism UI**: High-impact, responsive dark-mode user interface designed with fluid micro-animations for a comforting user experience.
- **Academic Demo Mode**: The current build uses a shared demo-user bypass. JWTs are issued by login/register routes but are not enforced by protected routes; this build must not be described as secure or multi-user private.

---

## 🏗️ System Architecture & Multimodal Fusion

MindScreen uses a **Late Fusion (Decision-Level Fusion)** approach. When audio is skipped or fewer than five analysis frames are available, the client sends no acoustic vector and the backend applies the documented prior `[0.25, 0.45, 0.20, 0.10]` at the existing 30% weight. This missing-modality policy is heuristic and has not been statistically validated. A recording exists temporarily as an in-memory browser Blob for local playback, but the assessment payload transmits only the descriptor vector and does not persist raw audio.

```
                      ┌────────────────────────────────────────┐
                      │            User Inputs                 │
                      └───────────────────┬────────────────────┘
                                          │
        ┌─────────────────────────────────┼─────────────────────────────────┐
        │                                 │                                 │
        ▼                                 ▼                                 ▼
┌──────────────┐                 ┌─────────────────┐               ┌────────────────┐
│   PHQ-9      │                 │  Journal Text   │               │ Voice Recording│
│ Questionnaire│                 │  (Free-form)    │               │ Browser stream │
└───────┬──────┘                 └────────┬────────┘               └───────┬────────┘
        │                                 │                                 │
        ▼                                 ▼                                 ▼
┌──────────────┐                 ┌─────────────────┐               ┌────────────────┐
│ Rule-Based   │                 │ Emotion Model   │               │ Web Audio API  │
│ Scoring      │                 │ + Rule Fallback │               │ Descriptors    │
└───────┬──────┘                 └────────┬────────┘               └───────┬────────┘
        │ (20% Weight)                    │ (50% Weight)                    │ (30% Weight)
        └────────────────────────┐        │        ┌────────────────────────┘
                                 ▼        ▼        ▼
                      ┌────────────────────────────────────────┐
                      │    Decision-Level Late Fusion Engine   │
                      │  Weighted Average + Crisis Safety Check │
                      └───────────────────┬────────────────────┘
                                          │
                                          ▼
                      ┌────────────────────────────────────────┐
                      │ Tier, Priority Score, Flags & Scores  │
                      └────────────────────────────────────────┘
```

### Fusion Weight Distribution
$$ \text{Final Score} = (0.50 \times \text{Text}) + (0.30 \times \text{Audio}) + (0.20 \times \text{PHQ-9}) $$

> **High-Risk Escalation:** A PHQ-9 total $\ge 20$, Item 9 $>0$, or affirmative self-directed crisis language forces the internal high-priority tier and a priority score of at least 0.90. The crisis flag is set only by Item 9 or affirmative crisis language; a high total alone is not labeled acute crisis.
>
> The API retains the legacy `risk_level: "severe"` value for this internal c3 tier; the interface displays **High Priority**. It is not a diagnosis.

---

## 🛠️ Technology Stack

### **Frontend**
- **Framework**: [React 19](https://react.dev/) + [TypeScript](https://www.typescriptlang.org/)
- **Build Tool**: [Vite 8](https://vitejs.dev/)
- **Styling**: [Tailwind CSS v4](https://tailwindcss.com/) (Vanilla CSS Variables, Dark Glassmorphism)
- **Animations**: [Framer Motion](https://www.framer.com/motion/)
- **Data Visualization**: [Recharts](https://recharts.org/)
- **Icons**: [Lucide React](https://lucide.dev/)
- **State & Data Fetching**: `@tanstack/react-query`, `axios`

### **Backend**
- **Framework**: [FastAPI](https://fastapi.tiangolo.com/) (Python 3.11)
- **ASGI Server**: Uvicorn
- **Database**: PostgreSQL (with automatic SQLite fallback for rapid local execution)
- **ORM**: SQLAlchemy + Alembic Migrations
- **Authentication status**: Password hashing and JWT creation exist, but protected routes currently use a shared demo-user bypass.
- **Rate Limiting**: `slowapi`

### **Machine Learning & Signal Processing**
- **NLP Transformer**: Hosted `j-hartmann/emotion-english-distilroberta-base`, mapped from emotion labels to screening tiers
- **Audio Processing**: Browser Web Audio API descriptors scored by a hand-designed server-side heuristic
- **Dataset status**: No repository evidence establishes training or validation on DAIC-WOZ acoustic data
- **Interpretability status**: Displayed lexical values are deterministic keyword indicators, not SHAP

---

## 📂 Project Structure

```
major project antigravity/
├── backend/
│   ├── main.py                  # FastAPI Application Entry & Routing
│   ├── config.py                # Environment Configuration & Settings
│   ├── database.py              # SQLAlchemy Database Setup & SQLite Fallback
│   ├── models/                  # Database Schemas (User, Assessment, Mood)
│   ├── routers/                 # API Endpoints (auth, predict, phq, mood, health)
│   ├── services/
│   │   ├── ml_service.py        # Hosted emotion inference, fallback, lexical indicators
│   │   ├── audio_service.py     # Heuristic scoring of browser acoustic descriptors
│   │   ├── fusion_service.py    # Multimodal Decision-Level Late Fusion Logic
│   │   ├── phq_service.py       # Clinical PHQ-9 Rule-based Scoring Engine
│   │   └── auth_service.py      # JWT Authentication & Demo-mode Security
│   └── ml_models/               # PyTorch Model Checkpoints (.pt)
│
├── frontend/
│   ├── src/
│   │   ├── App.tsx              # Main Router & Application Provider
│   │   ├── main.tsx             # Entry point
│   │   ├── index.css            # Dark Glassmorphism CSS Design Tokens
│   │   ├── components/          # Reusable UI (Sidebar, Layout, Buttons, Cards)
│   │   ├── pages/               # Pages (Landing, Register, Login, Dashboard, 
│   │   │                        #        Assessment, Results, History, MoodTracker)
│   │   └── api/                 # Axios Client & API Contracts
│   ├── package.json
│   └── vite.config.ts
│
├── docker-compose.yml           # Containerized Database & Deployment Setup
└── README.md
```

---

## 🚀 Getting Started

### Prerequisites

Ensure you have the following installed:
- [Node.js](https://nodejs.org/) (v18 or higher)
- [Python](https://www.python.org/) (v3.11 recommended)

---

### 1. Backend Setup

```bash
# Navigate to backend directory
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows (PowerShell):
.\venv\Scripts\Activate.ps1
# Mac/Linux:
# source venv/bin/activate

# Install dependencies
pip install -r backend/requirements.txt

# Run the FastAPI server
python main.py
```
> The API will start running at `http://localhost:8000`. API documentation is available at `http://localhost:8000/docs`.

---

### 2. Frontend Setup

```bash
# Navigate to frontend directory
cd frontend

# Install Node dependencies
npm install

# Start Vite development server
npm run dev
```
> The application will start running at `http://localhost:5173`.

---

## ⚡ API Endpoint Reference

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/health` | API Health Check |
| `POST` | `/api/auth/register` | User Account Registration |
| `POST` | `/api/auth/login` | User Login & JWT Retrieval |
| `POST` | `/api/predict/text` | Text emotion/fallback screening analysis |
| `POST` | `/api/predict/fused` | Multimodal Prediction (PHQ-9 + Text + Audio) |
| `GET` | `/api/phq/history` | Historical Assessment Records |
| `POST` | `/api/mood/log` | Daily Mood Log Entry |

---

## ⚠️ Medical Disclaimer

> **MindScreen is an academic research application created for demonstration purposes.**  
> It is **not** a certified diagnostic tool and does **not** replace professional medical advice, diagnosis, or treatment. If you or someone you know is in distress or experiencing a mental health crisis, please contact emergency services or reach out to a professional mental health provider immediately:
> - **iCall (India)**: +91 9152987821
> - **NIMHANS Helpline**: 080-46110007
> - **Vandrevala Foundation**: 1860-2662-345

---

## 📜 License & Acknowledgments

Developed as part of the **RVITM Major Project (BCS685)**.  
Uses the hosted Hugging Face `j-hartmann/emotion-english-distilroberta-base` model as an affective proxy. The repository contains DAIC-WOZ label/download experiments, but the production audio path is not trained or validated on DAIC-WOZ.

## Verification

```bash
pip install -r backend/requirements-dev.txt
pytest
python backend/run_submission_evidence.py
cd frontend
npm test
npm run build
```

The evidence script writes `benchmarks/submission_evidence.json`. It includes current implementation facts, deterministic HRE cases, a constructed crisis-language corpus, and a descriptive five-configuration weight-sensitivity analysis over constructed modality-score cases. The sensitivity analysis reports raw fusion separately from HRE and is not an accuracy study or weight optimization. Timing values are in-process local function microbenchmarks, not HTTP, database, browser extraction, hosted-API, network, cloud, or frontend-rendering measurements.
