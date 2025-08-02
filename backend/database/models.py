"""
SQLAlchemy models for Risk Monitor application
Minimal models with only essential fields for risk calculation
"""

from datetime import datetime
from sqlalchemy import Column, Integer, Boolean, String, DateTime, ForeignKey, Float, Text
from sqlalchemy.orm import relationship
from .database import Base


class User(Base):
    """
    User model for subscription holders
    """
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    # Relationships
    subscriptions = relationship("Subscription", back_populates="user")
    payments = relationship("Payment", back_populates="user")


class Subscription(Base):
    """
    Subscription model for subscription holders
    Supports subscription changes over time (basic → premium → pro)
    """
    __tablename__ = "user_subscriptions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    subscription_type = Column(String, nullable=False)  # basic, premium, pro, enterprise
    status = Column(String, nullable=False)  # active, cancelled, suspended
    monthly_amount = Column(Float, nullable=False)  # amount paid per month
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # New fields for subscription evolution
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    effective_from = Column(DateTime, default=datetime.utcnow, nullable=False)  # When this subscription version started
    effective_until = Column(DateTime, nullable=False)  # When this subscription version ended/will end

    # Relationships
    user = relationship("User", back_populates="subscriptions")
    payments = relationship("Payment", back_populates="subscription")
    
    @property
    def is_current(self):
        """Check if this is the current active subscription"""
        now = datetime.utcnow()
        return self.effective_until > now and self.status == "active"
    
    @property
    def is_expired(self):
        """Check if this subscription has expired"""
        return datetime.utcnow() > self.effective_until


class Payment(Base):
    """
    Payment model for subscription holders
    """
    __tablename__ = "subscription_payments"

    id = Column(Integer, primary_key=True, index=True)
    subscription_id = Column(Integer, ForeignKey("user_subscriptions.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)  # Direct relation for performance
    amount = Column(Float, nullable=False) # amount paid
    currency = Column(String, default="EUR", nullable=False) # currency of the payment
    status = Column(String, nullable=False, index=True)  # success, failed, declined
    payment_date = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    payment_method = Column(String, nullable=False) # card, paypal, bank_transfer
    
    failure_reason = Column(Text, nullable=True)  # Only for failed payments

    # Relationships
    subscription = relationship("Subscription", back_populates="payments")
    user = relationship("User", back_populates="payments")
    
    @property
    def is_failed(self):
        """Helper property to identify failed payments"""
        return self.status in ['failed', 'declined']
    
    @property
    def is_successful(self):
        """Helper property to identify successful payments"""
        return self.status == 'success'


