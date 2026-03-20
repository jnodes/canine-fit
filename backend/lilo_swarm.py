"""
Lilo Swarm: Multi-Agent Wellness Analysis System
=================================================
A swarm architecture for deep personalization of dog wellness insights.

Each dog profile gets a dedicated swarm of specialized agents:
- Activity Agent: Walk patterns, exercise intensity, recovery
- Nutrition Agent: Diet analysis, food safety, allergies
- Mood Agent: Behavioral signals, photo analysis, energy levels
- Environment Agent: Weather, air quality, seasonal factors
- Breed Agent: Genetic predispositions, breed-specific needs
- Healthspan Agent: Long-term trajectory, predictions
- Social Agent: Leaderboard context, community benchmarks
- Synthesizer: Combines all insights into cohesive report

Architecture inspired by ruv-FANN ephemeral intelligence pattern.
"""

import os
import json
import asyncio
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional, Any
from datetime import datetime, date
from enum import Enum
import logging

from dotenv import load_dotenv
load_dotenv()

from openai_integration import LlmChat, UserMessage

logger = logging.getLogger(__name__)

# ============== Configuration ==============

OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY', '')
DEFAULT_MODEL = os.environ.get('OPENAI_MODEL', 'gpt-4o')

# ============== Data Models ==============

class ConfidenceLevel(Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

@dataclass
class AgentInsight:
    """Insight from a specialized agent."""
    agent: str
    category: str
    finding: str
    confidence: ConfidenceLevel
    recommendation: str
    supporting_data: Dict[str, Any] = field(default_factory=dict)
    priority: int = 5  # 1-10, higher = more important

@dataclass
class SwarmReport:
    """Complete wellness report from swarm analysis."""
    dog_id: str
    dog_name: str
    breed: str
    age_years: float
    generated_at: datetime
    
    # Overall assessment
    overall_mood: str
    overall_score: float  # 0-100
    healthspan_delta: float  # Change in predicted lifespan days
    
    # Agent insights
    insights: List[AgentInsight]
    
    # Synthesized report
    summary: str
    key_recommendations: List[str]
    warnings: List[str]
    
    # Metadata
    agent_count: int
    analysis_duration_ms: float
    model_used: str


# ============== Base Agent ==============

class SwarmAgent:
    """Base class for swarm agents."""
    
    name: str = "BaseAgent"
    specialty: str = "General"
    system_prompt: str = ""
    
    def __init__(self, api_key: str = None, model: str = DEFAULT_MODEL):
        self.api_key = api_key or OPENAI_API_KEY
        self.model = model
        self.llm = LlmChat(
            api_key=self.api_key,
            system_message=self.system_prompt
        ).with_model("openai", model)
    
    async def analyze(self, context: Dict) -> AgentInsight:
        """Analyze context and return insight."""
        raise NotImplementedError
    
    def build_prompt(self, context: Dict) -> str:
        """Build analysis prompt from context."""
        raise NotImplementedError


# ============== Activity Agent ==============

class ActivityAgent(SwarmAgent):
    """Analyzes activity patterns, exercise intensity, and recovery."""
    
    name = "Activity Agent"
    specialty = "Exercise and Movement"
    
    system_prompt = """You are an expert canine physiotherapist and exercise scientist.
Analyze a dog's activity patterns and provide actionable insights.
Focus on: exercise intensity, recovery needs, breed-appropriate activity, 
walk quality vs quantity, and injury prevention.
Respond in JSON format with: finding, confidence, recommendation, priority."""

    async def analyze(self, context: Dict) -> AgentInsight:
        prompt = self.build_prompt(context)
        response = await self.llm.send_message(UserMessage(prompt))
        
        try:
            data = json.loads(response.text)
            return AgentInsight(
                agent=self.name,
                category="activity",
                finding=data.get("finding", "Activity patterns normal"),
                confidence=ConfidenceLevel(data.get("confidence", "medium")),
                recommendation=data.get("recommendation", "Continue current routine"),
                priority=data.get("priority", 5),
                supporting_data=context.get("activity_data", {})
            )
        except json.JSONDecodeError:
            return AgentInsight(
                agent=self.name,
                category="activity",
                finding="Activity patterns analyzed",
                confidence=ConfidenceLevel.MEDIUM,
                recommendation="Maintain consistent exercise routine",
                supporting_data=context.get("activity_data", {})
            )
    
    def build_prompt(self, context: Dict) -> str:
        dog = context.get("dog", {})
        logs = context.get("recent_logs", [])
        
        prompt = f"""Analyze this dog's activity patterns:

Dog: {dog.get('name', 'Unknown')} ({dog.get('breed', 'Unknown')})
Age: {dog.get('age_years', 0)} years
Recent Activity (last 7 days):
"""
        
        for log in logs[-7:]:
            prompt += f"""
- Date: {log.get('logged_at', 'N/A')}
  Steps: {log.get('steps', 0)}, 
  Active Minutes: {log.get('active_minutes', 0)},
  Mood: {log.get('mood', 'Unknown')},
  Notes: {log.get('notes', 'None')}"""
        
        prompt += """
Return JSON with:
{
  "finding": "What you observe about activity patterns",
  "confidence": "high/medium/low",
  "recommendation": "Specific actionable advice",
  "priority": 1-10
}"""
        return prompt


# ============== Nutrition Agent ==============

class NutritionAgent(SwarmAgent):
    """Analyzes diet, food safety, and nutritional balance."""
    
    name = "Nutrition Agent"
    specialty = "Diet and Nutrition"
    
    system_prompt = """You are a board-certified veterinary nutritionist.
Analyze a dog's diet and nutritional intake.
Focus on: balanced nutrition, food safety, breed-specific needs,
allergies/sensitivities, weight management, and supplement needs.
Respond in JSON format."""

    async def analyze(self, context: Dict) -> AgentInsight:
        prompt = self.build_prompt(context)
        response = await self.llm.send_message(UserMessage(prompt))
        
        try:
            data = json.loads(response.text)
            return AgentInsight(
                agent=self.name,
                category="nutrition",
                finding=data.get("finding", "Diet appears balanced"),
                confidence=ConfidenceLevel(data.get("confidence", "medium")),
                recommendation=data.get("recommendation", "Continue current diet"),
                priority=data.get("priority", 5),
                supporting_data=context.get("nutrition_data", {})
            )
        except json.JSONDecodeError:
            return AgentInsight(
                agent=self.name,
                category="nutrition",
                finding="Diet analyzed",
                confidence=ConfidenceLevel.MEDIUM,
                recommendation="Ensure consistent feeding schedule",
                supporting_data=context.get("nutrition_data", {})
            )
    
    def build_prompt(self, context: Dict) -> str:
        dog = context.get("dog", {})
        
        prompt = f"""Analyze this dog's nutritional profile:

Dog: {dog.get('name', 'Unknown')} ({dog.get('breed', 'Unknown')})
Age: {dog.get('age_years', 0)} years
Weight: {dog.get('weight_kg', 'Unknown')} kg
Target Weight: {dog.get('target_weight_kg', 'Not set')} kg
Current Diet Notes: {dog.get('diet_notes', 'None provided')}
"""
        
        logs = context.get("recent_logs", [])
        meal_logs = [l for l in logs if l.get('log_type') == 'meal']
        if meal_logs:
            prompt += "\nRecent Meals:"
            for log in meal_logs[-5:]:
                prompt += f"\n- {log.get('notes', 'Standard meal')}"
        
        prompt += """
Return JSON with:
{
  "finding": "What you observe about nutrition",
  "confidence": "high/medium/low", 
  "recommendation": "Specific dietary advice",
  "priority": 1-10
}"""
        return prompt


# ============== Mood Agent ==============

class MoodAgent(SwarmAgent):
    """Analyzes behavioral signals, energy levels, and emotional state."""
    
    name = "Mood Agent"
    specialty = "Behavioral and Emotional Health"
    
    system_prompt = """You are a canine behavioral specialist.
Analyze a dog's mood and emotional wellbeing.
Focus on: energy levels, behavioral changes, stress indicators,
social interactions, and mental stimulation needs.
Respond in JSON format."""

    async def analyze(self, context: Dict) -> AgentInsight:
        prompt = self.build_prompt(context)
        response = await self.llm.send_message(UserMessage(prompt))
        
        try:
            data = json.loads(response.text)
            return AgentInsight(
                agent=self.name,
                category="mood",
                finding=data.get("finding", "Mood appears stable"),
                confidence=ConfidenceLevel(data.get("confidence", "medium")),
                recommendation=data.get("recommendation", "Continue providing mental stimulation"),
                priority=data.get("priority", 5),
                supporting_data=context.get("mood_data", {})
            )
        except json.JSONDecodeError:
            return AgentInsight(
                agent=self.name,
                category="mood",
                finding="Mood patterns analyzed",
                confidence=ConfidenceLevel.MEDIUM,
                recommendation="Provide engaging activities",
                supporting_data=context.get("mood_data", {})
            )
    
    def build_prompt(self, context: Dict) -> str:
        dog = context.get("dog", {})
        logs = context.get("recent_logs", [])
        
        mood_data = [l.get('mood', 'unknown') for l in logs]
        
        prompt = f"""Analyze this dog's emotional state:

Dog: {dog.get('name', 'Unknown')} ({dog.get('breed', 'Unknown')})
Age: {dog.get('age_years', 0)} years
Recent Mood Entries: {', '.join(mood_data[-7:]) or 'No mood data'}

Recent Notes:
"""
        for log in logs[-5:]:
            if log.get('notes'):
                prompt += f"- {log.get('notes')}\n"
        
        prompt += """
Return JSON with:
{
  "finding": "What you observe about emotional state",
  "confidence": "high/medium/low",
  "recommendation": "Mental wellness advice",
  "priority": 1-10
}"""
        return prompt


# ============== Environment Agent ==============

class EnvironmentAgent(SwarmAgent):
    """Analyzes environmental factors: weather, air quality, living conditions."""
    
    name = "Environment Agent"
    specialty = "Environmental Health"
    
    system_prompt = """You are an environmental health specialist for dogs.
Analyze environmental factors affecting dog wellness.
Focus on: weather impacts, air quality, seasonal considerations,
geographic factors, and living environment safety.
Respond in JSON format."""

    async def analyze(self, context: Dict) -> AgentInsight:
        prompt = self.build_prompt(context)
        response = await self.llm.send_message(UserMessage(prompt))
        
        try:
            data = json.loads(response.text)
            return AgentInsight(
                agent=self.name,
                category="environment",
                finding=data.get("finding", "Environment appears suitable"),
                confidence=ConfidenceLevel(data.get("confidence", "medium")),
                recommendation=data.get("recommendation", "Continue monitoring conditions"),
                priority=data.get("priority", 5),
                supporting_data=context.get("environment_data", {})
            )
        except json.JSONDecodeError:
            return AgentInsight(
                agent=self.name,
                category="environment",
                finding="Environmental factors analyzed",
                confidence=ConfidenceLevel.MEDIUM,
                recommendation="Stay aware of weather conditions",
                supporting_data=context.get("environment_data", {})
            )
    
    def build_prompt(self, context: Dict) -> str:
        dog = context.get("dog", {})
        env_data = context.get("environment_data", {})
        
        prompt = f"""Analyze environmental factors for this dog:

Dog: {dog.get('name', 'Unknown')} ({dog.get('breed', 'Unknown')})
Climate/Location: {env_data.get('location', 'Not specified')}
Current Weather: {env_data.get('weather_summary', 'No data')}
Air Quality: {env_data.get('aqi', 'Unknown')} AQI
Temperature: {env_data.get('temperature', 'Unknown')}°C
Humidity: {env_data.get('humidity', 'Unknown')}%
UV Index: {env_data.get('uv_index', 'Unknown')}
"""
        
        prompt += """
Return JSON with:
{
  "finding": "What environmental factors affect this dog",
  "confidence": "high/medium/low",
  "recommendation": "Environmental optimization advice",
  "priority": 1-10
}"""
        return prompt


# ============== Breed Agent ==============

class BreedAgent(SwarmAgent):
    """Analyzes breed-specific needs and genetic predispositions."""
    
    name = "Breed Agent"
    specialty = "Breed-Specific Health"
    
    system_prompt = """You are a veterinary geneticist specializing in breed-specific health.
Analyze breed-specific health risks and needs.
Focus on: genetic predispositions, breed-specific exercise needs,
common health issues, ideal weight ranges, and lifespan expectations.
Respond in JSON format."""

    async def analyze(self, context: Dict) -> AgentInsight:
        prompt = self.build_prompt(context)
        response = await self.llm.send_message(UserMessage(prompt))
        
        try:
            data = json.loads(response.text)
            return AgentInsight(
                agent=self.name,
                category="breed",
                finding=data.get("finding", "Breed characteristics considered"),
                confidence=ConfidenceLevel(data.get("confidence", "medium")),
                recommendation=data.get("recommendation", "Breed-appropriate care"),
                priority=data.get("priority", 5),
                supporting_data=context.get("breed_data", {})
            )
        except json.JSONDecodeError:
            return AgentInsight(
                agent=self.name,
                category="breed",
                finding="Breed-specific analysis complete",
                confidence=ConfidenceLevel.MEDIUM,
                recommendation="Continue breed-appropriate care",
                supporting_data=context.get("breed_data", {})
            )
    
    def build_prompt(self, context: Dict) -> str:
        dog = context.get("dog", {})
        breed_data = context.get("breed_data", {})
        
        prompt = f"""Analyze breed-specific health for this dog:

Dog: {dog.get('name', 'Unknown')}
Breed: {dog.get('breed', 'Unknown')}
Age: {dog.get('age_years', 0)} years
Weight: {dog.get('weight_kg', 'Unknown')} kg
Breed Traits: {breed_data.get('traits', 'Standard')}"""
        
        if breed_data.get('common_issues'):
            prompt += f"\nCommon Issues for Breed: {', '.join(breed_data['common_issues'])}"
        
        if breed_data.get('ideal_weight_range'):
            prompt += f"\nIdeal Weight Range: {breed_data['ideal_weight_range']}"
        
        prompt += """
Return JSON with:
{
  "finding": "Breed-specific health observations",
  "confidence": "high/medium/low",
  "recommendation": "Breed-tailored advice",
  "priority": 1-10
}"""
        return prompt


# ============== Healthspan Agent ==============

class HealthspanAgent(SwarmAgent):
    """Predicts long-term health trajectory and optimal lifespan."""
    
    name = "Healthspan Agent"
    specialty = "Longevity Prediction"
    
    system_prompt = """You are a longevity scientist specializing in canine healthspan.
Predict long-term health trajectory and recommend interventions.
Focus on: healthspan optimization, preventive care, early disease detection,
lifestyle factors affecting longevity, and quality of life metrics.
Respond in JSON format."""

    async def analyze(self, context: Dict) -> AgentInsight:
        prompt = self.build_prompt(context)
        response = await self.llm.send_message(UserMessage(prompt))
        
        try:
            data = json.loads(response.text)
            return AgentInsight(
                agent=self.name,
                category="healthspan",
                finding=data.get("finding", "Healthspan trajectory assessed"),
                confidence=ConfidenceLevel(data.get("confidence", "medium")),
                recommendation=data.get("recommendation", "Continue healthy lifestyle"),
                priority=data.get("priority", 5),
                supporting_data=context.get("healthspan_data", {})
            )
        except json.JSONDecodeError:
            return AgentInsight(
                agent=self.name,
                category="healthspan",
                finding="Healthspan analysis complete",
                confidence=ConfidenceLevel.MEDIUM,
                recommendation="Focus on preventive care",
                supporting_data=context.get("healthspan_data", {})
            )
    
    def build_prompt(self, context: Dict) -> str:
        dog = context.get("dog", {})
        logs = context.get("recent_logs", [])
        stats = context.get("healthspan_stats", {})
        
        # Calculate average metrics
        avg_activity = sum(l.get('active_minutes', 0) for l in logs) / max(len(logs), 1)
        moods = [l.get('mood', 'neutral') for l in logs]
        
        prompt = f"""Predict healthspan trajectory for this dog:

Dog: {dog.get('name', 'Unknown')} ({dog.get('breed', 'Unknown')})
Age: {dog.get('age_years', 0)} years
Current Weight: {dog.get('weight_kg', 'Unknown')} kg
Target Weight: {dog.get('target_weight_kg', 'Not set')} kg

Current Healthspan Score: {stats.get('current_score', 'N/A')}
Average Daily Activity: {avg_activity:.0f} minutes
Recent Moods: {', '.join(moods[-7:]) or 'No data'}
Days Tracked: {len(logs)}
"""
        
        prompt += """
Return JSON with:
{
  "finding": "Healthspan trajectory observation",
  "confidence": "high/medium/low",
  "recommendation": "Longevity optimization advice",
  "priority": 1-10
}"""
        return prompt


# ============== Social Agent ==============

class SocialAgent(SwarmAgent):
    """Analyzes social dynamics and community benchmarks."""
    
    name = "Social Agent"
    specialty = "Social and Community"
    
    system_prompt = """You are a canine community analyst.
Analyze social dynamics and community positioning.
Focus on: leaderboard performance, breed comparisons, social activities,
play behavior, and community engagement opportunities.
Respond in JSON format."""

    async def analyze(self, context: Dict) -> AgentInsight:
        prompt = self.build_prompt(context)
        response = await self.llm.send_message(UserMessage(prompt))
        
        try:
            data = json.loads(response.text)
            return AgentInsight(
                agent=self.name,
                category="social",
                finding=data.get("finding", "Social analysis complete"),
                confidence=ConfidenceLevel(data.get("confidence", "medium")),
                recommendation=data.get("recommendation", "Engage with community"),
                priority=data.get("priority", 5),
                supporting_data=context.get("social_data", {})
            )
        except json.JSONDecodeError:
            return AgentInsight(
                agent=self.name,
                category="social",
                finding="Social analysis complete",
                confidence=ConfidenceLevel.MEDIUM,
                recommendation="Consider social activities",
                supporting_data=context.get("social_data", {})
            )
    
    def build_prompt(self, context: Dict) -> str:
        dog = context.get("dog", {})
        leaderboard = context.get("leaderboard_entry", {})
        
        prompt = f"""Analyze social position for this dog:

Dog: {dog.get('name', 'Unknown')} ({dog.get('breed', 'Unknown')})
Leaderboard Rank: {leaderboard.get('rank', 'Not ranked')} of {leaderboard.get('total', 'N/A')}
Total Points: {leaderboard.get('total_points', 0)}
Current Streak: {leaderboard.get('streak', 0)} days
Score: {leaderboard.get('score', 0)}
"""
        
        prompt += """
Return JSON with:
{
  "finding": "Social/community observations",
  "confidence": "high/medium/low",
  "recommendation": "Social optimization advice",
  "priority": 1-10
}"""
        return prompt


# ============== Synthesizer Agent ==============

class SynthesizerAgent(SwarmAgent):
    """Combines all agent insights into a coherent wellness report."""
    
    name = "Synthesizer Agent"
    specialty = "Report Generation"
    
    system_prompt = """You are a chief wellness officer synthesizing multi-agent insights.
Create a coherent, prioritized wellness report from multiple specialist insights.
Focus on: prioritization, conflict resolution, actionable recommendations,
clear communication, and holistic view.
Respond in JSON format."""

    async def synthesize(
        self,
        dog: Dict,
        insights: List[AgentInsight],
        all_context: Dict
    ) -> Dict:
        """Synthesize all insights into final report."""
        
        # Sort insights by priority
        sorted_insights = sorted(insights, key=lambda x: x.priority, reverse=True)
        
        # Build context for synthesis
        prompt = self.build_synthesis_prompt(dog, sorted_insights, all_context)
        
        response = await self.llm.send_message(UserMessage(prompt))
        
        try:
            data = json.loads(response.text)
            return data
        except json.JSONDecodeError:
            # Fallback synthesis
            return self._fallback_synthesis(dog, sorted_insights)
    
    def build_synthesis_prompt(
        self,
        dog: Dict,
        insights: List[AgentInsight],
        context: Dict
    ) -> str:
        prompt = f"""Create a comprehensive wellness report for {dog.get('name', 'Unknown')}.

DOG PROFILE:
- Name: {dog.get('name', 'Unknown')}
- Breed: {dog.get('breed', 'Unknown')}
- Age: {dog.get('age_years', 0)} years
- Weight: {dog.get('weight_kg', 'Unknown')} kg

AGENT INSIGHTS (sorted by priority):
"""
        for insight in insights:
            prompt += f"""
[{insight.agent}] ({insight.category})
Finding: {insight.finding}
Confidence: {insight.confidence.value}
Recommendation: {insight.recommendation}
Priority: {insight.priority}/10
"""

        prompt += """
Generate a final wellness report in JSON format:
{
  "overall_mood": "Happy/Good/Neutral/Concerned (one word)",
  "overall_score": 0-100,
  "healthspan_delta": -30 to +30 (days of life impacted),
  "summary": "2-3 sentence holistic summary",
  "key_recommendations": ["top 3 actionable items"],
  "warnings": ["any urgent concerns, or empty array"]
}"""
        return prompt
    
    def _fallback_synthesis(
        self,
        dog: Dict,
        insights: List[AgentInsight]
    ) -> Dict:
        """Fallback synthesis when LLM fails."""
        top_insights = insights[:3]
        recommendations = [i.recommendation for i in top_insights if i.recommendation]
        
        return {
            "overall_mood": "Good",
            "overall_score": 75.0,
            "healthspan_delta": 0.5,
            "summary": f"{dog.get('name', 'Your dog')} is doing well with room for optimization.",
            "key_recommendations": recommendations[:3] if recommendations else ["Maintain current routine"],
            "warnings": []
        }


# ============== Lilo Swarm Orchestrator ==============

class LiloSwarm:
    """
    Main orchestrator for Lilo wellness swarm.
    
    Coordinates multiple specialized agents to produce
    deeply personalized wellness reports.
    """
    
    def __init__(self, api_key: str = None, model: str = DEFAULT_MODEL):
        self.api_key = api_key or OPENAI_API_KEY
        self.model = model
        
        # Initialize agents
        self.agents = {
            "activity": ActivityAgent(api_key, model),
            "nutrition": NutritionAgent(api_key, model),
            "mood": MoodAgent(api_key, model),
            "environment": EnvironmentAgent(api_key, model),
            "breed": BreedAgent(api_key, model),
            "healthspan": HealthspanAgent(api_key, model),
            "social": SocialAgent(api_key, model),
        }
        self.synthesizer = SynthesizerAgent(api_key, model)
    
    async def analyze(self, context: Dict) -> SwarmReport:
        """
        Run full swarm analysis.
        
        Args:
            context: Dict containing:
                - dog: Dog profile data
                - recent_logs: Last 7-30 days of daily logs
                - healthspan_stats: Healthspan tracking data
                - environment_data: Weather/air quality (optional)
                - breed_data: Breed information (optional)
                - leaderboard_entry: Leaderboard position (optional)
        
        Returns:
            SwarmReport with all insights and synthesized report
        """
        import time
        start_time = time.time()
        
        dog = context.get("dog", {})
        all_insights = []
        
        # Run agents in parallel
        async def run_agent(name: str, agent: SwarmAgent) -> AgentInsight:
            try:
                return await agent.analyze(context)
            except Exception as e:
                logger.error(f"Agent {name} failed: {e}")
                return AgentInsight(
                    agent=agent.name,
                    category=name,
                    finding=f"Analysis incomplete due to error",
                    confidence=ConfidenceLevel.LOW,
                    recommendation="Manual review recommended",
                    priority=3
                )
        
        # Execute all agents concurrently
        tasks = [run_agent(name, agent) for name, agent in self.agents.items()]
        insights_results = await asyncio.gather(*tasks)
        all_insights.extend(insights_results)
        
        # Synthesize final report
        synthesis = await self.synthesizer.synthesize(dog, all_insights, context)
        
        duration_ms = (time.time() - start_time) * 1000
        
        # Build final report
        report = SwarmReport(
            dog_id=dog.get("id", "unknown"),
            dog_name=dog.get("name", "Unknown"),
            breed=dog.get("breed", "Unknown"),
            age_years=dog.get("age_years", 0),
            generated_at=datetime.utcnow(),
            
            overall_mood=synthesis.get("overall_mood", "Good"),
            overall_score=synthesis.get("overall_score", 75.0),
            healthspan_delta=synthesis.get("healthspan_delta", 0.0),
            
            insights=all_insights,
            summary=synthesis.get("summary", "Wellness analysis complete."),
            key_recommendations=synthesis.get("key_recommendations", []),
            warnings=synthesis.get("warnings", []),
            
            agent_count=len(self.agents),
            analysis_duration_ms=round(duration_ms, 2),
            model_used=self.model
        )
        
        return report
    
    async def quick_analyze(self, context: Dict) -> Dict:
        """
        Quick analysis using fewer agents for faster response.
        Uses only Activity, Mood, and Nutrition agents.
        """
        dog = context.get("dog", {})
        
        quick_agents = ["activity", "nutrition", "mood"]
        insights = []
        
        for name in quick_agents:
            agent = self.agents[name]
            try:
                insight = await agent.analyze(context)
                insights.append(insight)
            except Exception as e:
                logger.error(f"Quick agent {name} failed: {e}")
        
        return {
            "dog_name": dog.get("name", "Unknown"),
            "quick_insights": [asdict(i) for i in insights],
            "model_used": self.model
        }


# ============== Factory Function ==============

def create_swarm(api_key: str = None, model: str = None) -> LiloSwarm:
    """Create a configured Lilo swarm instance."""
    return LiloSwarm(api_key=api_key, model=model or DEFAULT_MODEL)


# ============== Enhancement 1: Ephemeral Agents ==============
# Inspired by ruv-FANN: spin up only needed agents per request

from dataclasses import dataclass
from typing import Set, List

class AgentSelector:
    """
    Determines which agents to run based on request context.
    This is the "ephemeral" part - we only instantiate what we need.
    """
    
    # Agent capabilities mapping
    AGENT_TRIGGERS = {
        "activity": {
            "triggers": ["active_minutes", "steps", "walks", "exercise", "play"],
            "priority": 1  # Always include if data exists
        },
        "nutrition": {
            "triggers": ["meals", "food", "diet", "weight", "treats"],
            "priority": 1
        },
        "mood": {
            "triggers": ["mood", "energy", "behavior", "photo"],
            "priority": 1
        },
        "environment": {
            "triggers": ["weather", "temperature", "air_quality", "aqi", "location"],
            "priority": 2
        },
        "breed": {
            "triggers": ["breed", "genetic", "size"],
            "priority": 2
        },
        "healthspan": {
            "triggers": ["healthspan", "lifespan", "veterinary", "age"],
            "priority": 2
        },
        "social": {
            "triggers": ["leaderboard", "points", "rank", "streak", "community"],
            "priority": 3
        }
    }
    
    @classmethod
    def select_agents(cls, context: Dict, mode: str = "auto") -> List[str]:
        """
        Select which agents to run based on context.
        
        Args:
            context: Request context with available data
            mode: "auto" (context-based), "quick" (3 agents), "full" (all 7), "minimal" (1)
        
        Returns:
            List of agent names to run
        """
        if mode == "quick":
            return ["activity", "nutrition", "mood"]
        elif mode == "full":
            return list(cls.AGENT_TRIGGERS.keys())
        elif mode == "minimal":
            return ["mood"]  # Just mood for fastest response
        
        # Auto mode: select based on available data
        selected = []
        context_str = json.dumps(context).lower()
        
        for agent, config in cls.AGENT_TRIGGERS.items():
            for trigger in config["triggers"]:
                if trigger in context_str:
                    if agent not in selected:
                        selected.append(agent)
                    break
        
        # Always include at least mood if nothing triggered
        if not selected:
            selected = ["mood"]
        
        # Sort by priority
        priority_map = {a: config["priority"] for a, config in cls.AGENT_TRIGGERS.items()}
        selected.sort(key=lambda x: priority_map.get(x, 99))
        
        return selected
    
    @classmethod
    def estimate_duration(cls, agent_count: int) -> Dict:
        """Estimate analysis duration based on agent count."""
        base_ms = 500  # Base overhead
        per_agent_ms = 300  # Average per agent
        return {
            "estimated_ms": base_ms + (per_agent_ms * agent_count),
            "tokens_estimate": agent_count * 200
        }


# ============== Enhancement 2: Agent Learning ==============
# Persist agent learnings per dog for continuous improvement

@dataclass
class AgentLearning:
    """Learned pattern from an agent about a specific dog."""
    dog_id: str
    agent: str
    category: str
    pattern: str  # What was learned
    evidence: List[str]  # Supporting data points
    confidence: float  # 0.0-1.0
    learned_at: datetime
    last_validated: datetime
    is_active: bool = True


class LearningStore:
    """
    Persistent learning storage for agent insights.
    
    Stores learned patterns per dog so agents can:
    - Remember what worked for this specific dog
    - Build on previous insights
    - Avoid repeating failed recommendations
    """
    
    def __init__(self, storage_path: str = None):
        self.storage_path = storage_path or "swarm_learnings.json"
        self._learnings: Dict[str, List[AgentLearning]] = {}
        self._load()
    
    def _load(self):
        """Load learnings from disk."""
        try:
            if os.path.exists(self.storage_path):
                with open(self.storage_path, 'r') as f:
                    data = json.load(f)
                    self._learnings = {
                        dog_id: [AgentLearning(**l) for l in learnings]
                        for dog_id, learnings in data.items()
                    }
        except Exception as e:
            logger.warning(f"Failed to load learnings: {e}")
            self._learnings = {}
    
    def _save(self):
        """Save learnings to disk."""
        try:
            data = {
                dog_id: [asdict(l) for l in learnings]
                for dog_id, learnings in self._learnings.items()
            }
            with open(self.storage_path, 'w') as f:
                json.dump(data, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Failed to save learnings: {e}")
    
    def store_learning(
        self,
        dog_id: str,
        insight: AgentInsight,
        validated: bool = False
    ) -> AgentLearning:
        """
        Store a new learning from an agent's insight.
        
        Args:
            dog_id: The dog's ID
            insight: The insight to learn from
            validated: Whether this was validated by user feedback
        """
        learning = AgentLearning(
            dog_id=dog_id,
            agent=insight.agent,
            category=insight.category,
            pattern=insight.recommendation,
            evidence=[insight.finding],
            confidence=0.7 if validated else 0.5,
            learned_at=datetime.utcnow(),
            last_validated=datetime.utcnow() if validated else datetime.min,
            is_active=True
        )
        
        if dog_id not in self._learnings:
            self._learnings[dog_id] = []
        
        # Check for duplicate patterns
        for existing in self._learnings[dog_id]:
            if existing.pattern == learning.pattern and existing.is_active:
                # Update confidence
                existing.confidence = min(1.0, existing.confidence + 0.1)
                existing.last_validated = datetime.utcnow()
                if validated:
                    existing.is_active = True
                self._save()
                return existing
        
        self._learnings[dog_id].append(learning)
        self._save()
        return learning
    
    def get_learnings(self, dog_id: str, agent: str = None) -> List[AgentLearning]:
        """Get learnings for a dog, optionally filtered by agent."""
        learnings = self._learnings.get(dog_id, [])
        if agent:
            learnings = [l for l in learnings if l.agent == agent and l.is_active]
        else:
            learnings = [l for l in learnings if l.is_active]
        return sorted(learnings, key=lambda x: x.confidence, reverse=True)
    
    def invalidate_learning(self, dog_id: str, pattern: str):
        """Mark a learning as inactive (e.g., user rejected it)."""
        learnings = self._learnings.get(dog_id, [])
        for learning in learnings:
            if learning.pattern == pattern:
                learning.is_active = False
        self._save()
    
    def get_context_for_agent(
        self,
        dog_id: str,
        agent: str,
        max_learnings: int = 3
    ) -> Dict:
        """
        Get learned context to inject into agent prompts.
        
        This is the "memory" aspect - agents remember what they learned
        about this specific dog over time.
        """
        learnings = self.get_learnings(dog_id, agent)[:max_learnings]
        
        if not learnings:
            return {"learnings": [], "context": "No prior learnings for this dog."}
        
        context_parts = []
        for l in learnings:
            context_parts.append(
                f"[{l.agent}] Previously learned: {l.pattern} "
                f"(confidence: {l.confidence:.0%}, validated: {l.is_active})"
            )
        
        return {
            "learnings": learnings,
            "context": "Prior insights about this dog: " + " ".join(context_parts)
        }
    
    def merge_with_context(
        self,
        base_context: Dict,
        dog_id: str,
        agents: List[str]
    ) -> Dict:
        """
        Merge learned patterns into base context for agents.
        
        This enriches the context with historical learnings,
        making each agent smarter about the specific dog.
        """
        enriched_context = base_context.copy()
        
        for agent in agents:
            agent_learnings = self.get_context_for_agent(dog_id, agent)
            key = f"{agent}_learnings"
            enriched_context[key] = agent_learnings
            
            # Also add to base context under agent-specific key
            if agent not in enriched_context:
                enriched_context[agent] = {}
            enriched_context[agent]["learned_patterns"] = agent_learnings["learnings"]
        
        return enriched_context


# Global learning store instance
_global_learning_store: Optional[LearningStore] = None

def get_learning_store() -> LearningStore:
    """Get or create the global learning store."""
    global _global_learning_store
    if _global_learning_store is None:
        _global_learning_store = LearningStore()
    return _global_learning_store


# ============== Enhanced Lilo Swarm with Ephemeral + Learning ==============

class LiloSwarmEnhanced:
    """
    Enhanced Lilo Swarm with ephemeral agents and learning.
    
    Key features:
    1. Ephemeral: Only spins up needed agents per request
    2. Learning: Persists and retrieves learnings per dog
    3. Adaptive: Agents get smarter about each dog over time
    """
    
    def __init__(self, api_key: str = None, model: str = DEFAULT_MODEL):
        self.api_key = api_key or OPENAI_API_KEY
        self.model = model
        self.learnings = get_learning_store()
        
        # Agent factory - creates agents on-demand
        self._agent_classes = {
            "activity": ActivityAgent,
            "nutrition": NutritionAgent,
            "mood": MoodAgent,
            "environment": EnvironmentAgent,
            "breed": BreedAgent,
            "healthspan": HealthspanAgent,
            "social": SocialAgent,
        }
        self._synthesizer = SynthesizerAgent(api_key, model)
    
    def _create_agent(self, name: str) -> SwarmAgent:
        """Create an agent instance (ephemeral - on-demand)."""
        agent_class = self._agent_classes.get(name)
        if not agent_class:
            raise ValueError(f"Unknown agent: {name}")
        return agent_class(self.api_key, self.model)
    
    async def analyze(
        self,
        context: Dict,
        mode: str = "auto"
    ) -> SwarmReport:
        """
        Run swarm analysis with ephemeral agents and learning.
        
        Args:
            context: Request context (dog, logs, etc.)
            mode: "auto", "quick", "full", or "minimal"
        
        Returns:
            SwarmReport with insights and synthesized report
        """
        import time
        start_time = time.time()
        
        dog = context.get("dog", {})
        dog_id = dog.get("id", "unknown")
        
        # Ephemeral agent selection
        selected_agents = AgentSelector.select_agents(context, mode)
        duration_estimate = AgentSelector.estimate_duration(len(selected_agents))
        
        logger.info(f"Swarm: Running {len(selected_agents)} agents: {selected_agents}")
        logger.info(f"Swarm: Estimated duration: {duration_estimate['estimated_ms']}ms")
        
        # Enrich context with learnings (enhancement 2)
        enriched_context = self.learnings.merge_with_context(
            context,
            dog_id,
            selected_agents
        )
        
        # Run selected agents (ephemeral)
        async def run_agent(name: str) -> AgentInsight:
            agent = self._create_agent(name)  # Create on-demand
            try:
                insight = await agent.analyze(enriched_context)
                # Store learning
                self.learnings.store_learning(dog_id, insight)
                return insight
            except Exception as e:
                logger.error(f"Agent {name} failed: {e}")
                return AgentInsight(
                    agent=name.title() + " Agent",
                    category=name,
                    finding=f"Analysis incomplete",
                    confidence=ConfidenceLevel.LOW,
                    recommendation="Manual review needed",
                    priority=3
                )
        
        # Execute agents concurrently
        tasks = [run_agent(name) for name in selected_agents]
        insights = await asyncio.gather(*tasks)
        
        # Synthesize report
        synthesis = await self._synthesizer.synthesize(dog, insights, enriched_context)
        
        duration_ms = (time.time() - start_time) * 1000
        
        return SwarmReport(
            dog_id=dog_id,
            dog_name=dog.get("name", "Unknown"),
            breed=dog.get("breed", "Unknown"),
            age_years=dog.get("age_years", 0),
            generated_at=datetime.utcnow(),
            overall_mood=synthesis.get("overall_mood", "Good"),
            overall_score=synthesis.get("overall_score", 75.0),
            healthspan_delta=synthesis.get("healthspan_delta", 0.0),
            insights=insights,
            summary=synthesis.get("summary", "Analysis complete."),
            key_recommendations=synthesis.get("key_recommendations", []),
            warnings=synthesis.get("warnings", []),
            agent_count=len(selected_agents),
            analysis_duration_ms=round(duration_ms, 2),
            model_used=self.model
        )
    
    async def quick_analyze(self, context: Dict) -> Dict:
        """Quick analysis with minimal agents."""
        report = await self.analyze(context, mode="quick")
        return {
            "dog_name": report.dog_name,
            "overall_mood": report.overall_mood,
            "summary": report.summary,
            "quick_insights": [asdict(i) for i in report.insights],
            "agent_count": report.agent_count,
            "analysis_duration_ms": report.analysis_duration_ms,
            "model_used": report.model_used
        }
    
    def get_dog_learnings(self, dog_id: str) -> List[Dict]:
        """Get all learnings for a specific dog."""
        learnings = self.learnings.get_learnings(dog_id)
        return [
            {
                "agent": l.agent,
                "category": l.category,
                "pattern": l.pattern,
                "confidence": l.confidence,
                "learned_at": l.learned_at.isoformat(),
                "is_active": l.is_active
            }
            for l in learnings
        ]
    
    def validate_learning(self, dog_id: str, pattern: str, accepted: bool):
        """
        Validate a learning based on user feedback.
        
        Args:
            dog_id: The dog's ID
            pattern: The pattern to validate
            accepted: True if user accepted, False if rejected
        """
        if accepted:
            # Re-store to boost confidence
            learnings = self.learnings.get_learnings(dog_id)
            for l in learnings:
                if l.pattern == pattern:
                    l.confidence = min(1.0, l.confidence + 0.15)
                    l.last_validated = datetime.utcnow()
                    self.learnings._save()
        else:
            # Mark as inactive
            self.learnings.invalidate_learning(dog_id, pattern)


def create_enhanced_swarm(api_key: str = None, model: str = None) -> LiloSwarmEnhanced:
    """Create an enhanced Lilo swarm instance."""
    return LiloSwarmEnhanced(api_key=api_key, model=model or DEFAULT_MODEL)


# ============== Enhancement 3: Forecasting Agent (ruv-FANN Integration) ==============

from activity_forecaster import (
    create_forecaster as create_activity_forecaster,
    logs_to_datapoints,
    ActivityForecaster
)

class ForecastingAgent(SwarmAgent):
    """
    Forecasting agent using time-series analysis.
    
    Provides activity predictions based on historical patterns.
    Uses statistical forecasting (can be enhanced with ruv-FANN neural networks).
    """
    
    name = "Forecasting Agent"
    specialty = "Activity Predictions"
    
    system_prompt = """You are a canine activity forecasting specialist.
Analyze activity patterns and provide predictions.
Focus on: trend analysis, pattern recognition, optimal activity scheduling,
and motivational insights based on forecast data.
Respond in JSON format."""

    async def analyze(self, context: Dict) -> AgentInsight:
        prompt = self.build_prompt(context)
        response = await self.llm.send_message(UserMessage(prompt))
        
        try:
            data = json.loads(response.text)
            return AgentInsight(
                agent=self.name,
                category="forecasting",
                finding=data.get("finding", "Forecast analyzed"),
                confidence=ConfidenceLevel(data.get("confidence", "medium")),
                recommendation=data.get("recommendation", "Stay consistent"),
                priority=data.get("priority", 5),
                supporting_data=context.get("forecast_data", {})
            )
        except json.JSONDecodeError:
            return AgentInsight(
                agent=self.name,
                category="forecasting",
                finding="Activity forecast analyzed",
                confidence=ConfidenceLevel.MEDIUM,
                recommendation="Continue tracking activity for better predictions",
                supporting_data=context.get("forecast_data", {})
            )
    
    def build_prompt(self, context: Dict) -> str:
        dog = context.get("dog", {})
        forecast_data = context.get("forecast_data", {})
        logs = context.get("recent_logs", [])
        
        prompt = f"""Analyze this dog's activity forecast:

Dog: {dog.get('name', 'Unknown')} ({dog.get('breed', 'Unknown')})

Forecast Analysis:
- Days Analyzed: {forecast_data.get('days_analyzed', len(logs))}
- Activity Trend: {forecast_data.get('activity_trend', 'stable')}
- Consistency Score: {forecast_data.get('consistency_score', 0):.0f}%
- Best Day: {forecast_data.get('best_day', 'Unknown')}
- Cycle Detected: {forecast_data.get('cycle_detected', 'None')}

Predictions:
"""
        for pred in forecast_data.get('predictions', [])[:3]:
            prompt += f"- {pred.get('date')}: {pred.get('predicted_minutes')} min ({pred.get('confidence')}%)\n"
        
        prompt += f"""
Recommendations:
{chr(10).join('- ' + r for r in forecast_data.get('recommendations', [])[:2])}

Return JSON with:
{{
  "finding": "What the forecast reveals about activity patterns",
  "confidence": "high/medium/low",
  "recommendation": "Actionable advice based on forecast",
  "priority": 1-10
}}"""
        return prompt


# ============== Enhanced Swarm with Forecasting Integration ==============

class LiloSwarmWithForecasting(LiloSwarmEnhanced):
    """
    Extended Lilo Swarm with ruv-FANN-style forecasting.
    
    Adds the ForecastingAgent to the swarm for activity predictions.
    """
    
    def __init__(self, api_key: str = None, model: str = DEFAULT_MODEL):
        super().__init__(api_key, model)
        
        # Add forecasting agent to agent classes
        self._agent_classes["forecasting"] = ForecastingAgent
    
    async def analyze_with_forecast(
        self,
        context: Dict,
        mode: str = "auto",
        include_forecast: bool = True
    ) -> SwarmReport:
        """
        Run swarm analysis including forecasting data.
        
        Args:
            context: Request context
            mode: Analysis mode
            include_forecast: Whether to generate forecast data
        
        Returns:
            SwarmReport with insights including forecasting
        """
        dog = context.get("dog", {})
        logs = context.get("recent_logs", [])
        
        # Generate forecast if requested and we have enough data
        if include_forecast and len(logs) >= 3:
            try:
                data_points = logs_to_datapoints(logs)
                forecaster = create_activity_forecaster()
                forecast = forecaster.forecast(
                    dog_id=dog.get("id", "unknown"),
                    dog_name=dog.get("name", "Unknown"),
                    data_points=data_points,
                    forecast_days=7
                )
                
                # Add forecast data to context
                context["forecast_data"] = {
                    "days_analyzed": forecast.days_analyzed,
                    "activity_trend": forecast.activity_trend,
                    "consistency_score": forecast.consistency_score,
                    "best_day": forecast.best_day,
                    "cycle_detected": forecast.cycle_detected,
                    "predictions": [
                        {"date": f.date, "predicted_minutes": f.predicted_minutes, "confidence": f.confidence}
                        for f in forecast.forecast
                    ],
                    "recommendations": forecast.recommendations,
                    "anomalies": forecast.anomalies
                }
                
                logger.info(f"Generated forecast: {forecast.activity_trend} trend, {forecast.consistency_score}% consistency")
                
            except Exception as e:
                logger.warning(f"Forecast generation failed: {e}")
                context["forecast_data"] = {"error": str(e)}
        
        # Run normal analysis
        return await self.analyze(context, mode)


def create_swarm_with_forecasting(api_key: str = None, model: str = None) -> LiloSwarmWithForecasting:
    """Create a Lilo swarm with forecasting capabilities."""
    return LiloSwarmWithForecasting(api_key=api_key, model=model or DEFAULT_MODEL)


# ============== Phase 2: Photo Agent (Mood Detection from Photos) ==============

from photo_mood_analyzer import PhotoMoodAgent, MoodLevel, EnergyLevel

class PhotoAgent(SwarmAgent):
    """
    Photo-based mood analysis agent.
    
    Analyzes photos for visual mood indicators and integrates
    with the swarm's wellness assessment.
    """
    
    name = "Photo Agent"
    specialty = "Visual Mood Analysis"
    
    system_prompt = """You are a canine photo mood analyst.
Analyze mood indicators from photo descriptions.
Focus on: visual cues, emotional state, physical presentation.
Respond in JSON format."""

    async def analyze(self, context: Dict) -> AgentInsight:
        prompt = self.build_prompt(context)
        response = await self.llm.send_message(UserMessage(prompt))
        
        try:
            data = json.loads(response.text)
            return AgentInsight(
                agent=self.name,
                category="photo_mood",
                finding=data.get("finding", "Photo mood analyzed"),
                confidence=ConfidenceLevel(data.get("confidence", "medium")),
                recommendation=data.get("recommendation", "Continue photo tracking"),
                priority=data.get("priority", 5),
                supporting_data=context.get("photo_data", {})
            )
        except json.JSONDecodeError:
            return AgentInsight(
                agent=self.name,
                category="photo_mood",
                finding="Photo mood analyzed",
                confidence=ConfidenceLevel.MEDIUM,
                recommendation="Continue tracking mood with photos",
                supporting_data=context.get("photo_data", {})
            )
    
    def build_prompt(self, context: Dict) -> str:
        dog = context.get("dog", {})
        photo_data = context.get("photo_data", {})
        
        prompt = f"""Analyze photo mood data for this dog:

Dog: {dog.get('name', 'Unknown')} ({dog.get('breed', 'Unknown')})

Photo Analysis Data:
- Mood: {photo_data.get('mood', 'unknown')}
- Mood Confidence: {photo_data.get('mood_confidence', 0):.0f}%
- Energy Level: {photo_data.get('energy', 'unknown')}
- Wellness Score: {photo_data.get('wellness_score', 0):.0f}
- Health Status: {photo_data.get('health_status', 'unknown')}
"""
        
        if photo_data.get('indicators'):
            prompt += f"\nMood Indicators: {', '.join(photo_data['indicators'])}"
        
        if photo_data.get('warnings'):
            prompt += f"\nWarnings: {', '.join(photo_data['warnings'])}"
        
        prompt += """
Return JSON with:
{
  "finding": "What the photo reveals about mood",
  "confidence": "high/medium/low",
  "recommendation": "Advice based on photo analysis",
  "priority": 1-10
}"""
        return prompt


# ============== Complete Swarm with Photo + Forecasting ==============

class LiloSwarmComplete(LiloSwarmWithForecasting):
    """
    Complete Lilo Swarm with all enhancements:
    - All 8 specialized agents
    - Forecasting integration
    - Photo mood analysis
    - Learning persistence
    - Ephemeral agent selection
    """
    
    def __init__(self, api_key: str = None, model: str = DEFAULT_MODEL):
        super().__init__(api_key, model)
        
        # Add photo agent
        self._agent_classes["photo"] = PhotoAgent
        
        # Photo analyzer for direct photo analysis
        self._photo_analyzer = PhotoMoodAgent(api_key, model)
    
    async def analyze_with_photo(
        self,
        context: Dict,
        mode: str = "auto",
        include_forecast: bool = True,
        include_photo_analysis: bool = False,
        photo_data: str = None
    ) -> SwarmReport:
        """
        Run complete swarm analysis including photo mood data.
        
        Args:
            context: Request context
            mode: Analysis mode
            include_forecast: Include activity forecasting
            include_photo_analysis: Run photo analysis
            photo_data: Base64 photo for analysis
        
        Returns:
            SwarmReport with all insights
        """
        # Add photo data to context if provided
        if include_photo_analysis and photo_data:
            try:
                photo_analysis = await self._photo_analyzer.analyze_photo(
                    photo_data=photo_data,
                    dog_id=context.get("dog", {}).get("id", "unknown")
                )
                
                context["photo_data"] = {
                    "mood": photo_analysis.mood.value,
                    "mood_confidence": photo_analysis.mood_confidence,
                    "energy": photo_analysis.energy_level.value,
                    "wellness_score": photo_analysis.overall_wellness_score,
                    "health_status": photo_analysis.health_status.value,
                    "indicators": photo_analysis.mood_indicators + photo_analysis.energy_indicators,
                    "warnings": photo_analysis.warnings
                }
                
                logger.info(f"Photo analysis complete: {photo_analysis.mood.value} mood detected")
                
            except Exception as e:
                logger.warning(f"Photo analysis failed: {e}")
                context["photo_data"] = {"error": str(e)}
        
        # Run base analysis with forecast
        return await self.analyze_with_forecast(context, mode, include_forecast)


def create_complete_swarm(api_key: str = None, model: str = None) -> LiloSwarmComplete:
    """Create the complete Lilo swarm with all features."""
    return LiloSwarmComplete(api_key=api_key, model=model or DEFAULT_MODEL)
