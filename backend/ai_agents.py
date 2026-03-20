"""
AI Agent System for Generating Dog Profiles
Creates realistic competitor profiles with AI-generated photos for the leaderboard
"""

import asyncio
import os
import random
import uuid
from datetime import datetime, timedelta, date
from typing import List, Dict, Optional
import logging
import base64

from dotenv import load_dotenv
load_dotenv()

from openai_integration import LlmChat, UserMessage

# Import shared scoring function from server.py
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from server import calculate_day_score

logger = logging.getLogger(__name__)

# Breed popularity weights (higher = more profiles generated)
BREED_POPULARITY = {
    "Golden Retriever": 10,
    "Labrador Retriever": 10,
    "German Shepherd": 8,
    "French Bulldog": 9,
    "Bulldog": 6,
    "Poodle": 7,
    "Beagle": 6,
    "Rottweiler": 5,
    "Yorkshire Terrier": 5,
    "Boxer": 5,
    "Dachshund": 6,
    "Siberian Husky": 7,
    "Great Dane": 4,
    "Doberman Pinscher": 4,
    "Shih Tzu": 5,
    "Boston Terrier": 4,
    "Bernese Mountain Dog": 4,
    "Pomeranian": 5,
    "Border Collie": 6,
    "Australian Shepherd": 6,
    "Cocker Spaniel": 5,
    "Cavalier King Charles Spaniel": 4,
    "Maltese": 4,
    "Chihuahua": 5,
    "Mixed Breed": 8,
}

# Typical weight ranges by breed (in lbs)
BREED_WEIGHTS = {
    "Golden Retriever": (55, 75),
    "Labrador Retriever": (55, 80),
    "German Shepherd": (50, 90),
    "French Bulldog": (16, 28),
    "Bulldog": (40, 50),
    "Poodle": (40, 70),
    "Beagle": (20, 30),
    "Rottweiler": (80, 135),
    "Yorkshire Terrier": (4, 7),
    "Boxer": (50, 80),
    "Dachshund": (16, 32),
    "Siberian Husky": (35, 60),
    "Great Dane": (110, 175),
    "Doberman Pinscher": (60, 100),
    "Shih Tzu": (9, 16),
    "Boston Terrier": (12, 25),
    "Bernese Mountain Dog": (70, 115),
    "Pomeranian": (3, 7),
    "Border Collie": (30, 55),
    "Australian Shepherd": (40, 65),
    "Cocker Spaniel": (20, 30),
    "Cavalier King Charles Spaniel": (12, 18),
    "Maltese": (4, 7),
    "Chihuahua": (3, 6),
    "Mixed Breed": (20, 60),
}


class DogProfileGenerator:
    """AI Agent for generating realistic dog profiles"""
    
    def __init__(self, db):
        self.db = db
        self.api_key = os.getenv('EMERGENT_LLM_KEY')
        
    async def generate_dog_names(self, breed: str, count: int) -> List[str]:
        """Use AI to generate realistic dog names for a breed"""
        chat = LlmChat(
            api_key=self.api_key,
            session_id=f"names-{breed}-{uuid.uuid4()}",
            system_message="You are a helpful assistant that generates realistic dog names."
        ).with_model("openai", "gpt-5.2")
        
        prompt = f"""Generate {count} unique, realistic dog names for {breed} dogs. 
Mix of popular names, cute names, and some creative ones.
Return ONLY the names, one per line, no numbering or extra text."""
        
        try:
            response = await chat.send_message(UserMessage(text=prompt))
            names = [name.strip() for name in response.strip().split('\n') if name.strip()]
            return names[:count]
        except Exception as e:
            logger.error(f"Error generating names: {e}")
            # Fallback names
            fallback = ["Max", "Bella", "Charlie", "Luna", "Cooper", "Daisy", "Buddy", "Sadie", 
                       "Rocky", "Molly", "Duke", "Bailey", "Tucker", "Maggie", "Bear", "Sophie"]
            return random.sample(fallback, min(count, len(fallback)))
    
    async def generate_health_journey(self, dog_name: str, breed: str, age: int, days: int = 30) -> List[Dict]:
        """Generate a realistic health journey with daily logs"""
        chat = LlmChat(
            api_key=self.api_key,
            session_id=f"journey-{dog_name}-{uuid.uuid4()}",
            system_message="You are a veterinary health expert creating realistic dog health data."
        ).with_model("openai", "gpt-5.2")
        
        prompt = f"""Create a {days}-day health journey for {dog_name}, a {age}-year-old {breed}.
Consider breed-specific health patterns and realistic daily variations.

For each day, provide: mood (great/good/okay/tired/unwell), exercise_level (none/light/moderate/active/intense), nutrition_quality (poor/fair/good/excellent)

Format as JSON array:
[{{"day": 1, "mood": "great", "exercise_level": "active", "nutrition_quality": "excellent"}}, ...]

Make it realistic with some variation - dogs have good and bad days. {breed}s typically have {"high energy" if breed in ["Border Collie", "Australian Shepherd", "Siberian Husky", "Labrador Retriever"] else "moderate energy"}.
Only output the JSON array, nothing else."""

        try:
            response = await chat.send_message(UserMessage(text=prompt))
            import json
            # Clean response
            response_text = response.strip()
            if response_text.startswith("```"):
                response_text = response_text.split("```")[1]
                if response_text.startswith("json"):
                    response_text = response_text[4:]
            journey = json.loads(response_text.strip())
            return journey
        except Exception as e:
            logger.error(f"Error generating health journey: {e}")
            # Fallback - generate random but realistic journey
            return self._generate_fallback_journey(days)
    
    def _generate_fallback_journey(self, days: int) -> List[Dict]:
        """Generate fallback health journey data"""
        moods = ["great", "good", "good", "okay", "tired"]  # Weighted towards positive
        exercises = ["light", "moderate", "moderate", "active", "active"]
        nutritions = ["good", "good", "excellent", "excellent", "fair"]
        
        journey = []
        for day in range(1, days + 1):
            journey.append({
                "day": day,
                "mood": random.choice(moods),
                "exercise_level": random.choice(exercises),
                "nutrition_quality": random.choice(nutritions)
            })
        return journey
    
    async def generate_dog_photo(self, breed: str, dog_name: str) -> Optional[str]:
        """Generate AI dog photo using Gemini Nano Banana"""
        try:
            chat = LlmChat(
                api_key=self.api_key,
                session_id=f"photo-{dog_name}-{uuid.uuid4()}",
                system_message="You are an AI that generates beautiful, realistic dog photos."
            ).with_model("gemini", "gemini-3-pro-image-preview").with_params(modalities=["image", "text"])
            
            # Create detailed prompt for realistic dog photo
            prompt = f"""Generate a beautiful, realistic portrait photo of a {breed} dog named {dog_name}. 
The dog should look happy and healthy, with a natural outdoor or home background. 
Professional pet photography style, good lighting, the dog looking at the camera with a friendly expression.
Make it look like a real photo, not cartoon or illustration."""

            msg = UserMessage(text=prompt)
            text, images = await chat.send_message_multimodal_response(msg)
            
            if images and len(images) > 0:
                # Return as base64 data URL
                img_data = images[0]['data']
                mime_type = images[0].get('mime_type', 'image/png')
                return f"data:{mime_type};base64,{img_data}"
            
            return None
        except Exception as e:
            logger.error(f"Error generating dog photo for {dog_name}: {e}")
            return None
    
    async def generate_lilo_insights(self, dog_name: str, breed: str, journey: List[Dict]) -> Dict:
        """Generate AI insights for a dog's health journey"""
        chat = LlmChat(
            api_key=self.api_key,
            session_id=f"insights-{dog_name}-{uuid.uuid4()}",
            system_message="You are Lilo, a friendly AI dog health companion providing personalized insights."
        ).with_model("openai", "gpt-5.2")
        
        # Summarize journey
        mood_counts = {}
        exercise_counts = {}
        for day in journey[-7:]:  # Last 7 days
            mood_counts[day['mood']] = mood_counts.get(day['mood'], 0) + 1
            exercise_counts[day['exercise_level']] = exercise_counts.get(day['exercise_level'], 0) + 1
        
        prompt = f"""Based on {dog_name}'s ({breed}) recent health data:
- Mood distribution (last 7 days): {mood_counts}
- Exercise distribution (last 7 days): {exercise_counts}

Generate a brief, personalized health insight as Lilo AI companion.
Return JSON: {{"mood": "Excellent/Good/Fair/Low", "summary": "2-3 sentence summary", "insights": ["insight1", "insight2", "insight3"], "recommendation": "one actionable tip"}}
Only output JSON."""

        try:
            response = await chat.send_message(UserMessage(text=prompt))
            import json
            response_text = response.strip()
            if response_text.startswith("```"):
                response_text = response_text.split("```")[1]
                if response_text.startswith("json"):
                    response_text = response_text[4:]
            return json.loads(response_text.strip())
        except Exception as e:
            logger.error(f"Error generating insights: {e}")
            return {
                "mood": "Good",
                "summary": f"{dog_name} is maintaining a healthy routine with consistent activity.",
                "insights": ["Regular exercise is benefiting overall health", "Mood has been stable", "Nutrition is on track"],
                "recommendation": "Keep up the great work with daily walks!"
            }


class LeaderboardPopulator:
    """Populates and maintains the leaderboard with AI-generated profiles"""
    
    def __init__(self, db):
        self.db = db
        self.generator = DogProfileGenerator(db)
    
    def calculate_profiles_per_breed(self, base_count: int = 5) -> Dict[str, int]:
        """Calculate number of profiles to generate per breed based on popularity"""
        profiles = {}
        for breed, popularity in BREED_POPULARITY.items():
            # Scale: popularity 10 = base_count * 2, popularity 1 = base_count * 0.2
            count = int(base_count * (popularity / 5))
            profiles[breed] = max(2, count)  # At least 2 per breed
        return profiles
    
    async def create_ai_dog_profile(self, name: str, breed: str, generate_photo: bool = True) -> Dict:
        """Create a complete AI dog profile"""
        # Generate age (1-12 years, weighted towards younger)
        age = random.choices(range(1, 13), weights=[3, 4, 4, 3, 3, 2, 2, 1, 1, 1, 1, 1])[0]
        
        # Generate weight based on breed
        weight_range = BREED_WEIGHTS.get(breed, (20, 60))
        weight = random.randint(weight_range[0], weight_range[1])
        
        # Generate birth date
        birth_year = datetime.now().year - age
        birth_month = random.randint(1, 12)
        birth_day = random.randint(1, 28)
        date_of_birth = f"{birth_year}-{birth_month:02d}-{birth_day:02d}"
        
        # Generate sex
        sex = random.choice(["male", "female"])
        
        # Activity level based on breed
        high_energy_breeds = ["Border Collie", "Australian Shepherd", "Siberian Husky", 
                            "Labrador Retriever", "Golden Retriever", "Boxer"]
        low_energy_breeds = ["Bulldog", "French Bulldog", "Shih Tzu", "Cavalier King Charles Spaniel"]
        
        if breed in high_energy_breeds:
            activity_level = random.choice(["high", "high", "medium"])
        elif breed in low_energy_breeds:
            activity_level = random.choice(["low", "medium", "medium"])
        else:
            activity_level = random.choice(["low", "medium", "high"])
        
        # Generate photo
        avatar_url = None
        if generate_photo:
            logger.info(f"Generating AI photo for {name} ({breed})...")
            avatar_url = await self.generator.generate_dog_photo(breed, name)
        
        # Create dog profile
        dog_id = str(uuid.uuid4())
        dog = {
            "id": dog_id,
            "name": name,
            "breed": breed,
            "avatar_url": avatar_url,
            "date_of_birth": date_of_birth,
            "weight_lbs": weight,
            "sex": sex,
            "activity_level": activity_level,
            "owner_id": "ai_generated",  # Mark as AI-generated
            "is_ai_profile": True,
            "created_at": datetime.utcnow()
        }
        
        return dog
    
    async def create_health_history(self, dog: Dict, days: int = 30) -> tuple:
        """Create health history (daily logs) for a dog"""
        dog_id = dog["id"]
        dog_name = dog["name"]
        breed = dog["breed"]
        
        # Calculate age
        if dog.get("date_of_birth"):
            birth_date = datetime.strptime(dog["date_of_birth"], "%Y-%m-%d")
            age = (datetime.now() - birth_date).days // 365
        else:
            age = 3
        
        # Generate health journey using AI
        logger.info(f"Generating health journey for {dog_name}...")
        journey = await self.generator.generate_health_journey(dog_name, breed, age, days)
        
        # Create daily logs
        daily_logs = []
        today = date.today()
        
        total_points = 0
        streak = 0
        current_streak = 0
        
        for i, day_data in enumerate(journey):
            log_date = today - timedelta(days=days - i - 1)
            
            # Calculate score for this day
            score = self._calculate_day_score(day_data)
            
            log = {
                "id": str(uuid.uuid4()),
                "dog_id": dog_id,
                "logged_at": datetime.combine(log_date, datetime.min.time()),
                "date": log_date.isoformat(),
                "mood": day_data["mood"],
                "exercise_level": day_data["exercise_level"],
                "nutrition_quality": day_data["nutrition_quality"],
                "points_earned": 10,
                "is_ai_generated": True
            }
            daily_logs.append(log)
            total_points += 10
            
            # Calculate streak (consecutive days from today)
            if i >= days - 7:  # Check last 7 days for streak
                if day_data["mood"] not in ["unwell"]:
                    current_streak += 1
                else:
                    current_streak = 0
        
        streak = min(current_streak, days)
        
        # Generate Lilo insights
        insights = await self.generator.generate_lilo_insights(dog_name, breed, journey)
        
        # Create Lilo report
        lilo_report = {
            "id": str(uuid.uuid4()),
            "dog_id": dog_id,
            "report_date": today.isoformat(),
            "mood": insights.get("mood", "Good"),
            "summary": insights.get("summary", f"{dog_name} is doing well."),
            "insights": insights.get("insights", []),
            "recommendation": insights.get("recommendation", "Keep up the good work!"),
            "healthspan_delta": round(random.uniform(-0.5, 2.0), 2),
            "created_at": datetime.utcnow(),
            "is_ai_generated": True
        }
        
        # Calculate final score
        if daily_logs:
            recent_scores = [self._calculate_day_score({"mood": log["mood"], 
                           "exercise_level": log["exercise_level"], 
                           "nutrition_quality": log["nutrition_quality"]}) for log in daily_logs[-7:]]
            final_score = int(sum(recent_scores) / len(recent_scores))
        else:
            final_score = 85
        
        # Create healthspan stats
        weekly_scores = []
        for i in range(7):
            day_date = (today - timedelta(days=6-i)).isoformat()
            if i < len(daily_logs):
                log = daily_logs[-(7-i)] if len(daily_logs) >= 7-i else daily_logs[0]
                score = self._calculate_day_score({
                    "mood": log["mood"],
                    "exercise_level": log["exercise_level"],
                    "nutrition_quality": log["nutrition_quality"]
                })
            else:
                score = random.randint(75, 95)
            weekly_scores.append({"date": day_date, "score": score})
        
        healthspan_stats = {
            "dog_id": dog_id,
            "owner_id": "ai_generated",
            "streak": streak,
            "total_points": total_points,
            "weekly_scores": weekly_scores,
            "current_score": final_score,
            "updated_at": datetime.utcnow(),
            "is_ai_generated": True
        }
        
        return daily_logs, lilo_report, healthspan_stats
    
    # _calculate_day_score removed - now uses shared calculate_day_score from server.py
    
    async def populate_leaderboard(self, generate_photos: bool = True, batch_size: int = 3):
        """Main function to populate the leaderboard with AI profiles"""
        profiles_per_breed = self.calculate_profiles_per_breed(base_count=5)
        total_profiles = sum(profiles_per_breed.values())
        
        logger.info(f"Starting leaderboard population: {total_profiles} total profiles across {len(profiles_per_breed)} breeds")
        
        created_count = 0
        
        for breed, count in profiles_per_breed.items():
            logger.info(f"Generating {count} profiles for {breed}...")
            
            # Generate names for this breed
            names = await self.generator.generate_dog_names(breed, count)
            
            for i, name in enumerate(names):
                try:
                    # Check if we should generate photo (rate limit)
                    should_generate_photo = generate_photos and (i < batch_size)
                    
                    # Create dog profile
                    dog = await self.create_ai_dog_profile(name, breed, generate_photo=should_generate_photo)
                    
                    # Create health history
                    daily_logs, lilo_report, healthspan_stats = await self.create_health_history(dog, days=30)
                    
                    # Insert into database
                    await self.db.dogs.insert_one(dog)
                    if daily_logs:
                        await self.db.daily_logs.insert_many(daily_logs)
                    await self.db.lilo_reports.insert_one(lilo_report)
                    await self.db.healthspan_stats.insert_one(healthspan_stats)
                    
                    created_count += 1
                    logger.info(f"Created profile {created_count}/{total_profiles}: {name} ({breed})")
                    
                    # Small delay to avoid rate limits
                    await asyncio.sleep(0.5)
                    
                except Exception as e:
                    logger.error(f"Error creating profile for {name} ({breed}): {e}")
                    continue
        
        logger.info(f"Leaderboard population complete! Created {created_count} profiles.")
        return created_count
    
    async def update_ai_profiles_activity(self):
        """Simulate daily activity for AI profiles (run daily via cron/scheduler)"""
        today = date.today().isoformat()
        
        # Get all AI dogs that haven't logged today
        ai_dogs = await self.db.dogs.find({"is_ai_profile": True}).to_list(1000)
        
        updated = 0
        for dog in ai_dogs:
            # Check if already logged today
            existing = await self.db.daily_logs.find_one({
                "dog_id": dog["id"],
                "date": today
            })
            
            if existing:
                continue
            
            # 90% chance of logging (simulates some inactive days)
            if random.random() > 0.9:
                continue
            
            # Generate today's log
            journey = self.generator._generate_fallback_journey(1)[0]
            
            log = {
                "id": str(uuid.uuid4()),
                "dog_id": dog["id"],
                "logged_at": datetime.utcnow(),
                "date": today,
                "mood": journey["mood"],
                "exercise_level": journey["exercise_level"],
                "nutrition_quality": journey["nutrition_quality"],
                "points_earned": 10,
                "is_ai_generated": True
            }
            
            await self.db.daily_logs.insert_one(log)
            
            # Update healthspan stats
            await self.db.healthspan_stats.update_one(
                {"dog_id": dog["id"]},
                {
                    "$inc": {"total_points": 10, "streak": 1},
                    "$set": {"updated_at": datetime.utcnow()}
                }
            )
            
            updated += 1
        
        logger.info(f"Updated activity for {updated} AI profiles")
        return updated
