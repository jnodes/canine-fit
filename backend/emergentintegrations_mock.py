"""
Mock/Proxy for emergentintegrations package.
Delegates to native integrations when available.
"""

# Try to import native integrations
try:
    from stripe_integration import (
        StripeCheckout,
        CheckoutSessionResponse,
        CheckoutStatusResponse,
        CheckoutSessionRequest,
    )
except ImportError:
    # Fallback to mock
    from .mock_stripe import (
        StripeCheckout,
        CheckoutSessionResponse,
        CheckoutStatusResponse,
        CheckoutSessionRequest,
    )

try:
    from openai_integration import LlmChat, UserMessage
except ImportError:
    # Fallback to mock
    from .mock_openai import LlmChat, UserMessage

__all__ = [
    'StripeCheckout',
    'CheckoutSessionResponse',
    'CheckoutStatusResponse',
    'CheckoutSessionRequest',
    'LlmChat',
    'UserMessage',
]
