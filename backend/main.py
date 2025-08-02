"""
FastAPI Risk Monitor API
Main application file
"""

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Optional
import uvicorn

from database import get_db, init_database
from database.schemas import UserRiskSummary, UserRiskAnalysis, SystemStats
from risk_calculator import RiskCalculator

# Initialize FastAPI app
app = FastAPI(
    title="Risk Monitor API",
    description="API for monitoring at-risk subscribers",
    version="1.0.0"
)

# Add CORS middleware for Streamlit
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8501", "http://127.0.0.1:8501"],  # Streamlit default ports
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize risk calculator
risk_calculator = RiskCalculator()

# Startup event to initialize database
@app.on_event("startup")
async def startup_event():
    """Initialize database on startup and populate if empty"""
    try:
        init_database()
        print("✅ Database initialized successfully")
        
        # Check if database is empty and populate if needed
        from database.models import User
        from database.database import SessionLocal
        
        db = SessionLocal()
        try:
            user_count = db.query(User).count()
            
            if user_count == 0:
                print("📊 Database is empty, populating with test data...")
                db.close()  # Close before populate_database creates its own session
                from populate_db import populate_database
                populate_database()
                print("🎉 Database populated with test data!")
            else:
                print(f"📈 Database has {user_count} users already")
        finally:
            db.close()
            
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")


@app.get("/")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "message": "Risk Monitor API is running",
        "version": "1.0.0"
    }


@app.get("/api/risky-users", response_model=List[UserRiskSummary])
async def get_risky_users(
    min_risk_score: Optional[float] = 0.4,  # Default: 40% as per brief
    limit: Optional[int] = 100,
    db: Session = Depends(get_db)
):
    """
    Get list of users with high risk scores
    
    Args:
        min_risk_score: Minimum risk score threshold (default: 0.4 = 40%)
        limit: Maximum number of users to return
        db: Database session
    
    Returns:
        List of risky users with summary information
    """
    try:
        risky_users = risk_calculator.get_risky_users(
            db=db, 
            min_risk_score=min_risk_score, 
            limit=limit
        )
        return risky_users
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching risky users: {str(e)}")


@app.get("/api/user/{user_id}/risk-analysis", response_model=UserRiskAnalysis)
async def get_user_risk_analysis(
    user_id: int,
    db: Session = Depends(get_db)
):
    """
    Get detailed risk analysis for a specific user
    
    Args:
        user_id: User ID to analyze
        db: Database session
    
    Returns:
        Detailed risk analysis with factors and recommendations
    """
    try:
        analysis = risk_calculator.analyze_user_risk(user_id, db)
        if not analysis:
            raise HTTPException(status_code=404, detail=f"User {user_id} not found")
        return analysis
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing user {user_id}: {str(e)}")


@app.get("/api/stats", response_model=SystemStats)
async def get_system_stats(db: Session = Depends(get_db)):
    """
    Get global system statistics
    
    Args:
        db: Database session
    
    Returns:
        System-wide risk statistics
    """
    try:
        stats = risk_calculator.get_risk_statistics(db)
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching statistics: {str(e)}")


@app.post("/api/alert/{user_id}")
async def send_risk_alert(
    user_id: int,
    db: Session = Depends(get_db)
):
    """
    Send risk alert for a specific user (placeholder for Slack integration)
    
    Args:
        user_id: User ID to send alert for
        db: Database session
    
    Returns:
        Alert status
    """
    try:
        # Get user risk analysis
        analysis = risk_calculator.analyze_user_risk(user_id, db)
        if not analysis:
            raise HTTPException(status_code=404, detail=f"User {user_id} not found")
        
        # TODO: Integrate with Slack notifier
        # For now, just return success
        return {
            "status": "success",
            "message": f"Alert sent for user {user_id}",
            "risk_level": analysis.risk_level,
            "risk_score": analysis.risk_score
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error sending alert for user {user_id}: {str(e)}")


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
