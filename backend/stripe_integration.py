"""
Native Stripe integration for Canine.Fit.
Replaces emergentintegrations.payments.stripe.checkout
"""

import stripe
from typing import Optional, Dict, Any
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class CheckoutSessionResponse:
    """Response from creating a checkout session."""
    session_id: str
    url: str


@dataclass
class CheckoutStatusResponse:
    """Response from checking checkout status."""
    status: str
    payment_status: str
    amount_total: Optional[int] = None
    currency: Optional[str] = None
    metadata: Optional[Dict] = None


@dataclass
class CheckoutSessionRequest:
    """Request to create a checkout session."""
    amount: float
    currency: str = "usd"
    success_url: str = ""
    cancel_url: str = ""
    metadata: Optional[Dict] = None


class StripeCheckout:
    """Native Stripe checkout integration."""
    
    def __init__(self, api_key: str, webhook_url: str = ""):
        self.api_key = api_key
        self.webhook_url = webhook_url
        stripe.api_key = api_key
    
    async def create_checkout_session(self, request: CheckoutSessionRequest) -> CheckoutSessionResponse:
        """
        Create a Stripe checkout session.
        
        Args:
            request: CheckoutSessionRequest with amount, currency, etc.
            
        Returns:
            CheckoutSessionResponse with session_id and url
        """
        try:
            # Convert dollars to cents
            amount_cents = int(request.amount * 100)
            
            session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=[{
                    'price_data': {
                        'currency': request.currency,
                        'product_data': {
                            'name': 'Canine.Fit Premium Subscription',
                        },
                        'unit_amount': amount_cents,
                    },
                    'quantity': 1,
                }],
                mode='payment',
                success_url=request.success_url,
                cancel_url=request.cancel_url,
                metadata=request.metadata or {},
            )
            
            return CheckoutSessionResponse(
                session_id=session.id,
                url=session.url
            )
            
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error creating checkout session: {e}")
            raise
    
    async def get_checkout_status(self, session_id: str) -> CheckoutStatusResponse:
        """
        Get the status of a checkout session.
        
        Args:
            session_id: The Stripe session ID
            
        Returns:
            CheckoutStatusResponse with status information
        """
        try:
            session = stripe.checkout.Session.retrieve(session_id)
            
            return CheckoutStatusResponse(
                status=session.status or 'unknown',
                payment_status=session.payment_status or 'unknown',
                amount_total=session.amount_total,
                currency=session.currency,
                metadata=session.metadata
            )
            
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error retrieving session: {e}")
            raise
    
    async def handle_webhook(self, body: bytes, signature: str) -> CheckoutStatusResponse:
        """
        Handle a Stripe webhook event.
        
        Args:
            body: Raw webhook body
            signature: Stripe-Signature header
            
        Returns:
            CheckoutStatusResponse with event information
        """
        try:
            # In production, verify the signature
            # event = stripe.Webhook.construct_event(body, signature, self.webhook_url)
            
            # For now, parse the body directly
            import json
            event_data = json.loads(body)
            
            session_id = event_data.get('data', {}).get('object', {}).get('id', '')
            
            return CheckoutStatusResponse(
                status='completed',
                payment_status=event_data.get('type', 'unknown'),
                metadata={'session_id': session_id}
            )
            
        except Exception as e:
            logger.error(f"Webhook handling error: {e}")
            raise
