"""
Generate realistic test data for Risk Monitor
Creates users with different risk profiles matching the brief requirements
"""

from datetime import datetime, timedelta
from faker import Faker
import random

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import SessionLocal, init_database
from database.models import User, Subscription, Payment

fake = Faker()

def clear_existing_data(db):
    """Clear existing test data"""
    print("🧹 Clearing existing data...")
    db.query(Payment).delete()
    db.query(Subscription).delete() 
    db.query(User).delete()
    db.commit()

def create_risky_user_pattern_1(db, base_date):
    """
    Pattern 1: Classic risky user from brief
    "Paient une fois, puis déclinent les paiements suivants"
    """
    user = User(
        name=fake.name(),
        email=fake.email(),
        created_at=base_date - timedelta(days=random.randint(30, 120))
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    
    # Premium subscription (higher amount = more risk)
    subscription = Subscription(
        user_id=user.id,
        subscription_type="premium",
        status="active",
        monthly_amount=79.99,
        created_at=user.created_at
    )
    db.add(subscription)
    db.commit()
    
    # Payment pattern: SUCCESS, then multiple FAILURES
    payments_data = [
        ("success", 0, None),
        ("failed", 30, "Insufficient funds"),
        ("declined", 60, "Card declined"),
        ("failed", 90, "Payment failed"),
    ]
    
    for status, days_ago, reason in payments_data:
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
    
    print(f"✅ Created risky user (Pattern 1): {user.name} - {user.email}")
    return user

def create_risky_user_pattern_2(db, base_date):
    """
    Pattern 2: >40% failures on last 3 payments
    """
    user = User(
        name=fake.name(),
        email=fake.email(),
        created_at=base_date - timedelta(days=random.randint(60, 200))
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    
    subscription = Subscription(
        user_id=user.id,
        subscription_type="basic",
        status="active", 
        monthly_amount=19.99,
        created_at=user.created_at
    )
    db.add(subscription)
    db.commit()
    
    # Last 3 payments: 2 failures = 66.7% > 40%
    payments_data = [
        ("failed", 0, "Card expired"),      # Most recent
        ("failed", 30, "Insufficient funds"), # Second
        ("success", 60, None),              # Third
        ("success", 90, None),              # Older (good history)
        ("success", 120, None),
        ("success", 150, None),
    ]
    
    for status, days_ago, reason in payments_data:
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
    
    print(f"✅ Created risky user (Pattern 2): {user.name} - {user.email}")
    return user

def create_healthy_user(db, base_date):
    """
    Create a healthy user with good payment history
    """
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
        subscription_type=random.choice(["basic", "premium", "pro"]),
        status="active",
        monthly_amount=random.choice([19.99, 49.99, 99.99]),
        created_at=user.created_at
    )
    db.add(subscription)
    db.commit()
    
    # Mostly successful payments (90%+ success rate)
    num_payments = random.randint(8, 15)
    for i in range(num_payments):
        # 90% success rate
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
    
    print(f"✅ Created healthy user: {user.name} - {user.email}")
    return user

def create_new_risky_user(db, base_date):
    """
    Create a new user (high risk due to account age)
    """
    user = User(
        name=fake.name(),
        email=fake.email(),
        created_at=base_date - timedelta(days=random.randint(1, 20))  # Very new
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    
    subscription = Subscription(
        user_id=user.id,
        subscription_type="pro",
        status="active",
        monthly_amount=149.99,  # High amount + new account = high risk
        created_at=user.created_at
    )
    db.add(subscription)
    db.commit()
    
    # Few payments, some failures
    payments_data = [
        ("failed", 0, "Card declined"),
        ("success", 15, None),
    ]
    
    for status, days_ago, reason in payments_data:
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
    
    print(f"✅ Created new risky user: {user.name} - {user.email}")
    return user

def generate_test_data():
    """Generate comprehensive test data"""
    print("🚀 Generating test data for Risk Monitor...")
    
    # Initialize database
    init_database()
    db = SessionLocal()
    
    try:
        # Clear existing data
        clear_existing_data(db)
        
        base_date = datetime.utcnow()
        
        # Create different user profiles
        print("\n📊 Creating risky users (Pattern 1 - classic brief pattern)...")
        for i in range(3):
            create_risky_user_pattern_1(db, base_date)
        
        print("\n📊 Creating risky users (Pattern 2 - >40% recent failures)...")
        for i in range(3):
            create_risky_user_pattern_2(db, base_date)
        
        print("\n📊 Creating new risky users (account age factor)...")
        for i in range(2):
            create_new_risky_user(db, base_date)
        
        print("\n📊 Creating healthy users...")
        for i in range(10):
            create_healthy_user(db, base_date)
        
        db.commit()
        print(f"\n🎉 Successfully created test data!")
        print(f"   • Total users: {db.query(User).count()}")
        print(f"   • Total subscriptions: {db.query(Subscription).count()}")
        print(f"   • Total payments: {db.query(Payment).count()}")
        
    except Exception as e:
        print(f"❌ Error generating test data: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    generate_test_data()