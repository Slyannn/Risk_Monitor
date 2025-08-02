"""
Pydantic schemas for Risk Monitor API
"""

from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from typing import List, Optional
from enum import Enum


# Subscription types
class SubscriptionType(str, Enum):
    basic = "basic"
    premium = "premium"
    pro = "pro"

# Subscription status
class SubscriptionStatus(str, Enum):
    active = "active"
    cancelled = "cancelled"
    suspended = "suspended"


class PaymentStatus(str, Enum):
    success = "success"
    failed = "failed"
    declined = "declined"


# User schemas 
class UserBase(BaseModel):
    name: str
    email: EmailStr


class UserCreate(UserBase):
    pass


class User(UserBase):
    id: int
    created_at: datetime
    is_active: bool

    class Config:
        from_attributes = True


# Subscription schemas
class SubscriptionBase(BaseModel):
    subscription_type: SubscriptionType
    monthly_amount: float = Field(..., gt=0)
    status: SubscriptionStatus = SubscriptionStatus.active


class SubscriptionCreate(SubscriptionBase):
    user_id: int
    effective_from: datetime
    effective_until: datetime


class Subscription(SubscriptionBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime
    effective_from: datetime
    effective_until: datetime

    class Config:
        from_attributes = True


# Payment schemas 
class PaymentBase(BaseModel):
    amount: float = Field(..., gt=0)
    currency: str = "EUR"
    payment_method: str


class PaymentCreate(PaymentBase):
    subscription_id: int
    user_id: int
    status: PaymentStatus = PaymentStatus.success


class Payment(PaymentBase):
    id: int
    subscription_id: int
    user_id: int
    status: PaymentStatus
    payment_date: datetime
    failure_reason: Optional[str] = None

    class Config:
        from_attributes = True


# Risk analysis schemas 
class UserRiskSummary(BaseModel):
    """User risk summary for dashboard"""
    id: int
    name: str
    email: str
    risk_score: float = Field(..., ge=0, le=1)
    failure_rate: float = Field(..., ge=0, le=1)
    total_payments: int
    failed_payments: int
    subscription_type: SubscriptionType
    monthly_amount: float
    created_at: datetime

    class Config:
        from_attributes = True


class UserRiskAnalysis(BaseModel):
    """Detailed risk analysis"""
    user_id: int
    user_name: str
    user_email: str
    risk_score: float = Field(..., ge=0, le=1)
    risk_level: str  # low, medium, high, critical
    failure_rate: float
    total_payments: int
    failed_payments: int
    successful_payments: int
    subscriptions_history: List[Subscription]
    payment_history: List[Payment]
    risk_factors: List[str]
    recommendations: List[str]

    class Config:
        from_attributes = True


# System statistics 
class SystemStats(BaseModel):
    """Global system statistics"""
    total_users: int
    high_risk_users: int
    total_payments: int
    failed_payments: int
    overall_failure_rate: float
    avg_risk_score: float

    class Config:
        from_attributes = True