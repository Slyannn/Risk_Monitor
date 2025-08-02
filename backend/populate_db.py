"""
Populate database with permanent test data for API testing
Creates realistic random user profiles for different risk scenarios
"""

from datetime import datetime, timedelta
from faker import Faker
import random

from database import SessionLocal, init_database
from database.models import User, Subscription, Payment

fake = Faker()

def create_risky_pattern_1(db, base_date):
    """Classic risky pattern: pay once then decline"""
    user = User(
        name=fake.name(),
        email=fake.email(),
        created_at=base_date - timedelta(days=random.randint(30, 120))
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    
    subscription = Subscription(
        user_id=user.id,
        subscription_type=random.choice(["basic", "premium"]),
        status="active",
        monthly_amount=random.choice([4.99, 6.99, 8.99]),
        created_at=user.created_at,
        effective_from=user.created_at,
        effective_until=base_date + timedelta(days=random.randint(30, 90))
    )
    db.add(subscription)
    db.commit()
    
    # Pattern: 1 success, then failures
    payment_pattern = [
        ("success", 0, None),
        ("failed", 30, random.choice(["Insufficient funds", "Card declined", "Payment failed"])),
        ("declined", 60, random.choice(["Card expired", "Bank declined"])),
        ("failed", 90, "Payment timeout"),
    ]
    
    for status, days_ago, reason in payment_pattern:
        payment = Payment(
            subscription_id=subscription.id,
            user_id=user.id,
            amount=subscription.monthly_amount,
            currency="EUR",
            payment_method=random.choice(["card", "paypal"]),
            status=status,
            payment_date=base_date - timedelta(days=days_ago),
            failure_reason=reason
        )
        db.add(payment)
    
    return user

def create_downgrade_pattern(db, base_date):
    """Downgrade pattern: premium to basic (departure signal)"""
    user = User(
        name=fake.name(),
        email=fake.email(),
        created_at=base_date - timedelta(days=random.randint(150, 300))
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    
    # Old premium subscription
    old_amount = random.choice([8.99, 12.99, 15.99])
    subscription_old = Subscription(
        user_id=user.id,
        subscription_type="premium",
        status="cancelled",
        monthly_amount=old_amount,
        created_at=user.created_at,
        effective_from=user.created_at,
        effective_until=base_date - timedelta(days=60)
    )
    db.add(subscription_old)
    db.commit()
    
    # Current basic subscription (downgrade)
    new_amount = random.choice([1.99, 2.99, 3.99])
    subscription_new = Subscription(
        user_id=user.id,
        subscription_type="basic",
        status="active",
        monthly_amount=new_amount,
        created_at=base_date - timedelta(days=60),
        effective_from=base_date - timedelta(days=60),
        effective_until=base_date + timedelta(days=random.randint(30, 90))
    )
    db.add(subscription_new)
    db.commit()
    
    # Payment history showing downgrade
    downgrade_payments = [
        ("success", 0, None, subscription_new.id, new_amount),
        ("success", 30, None, subscription_new.id, new_amount),
        ("success", 60, None, subscription_new.id, new_amount),
        ("success", 90, None, subscription_old.id, old_amount),
        ("success", 120, None, subscription_old.id, old_amount),
    ]
    
    for status, days_ago, reason, sub_id, amount in downgrade_payments:
        payment = Payment(
            subscription_id=sub_id,
            user_id=user.id,
            amount=amount,
            currency="EUR",
            payment_method=random.choice(["card", "paypal", "bank_transfer"]),
            status=status,
            payment_date=base_date - timedelta(days=days_ago),
            failure_reason=reason
        )
        db.add(payment)
    
    return user

def create_healthy_user(db, base_date):
    """Create a healthy user with good payment history"""
    user = User(
        name=fake.name(),
        email=fake.email(),
        created_at=base_date - timedelta(days=random.randint(200, 500))
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    
    subscription = Subscription(
        user_id=user.id,
        subscription_type=random.choice(["premium", "pro"]),
        status="active",
        monthly_amount=random.choice([9.99, 12.99, 15.99]),
        created_at=user.created_at,
        effective_from=user.created_at,
        effective_until=base_date + timedelta(days=random.randint(90, 180))
    )
    db.add(subscription)
    db.commit()
    
    # Healthy payment pattern (90%+ success)
    num_payments = random.randint(8, 15)
    for i in range(num_payments):
        status = "success" if random.random() < 0.9 else random.choice(["failed", "declined"])
        reason = fake.sentence() if status != "success" else None
        
        payment = Payment(
            subscription_id=subscription.id,
            user_id=user.id,
            amount=subscription.monthly_amount,
            currency="EUR",
            payment_method=random.choice(["card", "paypal", "bank_transfer"]),
            status=status,
            payment_date=base_date - timedelta(days=i * 30),
            failure_reason=reason
        )
        db.add(payment)
    
    return user

def create_recent_failures_user(db, base_date):
    """Create user with recent failures (>40% on last 3)"""
    user = User(
        name=fake.name(),
        email=fake.email(),
        created_at=base_date - timedelta(days=random.randint(60, 150))
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    
    subscription = Subscription(
        user_id=user.id,
        subscription_type="basic",
        status="active",
        monthly_amount=random.choice([1.99, 2.99]),
        created_at=user.created_at,
        effective_from=user.created_at,
        effective_until=base_date + timedelta(days=random.randint(30, 60))
    )
    db.add(subscription)
    db.commit()
    
    # Recent failures pattern (>40%)
    recent_pattern = [
        ("failed", 0, random.choice(["Insufficient funds", "Card declined"])),
        ("failed", 30, "Card expired"),
        ("success", 60, None),
        ("success", 90, None),
        ("success", 120, None),
    ]
    
    for status, days_ago, reason in recent_pattern:
        payment = Payment(
            subscription_id=subscription.id,
            user_id=user.id,
            amount=subscription.monthly_amount,
            currency="EUR",
            payment_method="card",
            status=status,
            payment_date=base_date - timedelta(days=days_ago),
            failure_reason=reason
        )
        db.add(payment)
    
    return user

def populate_database():
    """Create permanent test data for API"""
    print("🚀 Populating database with realistic test data...")
    
    # Initialize database
    init_database()
    db = SessionLocal()
    
    try:
        # Clear existing test data
        db.query(Payment).delete()
        db.query(Subscription).delete()
        db.query(User).delete()
        db.commit()
        
        base_date = datetime.utcnow()
        created_users = []
        
        print("📊 Creating risky users (Pattern 1 - classic brief pattern)...")
        for i in range(3):
            user = create_risky_pattern_1(db, base_date)
            created_users.append(user)
        
        print("📊 Creating risky users (Pattern 2 - downgrade signal)...")
        for i in range(3):
            user = create_downgrade_pattern(db, base_date)
            created_users.append(user)
        
        print("📊 Creating users with recent failures...")
        for i in range(2):
            user = create_recent_failures_user(db, base_date)
            created_users.append(user)
        
        print("📊 Creating healthy users...")
        for i in range(10):
            user = create_healthy_user(db, base_date)
            created_users.append(user)
        
        db.commit()
        
        print(f"✅ Database populated successfully!")
        print(f"   • Users: {db.query(User).count()}")
        print(f"   • Subscriptions: {db.query(Subscription).count()}")
        print(f"   • Payments: {db.query(Payment).count()}")
        
    except Exception as e:
        print(f"❌ Error populating database: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    populate_database()