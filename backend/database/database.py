"""
Database configuration and session management
"""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

load_dotenv()

# Database URL from environment variable
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:password@localhost:5432/risk_monitor")

# Create SQLAlchemy engine
engine = create_engine(DATABASE_URL)

# Create SessionLocal class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create Base class for models
Base = declarative_base()


def get_db():
    """
    Dependency function to get database session
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_tables():
    """
    Create all tables in the database
    """
    from .models import User, Subscription, Payment  # Import here to avoid circular imports
    Base.metadata.create_all(bind=engine)

def reset_database():
    """Drop all tables and recreate them"""
    print("🗑️ Dropping all tables...")
    Base.metadata.drop_all(bind=engine)
    
    print("🚀 Creating new tables...")
    Base.metadata.create_all(bind=engine)
    
    print("✅ Database reset complete!")

def init_database():
    """
    Initialize the database by creating all tables
    """
    create_tables()


def get_engine():
    """
    Get the SQLAlchemy engine
    """
    return engine