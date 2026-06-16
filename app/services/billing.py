"""Stripe billing integration - subscriptions, usage metering, invoicing."""
import stripe
from datetime import datetime, timedelta
import logging
from typing import Optional

logger = logging.getLogger(__name__)

class BillingService:
    """Manage Stripe subscriptions and billing."""
    
    def __init__(self, api_key: str):
        stripe.api_key = api_key
    
    def create_customer(self, tenant_id: str, email: str, company_name: str) -> str:
        """Create Stripe customer."""
        try:
            customer = stripe.Customer.create(
                email=email,
                name=company_name,
                metadata={"tenant_id": tenant_id}
            )
            return customer.id
        except stripe.error.StripeError as e:
            logger.error(f"Customer creation error: {e}")
            raise
    
    def create_subscription(self, customer_id: str, price_id: str, 
                          billing_cycle_anchor: Optional[datetime] = None) -> dict:
        """Create subscription."""
        try:
            params = {
                "customer": customer_id,
                "items": [{"price": price_id}],
                "payment_behavior": "default_incomplete",
                "expand": ["latest_invoice.payment_intent"],
            }
            
            if billing_cycle_anchor:
                params["billing_cycle_anchor"] = int(billing_cycle_anchor.timestamp())
            
            subscription = stripe.Subscription.create(**params)
            
            return {
                "subscription_id": subscription.id,
                "status": subscription.status,
                "current_period_start": subscription.current_period_start,
                "current_period_end": subscription.current_period_end,
                "client_secret": subscription.latest_invoice.payment_intent.client_secret
                if subscription.latest_invoice and subscription.latest_invoice.payment_intent
                else None
            }
        except stripe.error.StripeError as e:
            logger.error(f"Subscription creation error: {e}")
            raise
    
    def update_subscription(self, subscription_id: str, price_id: str) -> dict:
        """Update subscription (upgrade/downgrade)."""
        try:
            subscription = stripe.Subscription.retrieve(subscription_id)
            
            # Cancel old item
            stripe.SubscriptionItem.delete(subscription.items.data[0].id)
            
            # Add new item
            subscription = stripe.Subscription.modify(
                subscription_id,
                items=[{"price": price_id}],
                proration_behavior="create_prorations"
            )
            
            return {
                "subscription_id": subscription.id,
                "status": subscription.status,
            }
        except stripe.error.StripeError as e:
            logger.error(f"Subscription update error: {e}")
            raise
    
    def cancel_subscription(self, subscription_id: str, 
                           immediate: bool = False) -> dict:
        """Cancel subscription."""
        try:
            if immediate:
                subscription = stripe.Subscription.delete(subscription_id)
            else:
                subscription = stripe.Subscription.modify(
                    subscription_id,
                    cancel_at_period_end=True
                )
            
            return {
                "subscription_id": subscription.id,
                "status": subscription.status,
                "cancel_at": subscription.cancel_at,
            }
        except stripe.error.StripeError as e:
            logger.error(f"Subscription cancellation error: {e}")
            raise
    
    def get_invoice(self, invoice_id: str) -> dict:
        """Retrieve invoice."""
        try:
            invoice = stripe.Invoice.retrieve(invoice_id)
            return {
                "id": invoice.id,
                "amount": invoice.total,
                "currency": invoice.currency,
                "status": invoice.status,
                "url": invoice.hosted_invoice_url,
                "pdf": invoice.invoice_pdf
            }
        except stripe.error.StripeError as e:
            logger.error(f"Invoice retrieval error: {e}")
            raise
    
    def list_invoices(self, customer_id: str, limit: int = 10) -> list:
        """List customer invoices."""
        try:
            invoices = stripe.Invoice.list(customer=customer_id, limit=limit)
            return [
                {
                    "id": inv.id,
                    "amount": inv.total,
                    "date": inv.created,
                    "status": inv.status,
                    "url": inv.hosted_invoice_url
                }
                for inv in invoices.data
            ]
        except stripe.error.StripeError as e:
            logger.error(f"Invoice listing error: {e}")
            raise
    
    def create_payment_intent(self, customer_id: str, amount: int, 
                             description: str) -> dict:
        """Create one-time payment intent."""
        try:
            intent = stripe.PaymentIntent.create(
                customer=customer_id,
                amount=amount,
                currency="usd",
                description=description,
                confirm=False
            )
            
            return {
                "client_secret": intent.client_secret,
                "intent_id": intent.id,
                "status": intent.status
            }
        except stripe.error.StripeError as e:
            logger.error(f"Payment intent error: {e}")
            raise

class UsageMeter:
    """Track and bill usage - resumes processed, API calls, etc."""
    
    @staticmethod
    async def record_usage(db, tenant_id: str, metric_type: str, 
                          quantity: float, cost: float):
        """Record usage event for billing."""
        from app.models.base import BillingEvent
        
        try:
            event = BillingEvent(
                tenant_id=tenant_id,
                event_type=metric_type,
                quantity=quantity,
                cost=cost
            )
            db.add(event)
            db.commit()
            return event.id
        except Exception as e:
            logger.error(f"Usage recording error: {e}")
            db.rollback()
            raise
    
    @staticmethod
    async def get_month_usage(db, tenant_id: str) -> dict:
        """Get tenant's usage for current month."""
        from app.models.base import BillingEvent
        from sqlalchemy import func
        
        try:
            first_day = datetime.utcnow().replace(day=1)
            
            result = db.query(
                BillingEvent.event_type,
                func.sum(BillingEvent.quantity).label("total_quantity"),
                func.sum(BillingEvent.cost).label("total_cost")
            ).filter(
                BillingEvent.tenant_id == tenant_id,
                BillingEvent.created_at >= first_day
            ).group_by(BillingEvent.event_type).all()
            
            return {
                row[0]: {
                    "quantity": row[1],
                    "cost": row[2]
                }
                for row in result
            }
        except Exception as e:
            logger.error(f"Usage retrieval error: {e}")
            raise
    
    @staticmethod
    async def estimate_bill(usage_dict: dict, pricing: dict) -> float:
        """Estimate bill based on usage."""
        total = 0.0
        
        for metric_type, usage in usage_dict.items():
            if metric_type in pricing:
                rate = pricing[metric_type]
                total += usage.get("quantity", 0) * rate
        
        return total

class SubscriptionPlans:
    """Define subscription tiers and features."""
    
    PLANS = {
        "free": {
            "name": "Free",
            "price": 0,
            "monthly_resumes": 50,
            "monthly_api_calls": 5000,
            "features": [
                "Resume parsing",
                "Basic matching",
                "1 job posting",
                "Community support"
            ]
        },
        "pro": {
            "name": "Pro",
            "price": 299,
            "monthly_resumes": 1000,
            "monthly_api_calls": 100000,
            "features": [
                "Unlimited resume parsing",
                "Advanced matching",
                "20 job postings",
                "Interview generation",
                "Email support"
            ]
        },
        "enterprise": {
            "name": "Enterprise",
            "price": "custom",
            "monthly_resumes": 100000,
            "monthly_api_calls": 10000000,
            "features": [
                "Unlimited everything",
                "Custom integrations",
                "Dedicated account manager",
                "Phone support",
                "SLA",
                "Custom workflows"
            ]
        }
    }
    
    @staticmethod
    def get_plan(plan_name: str) -> Optional[dict]:
        """Get plan details."""
        return SubscriptionPlans.PLANS.get(plan_name)
    
    @staticmethod
    def get_price_id(plan_name: str) -> str:
        """Get Stripe price ID for plan."""
        stripe_price_ids = {
            "pro": "price_pro_usd",
            "enterprise": "price_enterprise_usd"
        }
        return stripe_price_ids.get(plan_name, "")
