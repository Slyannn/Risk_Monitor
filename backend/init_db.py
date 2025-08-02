"""
Simple database initialization for MVP
"""

from database import init_database

if __name__ == "__main__":
    print("🚀 Creating database tables...")
    try:
        init_database()
        print("🎉 Database ready!")
    except Exception as e:
        print(f"❌ Error: {e}")
        print("💡 Make sure PostgreSQL is running and database 'risk_monitor' exists")