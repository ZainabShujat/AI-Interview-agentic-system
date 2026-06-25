import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

load_dotenv()

# Determine database URL - default to local SQLite if Supabase/PostgreSQL is not provided
DATABASE_URL = os.getenv("DATABASE_URL") or os.getenv("SUPABASE_DATABASE_URL")

if not DATABASE_URL:
    # Use SQLite for local development
    DATABASE_URL = "sqlite:///./careeriq.db"
    connect_args = {"check_same_thread": False}
    print("Database: Running with local SQLite fallback (careeriq.db)")
else:
    connect_args = {}
    # SQLAlchemy requires postgresql:// instead of postgres:// for newer drivers
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
    print("Database: Running with configured Supabase/PostgreSQL database")

engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
