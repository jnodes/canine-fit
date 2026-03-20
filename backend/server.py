"""
Canine.Fit API Server - Supabase Edition
Migrated from MongoDB to Supabase for simplified architecture.

Key changes:
- Uses Supabase Auth for authentication (no custom tokens)
- Uses Supabase database with Row Level Security (RLS)
- Service role client for admin operations
- All other operations use authenticated client (RLS enforced)
"""

from fastapi import FastAPI, APIRouter, HTTPException, Depends, Header, Request, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from supabase import create_client, Client
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, field_validator
from typing import List, Optional, Dict
import uuid
from datetime import datetime, date, timedelta
import secrets
import re
import hmac

# Security imports
from slowapi.middleware import SlowAPIMiddleware

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# ============== Supabase Configuration ==============
SUPABASE_URL = os.environ.get('SUPABASE_URL', '')
SUPABASE_ANON_KEY = os.environ.get('SUPABASE_ANON_KEY', '')
SUPABASE_SERVICE_ROLE_KEY = os.environ.get('SUPABASE_SERVICE_ROLE_KEY', '')

# Rate limiter setup (will be attached to app after creation)
limiter = Limiter(key_func=get_remote_address)

# Create Supabase clients
# Regular client (uses RLS - for authenticated user operations)
supabase: Client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)

# Admin client (bypasses RLS - for admin operations only)
from supabase import create_client as create_admin_client
supabase_admin: Client = create_admin_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

# Security configuration
ALLOWED_ORIGINS = os.environ.get('ALLOWED_ORIGINS', 'http://localhost:3000,https://dog-fitness-hub.preview.emergentagent.com').split(',')
MAX_IMAGE_SIZE = int(os.environ.get('MAX_IMAGE_SIZE', 5000000))  # 5MB default

# Stripe integration (native)
from stripe_integration import StripeCheckout, CheckoutSessionResponse, CheckoutStatusResponse, CheckoutSessionRequest

# LLM integration for Lilo AI (native)
from openai_integration import LlmChat, UserMessage

# External services
from external_services import (
    search_breeds, get_breed_by_id, get_breed_health_insights,
    search_foods, get_food_by_id, analyze_food_for_dogs,
    get_current_weather, get_forecast, analyze_walk_conditions, find_best_walk_times,
    get_air_quality, analyze_air_quality,
    calculate_healthspan_contribution
)

# Create the main app
app = FastAPI(title="Canine.Fit API", version="2.0.0", description="Powered by Supabase")

# Attach rate limiter to app
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Create a router with versioned /api/v1 prefix
api_router = APIRouter(prefix="/api/v1")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ============== Shared Healthspan Scoring (Single Source of Truth) ==============

def calculate_day_score(log: dict) -> int:
    """Calculate healthspan score for a day. Shared across all modules."""
    score = 70
    
    mood_scores = {"great": 15, "good": 10, "okay": 5, "tired": 0, "unwell": -10}
    exercise_scores = {"intense": 15, "active": 12, "moderate": 8, "light": 4, "none": 0}
    nutrition_scores = {"excellent": 15, "good": 10, "fair": 5, "poor": 0}
    
    score += mood_scores.get(log.get("mood", "okay"), 5)
    score += exercise_scores.get(log.get("exercise_level", "light"), 4)
    score += nutrition_scores.get(log.get("nutrition_quality", "good"), 10)
    
    return min(100, max(0, score))

# ============== Subscription Plans ==============
SUBSCRIPTION_PLANS = {
    "monthly": {
        "name": "Monthly",
        "price": 9.00,
        "period": "month",
        "description": "Full access, cancel anytime"
    },
    "annual": {
        "name": "Annual",
        "price": 99.00,
        "period": "year",
        "description": "Save $9 vs monthly — best value"
    }
}

# ============== Models ==============

# Auth Models (using Supabase)
class UserCreate(BaseModel):
    email: str
    password: str
    name: str
    
    @field_validator('email')
    @classmethod
    def validate_email(cls, v: str) -> str:
        if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', v):
            raise ValueError('Invalid email format')
        return v.lower().strip()
    
    @field_validator('password')
    @classmethod
    def validate_password(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        if len(v) > 128:
            raise ValueError('Password must not exceed 128 characters')
        return v
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v: str) -> str:
        if not v or len(v.strip()) < 1:
            raise ValueError('Name is required')
        if len(v) > 100:
            raise ValueError('Name must not exceed 100 characters')
        return v.strip()

class UserLogin(BaseModel):
    email: str
    password: str
    
    @field_validator('email')
    @classmethod
    def validate_email(cls, v: str) -> str:
        return v.lower().strip()

class User(BaseModel):
    id: str
    email: str
    name: str
    is_premium: bool = False
    subscription_status: Optional[str] = None
    subscription_plan: Optional[str] = None
    subscription_expires: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

class AuthResponse(BaseModel):
    user: User
    access_token: str
    expires_in: int

# Dog Models
class DogCreate(BaseModel):
    name: str
    breed: str
    avatar_url: Optional[str] = None
    date_of_birth: Optional[str] = None
    weight_lbs: Optional[float] = None
    sex: Optional[str] = None
    activity_level: Optional[str] = None
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v: str) -> str:
        if not v or len(v.strip()) < 1:
            raise ValueError('Name is required')
        if len(v) > 50:
            raise ValueError('Name must not exceed 50 characters')
        return v.strip()
    
    @field_validator('weight_lbs')
    @classmethod
    def validate_weight(cls, v: Optional[float]) -> Optional[float]:
        if v is not None and (v <= 0 or v > 500):
            raise ValueError('Weight must be between 0 and 500 lbs')
        return v

class DogUpdate(BaseModel):
    name: Optional[str] = None
    breed: Optional[str] = None
    avatar_url: Optional[str] = None
    date_of_birth: Optional[str] = None
    weight_lbs: Optional[float] = None
    sex: Optional[str] = None
    activity_level: Optional[str] = None
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            if len(v.strip()) < 1:
                raise ValueError('Name cannot be empty')
            if len(v) > 50:
                raise ValueError('Name must not exceed 50 characters')
            return v.strip()
        return v
    
    @field_validator('weight_lbs')
    @classmethod
    def validate_weight(cls, v: Optional[float]) -> Optional[float]:
        if v is not None and (v <= 0 or v > 500):
            raise ValueError('Weight must be between 0 and 500 lbs')
        return v

class Dog(BaseModel):
    id: str
    name: str
    breed: str
    avatar_url: Optional[str] = None
    date_of_birth: Optional[str] = None
    weight_lbs: Optional[float] = None
    sex: Optional[str] = None
    activity_level: Optional[str] = None
    owner_id: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

# Daily Log Enums (whitelist validation)
DAILY_LOG_MOODS = {"great", "good", "okay", "tired", "unwell"}
DAILY_LOG_EXERCISE_LEVELS = {"intense", "active", "moderate", "light", "none"}
DAILY_LOG_NUTRITION_QUALITY = {"excellent", "good", "fair", "poor"}
MAX_NOTES_LENGTH = 500

class DailyLogCreate(BaseModel):
    dog_id: str
    mood: str
    exercise_level: str
    nutrition_quality: str
    notes: Optional[str] = None
    
    @field_validator('mood')
    @classmethod
    def validate_mood(cls, v: str) -> str:
        if v.lower() not in DAILY_LOG_MOODS:
            raise ValueError(f'Mood must be one of: {sorted(DAILY_LOG_MOODS)}')
        return v.lower()
    
    @field_validator('exercise_level')
    @classmethod
    def validate_exercise(cls, v: str) -> str:
        if v.lower() not in DAILY_LOG_EXERCISE_LEVELS:
            raise ValueError(f'Exercise level must be one of: {sorted(DAILY_LOG_EXERCISE_LEVELS)}')
        return v.lower()
    
    @field_validator('nutrition_quality')
    @classmethod
    def validate_nutrition(cls, v: str) -> str:
        if v.lower() not in DAILY_LOG_NUTRITION_QUALITY:
            raise ValueError(f'Nutrition quality must be one of: {sorted(DAILY_LOG_NUTRITION_QUALITY)}')
        return v.lower()
    
    @field_validator('notes')
    @classmethod
    def validate_notes(cls, v: Optional[str]) -> Optional[str]:
        if v and len(v) > MAX_NOTES_LENGTH:
            raise ValueError(f'Notes must not exceed {MAX_NOTES_LENGTH} characters')
        return v

class DailyLog(BaseModel):
    id: str
    dog_id: str
    logged_at: datetime = Field(default_factory=datetime.utcnow)
    date: str = Field(default_factory=lambda: date.today().isoformat())
    mood: str
    exercise_level: str
    nutrition_quality: str
    notes: Optional[str] = None
    points_earned: int = 10

# Lilo Report Models
class LiloReport(BaseModel):
    id: str
    dog_id: str
    report_date: str = Field(default_factory=lambda: date.today().isoformat())
    mood: str
    summary: str
    insights: List[str]
    recommendation: str
    healthspan_delta: Optional[float] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    disclaimer: str = "AI-generated insights are for informational purposes only and are not a substitute for professional veterinary advice. Always consult a qualified veterinarian for health concerns."

# Healthspan Models
class HealthspanScore(BaseModel):
    dog_id: str
    score: int
    streak: int
    total_points: int
    breed_rank: int
    weekly_scores: List[dict]
    disclaimer: str = "This score is for informational purposes only and is not a substitute for professional veterinary advice. Always consult a qualified veterinarian for health concerns."

# Payment Models
class CheckoutRequest(BaseModel):
    plan_id: str
    origin_url: str

class PaymentTransaction(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    session_id: str
    plan_id: str
    amount: float
    currency: str = "usd"
    status: str = "pending"
    payment_status: str = "pending"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

# ============== Security Helpers ==============

def secure_compare(a: str, b: str) -> bool:
    """Constant-time string comparison to prevent timing attacks."""
    return hmac.compare_digest(a, b)

def validate_admin_key(provided_key: Optional[str]) -> bool:
    """Validate admin key with constant-time comparison."""
    valid_key = os.environ.get('ADMIN_API_KEY')
    if not valid_key or not provided_key:
        return False
    return secure_compare(provided_key, valid_key)

# ============== Auth Dependencies (Supabase Auth) ==============

async def get_current_user(authorization: Optional[str] = Header(None)) -> dict:
    """
    Get current authenticated user from Supabase Bearer token.
    Uses Supabase Auth - no custom token management needed.
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    token = authorization[7:].strip()
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    # Set the session token
    supabase.auth.session = lambda: {"access_token": token, "token_type": "Bearer"}
    
    try:
        # Get user from Supabase Auth
        user_response = supabase.auth.get_user(token)
        if not user_response.user:
            raise HTTPException(status_code=401, detail="Invalid or expired token")
        
        # Get user profile from database (includes subscription info)
        profile_response = supabase.table('user_profiles').select('*').eq('id', user_response.user.id).execute()
        
        if profile_response.data:
            user_data = profile_response.data[0]
            user_data['email'] = user_response.user.email
            return user_data
        else:
            # Profile might not exist yet (race condition on signup)
            raise HTTPException(status_code=401, detail="User profile not found")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Auth error: {e}")
        raise HTTPException(status_code=401, detail="Invalid or expired token")

async def get_optional_user(authorization: Optional[str] = Header(None)) -> Optional[dict]:
    """Get current user if authenticated, None otherwise."""
    if not authorization or not authorization.startswith("Bearer "):
        return None
    
    try:
        return await get_current_user(authorization)
    except HTTPException:
        return None

def require_premium(current_user: dict = Depends(get_current_user)) -> dict:
    """Dependency that requires an active premium subscription."""
    if not current_user.get("is_premium", False):
        raise HTTPException(
            status_code=403,
            detail={
                "error": "premium_required",
                "message": "This feature requires a premium subscription",
                "upgrade_url": "/subscription"
            }
        )
    return current_user

def check_subscription_status(user: dict) -> dict:
    """Check if user's subscription is still active."""
    if not user.get("is_premium", False):
        return {"tier": "free", "premium": False}
    
    expires = user.get("subscription_expires")
    if expires:
        expires_dt = datetime.fromisoformat(expires.replace('Z', '+00:00')) if isinstance(expires, str) else expires
        if expires_dt < datetime.utcnow():
            return {"tier": "free", "premium": False, "expired": True}
    
    return {
        "tier": user.get("subscription_plan", "premium"),
        "premium": True,
        "expires": expires
    }

# ============== Auth Routes (Supabase Auth) ==============

@api_router.post("/auth/signup", response_model=AuthResponse)
@limiter.limit("10/minute")
async def signup(request: Request, user_data: UserCreate):
    """
    Create new user account using Supabase Auth.
    User profile is auto-created by database trigger.
    """
    try:
        # Create user in Supabase Auth
        auth_response = supabase.auth.sign_up({
            "email": user_data.email,
            "password": user_data.password,
            "options": {
                "data": {
                    "name": user_data.name
                }
            }
        })
        
        if auth_response.user is None:
            raise HTTPException(status_code=400, detail="Signup failed")
        
        # Supabase trigger creates user_profiles entry automatically
        # Fetch the created profile
        profile_response = supabase.table('user_profiles').select('*').eq('id', auth_response.user.id).execute()
        
        if not profile_response.data:
            raise HTTPException(status_code=500, detail="Profile creation failed")
        
        user_profile = profile_response.data[0]
        user_profile['email'] = auth_response.user.email
        
        return AuthResponse(
            user=User(**user_profile),
            access_token=auth_response.session.access_token,
            expires_in=auth_response.session.expires_in
        )
        
    except Exception as e:
        if "already registered" in str(e).lower():
            raise HTTPException(status_code=400, detail="Email already registered")
        logger.error(f"Signup error: {e}")
        raise HTTPException(status_code=500, detail="Signup failed")

@api_router.post("/auth/login", response_model=AuthResponse)
@limiter.limit("10/minute")
async def login(request: Request, credentials: UserLogin):
    """Login using Supabase Auth."""
    try:
        auth_response = supabase.auth.sign_in_with_password({
            "email": credentials.email,
            "password": credentials.password
        })
        
        if auth_response.user is None:
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        # Fetch user profile
        profile_response = supabase.table('user_profiles').select('*').eq('id', auth_response.user.id).execute()
        
        if not profile_response.data:
            raise HTTPException(status_code=404, detail="User profile not found")
        
        user_profile = profile_response.data[0]
        user_profile['email'] = auth_response.user.email
        
        return AuthResponse(
            user=User(**user_profile),
            access_token=auth_response.session.access_token,
            expires_in=auth_response.session.expires_in
        )
        
    except Exception as e:
        raise HTTPException(status_code=401, detail="Invalid credentials")

@api_router.post("/auth/logout")
@limiter.limit("20/minute")
async def logout(request: Request, authorization: Optional[str] = Header(None), current_user: dict = Depends(get_current_user)):
    """Logout - invalidate Supabase session."""
    try:
        supabase.auth.sign_out()
    except:
        pass  # Best effort
    return {"message": "Logged out successfully"}

@api_router.get("/auth/me")
async def get_me(current_user: dict = Depends(get_current_user)):
    """Get current user profile."""
    return User(**current_user)

# ============== GDPR / Privacy Routes ==============

@api_router.get("/auth/export-data")
async def export_user_data(current_user: dict = Depends(get_current_user)):
    """Export all user data in JSON format (GDPR Article 20)"""
    user_id = current_user["id"]
    
    # Use admin client to bypass RLS for export
    # Gather all user data
    user_data = {k: v for k, v in current_user.items() if k not in ['password_hash', 'stripe_customer_id']}
    
    # Get user's dogs
    dogs_response = supabase_admin.table('dogs').select('*').eq('owner_id', user_id).execute()
    dogs = dogs_response.data
    
    # Get daily logs for each dog
    dog_ids = [dog["id"] for dog in dogs]
    daily_logs_response = supabase_admin.table('daily_logs').select('*').in_('dog_id', dog_ids).execute()
    daily_logs = daily_logs_response.data
    
    # Get healthspan stats
    healthspan_response = supabase_admin.table('healthspan_stats').select('*').in_('dog_id', dog_ids).execute()
    healthspan_stats = healthspan_response.data
    
    # Get Lilo reports
    reports_response = supabase_admin.table('lilo_reports').select('*').in_('dog_id', dog_ids).execute()
    lilo_reports = reports_response.data
    
    # Get subscription info
    subscription_info = {
        "is_premium": current_user.get("is_premium", False),
        "subscription_status": current_user.get("subscription_status"),
        "subscription_plan": current_user.get("subscription_plan"),
        "subscription_expires": current_user.get("subscription_expires")
    }
    
    export_data = {
        "exported_at": datetime.utcnow().isoformat(),
        "user": user_data,
        "subscription": subscription_info,
        "dogs": dogs,
        "daily_logs": daily_logs,
        "healthspan_stats": healthspan_stats,
        "lilo_reports": lilo_reports
    }
    
    return export_data

@api_router.delete("/auth/delete-account")
async def delete_user_account(current_user: dict = Depends(get_current_user)):
    """
    Delete all user data (GDPR Article 17)
    Uses Supabase Admin client for cascade delete.
    """
    user_id = current_user["id"]
    
    # Delete user from Supabase Auth (cascades to profiles via FK)
    try:
        supabase_admin.auth.admin.delete_user(user_id)
    except Exception as e:
        logger.error(f"Failed to delete auth user: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete account")
    
    # Manual cleanup of any orphaned data (RLS might prevent cascade)
    for dog in supabase_admin.table('dogs').select('id').eq('owner_id', user_id).execute().data:
        supabase_admin.table('daily_logs').delete().eq('dog_id', dog['id']).execute()
        supabase_admin.table('healthspan_stats').delete().eq('dog_id', dog['id']).execute()
        supabase_admin.table('lilo_reports').delete().eq('dog_id', dog['id']).execute()
    
    # Delete dogs
    supabase_admin.table('dogs').delete().eq('owner_id', user_id).execute()
    
    # Delete payment transactions
    supabase_admin.table('payment_transactions').delete().eq('user_id', user_id).execute()
    
    return {
        "message": "Account and all associated data have been permanently deleted",
        "deleted_data": {
            "dogs": len(dog_ids) if 'dog_ids' in dir() else 0,
            "account": True
        }
    }

# ============== Dogs Routes ==============

@api_router.get("/dogs", response_model=List[Dog])
async def get_dogs(current_user: dict = Depends(get_current_user)):
    """Get all dogs for current user. RLS enforced."""
    response = supabase.table('dogs').select('*').eq('owner_id', current_user['id']).execute()
    return [Dog(**dog) for dog in response.data]

@api_router.post("/dogs", response_model=Dog)
@limiter.limit("10/minute")
async def create_dog(request: Request, dog_data: DogCreate, current_user: dict = Depends(get_current_user)):
    """Create a new dog profile. Free users limited to 1 dog."""
    # Check if free user has reached dog limit
    if not current_user.get("is_premium", False):
        existing_dogs_response = supabase.table('dogs').select('id', count='exact').eq('owner_id', current_user['id']).execute()
        existing_dogs_count = len(existing_dogs_response.data)
        
        if existing_dogs_count >= 1:
            raise HTTPException(
                status_code=403,
                detail={
                    "error": "dog_limit_reached",
                    "message": "Free accounts are limited to 1 dog. Upgrade to premium for unlimited dogs.",
                    "upgrade_url": "/subscription",
                    "current_dogs": existing_dogs_count,
                    "max_dogs": 1
                }
            )
    
    # Create dog
    dog_dict = dog_data.model_dump()
    dog_dict['owner_id'] = current_user['id']
    
    response = supabase.table('dogs').insert(dog_dict).execute()
    
    if not response.data:
        raise HTTPException(status_code=500, detail="Failed to create dog")
    
    return Dog(**response.data[0])

@api_router.put("/dogs/{dog_id}", response_model=Dog)
async def update_dog(dog_id: str, dog_data: DogUpdate, current_user: dict = Depends(get_current_user)):
    """Update dog. RLS enforces ownership."""
    # Check ownership
    check_response = supabase.table('dogs').select('id').eq('id', dog_id).eq('owner_id', current_user['id']).execute()
    if not check_response.data:
        raise HTTPException(status_code=404, detail="Dog not found")
    
    update_data = {k: v for k, v in dog_data.model_dump().items() if v is not None}
    if update_data:
        response = supabase.table('dogs').update(update_data).eq('id', dog_id).execute()
    else:
        response = check_response
    
    return Dog(**response.data[0])

@api_router.delete("/dogs/{dog_id}")
async def delete_dog(dog_id: str, current_user: dict = Depends(get_current_user)):
    """Delete dog. RLS enforces ownership."""
    response = supabase.table('dogs').delete().eq('id', dog_id).eq('owner_id', current_user['id']).execute()
    
    if not response.data:
        raise HTTPException(status_code=404, detail="Dog not found")
    
    return {"message": "Dog deleted successfully"}

# Photo Upload Model
class PhotoUpload(BaseModel):
    image_base64: str

# Allowed image MIME types
ALLOWED_IMAGE_TYPES = {'image/jpeg': '.jpg', 'image/png': '.png', 'image/webp': '.webp'}
BLOCKED_IMAGE_TYPES = {'image/svg+xml', 'image/svg', 'text/html', 'application/html'}

def validate_image_base64(image_data: str) -> tuple[bool, str, str]:
    """Validate base64 image data for security."""
    import base64
    
    if len(image_data) > MAX_IMAGE_SIZE:
        return False, f"Image too large. Maximum size is {MAX_IMAGE_SIZE // 1000000}MB", ""
    
    mime_type = None
    b64_data = image_data
    
    if image_data.startswith('data:'):
        try:
            header, b64_data = image_data.split(',', 1)
            mime_type = header.split(';')[0].replace('data:', '')
        except (ValueError, IndexError):
            return False, "Invalid image format header", ""
    
    b64_clean = re.sub(r'\s', '', b64_data)
    if not re.match(r'^[A-Za-z0-9+/=]*$', b64_clean):
        return False, "Invalid base64 encoding", ""
    
    try:
        image_bytes = base64.b64decode(b64_clean, validate=True)
    except Exception:
        return False, "Invalid base64 data", ""
    
    if len(image_bytes) < 50:
        return False, "Image data too small", ""
    
    actual_mime = detect_image_type(image_bytes)
    if not actual_mime:
        return False, "Unrecognized image format", ""
    
    if actual_mime.lower() in BLOCKED_IMAGE_TYPES:
        return False, f"Image type {actual_mime} is not allowed for security", ""
    
    if actual_mime.lower() not in [m.lower() for m in ALLOWED_IMAGE_TYPES.keys()]:
        return False, f"Image type {actual_mime} is not supported. Allowed: JPEG, PNG, WebP", ""
    
    if mime_type and mime_type.lower() != actual_mime.lower():
        return False, f"Image content ({actual_mime}) doesn't match claimed type ({mime_type})", ""
    
    validated_data = f"data:{actual_mime};base64,{b64_clean}"
    return True, "", validated_data

def detect_image_type(data: bytes) -> Optional[str]:
    """Detect image type from magic bytes."""
    if len(data) < 4:
        return None
    if data[0:3] == b'\xff\xd8\xff':
        return 'image/jpeg'
    if data[0:8] == b'\x89PNG\r\n\x1a\n':
        return 'image/png'
    if data[0:4] == b'RIFF' and data[8:12] == b'WEBP':
        return 'image/webp'
    try:
        text_start = data[:100].decode('utf-8', errors='ignore').strip().lower()
        if text_start.startswith('<svg') or text_start.startswith('<?xml'):
            return 'image/svg+xml'
    except:
        pass
    return None

@api_router.post("/dogs/{dog_id}/photo")
async def upload_dog_photo(dog_id: str, photo_data: PhotoUpload, current_user: dict = Depends(get_current_user)):
    """Upload a dog's profile photo. RLS enforces ownership."""
    # Check ownership
    check_response = supabase.table('dogs').select('id').eq('id', dog_id).eq('owner_id', current_user['id']).execute()
    if not check_response.data:
        raise HTTPException(status_code=404, detail="Dog not found")
    
    is_valid, error_msg, validated_base64 = validate_image_base64(photo_data.image_base64)
    if not is_valid:
        raise HTTPException(status_code=400, detail=error_msg)
    
    response = supabase.table('dogs').update({
        "avatar_url": validated_base64,
        "updated_at": datetime.utcnow().isoformat()
    }).eq('id', dog_id).execute()
    
    return Dog(**response.data[0])

# ============== Daily Logs Routes ==============

@api_router.get("/daily-logs/{dog_id}", response_model=List[DailyLog])
async def get_daily_logs(dog_id: str, current_user: dict = Depends(get_current_user)):
    """Get daily logs for a dog. RLS enforces ownership."""
    # Check dog ownership
    check_response = supabase.table('dogs').select('id').eq('id', dog_id).eq('owner_id', current_user['id']).execute()
    if not check_response.data:
        raise HTTPException(status_code=404, detail="Dog not found")
    
    response = supabase.table('daily_logs').select('*').eq('dog_id', dog_id).order('logged_at', desc=True).limit(100).execute()
    return [DailyLog(**log) for log in response.data]

@api_router.get("/daily-logs/{dog_id}/today")
async def get_today_log(dog_id: str, current_user: dict = Depends(get_current_user)):
    """Get today's log for a dog."""
    check_response = supabase.table('dogs').select('id').eq('id', dog_id).eq('owner_id', current_user['id']).execute()
    if not check_response.data:
        raise HTTPException(status_code=404, detail="Dog not found")
    
    today = date.today().isoformat()
    response = supabase.table('daily_logs').select('*').eq('dog_id', dog_id).eq('date', today).execute()
    return DailyLog(**response.data[0]) if response.data else None

@api_router.post("/daily-logs", response_model=DailyLog)
async def create_daily_log(log_data: DailyLogCreate, current_user: dict = Depends(get_current_user)):
    """Create daily log. RLS enforces dog ownership."""
    # Check dog ownership
    check_response = supabase.table('dogs').select('id').eq('id', log_data.dog_id).eq('owner_id', current_user['id']).execute()
    if not check_response.data:
        raise HTTPException(status_code=404, detail="Dog not found")
    
    today = date.today().isoformat()
    
    # Check for existing log today
    existing_response = supabase.table('daily_logs').select('id').eq('dog_id', log_data.dog_id).eq('date', today).execute()
    if existing_response.data:
        raise HTTPException(status_code=400, detail="Already logged for today")
    
    # Create log
    log_dict = log_data.model_dump()
    log_dict['date'] = today
    log_dict['logged_at'] = datetime.utcnow().isoformat()
    
    response = supabase.table('daily_logs').insert(log_dict).execute()
    
    # Update healthspan stats (trigger handles this in Supabase, but call manually for consistency)
    await update_healthspan_stats(log_data.dog_id, current_user['id'])
    
    return DailyLog(**response.data[0])

# ============== Healthspan Routes ==============

async def update_healthspan_stats(dog_id: str, owner_id: str):
    """Update healthspan stats for a dog."""
    logs_response = supabase.table('daily_logs').select('*').eq('dog_id', dog_id).order('date', desc=True).limit(365).execute()
    logs = logs_response.data
    
    streak = 0
    today = date.today()
    for i, log in enumerate(logs):
        expected_date = (today - timedelta(days=i)).isoformat()
        if log.get("date") == expected_date:
            streak += 1
        else:
            break
    
    total_points = len(logs) * 10
    
    weekly_scores = []
    for i in range(7):
        day_date = (today - timedelta(days=6-i)).isoformat()
        day_log = next((l for l in logs if l.get("date") == day_date), None)
        score = calculate_day_score(day_log) if day_log else 0
        weekly_scores.append({
            "date": day_date,
            "score": score
        })
    
    # Check if stats exist
    existing = supabase.table('healthspan_stats').select('id').eq('dog_id', dog_id).execute()
    
    stats = {
        "dog_id": dog_id,
        "total_points": total_points,
        "streak": streak,
        "weekly_scores": weekly_scores,
        "calculated_at": datetime.utcnow().isoformat()
    }
    
    if existing.data:
        supabase.table('healthspan_stats').update(stats).eq('dog_id', dog_id).execute()
    else:
        stats["current_score"] = 85
        supabase.table('healthspan_stats').insert(stats).execute()

@api_router.get("/healthspan/{dog_id}", response_model=HealthspanScore)
async def get_healthspan(dog_id: str, current_user: dict = Depends(get_current_user)):
    """Get healthspan score for a dog."""
    dog_response = supabase.table('dogs').select('id').eq('id', dog_id).eq('owner_id', current_user['id']).execute()
    if not dog_response.data:
        raise HTTPException(status_code=404, detail="Dog not found")
    
    stats_response = supabase.table('healthspan_stats').select('*').eq('dog_id', dog_id).execute()
    
    if not stats_response.data:
        return HealthspanScore(
            dog_id=dog_id,
            score=85,
            streak=0,
            total_points=0,
            breed_rank=50,
            weekly_scores=[]
        )
    
    stats = stats_response.data[0]
    
    # Get latest log for current score
    latest_log_response = supabase.table('daily_logs').select('*').eq('dog_id', dog_id).order('logged_at', desc=True).limit(1).execute()
    current_score = calculate_day_score(latest_log_response.data[0]) if latest_log_response.data else 85
    
    # Calculate rank
    rank_response = supabase.table('healthspan_stats').select('total_points').gt('total_points', stats.get('total_points', 0)).execute()
    breed_rank = len(rank_response.data) + 1
    
    return HealthspanScore(
        dog_id=dog_id,
        score=current_score,
        streak=stats.get('streak', 0),
        total_points=stats.get('total_points', 0),
        breed_rank=breed_rank,
        weekly_scores=stats.get('weekly_scores', [])
    )

# ============== Lilo AI Routes ==============

async def generate_ai_insights(dog: dict, logs: List[dict]) -> dict:
    """Generate AI-powered insights using GPT."""
    llm_key = os.environ.get('OPENAI_API_KEY')
    if not llm_key:
        raise HTTPException(status_code=500, detail="AI service not configured")
    
    dog_info = f"""
Dog Profile:
- Name: {dog.get('name', 'Unknown')}
- Breed: {dog.get('breed', 'Unknown')}
- Age/DOB: {dog.get('date_of_birth', 'Unknown')}
- Weight: {dog.get('weight_lbs', 'Unknown')} lbs
- Activity Level: {dog.get('activity_level', 'Unknown')}
"""
    
    logs_summary = "Recent Health Logs (last 7 days):\n"
    for log in logs[:7]:
        logs_summary += f"- {log.get('date', 'Unknown')}: Mood={log.get('mood', 'N/A')}, Exercise={log.get('exercise_level', 'N/A')}, Nutrition={log.get('nutrition_quality', 'N/A')}\n"
    
    if not logs:
        logs_summary = "No recent health logs available."
    
    chat = LlmChat(
        api_key=llm_key,
        session_id=f"lilo-{dog.get('id', 'unknown')}-{datetime.utcnow().isoformat()}",
        system_message="""You are Lilo, a friendly and knowledgeable AI companion for dog health. 
You provide personalized, actionable health insights based on dog profiles and daily health logs.
Be warm, encouraging, and specific to the dog's breed and individual characteristics.
Always provide practical recommendations that dog owners can implement.
Keep responses concise but informative."""
    ).with_model("openai", "gpt-5.2")
    
    prompt = f"""Based on the following dog profile and recent health logs, provide a health report.

{dog_info}

{logs_summary}

Please provide:
1. A brief overall mood assessment (one word: Excellent, Good, Fair, or Low)
2. A 2-3 sentence summary of {dog.get('name', 'the dog')}'s health this week
3. 3 specific insights based on the data (trends, patterns, or observations)
4. 1 actionable recommendation for the owner

Format your response as JSON with these exact keys:
{{"mood": "...", "summary": "...", "insights": ["...", "...", "..."], "recommendation": "..."}}

Only output the JSON, nothing else."""

    try:
        user_message = UserMessage(text=prompt)
        response = await chat.send_message(user_message)
        
        import json
        response_text = response.strip()
        if response_text.startswith("```json"):
            response_text = response_text[7:]
        if response_text.startswith("```"):
            response_text = response_text[3:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]
        
        return json.loads(response_text.strip())
    except Exception as e:
        logger.error(f"AI generation error: {e}")
        return {
            "mood": "Good",
            "summary": f"{dog.get('name', 'Your dog')} is maintaining a healthy routine. Keep up the good work!",
            "insights": [
                "Regular logging helps track health patterns",
                "Consistency in daily routines benefits your dog's wellbeing",
                "Consider varying activities to keep your dog engaged"
            ],
            "recommendation": "Continue with your current routine and watch for any changes in behavior or appetite."
        }

@api_router.get("/lilo-ai/{dog_id}", response_model=List[LiloReport])
@limiter.limit("30/minute")
async def get_lilo_reports(request: Request, dog_id: str, current_user: dict = Depends(require_premium)):
    """Get Lilo AI reports for a dog. Premium feature."""
    dog_response = supabase.table('dogs').select('id').eq('id', dog_id).eq('owner_id', current_user['id']).execute()
    if not dog_response.data:
        raise HTTPException(status_code=404, detail="Dog not found")
    
    response = supabase.table('lilo_reports').select('*').eq('dog_id', dog_id).order('created_at', desc=True).limit(30).execute()
    return [LiloReport(**report) for report in response.data]

@api_router.post("/lilo-ai/{dog_id}", response_model=LiloReport)
@limiter.limit("5/minute")
async def generate_lilo_report(request: Request, dog_id: str, current_user: dict = Depends(require_premium)):
    """Generate new Lilo AI report. Premium feature."""
    dog_response = supabase.table('dogs').select('*').eq('id', dog_id).eq('owner_id', current_user['id']).execute()
    if not dog_response.data:
        raise HTTPException(status_code=404, detail="Dog not found")
    
    dog = dog_response.data[0]
    
    recent_logs_response = supabase.table('daily_logs').select('*').eq('dog_id', dog_id).order('logged_at', desc=True).limit(7).execute()
    recent_logs = recent_logs_response.data
    
    ai_response = await generate_ai_insights(dog, recent_logs)
    
    import random
    healthspan_delta = random.uniform(-0.5, 2.0) if recent_logs else 0
    
    report_data = {
        "dog_id": dog_id,
        "mood": ai_response.get("mood", "Good"),
        "summary": ai_response.get("summary", f"{dog['name']} is doing well."),
        "insights": ai_response.get("insights", ["Keep up the great work!"]),
        "recommendation": ai_response.get("recommendation", "Continue your current routine."),
        "healthspan_delta": round(healthspan_delta, 2)
    }
    
    response = supabase.table('lilo_reports').insert(report_data).execute()
    return LiloReport(**response.data[0])

# ============== Lilo Swarm Routes (Enhanced AI) ==============

from lilo_swarm import create_enhanced_swarm, SwarmReport, AgentSelector
from dataclasses import asdict

@api_router.get("/lilo-swarm/{dog_id}/preview")
async def get_swarm_preview(
    request: Request,
    dog_id: str,
    mode: str = "quick",
    current_user: dict = Depends(get_current_user)
):
    """
    Quick swarm analysis preview.
    
    Modes:
    - quick: 3 agents (activity, nutrition, mood) - Free
    - minimal: 1 agent (mood only) - Free, fastest
    - auto: Context-based selection - Free
    """
    # Verify dog ownership
    dog_response = supabase.table('dogs').select('*').eq('id', dog_id).eq('owner_id', current_user['id']).execute()
    if not dog_response.data:
        raise HTTPException(status_code=404, detail="Dog not found")
    
    dog = dog_response.data[0]
    
    # Get recent logs
    logs_response = supabase.table('daily_logs').select('*').eq('dog_id', dog_id).order('logged_at', desc=True).limit(7).execute()
    recent_logs = logs_response.data
    
    # Build context
    context = {
        "dog": dog,
        "recent_logs": recent_logs,
        "activity_data": {"avg_active_minutes": sum(l.get('active_minutes', 0) for l in recent_logs) / max(len(recent_logs), 1)},
        "mood_data": {"moods": [l.get('mood') for l in recent_logs]}
    }
    
    try:
        swarm = create_enhanced_swarm()
        quick_result = await swarm.quick_analyze(context)
        return {
            **quick_result,
            "mode": mode,
            "learnings_count": len(swarm.get_dog_learnings(dog_id))
        }
    except Exception as e:
        logger.error(f"Swarm preview error: {e}")
        raise HTTPException(status_code=503, detail="Swarm analysis temporarily unavailable")


@api_router.post("/lilo-swarm/{dog_id}")
async def generate_swarm_report(
    request: Request,
    dog_id: str,
    mode: str = "auto",
    current_user: dict = Depends(require_premium)
):
    """
    Generate swarm wellness report with ephemeral agents and learning.
    
    Modes:
    - auto: Context-based selection (recommended)
    - quick: 3 agents for faster response
    - full: All 7 agents for maximum depth
    - minimal: 1 agent, fastest
    
    Premium feature.
    """
    # Verify dog ownership
    dog_response = supabase.table('dogs').select('*').eq('id', dog_id).eq('owner_id', current_user['id']).execute()
    if not dog_response.data:
        raise HTTPException(status_code=404, detail="Dog not found")
    
    dog = dog_response.data[0]
    
    # Get recent logs (last 30 days)
    logs_response = supabase.table('daily_logs').select('*').eq('dog_id', dog_id).order('logged_at', desc=True).limit(30).execute()
    recent_logs = logs_response.data
    
    # Get healthspan stats
    stats_response = supabase.table('healthspan_stats').select('*').eq('dog_id', dog_id).order('date', desc=True).limit(1).execute()
    healthspan_stats = stats_response.data[0] if stats_response.data else {}
    
    # Get leaderboard entry
    lb_response = supabase.table('leaderboard_entries').select('*').eq('dog_id', dog_id).execute()
    leaderboard_entry = lb_response.data[0] if lb_response.data else {}
    
    # Build full context
    context = {
        "dog": dog,
        "recent_logs": recent_logs,
        "healthspan_stats": healthspan_stats,
        "leaderboard_entry": {
            "rank": leaderboard_entry.get('rank', 0),
            "total_points": leaderboard_entry.get('total_points', 0),
            "streak": leaderboard_entry.get('streak', 0),
            "score": leaderboard_entry.get('current_score', 85),
            "total": 100
        },
        "environment_data": {
            "location": "User location",
            "weather_summary": "Current conditions",
            "aqi": "Good"
        },
        "breed_data": {
            "traits": "Standard",
            "common_issues": [],
            "ideal_weight_range": " breed appropriate"
        }
    }
    
    try:
        swarm = create_enhanced_swarm()
        report = await swarm.analyze(context, mode=mode)
        
        # Store report in database
        report_data = {
            "dog_id": dog_id,
            "mood": report.overall_mood,
            "summary": report.summary,
            "insights": json.dumps([asdict(i) for i in report.insights]),
            "recommendation": ", ".join(report.key_recommendations),
            "healthspan_delta": report.healthspan_delta
        }
        
        stored = supabase.table('lilo_reports').insert(report_data).execute()
        
        return {
            "report_id": stored.data[0]['id'] if stored.data else None,
            "dog_name": report.dog_name,
            "overall_mood": report.overall_mood,
            "overall_score": report.overall_score,
            "healthspan_delta": report.healthspan_delta,
            "summary": report.summary,
            "key_recommendations": report.key_recommendations,
            "warnings": report.warnings,
            "insights": [asdict(i) for i in report.insights],
            "agent_count": report.agent_count,
            "analysis_duration_ms": report.analysis_duration_ms,
            "model_used": report.model_used,
            "mode_used": mode,
            "learnings_count": len(swarm.get_dog_learnings(dog_id)),
            "generated_at": report.generated_at.isoformat()
        }
        
    except Exception as e:
        logger.error(f"Swarm report error: {e}")
        raise HTTPException(status_code=503, detail="Swarm analysis temporarily unavailable")


@api_router.get("/lilo-swarm/{dog_id}/learnings")
async def get_swarm_learnings(
    dog_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get all learned patterns for a dog's swarm."""
    # Verify dog ownership
    dog_response = supabase.table('dogs').select('*').eq('id', dog_id).eq('owner_id', current_user['id']).execute()
    if not dog_response.data:
        raise HTTPException(status_code=404, detail="Dog not found")
    
    try:
        swarm = create_enhanced_swarm()
        learnings = swarm.get_dog_learnings(dog_id)
        return {
            "dog_id": dog_id,
            "dog_name": dog_response.data[0].get("name"),
            "learnings_count": len(learnings),
            "learnings": learnings
        }
    except Exception as e:
        logger.error(f"Get learnings error: {e}")
        raise HTTPException(status_code=503, detail="Could not retrieve learnings")


@api_router.post("/lilo-swarm/{dog_id}/validate")
async def validate_learning(
    dog_id: str,
    validation: dict,
    current_user: dict = Depends(get_current_user)
):
    """
    Validate a learned pattern based on user feedback.
    
    Body: {"pattern": "...", "accepted": true/false}
    """
    # Verify dog ownership
    dog_response = supabase.table('dogs').select('*').eq('id', dog_id).eq('owner_id', current_user['id']).execute()
    if not dog_response.data:
        raise HTTPException(status_code=404, detail="Dog not found")
    
    pattern = validation.get("pattern", "")
    accepted = validation.get("accepted", True)
    
    if not pattern:
        raise HTTPException(status_code=400, detail="Pattern is required")
    
    try:
        swarm = create_enhanced_swarm()
        swarm.validate_learning(dog_id, pattern, accepted)
        return {
            "success": True,
            "dog_id": dog_id,
            "pattern": pattern,
            "accepted": accepted,
            "message": "Learning validated and updated" if accepted else "Learning invalidated"
        }
    except Exception as e:
        logger.error(f"Validate learning error: {e}")
        raise HTTPException(status_code=503, detail="Could not validate learning")


# ============== Activity Forecasting Routes (ruv-FANN Inspired) ==============

from activity_forecaster import (
    create_forecaster,
    create_recovery_forecaster,
    logs_to_datapoints
)

@api_router.get("/activity-forecast/{dog_id}")
async def get_activity_forecast(
    request: Request,
    dog_id: str,
    days: int = 7,
    current_user: dict = Depends(get_current_user)
):
    """
    Get activity forecast for a dog.
    
    Uses time-series analysis to predict future activity patterns.
    Free feature - great for motivation!
    
    Args:
        days: Number of days to forecast (default: 7, max: 14)
    """
    # Verify dog ownership
    dog_response = supabase.table('dogs').select('*').eq('id', dog_id).eq('owner_id', current_user['id']).execute()
    if not dog_response.data:
        raise HTTPException(status_code=404, detail="Dog not found")
    
    dog = dog_response.data[0]
    
    # Get historical activity logs (last 30 days)
    logs_response = supabase.table('daily_logs').select('*').eq('dog_id', dog_id).order('logged_at', desc=True).limit(30).execute()
    logs = logs_response.data
    
    if len(logs) < 3:
        return {
            "error": "insufficient_data",
            "message": f"Need at least 3 days of data. Currently have {len(logs)} days.",
            "days_needed": 3 - len(logs),
            "dog_name": dog.get("name")
        }
    
    # Convert to data points
    data_points = logs_to_datapoints(logs)
    
    # Generate forecast
    forecaster = create_forecaster()
    forecast = forecaster.forecast(
        dog_id=dog_id,
        dog_name=dog.get("name", "Unknown"),
        data_points=data_points,
        forecast_days=min(days, 14)  # Cap at 14 days
    )
    
    return {
        "forecast_id": f"forecast_{dog_id}_{datetime.utcnow().strftime('%Y%m%d')}",
        "dog_id": dog_id,
        "dog_name": forecast.dog_name,
        "generated_at": forecast.generated_at.isoformat(),
        "analysis": {
            "days_analyzed": forecast.days_analyzed,
            "avg_daily_minutes": forecast.avg_daily_minutes,
            "avg_daily_steps": forecast.avg_daily_steps,
            "activity_trend": forecast.activity_trend,
            "consistency_score": forecast.consistency_score,
            "best_day": forecast.best_day,
            "cycle_detected": forecast.cycle_detected
        },
        "predictions": [
            {
                "date": f.date,
                "predicted_minutes": f.predicted_minutes,
                "confidence": f.confidence,
                "trend": f.trend,
                "factors": f.factors
            }
            for f in forecast.forecast
        ],
        "anomalies": forecast.anomalies,
        "recommendations": forecast.recommendations
    }


@api_router.get("/activity-forecast/{dog_id}/summary")
async def get_forecast_summary(
    dog_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Get a quick forecast summary without full details.
    Perfect for dashboard widgets.
    """
    # Verify dog ownership
    dog_response = supabase.table('dogs').select('*').eq('id', dog_id).eq('owner_id', current_user['id']).execute()
    if not dog_response.data:
        raise HTTPException(status_code=404, detail="Dog not found")
    
    dog = dog_response.data[0]
    
    # Get recent logs
    logs_response = supabase.table('daily_logs').select('*').eq('dog_id', dog_id).order('logged_at', desc=True).limit(14).execute()
    logs = logs_response.data
    
    if len(logs) < 3:
        return {
            "trend": "unknown",
            "prediction_tomorrow": None,
            "confidence": 0,
            "message": "Need more data"
        }
    
    data_points = logs_to_datapoints(logs)
    forecaster = create_forecaster()
    forecast = forecaster.forecast(dog_id, dog.get("name", "Unknown"), data_points, 1)
    
    tomorrow = forecast.forecast[0] if forecast.forecast else None
    
    return {
        "dog_name": forecast.dog_name,
        "trend": forecast.activity_trend,
        "prediction_tomorrow": tomorrow.predicted_minutes if tomorrow else None,
        "confidence": tomorrow.confidence if tomorrow else 0,
        "consistency": forecast.consistency_score,
        "best_day": forecast.best_day,
        "recommendation": forecast.recommendations[0] if forecast.recommendations else None
    }


@api_router.get("/recovery-estimate/{dog_id}")
async def get_recovery_estimate(
    dog_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Estimate recovery time for a dog.
    
    Based on age, health history, and current wellness score.
    Premium feature.
    """
    # Verify premium access
    if not current_user.get("is_premium", False):
        raise HTTPException(status_code=403, detail="Premium feature")
    
    # Verify dog ownership
    dog_response = supabase.table('dogs').select('*').eq('id', dog_id).eq('owner_id', current_user['id']).execute()
    if not dog_response.data:
        raise HTTPException(status_code=404, detail="Dog not found")
    
    dog = dog_response.data[0]
    
    # Get healthspan stats
    stats_response = supabase.table('healthspan_stats').select('*').eq('dog_id', dog_id).order('date', desc=True).limit(1).execute()
    health_score = 80.0  # Default
    if stats_response.data:
        health_score = stats_response.data[0].get('current_score', 80.0)
    
    # Calculate recovery estimate
    recovery_forecaster = create_recovery_forecaster()
    estimate = recovery_forecaster.estimate_recovery(
        dog_age=dog.get('age_years', 3),
        previous_recovery_days=[],  # Would need historical data
        current_health_score=health_score
    )
    
    return {
        "dog_id": dog_id,
        "dog_name": dog.get('name'),
        "dog_age": dog.get('age_years'),
        "current_health_score": health_score,
        "recovery_estimate": estimate
    }


# ============== Photo Mood Analysis Routes ==============

from photo_mood_analyzer import create_photo_analyzer, create_photo_analysis_agent
from pydantic import BaseModel

class PhotoAnalysisRequest(BaseModel):
    photo_data: str  # Base64 encoded image
    photo_id: Optional[str] = None

@api_router.post("/photos/{dog_id}/analyze")
async def analyze_dog_photo(
    request: Request,
    dog_id: str,
    analysis_request: PhotoAnalysisRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Analyze a dog photo for mood and wellness indicators.
    
    Accepts base64-encoded images and returns mood analysis.
    Premium feature - requires subscription.
    """
    # Verify premium access
    if not current_user.get("is_premium", False):
        raise HTTPException(status_code=403, detail="Premium feature")
    
    # Verify dog ownership
    dog_response = supabase.table('dogs').select('*').eq('id', dog_id).eq('owner_id', current_user['id']).execute()
    if not dog_response.data:
        raise HTTPException(status_code=404, detail="Dog not found")
    
    dog = dog_response.data[0]
    photo_id = analysis_request.photo_id or f"photo_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
    
    try:
        analyzer = create_photo_analyzer()
        analysis = await analyzer.analyze_photo(
            photo_data=analysis_request.photo_data,
            dog_id=dog_id,
            photo_id=photo_id
        )
        
        return {
            "photo_id": photo_id,
            "dog_id": dog_id,
            "dog_name": dog.get('name'),
            "analyzed_at": analysis.analyzed_at.isoformat(),
            "mood": {
                "state": analysis.mood.value,
                "confidence": analysis.mood_confidence,
                "indicators": analysis.mood_indicators
            },
            "energy": {
                "level": analysis.energy_level.value,
                "indicators": analysis.energy_indicators
            },
            "health": {
                "status": analysis.health_status.value,
                "notes": analysis.health_notes
            },
            "physical": {
                "posture_score": analysis.posture_score,
                "eye_clarity": analysis.eye_clarity,
                "coat_condition": analysis.coat_condition,
                "apparent_weight": analysis.apparent_weight
            },
            "wellness_score": analysis.overall_wellness_score,
            "recommendations": analysis.recommendations,
            "warnings": analysis.warnings,
            "analysis_method": analysis.analysis_method
        }
        
    except Exception as e:
        logger.error(f"Photo analysis error: {e}")
        raise HTTPException(status_code=503, detail="Photo analysis failed")


@api_router.get("/photos/{dog_id}/mood-history")
async def get_mood_history(
    dog_id: str,
    days: int = 7,
    current_user: dict = Depends(get_current_user)
):
    """
    Get aggregated mood history from photo analyses.
    
    Returns trend analysis and insights from recent photo analyses.
    """
    # Verify dog ownership
    dog_response = supabase.table('dogs').select('*').eq('id', dog_id).eq('owner_id', current_user['id']).execute()
    if not dog_response.data:
        raise HTTPException(status_code=404, detail="Dog not found")
    
    dog = dog_response.data[0]
    
    # For now, return mock data
    # In production, this would query stored photo analyses
    return {
        "dog_id": dog_id,
        "dog_name": dog.get('name'),
        "period_days": days,
        "photo_count": 0,
        "message": "Photo mood history will be available after analyzing photos",
        "dominant_mood": "unknown",
        "mood_trend": "stable",
        "insights": ["Upload photos to build mood history"]
    }


@api_router.post("/photos/{dog_id}/analyze-quick")
async def quick_photo_check(
    request: Request,
    dog_id: str,
    analysis_request: PhotoAnalysisRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Quick photo mood check - simplified analysis.
    
    Free feature - basic mood assessment only.
    """
    # Verify dog ownership
    dog_response = supabase.table('dogs').select('*').eq('id', dog_id).eq('owner_id', current_user['id']).execute()
    if not dog_response.data:
        raise HTTPException(status_code=404, detail="Dog not found")
    
    try:
        analyzer = create_photo_analyzer()
        analysis = await analyzer.analyze_photo(
            photo_data=analysis_request.photo_data,
            dog_id=dog_id
        )
        
        return {
            "dog_id": dog_id,
            "mood": analysis.mood.value,
            "mood_confidence": analysis.mood_confidence,
            "energy": analysis.energy_level.value,
            "quick_summary": f"{dog.get('name')} appears {analysis.mood.value}",
            "recommendation": analysis.recommendations[0] if analysis.recommendations else None
        }
        
    except Exception as e:
        logger.error(f"Quick photo analysis error: {e}")
        raise HTTPException(status_code=503, detail="Analysis failed")


# ============== Stripe Payment Routes ==============

@api_router.get("/subscription/plans")
async def get_subscription_plans():
    """Get available subscription plans"""
    return SUBSCRIPTION_PLANS

@api_router.post("/subscription/checkout")
async def create_checkout_session(request: CheckoutRequest, http_request: Request, current_user: dict = Depends(get_current_user)):
    """Create a Stripe checkout session for subscription."""
    
    if request.plan_id not in SUBSCRIPTION_PLANS:
        raise HTTPException(status_code=400, detail="Invalid subscription plan")
    
    plan = SUBSCRIPTION_PLANS[request.plan_id]
    amount = plan["price"]
    
    stripe_api_key = os.environ.get('STRIPE_API_KEY')
    if not stripe_api_key:
        raise HTTPException(status_code=500, detail="Payment service not configured")
    
    success_url = f"{request.origin_url}/subscription/success?session_id={{CHECKOUT_SESSION_ID}}"
    cancel_url = f"{request.origin_url}/subscription/cancel"
    
    host_url = str(http_request.base_url)
    webhook_url = f"{host_url}api/v1/webhook/stripe"
    stripe_checkout = StripeCheckout(api_key=stripe_api_key, webhook_url=webhook_url)
    
    checkout_request = CheckoutSessionRequest(
        amount=amount,
        currency="usd",
        success_url=success_url,
        cancel_url=cancel_url,
        metadata={
            "user_id": current_user["id"],
            "plan_id": request.plan_id,
            "plan_name": plan["name"]
        }
    )
    
    session = await stripe_checkout.create_checkout_session(checkout_request)
    
    # Create payment transaction record
    transaction_data = {
        "user_id": current_user["id"],
        "session_id": session.session_id,
        "plan_id": request.plan_id,
        "amount": amount,
        "status": "initiated",
        "payment_status": "pending"
    }
    
    supabase_admin.table('payment_transactions').insert(transaction_data).execute()
    
    return {
        "checkout_url": session.url,
        "session_id": session.session_id
    }

@api_router.get("/subscription/status/{session_id}")
async def get_checkout_status(session_id: str, current_user: dict = Depends(get_current_user)):
    """Check the status of a checkout session."""
    stripe_api_key = os.environ.get('STRIPE_API_KEY')
    if not stripe_api_key:
        raise HTTPException(status_code=500, detail="Payment service not configured")
    
    stripe_checkout = StripeCheckout(api_key=stripe_api_key, webhook_url="")
    
    try:
        status = await stripe_checkout.get_checkout_status(session_id)
        
        # Update transaction
        transaction_response = supabase_admin.table('payment_transactions').select('*').eq('session_id', session_id).execute()
        
        if transaction_response.data and transaction_response.data[0].get("payment_status") != "paid":
            update_data = {
                "status": status.status,
                "payment_status": status.payment_status,
                "updated_at": datetime.utcnow().isoformat()
            }
            
            supabase_admin.table('payment_transactions').update(update_data).eq('session_id', session_id).execute()
            
            if status.payment_status == "paid":
                plan_id = status.metadata.get("plan_id", "monthly")
                plan = SUBSCRIPTION_PLANS.get(plan_id, SUBSCRIPTION_PLANS["monthly"])
                
                if plan["period"] == "month":
                    expires = datetime.utcnow() + timedelta(days=30)
                else:
                    expires = datetime.utcnow() + timedelta(days=365)
                
                supabase_admin.table('user_profiles').update({
                    "is_premium": True,
                    "subscription_status": "active",
                    "subscription_plan": plan_id,
                    "subscription_expires": expires.isoformat(),
                    "updated_at": datetime.utcnow().isoformat()
                }).eq('id', current_user["id"]).execute()
        
        return {
            "status": status.status,
            "payment_status": status.payment_status,
            "amount_total": status.amount_total,
            "currency": status.currency
        }
    except Exception as e:
        logger.error(f"Error checking checkout status: {e}")
        raise HTTPException(status_code=500, detail="Failed to check payment status")

@api_router.get("/subscription/current")
async def get_current_subscription(current_user: dict = Depends(get_current_user)):
    """Get current user's subscription status."""
    return {
        "is_premium": current_user.get("is_premium", False),
        "subscription_status": current_user.get("subscription_status"),
        "subscription_plan": current_user.get("subscription_plan"),
        "subscription_expires": current_user.get("subscription_expires")
    }

@api_router.post("/webhook/stripe")
async def stripe_webhook(request: Request):
    """Handle Stripe webhooks."""
    stripe_api_key = os.environ.get('STRIPE_API_KEY')
    if not stripe_api_key:
        raise HTTPException(status_code=500, detail="Payment service not configured")
    
    body = await request.body()
    signature = request.headers.get("Stripe-Signature", "")
    
    try:
        stripe_checkout = StripeCheckout(api_key=stripe_api_key, webhook_url="")
        webhook_response = await stripe_checkout.handle_webhook(body, signature)
        
        if webhook_response.session_id:
            supabase_admin.table('payment_transactions').update({
                "status": webhook_response.event_type,
                "payment_status": webhook_response.payment_status,
                "updated_at": datetime.utcnow().isoformat()
            }).eq('session_id', webhook_response.session_id).execute()
        
        return {"received": True}
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return {"received": True}

# ============== Dog Breeds ==============

DOG_BREEDS = [
    "Golden Retriever", "Labrador Retriever", "German Shepherd", "French Bulldog",
    "Bulldog", "Poodle", "Beagle", "Rottweiler", "Yorkshire Terrier", "Boxer",
    "Dachshund", "Siberian Husky", "Great Dane", "Doberman Pinscher", "Shih Tzu",
    "Boston Terrier", "Bernese Mountain Dog", "Pomeranian", "Havanese", "Cavalier King Charles Spaniel",
    "Border Collie", "Australian Shepherd", "Cocker Spaniel", "Maltese", "Chihuahua",
    "Mixed Breed", "Other"
]

@api_router.get("/dog-breeds")
async def get_dog_breeds():
    return DOG_BREEDS

# ============== Food Safety ==============

TOXIC_FOODS = {
    "chocolate": {"toxic": True, "severity": "high", "reason": "Contains theobromine which is toxic to dogs"},
    "grapes": {"toxic": True, "severity": "high", "reason": "Can cause kidney failure"},
    "raisins": {"toxic": True, "severity": "high", "reason": "Can cause kidney failure"},
    "onions": {"toxic": True, "severity": "medium", "reason": "Can cause anemia"},
    "garlic": {"toxic": True, "severity": "medium", "reason": "Can cause anemia in large amounts"},
    "xylitol": {"toxic": True, "severity": "high", "reason": "Can cause liver failure and hypoglycemia"},
    "avocado": {"toxic": True, "severity": "low", "reason": "Contains persin which can cause vomiting"},
    "macadamia nuts": {"toxic": True, "severity": "medium", "reason": "Can cause weakness and vomiting"},
    "alcohol": {"toxic": True, "severity": "high", "reason": "Can cause intoxication, coma, or death"},
    "caffeine": {"toxic": True, "severity": "high", "reason": "Can cause restlessness, rapid breathing, and heart palpitations"},
    "chicken": {"toxic": False, "severity": "none", "reason": "Safe when cooked and boneless"},
    "carrots": {"toxic": False, "severity": "none", "reason": "Healthy snack, good for teeth"},
    "apples": {"toxic": False, "severity": "none", "reason": "Safe without seeds and core"},
    "blueberries": {"toxic": False, "severity": "none", "reason": "Rich in antioxidants"},
    "peanut butter": {"toxic": False, "severity": "none", "reason": "Safe if xylitol-free"},
    "rice": {"toxic": False, "severity": "none", "reason": "Easy to digest, good for upset stomach"},
    "pumpkin": {"toxic": False, "severity": "none", "reason": "Good for digestion"},
    "sweet potato": {"toxic": False, "severity": "none", "reason": "Healthy and nutritious"},
    "salmon": {"toxic": False, "severity": "none", "reason": "Rich in omega-3, cook thoroughly"},
    "eggs": {"toxic": False, "severity": "none", "reason": "Great protein source when cooked"},
}

@api_router.get("/food-search")
@limiter.limit("30/minute")
async def search_food(request: Request, query: str, current_user: dict = Depends(require_premium)):
    """Search food safety database. Premium feature."""
    query_lower = query.lower()
    results = []
    
    for food, info in TOXIC_FOODS.items():
        if query_lower in food:
            results.append({
                "food": food,
                "safe": not info["toxic"],
                "severity": info["severity"],
                "reason": info["reason"]
            })
    
    if not results:
        return {"message": f"No information found for '{query}'. When in doubt, consult your vet."}
    
    return results

# ============== External API Services ==============

@api_router.get("/breeds/search")
async def api_search_breeds(q: str, limit: int = 10):
    """Search dog breeds by name (Free feature)."""
    breeds = await search_breeds(q)
    return {"breeds": breeds[:limit]}

@api_router.get("/breeds/{breed_id}/insights")
async def api_get_breed_insights(breed_id: str, current_user: dict = Depends(get_current_user)):
    """Get health insights for a specific breed."""
    breed = await get_breed_by_id(breed_id)
    if not breed:
        search_results = await search_breeds(breed_id)
        if search_results:
            breed = search_results[0]
        else:
            raise HTTPException(status_code=404, detail="Breed not found")
    
    insights = get_breed_health_insights(breed)
    return insights

@api_router.post("/foods/search")
@limiter.limit("30/minute")
async def api_search_foods_usda(request: Request, query: str, limit: int = 10, current_user: dict = Depends(require_premium)):
    """Search foods using USDA database. Premium feature."""
    foods = await search_foods(query, limit)
    results = [analyze_food_for_dogs(food) for food in foods]
    return {"foods": results}

@api_router.get("/foods/{fdc_id}")
@limiter.limit("30/minute")
async def api_get_food_details(request: Request, fdc_id: str, current_user: dict = Depends(require_premium)):
    """Get detailed nutrition info for a specific food. Premium feature."""
    food = await get_food_by_id(fdc_id)
    if not food:
        raise HTTPException(status_code=404, detail="Food not found")
    
    analysis = analyze_food_for_dogs(food)
    return analysis

@api_router.get("/weather/current")
async def api_get_weather(lat: float, lon: float, current_user: dict = Depends(get_current_user)):
    """Get current weather and walk recommendations. FREE for all users."""
    weather = await get_current_weather(lat, lon)
    if not weather:
        raise HTTPException(status_code=503, detail="Weather service unavailable")
    
    analysis = analyze_walk_conditions(weather)
    return {
        "weather": weather,
        "walk_analysis": analysis
    }

@api_router.get("/weather/forecast")
async def api_get_weather_forecast(lat: float, lon: float, hours: int = 24, current_user: dict = Depends(get_current_user)):
    """Get weather forecast with best walk times. FREE for all users."""
    forecast = await get_forecast(lat, lon, hours)
    if not forecast:
        raise HTTPException(status_code=503, detail="Forecast service unavailable")
    
    best_times = find_best_walk_times(forecast)
    
    return {
        "forecast": forecast,
        "best_walk_times": best_times
    }

@api_router.get("/air-quality")
@limiter.limit("30/minute")
async def api_get_air_quality(request: Request, zip_code: str, current_user: dict = Depends(require_premium)):
    """Get air quality index for location. Premium feature."""
    aqi_data = await get_air_quality(zip_code)
    if not aqi_data:
        raise HTTPException(status_code=503, detail="Air quality service unavailable")
    
    analysis = analyze_air_quality(aqi_data)
    return analysis

@api_router.post("/healthspan/calculate")
async def api_calculate_healthspan(
    activity_score: float,
    nutrition_score: float,
    environmental_score: float,
    breed_baseline: float = 85.0,
    current_user: dict = Depends(get_current_user)
):
    """Calculate healthspan score based on multiple factors."""
    result = calculate_healthspan_contribution(
        activity_score,
        nutrition_score,
        environmental_score,
        breed_baseline
    )
    return result

# ============== Root Route ==============

@api_router.get("/")
async def root():
    return {"message": "Welcome to Canine.Fit API", "version": "2.0.0", "database": "Supabase"}

# ============== AI Agent Routes (Admin) ==============

from ai_agents import LeaderboardPopulator, DogProfileGenerator

@api_router.post("/admin/populate-leaderboard")
@limiter.limit("1/minute")
async def populate_leaderboard(
    request: Request,
    generate_photos: bool = True,
    batch_size: int = 3,
    admin_key: str = Header(None, alias="X-Admin-Key")
):
    """Populate leaderboard with AI-generated dog profiles (Admin only)"""
    if not validate_admin_key(admin_key):
        logger.warning(f"Invalid admin key attempt from {request.client.host}")
        raise HTTPException(status_code=403, detail="Invalid admin key")
    
    # Note: AI agent functions need adaptation for Supabase
    # For now, return a message that this needs updating
    return {
        "message": "Leaderboard population requires update for Supabase",
        "note": "AI agent functions need adaptation for Supabase client"
    }

@api_router.post("/admin/update-ai-activity")
@limiter.limit("5/minute")
async def update_ai_activity(
    request: Request,
    admin_key: str = Header(None, alias="X-Admin-Key")
):
    """Update daily activity for AI profiles (Admin only)"""
    if not validate_admin_key(admin_key):
        logger.warning(f"Invalid admin key attempt from {request.client.host}")
        raise HTTPException(status_code=403, detail="Invalid admin key")
    
    return {"message": "AI activity update requires Supabase adaptation"}

@api_router.get("/admin/ai-profiles-count")
@limiter.limit("10/minute")
async def get_ai_profiles_count(
    request: Request,
    admin_key: str = Header(None, alias="X-Admin-Key")
):
    """Get count of AI-generated profiles"""
    if not validate_admin_key(admin_key):
        logger.warning(f"Invalid admin key attempt from {request.client.host}")
        raise HTTPException(status_code=403, detail="Invalid admin key")
    
    dogs_response = supabase_admin.table('dogs').select('id', count='exact').eq('is_ai_profile', True).execute()
    logs_response = supabase_admin.table('daily_logs').select('id', count='exact').eq('is_ai_generated', True).execute()
    
    return {
        "ai_dog_profiles": len(dogs_response.data),
        "ai_daily_logs": len(logs_response.data)
    }

@api_router.delete("/admin/clear-ai-profiles")
@limiter.limit("1/minute")
async def clear_ai_profiles(
    request: Request,
    admin_key: str = Header(None, alias="X-Admin-Key")
):
    """Clear all AI-generated profiles (Admin only)"""
    if not validate_admin_key(admin_key):
        logger.warning(f"Invalid admin key attempt from {request.client.host}")
        raise HTTPException(status_code=403, detail="Invalid admin key")
    
    dogs_deleted = supabase_admin.table('dogs').delete().eq('is_ai_profile', True).execute()
    logs_deleted = supabase_admin.table('daily_logs').delete().eq('is_ai_generated', True).execute()
    stats_deleted = supabase_admin.table('healthspan_stats').delete().eq('is_ai_generated', True).execute()
    reports_deleted = supabase_admin.table('lilo_reports').delete().eq('is_ai_generated', True).execute()
    
    return {
        "deleted": {
            "dogs": len(dogs_deleted.data) if dogs_deleted.data else 0,
            "daily_logs": len(logs_deleted.data) if logs_deleted.data else 0,
            "healthspan_stats": len(stats_deleted.data) if stats_deleted.data else 0,
            "lilo_reports": len(reports_deleted.data) if reports_deleted.data else 0
        }
    }

# ============== Enhanced Leaderboard (Premium) ==============

@api_router.get("/leaderboard/{breed}")
@limiter.limit("30/minute")
async def get_breed_leaderboard(request: Request, breed: str, current_user: dict = Depends(require_premium), limit: int = 50):
    """Get leaderboard for a specific breed. Premium feature."""
    response = supabase.table('leaderboard_entries').select(
        '*, dogs(id, name, breed, avatar_url, owner_id)'
    ).eq('breed', breed).order('total_points', desc=True).limit(limit).execute()
    
    leaderboard = []
    for i, entry in enumerate(response.data):
        dog = entry.get('dogs', {})
        leaderboard.append({
            "rank": i + 1,
            "id": entry.get('dog_id'),
            "name": dog.get('name', 'Unknown'),
            "breed": entry.get('breed'),
            "avatar_url": dog.get('avatar_url'),
            "total_points": entry.get('total_points', 0),
            "streak": entry.get('streak', 0),
            "score": entry.get('current_score', 85),
            "is_ai": dog.get('is_ai_profile', False)
        })
    
    return leaderboard

@api_router.get("/leaderboard")
@limiter.limit("30/minute")
async def get_global_leaderboard(request: Request, current_user: dict = Depends(require_premium), limit: int = 100):
    """Get global leaderboard across all breeds. Premium feature."""
    response = supabase.table('leaderboard_entries').select(
        '*, dogs(id, name, breed, avatar_url, owner_id, is_ai_profile)'
    ).order('total_points', desc=True).limit(limit).execute()
    
    leaderboard = []
    for i, entry in enumerate(response.data):
        dog = entry.get('dogs', {})
        leaderboard.append({
            "rank": i + 1,
            "id": entry.get('dog_id'),
            "name": dog.get('name', 'Unknown'),
            "breed": entry.get('breed'),
            "avatar_url": dog.get('avatar_url'),
            "total_points": entry.get('total_points', 0),
            "streak": entry.get('streak', 0),
            "score": entry.get('current_score', 85),
            "is_ai": entry.get('is_ai_profile', False)
        })
    
    return leaderboard

# Include the router
app.include_router(api_router)

# CORS middleware - restricted to specific origins
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=ALLOWED_ORIGINS,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)

# Security headers middleware
class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        return response

app.add_middleware(SecurityHeadersMiddleware)

@app.on_event("shutdown")
async def shutdown_clients():
    pass  # Supabase client doesn't need explicit cleanup
