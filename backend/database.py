from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from config import settings

connect_args = {}
if settings.DATABASE_URL.startswith("sqlite"):
    connect_args["check_same_thread"] = False

try:
    engine = create_engine(
        settings.DATABASE_URL,
        pool_size=10,
        max_overflow=20,
        pool_pre_ping=True,
        echo=settings.DEBUG,
    )
    with engine.connect() as conn:
        pass
except Exception as e:
    print(f"Primary DB connection failed ({e}). Falling back to local SQLite database.")
    engine = create_engine(
        "sqlite:///./mental_health.db",
        connect_args={"check_same_thread": False},
        echo=settings.DEBUG,
    )

# Session factory — create one session per request
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class all models inherit from
Base = declarative_base()

# ── DEPENDENCY INJECTION ──────────────────────────────────────────────
# FastAPI calls this for every route that needs DB
def get_db():
    db = SessionLocal()
    try:
        yield db          # Give the session to the route handler
    finally:
        db.close()        # ALWAYS close — prevents connection leaks
