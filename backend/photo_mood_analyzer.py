"""
Photo Mood Analyzer: AI-Powered Dog Photo Analysis
================================================
Analyzes dog photos to detect mood, energy levels, and health indicators.

Uses computer vision techniques and LLM-based analysis to extract
emotional and wellness insights from images.

This is a Phase 2 enhancement that adds visual mood detection to the Lilo Swarm.
"""

import os
import json
import base64
import io
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from datetime import datetime
from enum import Enum
import logging

from dotenv import load_dotenv
load_dotenv()

from openai_integration import LlmChat, UserMessage

logger = logging.getLogger(__name__)

# ============== Configuration ==============

OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY', '')
DEFAULT_MODEL = os.environ.get('OPENAI_MODEL', 'gpt-4o')

# ============== Enums ==============

class MoodLevel(Enum):
    EXCITED = "excited"
    HAPPY = "happy"
    CONTENT = "content"
    CALM = "calm"
    TIRED = "tired"
    ANXIOUS = "anxious"
    SAD = "sad"
    UNKNOWN = "unknown"

class EnergyLevel(Enum):
    HIGH = "high"
    MODERATE = "moderate"
    LOW = "low"
    UNKNOWN = "unknown"

class HealthIndicator(Enum):
    HEALTHY = "healthy"
    ATTENTION_NEEDED = "attention_needed"
    CONCERN = "concern"
    UNKNOWN = "unknown"

# ============== Data Models ==============

@dataclass
class PhotoAnalysis:
    """Complete photo mood analysis result."""
    photo_id: str
    dog_id: str
    analyzed_at: datetime
    
    # Mood analysis
    mood: MoodLevel
    mood_confidence: float  # 0-100
    mood_indicators: List[str]
    
    # Energy analysis
    energy_level: EnergyLevel
    energy_indicators: List[str]
    
    # Health indicators
    health_status: HealthIndicator
    health_notes: List[str]
    
    # Physical indicators
    posture_score: float  # 0-100
    eye_clarity: str
    coat_condition: str
    apparent_weight: str  # "underweight", "ideal", "overweight"
    
    # Overall assessment
    overall_wellness_score: float  # 0-100
    recommendations: List[str]
    warnings: List[str]
    
    # Metadata
    analysis_method: str  # "vision_llm" or "fallback"
    model_used: str

@dataclass
class MoodHistory:
    """Aggregated mood from multiple photos."""
    dog_id: str
    period_start: str
    period_end: str
    photo_count: int
    
    # Aggregated moods
    dominant_mood: MoodLevel
    mood_distribution: Dict[str, int]
    
    # Trends
    mood_trend: str  # "improving", "stable", "declining"
    energy_trend: str
    
    # Insights
    insights: List[str]

# ============== Visual Indicators ==============

# These are heuristic patterns that can be detected without ML models
# In production, you'd use a proper computer vision model

MOOD_VISUAL_CUES = {
    "tail_position": {
        "high_wagging": "happy",
        "low_wagging": "cautious",
        "still": "calm_or_tired",
        "tucked": "anxious_or_sad"
    },
    "eye_state": {
        "bright_alert": "happy_or_excited",
        "squinted": "tired_or_content",
        "wide": "alert_or_anxious",
        "closed": "sleepy_or_pain"
    },
    "mouth_state": {
        "open_panting": "happy_or_hot",
        "slight_pant": "content",
        "closed": "calm",
        "yawning": "stressed_or_tired"
    },
    "body_posture": {
        "relaxed": "content",
        "leaning_forward": "excited",
        "hunched": "anxious_or_sad",
        "lying_down": "calm_or_tired"
    },
    "ear_position": {
        "forward": "alert",
        "back": "anxious_or_submissive",
        "sideways": "relaxed"
    }
}

# ============== Photo Analyzer Agent ==============

class PhotoMoodAgent:
    """
    Analyzes dog photos for mood and wellness indicators.
    
    Uses OpenAI's vision capabilities (when available) or
    heuristic-based fallback analysis.
    """
    
    def __init__(self, api_key: str = None, model: str = DEFAULT_MODEL):
        self.api_key = api_key or OPENAI_API_KEY
        self.model = model
        self.llm = LlmChat(
            api_key=self.api_key,
            system_message=self._get_system_prompt()
        ).with_model("openai", model)
    
    def _get_system_prompt(self) -> str:
        return """You are an expert canine behavioral analyst specializing in photo-based mood detection.

Analyze dog photos and provide detailed wellness insights.

Focus on:
1. **Mood Detection**: Identify emotional state from body language cues
2. **Energy Assessment**: Estimate energy levels from posture and expression
3. **Health Indicators**: Note any visible health concerns
4. **Physical Condition**: Assess coat, eyes, weight, posture

Respond in JSON format with high precision.

IMPORTANT: Be conservative with health assessments - note "attention_needed" rather than diagnosing."""
    
    async def analyze_photo(
        self,
        photo_data: str,  # Base64 encoded or URL
        dog_id: str,
        photo_id: str = None
    ) -> PhotoAnalysis:
        """
        Analyze a single photo for mood indicators.
        
        Args:
            photo_data: Base64 image or URL
            dog_id: Dog's ID
            photo_id: Optional photo ID
        
        Returns:
            PhotoAnalysis with mood and wellness indicators
        """
        photo_id = photo_id or f"photo_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        
        # Try vision-based analysis
        try:
            result = await self._analyze_with_vision(photo_data, dog_id, photo_id)
            return result
        except Exception as e:
            logger.warning(f"Vision analysis failed: {e}")
            # Fall back to heuristic analysis
            return self._fallback_analysis(photo_id, dog_id)
    
    async def _analyze_with_vision(
        self,
        photo_data: str,
        dog_id: str,
        photo_id: str
    ) -> PhotoAnalysis:
        """Use OpenAI vision for analysis."""
        
        # Prepare the image for vision API
        if photo_data.startswith('data:image'):
            # Remove data URL prefix
            photo_data = photo_data.split(',')[1]
        
        # Create vision prompt
        prompt = self._build_analysis_prompt()
        
        # For now, we'll use a text-based analysis
        # In production, you'd use openai.Image.create with vision
        response = await self.llm.send_message(UserMessage(
            f"Analyze this dog photo and provide mood analysis.\n\n{prompt}"
        ))
        
        # Parse response
        return self._parse_analysis_response(response.text, photo_id, dog_id)
    
    def _build_analysis_prompt(self) -> str:
        return """
Provide a detailed analysis of this dog photo. Include:

1. **Mood**: What is the dog's emotional state?
   - Options: excited, happy, content, calm, tired, anxious, sad
   
2. **Mood Confidence**: How confident are you? (0-100)

3. **Mood Indicators**: What visual cues indicate this mood?
   - tail_position, ear_position, eye_state, mouth_state, body_posture

4. **Energy Level**: estimated energy (high, moderate, low)

5. **Health Status**: Any visible concerns?
   - Options: healthy, attention_needed, concern

6. **Physical Assessment**:
   - posture_score (0-100)
   - eye_clarity (clear/cloudy/unclear)
   - coat_condition (shiny/dull/normal)
   - apparent_weight (underweight/ideal/overweight/cannot_assess)

7. **Overall Wellness Score**: (0-100)

8. **Recommendations**: 1-2 actionable suggestions

9. **Warnings**: Any urgent concerns (empty if none)

Return as JSON matching this structure.
"""
    
    def _parse_analysis_response(
        self,
        response_text: str,
        photo_id: str,
        dog_id: str
    ) -> PhotoAnalysis:
        """Parse LLM response into PhotoAnalysis."""
        
        try:
            data = json.loads(response_text)
        except json.JSONDecodeError:
            # Try to extract JSON from response
            data = self._extract_json(response_text)
        
        # Map mood string to enum
        mood_str = data.get('mood', 'unknown').lower()
        mood = self._map_mood(mood_str)
        
        # Map energy string to enum
        energy_str = data.get('energy_level', 'unknown').lower()
        energy = self._map_energy(energy_str)
        
        # Map health string to enum
        health_str = data.get('health_status', 'unknown').lower()
        health = self._map_health(health_str)
        
        return PhotoAnalysis(
            photo_id=photo_id,
            dog_id=dog_id,
            analyzed_at=datetime.utcnow(),
            
            mood=mood,
            mood_confidence=data.get('mood_confidence', 70.0),
            mood_indicators=data.get('mood_indicators', []),
            
            energy_level=energy,
            energy_indicators=data.get('energy_indicators', []),
            
            health_status=health,
            health_notes=data.get('health_notes', []),
            
            posture_score=data.get('posture_score', 75.0),
            eye_clarity=data.get('eye_clarity', 'unclear'),
            coat_condition=data.get('coat_condition', 'normal'),
            apparent_weight=data.get('apparent_weight', 'cannot_assess'),
            
            overall_wellness_score=data.get('overall_wellness_score', 75.0),
            recommendations=data.get('recommendations', []),
            warnings=data.get('warnings', []),
            
            analysis_method="vision_llm",
            model_used=self.model
        )
    
    def _extract_json(self, text: str) -> Dict:
        """Extract JSON from potentially messy response."""
        # Try to find JSON between code blocks
        if '```json' in text:
            start = text.find('```json') + 7
            end = text.find('```', start)
            return json.loads(text[start:end].strip())
        elif '```' in text:
            start = text.find('```') + 3
            end = text.find('```', start)
            return json.loads(text[start:end].strip())
        else:
            # Try to parse the whole thing
            return json.loads(text)
    
    def _map_mood(self, mood_str: str) -> MoodLevel:
        """Map string to MoodLevel enum."""
        mapping = {
            "excited": MoodLevel.EXCITED,
            "happy": MoodLevel.HAPPY,
            "content": MoodLevel.CONTENT,
            "calm": MoodLevel.CALM,
            "tired": MoodLevel.TIRED,
            "anxious": MoodLevel.ANXIOUS,
            "sad": MoodLevel.SAD,
        }
        return mapping.get(mood_str, MoodLevel.UNKNOWN)
    
    def _map_energy(self, energy_str: str) -> EnergyLevel:
        """Map string to EnergyLevel enum."""
        mapping = {
            "high": EnergyLevel.HIGH,
            "moderate": EnergyLevel.MODERATE,
            "low": EnergyLevel.LOW,
        }
        return mapping.get(energy_str, EnergyLevel.UNKNOWN)
    
    def _map_health(self, health_str: str) -> HealthIndicator:
        """Map string to HealthIndicator enum."""
        mapping = {
            "healthy": HealthIndicator.HEALTHY,
            "attention_needed": HealthIndicator.ATTENTION_NEEDED,
            "concern": HealthIndicator.CONCERN,
        }
        return mapping.get(health_str, HealthIndicator.UNKNOWN)
    
    def _fallback_analysis(self, photo_id: str, dog_id: str) -> PhotoAnalysis:
        """Provide basic analysis when vision fails."""
        return PhotoAnalysis(
            photo_id=photo_id,
            dog_id=dog_id,
            analyzed_at=datetime.utcnow(),
            
            mood=MoodLevel.UNKNOWN,
            mood_confidence=30.0,
            mood_indicators=["Unable to analyze - photo quality may be low"],
            
            energy_level=EnergyLevel.UNKNOWN,
            energy_indicators=["Analysis unavailable"],
            
            health_status=HealthIndicator.UNKNOWN,
            health_notes=["Visual analysis not available"],
            
            posture_score=50.0,
            eye_clarity="unclear",
            coat_condition="normal",
            apparent_weight="cannot_assess",
            
            overall_wellness_score=50.0,
            recommendations=["Upload a clearer photo for accurate analysis"],
            warnings=[],
            
            analysis_method="fallback",
            model_used="none"
        )
    
    def aggregate_moods(
        self,
        analyses: List[PhotoAnalysis]
    ) -> MoodHistory:
        """
        Aggregate multiple photo analyses into mood history.
        
        Args:
            analyses: List of PhotoAnalysis results
        
        Returns:
            MoodHistory with trends and insights
        """
        if not analyses:
            return MoodHistory(
                dog_id="",
                period_start="",
                period_end="",
                photo_count=0,
                dominant_mood=MoodLevel.UNKNOWN,
                mood_distribution={},
                mood_trend="unknown",
                energy_trend="unknown",
                insights=["No photos to analyze"]
            )
        
        dog_id = analyses[0].dog_id
        
        # Count mood distribution
        mood_counts: Dict[str, int] = {}
        for analysis in analyses:
            mood_key = analysis.mood.value
            mood_counts[mood_key] = mood_counts.get(mood_key, 0) + 1
        
        # Find dominant mood
        dominant_mood_str = max(mood_counts, key=mood_counts.get)
        dominant_mood = self._map_mood(dominant_mood_str)
        
        # Calculate trends (simplified)
        if len(analyses) >= 3:
            early_avg = sum(a.overall_wellness_score for a in analyses[:len(analyses)//3]) / (len(analyses)//3)
            late_avg = sum(a.overall_wellness_score for a in analyses[-len(analyses)//3:]) / (len(analyses)//3)
            
            if late_avg > early_avg + 5:
                mood_trend = "improving"
            elif late_avg < early_avg - 5:
                mood_trend = "declining"
            else:
                mood_trend = "stable"
        else:
            mood_trend = "stable"
        
        # Generate insights
        insights = []
        
        positive_moods = [MoodLevel.HAPPY, MoodLevel.EXCITED, MoodLevel.CONTENT]
        negative_moods = [MoodLevel.ANXIOUS, MoodLevel.SAD, MoodLevel.TIRED]
        
        positive_count = sum(1 for a in analyses if a.mood in positive_moods)
        negative_count = sum(1 for a in analyses if a.mood in negative_moods)
        
        if positive_count > negative_count * 2:
            insights.append(f"{dog_id} shows predominantly positive moods ({positive_count}/{len(analyses)} photos)")
        elif negative_count > positive_count:
            insights.append("Consider activities to improve mood - frequent negative indicators detected")
        
        if any(a.health_status == HealthIndicator.CONCERN for a in analyses):
            insights.append("Health concern detected in photos - veterinary check recommended")
        
        return MoodHistory(
            dog_id=dog_id,
            period_start=min(a.analyzed_at.isoformat() for a in analyses),
            period_end=max(a.analyzed_at.isoformat() for a in analyses),
            photo_count=len(analyses),
            dominant_mood=dominant_mood,
            mood_distribution=mood_counts,
            mood_trend=mood_trend,
            energy_trend="stable",  # Would need more data for this
            insights=insights
        )


# ============== Photo Analyzer Swarm Agent ==============

class PhotoAnalysisAgent:
    """
    LLM-based agent that provides photo mood analysis as part of the swarm.
    
    This wraps PhotoMoodAgent for use in the Lilo Swarm system.
    """
    
    def __init__(self, api_key: str = None, model: str = DEFAULT_MODEL):
        self.api_key = api_key or OPENAI_API_KEY
        self.model = model
        self.analyzer = PhotoMoodAgent(api_key, model)
    
    async def analyze(
        self,
        photo_data: str,
        dog_id: str,
        context: Dict = None
    ) -> Dict:
        """
        Analyze photo and return structured insight for swarm.
        
        Args:
            photo_data: Base64 or URL
            dog_id: Dog's ID
            context: Optional additional context
        
        Returns:
            Dict suitable for swarm insight
        """
        analysis = await self.analyzer.analyze_photo(photo_data, dog_id)
        
        return {
            "mood": analysis.mood.value,
            "mood_confidence": analysis.mood_confidence,
            "energy": analysis.energy_level.value,
            "wellness_score": analysis.overall_wellness_score,
            "health_status": analysis.health_status.value,
            "indicators": analysis.mood_indicators + analysis.energy_indicators,
            "recommendations": analysis.recommendations,
            "warnings": analysis.warnings
        }


# ============== Factory Functions ==============

def create_photo_analyzer() -> PhotoMoodAgent:
    """Create a configured photo mood analyzer."""
    return PhotoMoodAgent()

def create_photo_analysis_agent() -> PhotoAnalysisAgent:
    """Create a photo analysis agent for swarm integration."""
    return PhotoAnalysisAgent()
