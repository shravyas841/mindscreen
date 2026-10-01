from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from config import settings
from database import engine, Base
from middleware.rate_limit import limiter
from routers import auth, predict, phq, mood, health, chat

# Create tables in the database
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="MindScreen API",
    description="Mental Health Screening Platform — RVITM BCS685",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

@app.get("/", include_in_schema=False)
def root():
    return RedirectResponse(url="/docs")

# Rate Limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS configuration — include all local dev ports + production Vercel URL
allowed_origins = [
    "http://localhost:5173",
    "http://localhost:5174",
    "http://localhost:5175",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:5174",
    "http://127.0.0.1:5175",
    "http://localhost:3000",
    "https://mindscreen.vercel.app",
    *[origin.strip() for origin in settings.ALLOWED_ORIGINS.split(",") if origin.strip()],
]
# Deduplicate
allowed_origins = list(dict.fromkeys(allowed_origins))

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(health.router)
app.include_router(auth.router)
app.include_router(predict.router)
app.include_router(phq.router)
app.include_router(mood.router)
app.include_router(chat.router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
