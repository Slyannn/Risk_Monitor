"""
Risk Score Calculator
Core business logic for identifying risky subscription users
"""

from datetime import datetime, timedelta
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func

from database.models import User, Subscription, Payment
from database.schemas import UserRiskSummary, UserRiskAnalysis, SystemStats


class RiskCalculator:
    """
    Calculates risk scores for subscription users
    """
    
    def __init__(self):
        # Risk thresholds
        self.HIGH_RISK_THRESHOLD = 0.4  # 40%
        self.CRITICAL_RISK_THRESHOLD = 0.7  # 70%
        
        # Recent period for analysis (3 months)
        self.RECENT_DAYS = 90

    def calculate_user_risk_score(self, user_id: int, db: Session) -> Optional[float]:
        """
        Calculate risk score for a specific user based on the brief:
        "Identifier les utilisateurs ayant plus de 40% d'échecs sur les 3 derniers paiements"
        
        Returns score between 0.0 and 1.0
        """
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return None
            
        # Get user's payments ordered by date (most recent first)
        payments = db.query(Payment).filter(Payment.user_id == user_id)\
                     .order_by(Payment.payment_date.desc()).all()
        
        if not payments:
            return 0.0
            
        # Focus on the 3 most recent payments (core requirement)
        recent_payments = payments[:3]
        
        if len(recent_payments) < 2:  # Need at least 2 payments to assess risk
            return 0.0
            
        # Calculate failure rate on recent payments (primary factor)
        recent_failures = sum(1 for p in recent_payments if p.is_failed)
        recent_failure_rate = recent_failures / len(recent_payments)
        
        # Base risk score = recent failure rate (primary indicator)
        base_risk = recent_failure_rate
        
        # Additional risk factors (lighter weight)
        overall_failure_rate = self._calculate_failure_rate(payments)
        age_factor = self._calculate_age_factor(user.created_at)
        amount_factor = self._calculate_amount_factor(payments)  # Includes downgrade detection
        
        # Pattern bonus: "paient une fois, puis déclinent les paiements suivants"
        pattern_bonus = self._calculate_pattern_bonus(payments)
        
        # Final weighted score
        risk_score = (
            base_risk * 0.5 +              # 50% - Recent failures (main criterion)
            amount_factor * 0.20 +         # 20% - Amount level + downgrade detection (important!)
            overall_failure_rate * 0.15 +  # 15% - Overall pattern
            age_factor * 0.05 +             # 5% - Account age
            pattern_bonus * 0.10            # 10% - Specific "pay once then decline" pattern
        )
        
        return min(risk_score, 1.0)

    def _calculate_failure_rate(self, payments: List[Payment]) -> float:
        """Calculate overall payment failure rate"""
        if not payments:
            return 0.0
            
        total_payments = len(payments)
        failed_payments = sum(1 for p in payments if p.is_failed)
        
        return failed_payments / total_payments

    def _calculate_recent_failure_rate(self, payments: List[Payment]) -> float:
        """Calculate failure rate for recent payments (last 3 months)"""
        recent_cutoff = datetime.utcnow() - timedelta(days=self.RECENT_DAYS) # 3 months ago(90 days)
        recent_payments = [p for p in payments if p.payment_date >= recent_cutoff]
        
        if not recent_payments:
            return 0.0
            
        total_recent = len(recent_payments)
        failed_recent = sum(1 for p in recent_payments if p.is_failed)
        
        return failed_recent / total_recent

    def _calculate_age_factor(self, created_at: datetime) -> float:
        """
        Calculate age factor - newer accounts are riskier
        Returns value between 0.0 and 1.0
        """
        account_age_days = (datetime.utcnow() - created_at).days
        
        if account_age_days < 30:      # Less than 1 month
            return 0.8
        elif account_age_days < 90:    # Less than 3 months  
            return 0.5
        elif account_age_days < 180:   # Less than 6 months
            return 0.3
        else:                          # 6+ months
            return 0.1

    def _calculate_amount_factor(self, payments: List[Payment]) -> float:
        """
        Calculate amount factor - low amounts = low risk potential
        Focus on recent payments (subscription evolution aware)
        Returns value between 0.0 and 1.0
        """
        if not payments:
            return 0.0
        
        # Sort payments by date (most recent first)
        sorted_payments = sorted(payments, key=lambda x: x.payment_date, reverse=True)
        
        # Focus on recent payment amounts (last 3 payments for current subscription level)
        recent_payments = sorted_payments[:3]
        if len(recent_payments) == 0:
            return 0.0
            
        # Use the most recent payment amount (current subscription level)
        current_amount = recent_payments[0].amount
        
        # Check for subscription changes (downgrades are much more risky than upgrades)
        change_bonus = 0.0
        if len(sorted_payments) >= 3:
            old_amounts = [p.amount for p in sorted_payments[2:5]]  # 3-5 payments ago
            if old_amounts:
                avg_old_amount = sum(old_amounts) / len(old_amounts)
                
                # DOWNGRADE: much higher risk (user preparing to leave)
                if current_amount < avg_old_amount * 0.7:  # 30%+ decrease
                    change_bonus = 0.9  # Very high downgrade risk bonus
                
                # UPGRADE: lower risk (user more engaged) 
                elif current_amount > avg_old_amount * 1.5:  # 50%+ increase
                    change_bonus = -0.1  # Small upgrade bonus (reduces risk)
        
        # Progressive risk based on engagement level (family sharing context)
        # Lower prices = higher risk of leaving platform
        base_risk = 0.0
        if current_amount <= 1.2:          # Very low value (basic share) - HIGHEST RISK
            base_risk = 1.0
        elif current_amount <= 3:        # Low value (basic premium) - HIGH RISK  
            base_risk = 0.7
        elif current_amount <= 6:        # Medium value (premium single) - MEDIUM RISK
            base_risk = 0.4
        elif current_amount <= 10:       # High value (premium bundle) - LOW RISK
            base_risk = 0.2
        else:                           # Very high value (multiple premium services) - LOWEST RISK
            base_risk = 0.1
        
        return max(0.0, min(base_risk + change_bonus, 1.0))

    def _calculate_pattern_bonus(self, payments: List[Payment]) -> float:
        """
        Detect the specific pattern: "pay once, then decline subsequent payments"
    
        """
        if len(payments) < 3:
            return 0.0
            
        # Sort payments by date (oldest first for pattern detection)
        sorted_payments = sorted(payments, key=lambda x: x.payment_date)
        
        # Check if first payment was successful and subsequent ones failed
        if len(sorted_payments) >= 3:
            first_payment = sorted_payments[0]
            subsequent_payments = sorted_payments[1:4]  # Next 3 payments
            
            # Pattern: First payment success, then multiple failures
            if (first_payment.is_successful and 
                sum(1 for p in subsequent_payments if p.is_failed) >= 2):
                return 0.8  # High pattern bonus
                
        # Alternative pattern: Early success followed by recent failures
        if len(sorted_payments) >= 4:
            early_payments = sorted_payments[:2]
            recent_payments = sorted_payments[-2:]
            
            early_success_rate = sum(1 for p in early_payments if p.is_successful) / len(early_payments)
            recent_failure_rate = sum(1 for p in recent_payments if p.is_failed) / len(recent_payments)
            
            if early_success_rate >= 0.5 and recent_failure_rate >= 0.5:
                return 0.5  # Moderate pattern bonus
                
        return 0.0

    def get_risky_users(self, db: Session, min_risk_score: float = None, limit: int = 100) -> List[UserRiskSummary]:
        """
        Get list of users with high risk scores
        """
        if min_risk_score is None:
            min_risk_score = self.HIGH_RISK_THRESHOLD
            
        risky_users = []
        
        # Get all active users with payments
        users = db.query(User).filter(User.is_active == True).all()
        
        for user in users:
            # Calculate risk score
            risk_score = self.calculate_user_risk_score(user.id, db)
            
            if risk_score is None or risk_score < min_risk_score:
                continue
                
            # Get user's subscription info
            subscription = db.query(Subscription).filter(Subscription.user_id == user.id).first()
            if not subscription:
                continue
                
            # Get payment stats
            payments = db.query(Payment).filter(Payment.user_id == user.id).all()
            total_payments = len(payments)
            failed_payments = sum(1 for p in payments if p.is_failed)
            failure_rate = failed_payments / total_payments if total_payments > 0 else 0
            
            # Create risk summary
            user_risk = UserRiskSummary(
                id=user.id,
                name=user.name,
                email=user.email,
                risk_score=risk_score,
                failure_rate=failure_rate,
                total_payments=total_payments,
                failed_payments=failed_payments,
                subscription_type=subscription.subscription_type,
                monthly_amount=subscription.monthly_amount,
                created_at=user.created_at
            )
            
            risky_users.append(user_risk)
        
        # Sort by risk score (highest first)
        risky_users.sort(key=lambda x: x.risk_score, reverse=True)
        
        return risky_users[:limit]

    def analyze_user_risk(self, user_id: int, db: Session) -> Optional[UserRiskAnalysis]:
        """
        Get detailed risk analysis for a specific user
        """
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return None
            
        # Calculate risk score
        risk_score = self.calculate_user_risk_score(user_id, db)
        if risk_score is None:
            return None
            
        # Get risk level and factors
        risk_level = self.get_risk_level(risk_score)
        risk_factors = self.get_risk_factors(user_id, db)
        recommendations = self.get_recommendations(risk_level)
        
        # Get payment statistics
        payments = db.query(Payment).filter(Payment.user_id == user_id).all()
        total_payments = len(payments)
        failed_payments = sum(1 for p in payments if p.is_failed)
        successful_payments = total_payments - failed_payments
        
        # Get Subscription history
        subscriptions_history = db.query(Subscription).filter(Subscription.user_id == user_id).all()
        

        
        # Get recent payment history (last 10)
        recent_payments = sorted(payments, key=lambda x: x.payment_date, reverse=True)[:10]
        
        return UserRiskAnalysis(
            user_id=user.id,
            user_name=user.name,
            user_email=user.email,
            risk_score=risk_score,
            risk_level=risk_level,
            failure_rate=failed_payments / total_payments if total_payments > 0 else 0,
            total_payments=total_payments,
            failed_payments=failed_payments,
            successful_payments=successful_payments,
            subscriptions_history=subscriptions_history,
            payment_history=recent_payments,
            risk_factors=risk_factors,
            recommendations=recommendations
        )

    def get_risk_statistics(self, db: Session) -> SystemStats:
        """
        Get global system statistics
        """
        # Count total users
        total_users = db.query(User).count()
        
        # Count high risk users (using same threshold as get_risky_users)
        high_risk_users = len(self.get_risky_users(db, min_risk_score=self.HIGH_RISK_THRESHOLD))
        
        # Count total and failed payments
        total_payments = db.query(Payment).count()
        failed_payments = db.query(Payment).filter(
            Payment.status.in_(['failed', 'declined'])
        ).count()
        
        # Calculate overall failure rate
        overall_failure_rate = failed_payments / total_payments if total_payments > 0 else 0
        
        # Calculate average risk score
        all_users = db.query(User).all()
        risk_scores = []
        for user in all_users:
            score = self.calculate_user_risk_score(user.id, db)
            if score is not None:
                risk_scores.append(score)
        
        avg_risk_score = sum(risk_scores) / len(risk_scores) if risk_scores else 0
        
        return SystemStats(
            total_users=total_users,
            high_risk_users=high_risk_users,
            total_payments=total_payments,
            failed_payments=failed_payments,
            overall_failure_rate=overall_failure_rate,
            avg_risk_score=avg_risk_score
        )

    def get_risk_level(self, risk_score: float) -> str:
        """
        Classify risk score into levels
        """
        if risk_score >= self.CRITICAL_RISK_THRESHOLD:
            return "critical"
        elif risk_score >= self.HIGH_RISK_THRESHOLD:
            return "high"
        elif risk_score >= 0.2:
            return "medium"
        else:
            return "low"

    def get_risk_factors(self, user_id: int, db: Session) -> List[str]:
        """
        Get human-readable risk factors for a user based on the algorithm
        """
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return []
            
        payments = db.query(Payment).filter(Payment.user_id == user_id)\
                     .order_by(Payment.payment_date.desc()).all()
        if not payments:
            return ["No payment history"]
            
        factors = []
        
        # PRIMARY FACTOR: Check last 3 payments (core requirement from brief)
        recent_payments = payments[:3]
        if len(recent_payments) >= 2:
            recent_failures = sum(1 for p in recent_payments if p.is_failed)
            recent_failure_rate = recent_failures / len(recent_payments)
            
            if recent_failure_rate > 0.4:  # Main criterion from brief
                factors.append(f"High failure rate on recent payments ({recent_failure_rate:.1%})")
                factors.append(f"Failed {recent_failures}/{len(recent_payments)} of last payments")
        
        # Check for the specific problematic pattern
        pattern_bonus = self._calculate_pattern_bonus(payments)
        if pattern_bonus > 0.5:
            factors.append("Classic pattern: paid initially, then declined subsequent payments")
        elif pattern_bonus > 0.2:
            factors.append("Early success followed by recent payment failures")
        
        # Check for subscription changes (downgrades are warning signs)
        if len(payments) >= 3:
            sorted_payments = sorted(payments, key=lambda x: x.payment_date, reverse=True)
            current_amount = sorted_payments[0].amount
            old_amounts = [p.amount for p in sorted_payments[2:5]]
            if old_amounts:
                avg_old_amount = sum(old_amounts) / len(old_amounts)
                
                # DOWNGRADE detected - major warning sign
                if current_amount < avg_old_amount * 0.7:
                    factors.append(f"⚠️ DOWNGRADE DETECTED: {avg_old_amount:.2f}€ → {current_amount:.2f}€ (Departure signal)")
                
                # Upgrade detected - positive sign
                elif current_amount > avg_old_amount * 1.5:
                    factors.append(f"✅ Recent upgrade: {avg_old_amount:.2f}€ → {current_amount:.2f}€ (Positive engagement)")
        
        # Low amount warning
        if len(payments) > 0:
            current_amount = sorted(payments, key=lambda x: x.payment_date, reverse=True)[0].amount
            if current_amount <= 3:
                factors.append(f"💰 Low cost subscription ({current_amount:.2f}€) - High departure risk")
            
        # Overall pattern
        overall_failure_rate = self._calculate_failure_rate(payments)
        if overall_failure_rate > 0.3:
            factors.append(f"Overall failure rate: {overall_failure_rate:.1%}")
            
        # Account age (secondary factor)
        account_age_days = (datetime.utcnow() - user.created_at).days
        if account_age_days < 30:
            factors.append("New account (less than 30 days)")
            
        # Check for consecutive recent failures
        if len(recent_payments) >= 2:
            consecutive_failures = all(p.is_failed for p in recent_payments[:2])
            if consecutive_failures:
                factors.append("Multiple consecutive recent failures")
        
        return factors if factors else ["Low risk profile"]

    def get_recommendations(self, risk_level: str) -> List[str]:
        """
        Get recommendations based on risk level
        """
        recommendations = {
            "critical": [
                "Immediate contact required for payment method verification",
                "Consider temporary account restrictions",
                "Review subscription value proposition with user",
                "Implement payment retry with different methods"
            ],
            "high": [
                "Proactive outreach for payment method update",
                "Offer payment assistance or alternative methods", 
                "Monitor closely for upcoming payments",
                "Consider retention campaigns"
            ],
            "medium": [
                "Send automated payment reminder emails",
                "Monitor payment patterns for changes",
                "Consider targeted retention offers"
            ],
            "low": [
                "Continue standard monitoring",
                "Maintain regular communication"
            ]
        }
        
        return recommendations.get(risk_level, ["Continue monitoring"])

    def get_system_stats(self, db: Session) -> Dict:
        """
        Get overall system risk statistics
        """
        # Total active users
        total_users = db.query(User).filter(User.is_active == True).count()
        
        # Calculate high risk users
        high_risk_users = len(self.get_risky_users(db, self.HIGH_RISK_THRESHOLD, 1000))
        
        # Payment statistics
        total_payments = db.query(Payment).count()
        failed_payments = db.query(Payment).filter(
            Payment.is_failed == True
        ).count()
        
        overall_failure_rate = failed_payments / total_payments if total_payments > 0 else 0
        
        return {
            "total_users": total_users,
            "high_risk_users": high_risk_users,
            "total_payments": total_payments,
            "failed_payments": failed_payments,
            "overall_failure_rate": overall_failure_rate,
            "risk_percentage": (high_risk_users / total_users * 100) if total_users > 0 else 0
        }