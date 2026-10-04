from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse
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

@app.exception_handler(RateLimitExceeded)
async def rate_limit_exceeded_handler(request, exc):
    return JSONResponse(status_code=429, content={"detail": "Rate limit exceeded"})

# CORS configuration: production trusts only explicitly configured origins.
development_origins = [
    "http://localhost:5173",
    "http://localhost:5174",
    "http://localhost:5175",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:5174",
    "http://127.0.0.1:5175",
    "http://localhost:3000",
]
configured_origins = [origin.strip() for origin in settings.ALLOWED_ORIGINS.split(",") if origin.strip()]
allowed_origins = configured_origins
if settings.ENVIRONMENT.lower() != "production":
    allowed_origins = [*development_origins, *configured_origins]
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
