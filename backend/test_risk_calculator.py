"""
Test the risk calculator with sample data
"""

from datetime import datetime, timedelta
from database import SessionLocal
from database.models import User, Subscription, Payment
from risk_calculator import RiskCalculator


def create_test_data(db):
    """Create test users matching the exact patterns from the brief"""
    
    # Test User 1: "Paid once, then declined subsequent payments"
    user1 = User(name="Classic Risky User", email="classic@test.com")
    db.add(user1)
    db.commit()
    db.refresh(user1)
    
    subscription1 = Subscription(
        user_id=user1.id,
        subscription_type="premium",
        status="active",
        monthly_amount=6.99  # Netflix Premium family share
    )
    db.add(subscription1)
    db.commit()
    
    # Pattern: 1 success, then 3 failures
    payment_pattern = [
        ("success", 0, None),                    # First payment: SUCCESS
        ("failed", 30, "Insufficient funds"),   # Then decline
        ("declined", 60, "Card declined"),      # Then decline
        ("failed", 90, "Payment failed"),       # Then decline
    ]
    
    for status, days_ago, reason in payment_pattern:
        payment = Payment(
            subscription_id=subscription1.id,
            user_id=user1.id,
            amount=6.99,
            currency="EUR",
            payment_method="card",
            status=status,
            payment_date=datetime.utcnow() - timedelta(days=days_ago),
            failure_reason=reason
        )
        db.add(payment)
    
    # Test User 2: Low Risk (mostly successful)
    user2 = User(name="Low Risk User", email="low@test.com", created_at=datetime.utcnow() - timedelta(days=365))
    db.add(user2)
    db.commit()
    db.refresh(user2)
    
    subscription2 = Subscription(
        user_id=user2.id,
        subscription_type="basic",
        status="active",
        monthly_amount=3.99  # Spotify family share
    )
    db.add(subscription2)
    db.commit()
    
    # Create payments with low failure rate
    for i in range(12):
        status = "failed" if i == 2 else "success"  # Only 1 failure out of 12
        payment = Payment(
            subscription_id=subscription2.id,
            user_id=user2.id,
            amount=3.99,
            currency="EUR",
            payment_method="card",
            status=status,
            payment_date=datetime.utcnow() - timedelta(days=i*30),
            failure_reason="Card expired" if status == "failed" else None
        )
        db.add(payment)
    
    # Test User 3: HIGH RISK - >40% failures on last 3 payments 
    user3 = User(name="40% Failure User", email="40percent@test.com")
    db.add(user3)
    db.commit()
    db.refresh(user3)
    
    subscription3 = Subscription(
        user_id=user3.id,
        subscription_type="basic",
        status="active",
        monthly_amount=1.99
    )
    db.add(subscription3)
    db.commit()
    
    # Last 3 payments: 2 failures out of 3 = 66.7% failure rate (>40% threshold)
    recent_payment_pattern = [
        ("failed", 0, "Insufficient funds"),    # Most recent: FAILED
        ("failed", 30, "Card expired"),         # Second: FAILED  
        ("success", 60, None),                  # Third: SUCCESS
        ("success", 90, None),                  # Older payments were good
        ("success", 120, None),
    ]
    
    for status, days_ago, reason in recent_payment_pattern:
        payment = Payment(
            subscription_id=subscription3.id,
            user_id=user3.id,
            amount=1.99,
            currency="EUR",
            payment_method="card",
            status=status,
            payment_date=datetime.utcnow() - timedelta(days=days_ago),
            failure_reason=reason
        )
        db.add(payment)
    
    # Test User 4: DOWNGRADE Pattern (upgrade puis downgrade - signal de départ)
    user4 = User(
        name="Downgrading User", 
        email="downgrade@test.com",
        created_at=datetime.utcnow() - timedelta(days=150)
    )
    db.add(user4)
    db.commit()
    db.refresh(user4)
    
    # Phase 1: Premium bundle (was engaged)
    subscription4_premium = Subscription(
        user_id=user4.id,
        subscription_type="premium",
        status="cancelled",
        monthly_amount=8.99,  # Netflix + Spotify bundle
        created_at=datetime.utcnow() - timedelta(days=150),
        effective_from=datetime.utcnow() - timedelta(days=150),
        effective_until=datetime.utcnow() - timedelta(days=60)
    )
    db.add(subscription4_premium)
    db.commit()
    
    # Phase 2: Downgrade vers basic (Departure signal)
    subscription4_basic = Subscription(
        user_id=user4.id,
        subscription_type="basic",
        status="active",
        monthly_amount=2.99,  # Netflix Basic seulement
        created_at=datetime.utcnow() - timedelta(days=60),
        effective_from=datetime.utcnow() - timedelta(days=60),
        effective_until=datetime.utcnow() + timedelta(days=30)
    )
    db.add(subscription4_basic)
    db.commit()
    
    # Payment history - DOWNGRADE PATTERN (very risky)
    downgrade_payments = [
        # Phase 2: Basic (current) - DOWNGRADE = HIGH RISK
        ("success", 0, None, subscription4_basic.id, 1.20),                    # Basic actuel: OK mais bas coût
        ("success", 30, None, subscription4_basic.id, 1.99),                   # Basic: OK mais downgrade detected
        ("success", 60, None, subscription4_basic.id, 2.99),                   # Début downgrade
        
        # Phase 1: Premium (former) - Was well engaged
        ("success", 90, None, subscription4_premium.id, 8.99),                 # Premium précédent: était OK
        ("success", 120, None, subscription4_premium.id, 8.99),                # Premium: était engagé
        ("success", 150, None, subscription4_premium.id, 8.99),                # Premium: payait bien
    ]
    
    for status, days_ago, reason, sub_id, amount in downgrade_payments:
        payment = Payment(
            subscription_id=sub_id,
            user_id=user4.id,
            amount=amount,
            currency="EUR",
            payment_method="card",
            status=status,
            payment_date=datetime.utcnow() - timedelta(days=days_ago),
            failure_reason=reason
        )
        db.add(payment)

    db.commit()
    return [user1, user2, user3, user4]


def test_risk_calculator():
    """Test the risk calculator functionality"""
    
    print("🧪 Testing Risk Calculator...")
    
    db = SessionLocal()
    calculator = RiskCalculator()
    
    try:
        # Create test data
        print("📝 Creating test data...")
        test_users = create_test_data(db)
        
        # Test individual risk scores
        print("\n📊 Individual Risk Scores:")
        for user in test_users:
            risk_score = calculator.calculate_user_risk_score(user.id, db)
            risk_level = calculator.get_risk_level(risk_score)
            risk_factors = calculator.get_risk_factors(user.id, db)
            recommendations = calculator.get_recommendations(risk_level)
            
            print(f"\n👤 {user.name}:")
            print(f"   Risk Score: {risk_score:.1%}")
            print(f"   Risk Level: {risk_level.upper()}")
            print(f"   Risk Factors: {', '.join(risk_factors)}")
            print(f"   Recommendations: {', '.join(recommendations[:3])}")
            
            # Special analysis for subscription evolution users
            if user.name in ["Evolving User", "Downgrading User"]:
                print(f"   📊 Subscription Evolution:")
                subscriptions = db.query(Subscription).filter(Subscription.user_id == user.id).order_by(Subscription.effective_from).all()
                for sub in subscriptions:
                    status_icon = "📉" if sub.is_current else "📈"
                    end_date = sub.effective_until.strftime('%Y-%m-%d') if sub.effective_until else 'current'
                    print(f"      {status_icon} {sub.subscription_type}: {sub.monthly_amount}€ ({sub.effective_from.strftime('%Y-%m-%d')} - {end_date})")
                
                if user.name == "Downgrading User":
                    print(f"   ⚠️ DOWNGRADE PATTERN: User reduced from premium to basic - Departure signal!")
                    print(f"      Recommendation: Contact urgently, investigate satisfaction")
                elif risk_score > 0.5:
                    print(f"   💡 Pattern: Upgraded to expensive bundle but can't pay!")
                    print(f"      Recommendation: Contact immediately, offer downgrade")
        
        # Test risky users query
        print("\n🚨 High Risk Users (>40%):")
        risky_users = calculator.get_risky_users(db, min_risk_score=0.4)
        
        for user_risk in risky_users:
            print(f"   {user_risk.name}: {user_risk.risk_score:.1%} "
                  f"(failures: {user_risk.failed_payments}/{user_risk.total_payments})")
        
        # Test system statistics
        print("\n📈 System Statistics:")
        stats = calculator.get_system_stats(db)
        print(f"   Total Users: {stats['total_users']}")
        print(f"   High Risk Users: {stats['high_risk_users']}")
        print(f"   Overall Failure Rate: {stats['overall_failure_rate']:.1%}")
        print(f"   Risk Percentage: {stats['risk_percentage']:.1f}%")
        
        print("\n✅ Risk Calculator test completed successfully!")
        
        # Clean up test data
        for user in test_users:
            db.query(Payment).filter(Payment.user_id == user.id).delete()
            db.query(Subscription).filter(Subscription.user_id == user.id).delete()
            db.delete(user)
        db.commit()
        print("🧹 Test data cleaned up")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    test_risk_calculator()