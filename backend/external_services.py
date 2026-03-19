"""
External API Services for Canine.Fit
Integrates with Dog API, USDA Food DB, OpenWeatherMap, AirNow, and more.
"""

import os
import httpx
from typing import Optional, Dict, Any, List
from functools import lru_cache


# API Keys from environment
DOG_API_KEY = os.environ.get('DOG_API_KEY', '')
USDA_API_KEY = os.environ.get('USDA_API_KEY', '')
OPENWEATHERMAP_API_KEY = os.environ.get('OPENWEATHERMAP_API_KEY', '')
AIRNOW_API_KEY = os.environ.get('AIRNOW_API_KEY', '')
SPOTIFY_CLIENT_ID = os.environ.get('SPOTIFY_CLIENT_ID', '')
SPOTIFY_CLIENT_SECRET = os.environ.get('SPOTIFY_CLIENT_SECRET', '')


# ============== Dog API (Breed Information) ==============

DOG_API_BASE = "https://api.thedogapi.com/v1"


async def search_breeds(query: str) -> List[Dict[str, Any]]:
    """
    Search for dog breeds by name.
    Returns breed information including weight, height, life span, temperament.
    """
    if not DOG_API_KEY:
        return []
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                f"{DOG_API_BASE}/breeds/search",
                params={"q": query},
                headers={"x-api-key": DOG_API_KEY},
                timeout=10.0
            )
            if response.status_code == 200:
                return response.json()
        except Exception:
            pass
    return []


async def get_breed_by_id(breed_id: str) -> Optional[Dict[str, Any]]:
    """Get detailed breed information by ID."""
    if not DOG_API_KEY:
        return None
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                f"{DOG_API_BASE}/breeds/{breed_id}",
                headers={"x-api-key": DOG_API_KEY},
                timeout=10.0
            )
            if response.status_code == 200:
                return response.json()
        except Exception:
            pass
    return None


async def get_breeds_by_group(group: str) -> List[Dict[str, Any]]:
    """Get all breeds in a specific group (e.g., 'sporting', 'herding')."""
    if not DOG_API_KEY:
        return []
    
    all_breeds = await get_all_breeds()
    return [b for b in all_breeds if b.get('breed_group', '').lower() == group.lower()]


@lru_cache(maxsize=1)
async def get_all_breeds() -> List[Dict[str, Any]]:
    """Get all dog breeds (cached)."""
    if not DOG_API_KEY:
        return []
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                f"{DOG_API_BASE}/breeds",
                headers={"x-api-key": DOG_API_KEY},
                timeout=15.0
            )
            if response.status_code == 200:
                return response.json()
        except Exception:
            pass
    return []


def get_breed_health_insights(breed_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate health insights based on breed characteristics.
    This is rules-based (no LLM needed) for deterministic insights.
    """
    insights = []
    
    # Weight insights
    weight_metric = breed_data.get('weight', {})
    if weight_metric:
        weight_min = weight_metric.get('metric', '').split('-')
        if len(weight_min) == 2:
            try:
                min_kg = float(weight_min[0])
                max_kg = float(weight_min[1])
                avg_weight_kg = (min_kg + max_kg) / 2
                avg_weight_lbs = avg_weight_kg * 2.205
                insights.append({
                    "type": "weight",
                    "title": f"Healthy Weight Range",
                    "description": f"For {breed_data.get('name', 'this breed')}: {weight_min[0]}-{weight_min[1]} kg ({int(avg_weight_lbs * 0.9)}-{int(avg_weight_lbs * 1.1)} lbs)",
                    "metric": f"{int(avg_weight_lbs * 0.9)}-{int(avg_weight_lbs * 1.1)} lbs"
                })
            except ValueError:
                pass
    
    # Lifespan insights
    life_span = breed_data.get('life_span', '')
    if life_span:
        insights.append({
            "type": "lifespan",
            "title": "Average Lifespan",
            "description": f"{breed_data.get('name', 'This breed')} typically lives {life_span}",
            "metric": life_span
        })
    
    # Breed group
    breed_group = breed_data.get('breed_group', '')
    if breed_group:
        group_info = {
            "sporting": "Active breeds needing lots of exercise (swimming, fetching)",
            "herding": "High-energy dogs requiring mental stimulation",
            "working": "Strong breeds bred for guarding and rescue",
            "terrier": "Energetic dogs with strong prey drives",
            "toy": "Small breeds ideal for apartment living",
            "non-sporting": "Diverse group with varying exercise needs",
            "hound": "Athletic breeds great for runners",
            "miscellaneous": "Rare breeds with unique characteristics"
        }
        if breed_group.lower() in group_info:
            insights.append({
                "type": "activity",
                "title": f"{breed_group} Group",
                "description": group_info[breed_group.lower()],
                "metric": breed_group
            })
    
    # Temperament
    temperament = breed_data.get('temperament', '')
    if temperament:
        traits = [t.strip() for t in temperament.split(',')]
        activity_traits = [t for t in traits if t.lower() in 
            ['active', 'energetic', 'playful', 'athletic', 'high-energy', 'sporting']]
        if activity_traits:
            insights.append({
                "type": "personality",
                "title": "Activity Level",
                "description": f"This breed is known for: {', '.join(activity_traits)}",
                "metric": "High" if len(activity_traits) > 1 else "Moderate"
            })
    
    return {
        "breed_name": breed_data.get('name', 'Unknown'),
        "breed_id": breed_data.get('id'),
        "origin": breed_data.get('origin', 'Unknown'),
        "image_url": breed_data.get('image', {}).get('url', ''),
        "insights": insights
    }


# ============== USDA FoodData Central ==============

USDA_API_BASE = "https://api.nal.usda.gov/fdc/v1"


async def search_foods(query: str, limit: int = 10) -> List[Dict[str, Any]]:
    """
    Search USDA food database for nutritional information.
    Much more accurate than manual food databases.
    """
    if not USDA_API_KEY:
        return []
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                f"{USDA_API_BASE}/foods/search",
                params={
                    "api_key": USDA_API_KEY,
                    "query": query,
                    "pageSize": limit,
                    "dataType": ["Foundation", "SR Legacy"]
                },
                timeout=10.0
            )
            if response.status_code == 200:
                data = response.json()
                return data.get('foods', [])
        except Exception:
            pass
    return []


async def get_food_by_id(fdc_id: str) -> Optional[Dict[str, Any]]:
    """Get detailed food nutrient information by FDC ID."""
    if not USDA_API_KEY:
        return None
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                f"{USDA_API_BASE}/food/{fdc_id}",
                params={"api_key": USDA_API_KEY},
                timeout=10.0
            )
            if response.status_code == 200:
                return response.json()
        except Exception:
            pass
    return None


def analyze_food_for_dogs(food_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Analyze a food's safety and nutrition for dogs.
    Returns verdict and key nutritional info.
    """
    description = food_data.get('description', '').lower()
    brand = food_data.get('brandOwner', '')
    
    # Get key nutrients
    nutrients = {}
    for nutrient in food_data.get('foodNutrients', []):
        nutrient_id = nutrient.get('nutrientId')
        value = nutrient.get('value', 0)
        unit = nutrient.get('unitName', '')
        
        # Map common nutrient IDs
        nutrient_map = {
            1003: ('protein', 'Protein'),
            1004: ('fat', 'Fat'),
            1005: ('carbs', 'Carbohydrates'),
            1008: ('calories', 'Calories'),
            2000: ('sugar', 'Sugars'),
            1079: ('fiber', 'Fiber'),
            1093: ('sodium', 'Sodium'),
        }
        
        if nutrient_id in nutrient_map:
            key, name = nutrient_map[nutrient_id]
            nutrients[key] = {"value": value, "unit": unit, "name": name}
    
    # Toxic foods check (basic - should be expanded)
    toxic_keywords = {
        'chocolate': 'TOXIC - Contains theobromine, dangerous for dogs',
        'onion': 'TOXIC - Contains compounds that damage red blood cells',
        'garlic': 'HARMFUL - Can cause anemia in dogs',
        'grape': 'TOXIC - Can cause kidney failure',
        'raisin': 'TOXIC - Can cause kidney failure',
        'xylitol': 'TOXIC - Extremely dangerous, causes liver failure',
        'avocado': 'CAUTION - Contains persin, not recommended for dogs',
        'macadamia': 'TOXIC - Can cause weakness and vomiting',
        'alcohol': 'TOXIC - Never give alcohol to dogs',
        'coffee': 'TOXIC - Contains caffeine, dangerous for dogs',
        'tea': 'TOXIC - Contains caffeine, dangerous for dogs',
    }
    
    warnings = []
    verdict = "SAFE"
    
    for keyword, warning in toxic_keywords.items():
        if keyword in description:
            warnings.append(warning)
            verdict = "TOXIC" if "TOXIC" in warning else "CAUTION"
    
    # Check for unhealthy levels (per 100g serving)
    serving_calories = nutrients.get('calories', {}).get('value', 0)
    serving_sodium = nutrients.get('sodium', {}).get('value', 0)
    
    if serving_sodium > 400:
        warnings.append(f"High sodium content ({int(serving_sodium)}mg) - not ideal for dogs")
        if verdict == "SAFE":
            verdict = "CAUTION"
    
    return {
        "food_name": food_data.get('description', 'Unknown'),
        "brand": brand,
        "verdict": verdict,
        "warnings": warnings,
        "nutrients_per_100g": nutrients,
        "fdc_id": food_data.get('fdcId'),
        "category": food_data.get('category', '')
    }


# ============== OpenWeatherMap ==============

WEATHER_API_BASE = "https://api.openweathermap.org/data/2.5"


async def get_current_weather(lat: float, lon: float) -> Optional[Dict[str, Any]]:
    """
    Get current weather conditions.
    Useful for determining walk safety and timing.
    """
    if not OPENWEATHERMAP_API_KEY:
        return None
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                f"{WEATHER_API_BASE}/weather",
                params={
                    "lat": lat,
                    "lon": lon,
                    "appid": OPENWEATHERMAP_API_KEY,
                    "units": "imperial"  # Fahrenheit for US users
                },
                timeout=10.0
            )
            if response.status_code == 200:
                return response.json()
        except Exception:
            pass
    return None


async def get_forecast(lat: float, lon: float, hours: int = 24) -> Optional[Dict[str, Any]]:
    """Get weather forecast for planning walks."""
    if not OPENWEATHERMAP_API_KEY:
        return None
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                f"{WEATHER_API_BASE}/forecast",
                params={
                    "lat": lat,
                    "lon": lon,
                    "appid": OPENWEATHERMAP_API_KEY,
                    "units": "imperial",
                    "cnt": int(hours / 3)  # 3-hour intervals
                },
                timeout=10.0
            )
            if response.status_code == 200:
                return response.json()
        except Exception:
            pass
    return None


def analyze_walk_conditions(weather: Dict[str, Any]) -> Dict[str, Any]:
    """
    Analyze weather conditions for dog walking suitability.
    Returns recommendations based on temperature, rain, etc.
    """
    main = weather.get('main', {})
    weather_list = weather.get('weather', [{}])
    current_weather = weather_list[0] if weather_list else {}
    
    temp = main.get('temp', 70)
    feels_like = main.get('feels_like', temp)
    humidity = main.get('humidity', 50)
    condition = current_weather.get('main', 'Clear')
    description = current_weather.get('description', '')
    icon = current_weather.get('icon', '01d')
    
    recommendations = []
    score = 100
    issues = []
    
    # Temperature checks
    if temp < 32:
        recommendations.append(f"❄️ Very cold ({int(temp)}°F) - Consider a coat for short-haired dogs")
        score -= 30
        issues.append("too_cold")
    elif temp < 45:
        recommendations.append(f"🌡️ Chilly ({int(temp)}°F) - A light jacket may help")
        score -= 10
    elif temp > 95:
        recommendations.append(f"🔥 Very hot ({int(temp)}°F) - Risk of heat stroke, walk early morning or evening")
        score -= 40
        issues.append("too_hot")
    elif temp > 85:
        recommendations.append(f"☀️ Hot ({int(temp)}°F) - Hot pavement can burn paws, stay on grass")
        score -= 20
        issues.append("hot_pavement")
    
    # Feels like temperature
    if feels_like < 32:
        recommendations.append(f"🥶 Feels like {int(feels_like)}°F - Limit outdoor time")
        score -= 15
    
    # Rain checks
    if 'rain' in condition.lower() or 'drizzle' in condition.lower():
        recommendations.append("🌧️ Rain expected - Consider rain gear or indoor play")
        score -= 20
        issues.append("rain")
    
    if 'thunderstorm' in condition.lower():
        recommendations.append("⛈️ Thunderstorm - Not safe for walks, lightning risk")
        score -= 50
        issues.append("thunderstorm")
    
    # Wind checks
    wind = weather.get('wind', {}).get('speed', 0)
    if wind > 25:
        recommendations.append(f"💨 Strong winds ({int(wind)} mph) - Small dogs may struggle")
        score -= 10
    
    # Air quality hint (via description)
    if 'smoke' in description.lower() or 'haze' in description.lower():
        recommendations.append("🌫️ Poor air quality - Limit strenuous activity")
        score -= 15
        issues.append("poor_air")
    
    # Good conditions
    if score >= 80 and not issues:
        if 50 <= temp <= 75:
            recommendations.append(f"✅ Perfect weather for a walk! {int(temp)}°F and {condition}")
        else:
            recommendations.append(f"👍 Good conditions for a walk - {description}")
    
    return {
        "temperature": int(temp),
        "feels_like": int(feels_like),
        "condition": condition,
        "description": description,
        "icon": icon,
        "humidity": humidity,
        "wind_speed": int(wind),
        "walk_score": max(0, score),
        "recommendations": recommendations,
        "issues": issues,
        "best_for": "walk" if score >= 60 else "indoor_play"
    }


def find_best_walk_times(forecast: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Find the best times to walk based on forecast.
    Returns hourly recommendations.
    """
    if not forecast or 'list' not in forecast:
        return []
    
    best_times = []
    list_items = forecast.get('list', [])
    
    for item in list_items:
        dt = item.get('dt', 0)
        main = item.get('main', {})
        weather = item.get('weather', [{}])[0]
        
        temp = main.get('temp', 70)
        condition = weather.get('main', 'Clear')
        icon = weather.get('icon', '01d')
        
        # Score this time slot
        score = 100
        
        # Ideal walking temp: 50-75°F
        if 50 <= temp <= 75:
            score += 20
        elif temp < 40 or temp > 85:
            score -= 30
        
        # Avoid rain/storms
        if 'rain' in condition.lower() or 'storm' in condition.lower():
            score -= 40
        
        # Prefer daytime
        from datetime import datetime
        hour = datetime.fromtimestamp(dt).hour
        if 7 <= hour <= 9:
            score += 15  # Morning walk bonus
        elif 17 <= hour <= 19:
            score += 15  # Evening walk bonus
        
        if score >= 60:
            best_times.append({
                "timestamp": dt,
                "hour": hour,
                "temp": int(temp),
                "condition": condition,
                "icon": icon,
                "score": min(100, score),
                "label": f"{hour}:00"
            })
    
    # Sort by score and return top 4
    best_times.sort(key=lambda x: x['score'], reverse=True)
    return best_times[:4]


# ============== AirNow (Air Quality) ==============

AIRNOW_API_BASE = "https://www.airnowapi.org"


async def get_air_quality(zip_code: str) -> Optional[Dict[str, Any]]:
    """
    Get air quality index for a location.
    Important for dogs with respiratory issues.
    """
    if not AIRNOW_API_KEY:
        return None
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                f"{AIRNOW_API_BASE}/aq/observation/zipCode/current",
                params={
                    "format": "application/json",
                    "zipCode": zip_code,
                    "distance": 25,
                    "API_KEY": AIRNOW_API_KEY
                },
                timeout=10.0
            )
            if response.status_code == 200:
                data = response.json()
                if data and len(data) > 0:
                    return data[0]
        except Exception:
            pass
    return None


def analyze_air_quality(aqi_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Analyze air quality for dog walking safety.
    """
    aqi = aqi_data.get('AQI', 0)
    category = aqi_data.get('Category', {}).get('Name', 'Unknown')
    
    recommendations = []
    health_advice = ""
    
    if aqi <= 50:
        recommendations.append("✅ Air quality is good - Great for outdoor activities!")
        health_advice = "Ideal conditions for all dogs"
    elif aqi <= 100:
        recommendations.append("⚠️ Air quality is moderate - Safe for most dogs")
        health_advice = "Moderate conditions, watch for symptoms in sensitive dogs"
    elif aqi <= 150:
        recommendations.append("🔴 Unhealthy for sensitive groups - Limit outdoor exercise")
        health_advice = "Dogs with respiratory issues should stay indoors"
    else:
        recommendations.append("⛔ Air quality is unhealthy - Keep dogs indoors")
        health_advice = "All outdoor activities should be avoided"
    
    return {
        "aqi": aqi,
        "category": category,
        "recommendations": recommendations,
        "health_advice": health_advice,
        "date_issued": aqi_data.get('DateObserved', ''),
        "reporting_area": aqi_data.get('ReportingArea', 'Unknown')
    }


# ============== Helper Functions ==============

def calculate_healthspan_contribution(
    activity_score: float,
    nutrition_score: float,
    environmental_score: float,
    breed_baseline: float = 85.0
) -> Dict[str, Any]:
    """
    Calculate healthspan score based on multiple factors.
    This is the core healthspan calculation engine.
    """
    # Weighted average (activity matters most)
    overall_score = (
        activity_score * 0.4 +
        nutrition_score * 0.35 +
        environmental_score * 0.25
    )
    
    # Adjust for breed baseline
    relative_performance = overall_score - breed_baseline
    
    # Calculate projected lifespan impact
    # Based on research: 1 point of healthspan ≈ 0.1 months of life
    monthly_impact = relative_performance * 0.1
    
    return {
        "overall_healthspan_score": round(overall_score, 1),
        "activity_score": round(activity_score, 1),
        "nutrition_score": round(nutrition_score, 1),
        "environmental_score": round(environmental_score, 0),
        "breed_baseline": breed_baseline,
        "relative_performance": round(relative_performance, 1),
        "projected_months_impact": round(monthly_impact, 1),
        "rating": _get_rating(overall_score)
    }


def _get_rating(score: float) -> str:
    """Convert score to rating."""
    if score >= 95:
        return "Excellent"
    elif score >= 85:
        return "Good"
    elif score >= 75:
        return "Fair"
    elif score >= 65:
        return "Needs Improvement"
    else:
        return "Critical"
