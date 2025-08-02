"""
Reset database - Drop all tables and recreate them
For use when schema changes
"""

from database.database import engine, Base
from database.models import User, Subscription, Payment

def reset_database():
    """Drop all tables and recreate them"""
    print("🗑️ Dropping all tables...")
    Base.metadata.drop_all(bind=engine)
    
    print("🚀 Creating new tables...")
    Base.metadata.create_all(bind=engine)
    
    print("✅ Database reset complete!")

if __name__ == "__main__":
    reset_database()