"""
Stripe integrácia pre monetizáciu ILUMINATI SYSTEM
Subscription management a payment processing
"""

import os
import stripe
from typing import Optional, Dict
from services.auth import UserTier, update_user_tier
from services.database import get_db_session

# Stripe konfigurácia
stripe.api_key = os.getenv("STRIPE_SECRET_KEY", "sk_test_...")  # V produkcii z env
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET", "")

# Subscription prices (v centoch)
PRICES = {
    UserTier.PRO: os.getenv("STRIPE_PRO_PRICE_ID", "price_pro_monthly"),
    UserTier.ENTERPRISE: os.getenv("STRIPE_ENTERPRISE_PRICE_ID", "price_enterprise_monthly"),
}

# Default prices (ak nie sú nastavené)
DEFAULT_PRICES = {
    UserTier.PRO: 1999,  # $19.99/month
    UserTier.ENTERPRISE: 9999,  # $99.99/month
}


def create_checkout_session(user_id: int, user_email: str, tier: UserTier) -> Dict:
    """
    Vytvorí Stripe checkout session pre upgrade tieru.
    Creates or retrieves Stripe customer and stores customer ID in user record.
    
    Args:
        user_id: ID používateľa
        user_email: Email používateľa
        tier: Tier na upgrade (PRO alebo ENTERPRISE)
    
    Returns:
        Dict s checkout session URL
    """
    try:
        price_id = PRICES.get(tier)
        
        # Ak nie je price_id, vytvoriť price
        if not price_id or price_id.startswith("price_"):
            # Použiť existujúci price_id
            pass
        else:
            # Vytvoriť nový price (pre testovanie)
            price_id = None
        
        # Get or create Stripe customer
        # First, try to get existing customer by email
        customers = stripe.Customer.list(email=user_email, limit=1)
        if customers.data:
            customer = customers.data[0]
        else:
            # Create new customer if not exists
            customer = stripe.Customer.create(
                email=user_email,
                metadata={'user_id': str(user_id)}
            )
        
        # Store Stripe customer ID in database
        with get_db_session() as db:
            if db:
                from services.auth import User
                user = db.query(User).filter(User.id == user_id).first()
                if user and user.stripe_customer_id != customer.id:
                    user.stripe_customer_id = customer.id
                    db.commit()
        
        # Vytvoriť checkout session
        checkout_session = stripe.checkout.Session.create(
            customer=customer.id,  # Use customer ID instead of customer_email
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'eur',
                    'product_data': {
                        'name': f'ILUMINATI SYSTEM - {tier.value.upper()}',
                        'description': f'Upgrade na {tier.value.upper()} tier',
                    },
                    'unit_amount': DEFAULT_PRICES.get(tier, 1999),
                    'recurring': {
                        'interval': 'month',
                    },
                },
                'quantity': 1,
            }],
            mode='subscription',
            success_url=f"{os.getenv('FRONTEND_URL', 'http://localhost:5173')}/payment/success?session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=f"{os.getenv('FRONTEND_URL', 'http://localhost:5173')}/payment/cancel",
            metadata={
                'user_id': str(user_id),
                'tier': tier.value,
            },
        )
        
        return {
            "session_id": checkout_session.id,
            "url": checkout_session.url,
            "status": "created"
        }
    except Exception as e:
        return {
            "error": str(e),
            "status": "error"
        }


def handle_webhook(payload: bytes, signature: str) -> Dict:
    """
    Spracuje Stripe webhook event.
    
    Args:
        payload: Raw webhook payload
        signature: Stripe signature
    
    Returns:
        Dict s výsledkom
    """
    try:
        event = stripe.Webhook.construct_event(
            payload, signature, STRIPE_WEBHOOK_SECRET
        )
    except ValueError:
        return {"error": "Invalid payload", "status": "error"}
    except stripe.error.SignatureVerificationError:
        return {"error": "Invalid signature", "status": "error"}
    
    # Spracovať event
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        user_id = int(session['metadata']['user_id'])
        tier_str = session['metadata']['tier']
        tier = UserTier(tier_str)
        
        # Aktualizovať tier používateľa
        with get_db_session() as db:
            if db:
                update_user_tier(db, user_id, tier)
        
        return {
            "status": "success",
            "user_id": user_id,
            "tier": tier_str
        }
    
    elif event['type'] == 'customer.subscription.deleted':
        # Subscription zrušená - downgrade na FREE
        # Use Stripe customer ID to look up user (not email, which isn't in subscription object)
        subscription = event['data']['object']
        customer_id = subscription.get('customer')
        
        if customer_id:
            with get_db_session() as db:
                if db:
                    from services.auth import get_user_by_stripe_customer_id
                    user = get_user_by_stripe_customer_id(db, customer_id)
                    if user:
                        update_user_tier(db, user.id, UserTier.FREE)
                        return {
                            "status": "success",
                            "action": "downgrade_to_free",
                            "user_id": user.id
                        }
        
        return {
            "status": "success",
            "action": "downgrade_to_free",
            "note": "No user found for customer_id"
        }
    
    return {"status": "ignored", "event_type": event['type']}


def get_subscription_status(user_email: str) -> Optional[Dict]:
    """
    Získa status subscriptionu pre používateľa.
    
    Args:
        user_email: Email používateľa
    
    Returns:
        Dict so subscription status alebo None
    """
    try:
        customers = stripe.Customer.list(email=user_email, limit=1)
        if not customers.data:
            return None
        
        customer = customers.data[0]
        subscriptions = stripe.Subscription.list(customer=customer.id, limit=1)
        
        if not subscriptions.data:
            return None
        
        subscription = subscriptions.data[0]
        return {
            "status": subscription.status,
            "current_period_end": subscription.current_period_end,
            "cancel_at_period_end": subscription.cancel_at_period_end,
        }
    except Exception as e:
        return {"error": str(e)}


def cancel_subscription(user_email: str) -> Dict:
    """
    Zruší subscription používateľa.
    
    Args:
        user_email: Email používateľa
    
    Returns:
        Dict s výsledkom
    """
    try:
        customers = stripe.Customer.list(email=user_email, limit=1)
        if not customers.data:
            return {"error": "Customer not found", "status": "error"}
        
        customer = customers.data[0]
        subscriptions = stripe.Subscription.list(customer=customer.id, limit=1)
        
        if not subscriptions.data:
            return {"error": "No active subscription", "status": "error"}
        
        subscription = subscriptions.data[0]
        canceled = stripe.Subscription.modify(
            subscription.id,
            cancel_at_period_end=True
        )
        
        return {
            "status": "success",
            "canceled": True,
            "cancel_at_period_end": canceled.cancel_at_period_end
        }
    except Exception as e:
        return {"error": str(e), "status": "error"}

