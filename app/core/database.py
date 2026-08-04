from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from supabase import create_client, Client
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

# SQLAlchemy Engine dengan connection pooling & pre-ping
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
    pool_recycle=300,
    pool_timeout=10
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class Base(DeclarativeBase):
    pass

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Inisialisasi Supabase Client via Service Role Key (Supabase Client SDK)
supabase_client: Client | None = None
if settings.SUPABASE_URL and settings.SUPABASE_SERVICE_ROLE_KEY:
    try:
        supabase_client = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_ROLE_KEY)
    except Exception as e:
        logger.warning(f"Gagal menginisialisasi Supabase Client SDK: {e}")

def get_supabase_client() -> Client | None:
    return supabase_client

