"""
Simple database test for MVP
"""

from database import SessionLocal
from database.models import User

if __name__ == "__main__":
    print("🧪 Testing database...")
    
    db = SessionLocal()
    try:
        # Create test user
        user = User(name="Test User", email="test@example.com")
        db.add(user)
        db.commit()
        
        # Read user back
        found = db.query(User).filter(User.email == "test@example.com").first()
        print(f"✅ Created and found user: {found.name}")
        
        # Clean up
        db.delete(found)
        db.commit()
        print("✅ Database works!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        db.rollback()
    finally:
        db.close()