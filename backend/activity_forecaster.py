"""
Activity Forecaster: Time-Series Forecasting for Dog Wellness
============================================================
Inspired by ruv-FANN ephemeral intelligence pattern.

This module provides time-series forecasting for dog activity patterns:
- Activity trend analysis
- Cyclic pattern detection (daily, weekly)
- Anomaly detection
- Future activity predictions
- Recovery time forecasting

The forecasting uses lightweight statistical methods that can be enhanced
with ruv-FANN neural networks when available.
"""

import os
import json
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional, Tuple, Any
from datetime import datetime, date, timedelta
from collections import defaultdict
import statistics
import logging

logger = logging.getLogger(__name__)

# ============== Data Models ==============

@dataclass
class ActivityDataPoint:
    """Single activity data point."""
    date: str
    active_minutes: int
    steps: int
    walks: int
    mood: str
    quality_score: float = 0.0  # 0-100

@dataclass
class ForecastResult:
    """Forecast for a single day."""
    date: str
    predicted_minutes: int
    confidence: float  # 0-100
    trend: str  # "increasing", "stable", "decreasing"
    factors: List[str]  # What influenced the prediction

@dataclass
class ActivityForecast:
    """Complete activity forecast report."""
    dog_id: str
    dog_name: str
    generated_at: datetime
    
    # Historical summary
    days_analyzed: int
    avg_daily_minutes: float
    avg_daily_steps: float
    activity_trend: str  # "improving", "stable", "declining"
    consistency_score: float  # 0-100
    
    # Pattern detection
    best_day: str  # Day of week with most activity
    best_time: str  # Time of day preference
    cycle_detected: Optional[str]  # "daily", "weekly", or None
    
    # Predictions
    forecast: List[ForecastResult]
    forecast_days: int
    
    # Anomalies
    anomalies: List[Dict]  # Unusual activity patterns
    anomaly_count: int
    
    # Recommendations
    recommendations: List[str]

# ============== Statistical Forecasting Engine ==============

class SimpleMovingAverage:
    """Simple moving average for smoothing."""
    
    def __init__(self, window: int = 7):
        self.window = window
    
    def calculate(self, data: List[float]) -> List[float]:
        if len(data) < self.window:
            return data
        
        result = []
        for i in range(len(data)):
            start = max(0, i - self.window + 1)
            window_data = data[start:i + 1]
            result.append(sum(window_data) / len(window_data))
        
        return result
    
    def predict_next(self, data: List[float]) -> float:
        if not data:
            return 0.0
        recent = data[-self.window:] if len(data) >= self.window else data
        return sum(recent) / len(recent)

class ExponentialSmoothing:
    """Exponential smoothing for trend-aware forecasting."""
    
    def __init__(self, alpha: float = 0.3):
        self.alpha = alpha  # Smoothing factor (0-1)
    
    def calculate(self, data: List[float]) -> Tuple[List[float], float, float]:
        if not data:
            return [], 0.0, 0.0
        
        smoothed = [data[0]]
        level = data[0]
        trend = 0.0
        
        for i in range(1, len(data)):
            # Double exponential smoothing
            prev_level = level
            level = self.alpha * data[i] + (1 - self.alpha) * (level + trend)
            trend = 0.1 * (level - prev_level) + 0.9 * trend
            smoothed.append(level + trend)
        
        # Predict next value
        predicted = level + trend
        confidence = self._calculate_confidence(data, smoothed)
        
        return smoothed, predicted, confidence
    
    def _calculate_confidence(self, data: List[float], smoothed: List[float]) -> float:
        if len(data) < 2:
            return 50.0
        
        # Calculate standard deviation of errors
        errors = [abs(data[i] - smoothed[i]) for i in range(len(data))]
        std_dev = statistics.stdev(errors) if len(errors) > 1 else 0
        
        # Convert to confidence percentage
        mean_val = statistics.mean(data) if data else 1
        cv = std_dev / mean_val if mean_val > 0 else 1
        
        confidence = max(0, min(100, 100 - (cv * 100)))
        return confidence

class TrendAnalyzer:
    """Analyzes trends in activity data."""
    
    def __init__(self):
        self.min_data_points = 5
    
    def analyze(self, data: List[float]) -> Dict:
        if len(data) < self.min_data_points:
            return {
                "trend": "insufficient_data",
                "slope": 0.0,
                "strength": 0.0,
                "prediction": statistics.mean(data) if data else 0
            }
        
        # Calculate linear regression
        n = len(data)
        x = list(range(n))
        
        x_mean = sum(x) / n
        y_mean = sum(data) / n
        
        numerator = sum((x[i] - x_mean) * (data[i] - y_mean) for i in range(n))
        denominator = sum((x[i] - x_mean) ** 2 for i in range(n))
        
        if denominator == 0:
            slope = 0
        else:
            slope = numerator / denominator
        
        # Calculate R-squared (trend strength)
        ss_tot = sum((data[i] - y_mean) ** 2 for i in range(n))
        ss_res = sum((data[i] - (y_mean + slope * (i - x_mean))) ** 2 for i in range(n))
        
        r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0
        
        # Determine trend direction
        if abs(slope) < 0.1:
            trend = "stable"
        elif slope > 0:
            trend = "increasing"
        else:
            trend = "decreasing"
        
        # Predict next value
        prediction = y_mean + slope * n
        
        return {
            "trend": trend,
            "slope": slope,
            "strength": abs(r_squared),  # 0-1
            "prediction": max(0, prediction),
            "weekly_change": slope * 7
        }

class PatternDetector:
    """Detects cyclic patterns in activity data."""
    
    def __init__(self):
        self.day_names = ["Monday", "Tuesday", "Wednesday", "Thursday", 
                         "Friday", "Saturday", "Sunday"]
    
    def detect_day_of_week_pattern(
        self, 
        data_points: List[ActivityDataPoint]
    ) -> Dict:
        """Detect if activity varies by day of week."""
        
        # Group by day of week
        day_stats = defaultdict(list)
        for dp in data_points:
            day_of_week = datetime.fromisoformat(dp.date).weekday()
            day_stats[day_of_week].append(dp.active_minutes)
        
        # Calculate averages
        day_averages = {}
        for day_idx, minutes_list in day_stats.items():
            if minutes_list:
                day_averages[self.day_names[day_idx]] = statistics.mean(minutes_list)
        
        if len(day_averages) < 3:
            return {"detected": False}
        
        # Find best day
        best_day = max(day_averages, key=day_averages.get)
        overall_avg = statistics.mean(day_averages.values())
        
        # Check for significant variation
        variance = statistics.stdev(day_averages.values()) if len(day_averages) > 1 else 0
        cv = variance / overall_avg if overall_avg > 0 else 0
        
        return {
            "detected": cv > 0.15,  # 15% coefficient of variation
            "best_day": best_day,
            "best_day_avg": day_averages.get(best_day, 0),
            "day_averages": day_averages,
            "variation_coefficient": cv
        }
    
    def detect_time_of_day_pattern(self, logs: List[Dict]) -> Dict:
        """Detect preferred activity times from log notes."""
        # This would ideally parse timestamps
        # For now, return placeholder
        return {
            "detected": False,
            "preferred_time": "morning",
            "confidence": 50.0
        }

class AnomalyDetector:
    """Detects unusual activity patterns."""
    
    def __init__(self, threshold: float = 2.0):
        self.threshold = threshold  # Standard deviations
    
    def detect(self, data: List[float]) -> List[Dict]:
        if len(data) < 5:
            return []
        
        mean = statistics.mean(data)
        std_dev = statistics.stdev(data)
        
        anomalies = []
        for i, value in enumerate(data):
            z_score = abs(value - mean) / std_dev if std_dev > 0 else 0
            
            if z_score > self.threshold:
                anomalies.append({
                    "index": i,
                    "value": value,
                    "z_score": z_score,
                    "type": "spike" if value > mean else "dip",
                    "deviation_pct": ((value - mean) / mean * 100) if mean > 0 else 0
                })
        
        return anomalies

# ============== Activity Forecaster ==============

class ActivityForecaster:
    """
    Main forecasting engine for dog activity.
    
    Combines multiple statistical methods for comprehensive forecasting.
    """
    
    def __init__(self):
        self.sma = SimpleMovingAverage(window=7)
        self.exp_smooth = ExponentialSmoothing(alpha=0.3)
        self.trend = TrendAnalyzer()
        self.pattern = PatternDetector()
        self.anomaly = AnomalyDetector(threshold=2.0)
    
    def forecast(
        self,
        dog_id: str,
        dog_name: str,
        data_points: List[ActivityDataPoint],
        forecast_days: int = 7
    ) -> ActivityForecast:
        """
        Generate comprehensive activity forecast.
        
        Args:
            dog_id: Dog's ID
            dog_name: Dog's name
            data_points: Historical activity data
            forecast_days: Number of days to forecast
        
        Returns:
            ActivityForecast with predictions and insights
        """
        
        # Sort by date
        data_points = sorted(data_points, key=lambda x: x.date)
        
        # Extract time series
        minutes_series = [dp.active_minutes for dp in data_points]
        steps_series = [dp.steps for dp in data_points]
        
        # Calculate historical stats
        days_analyzed = len(data_points)
        avg_daily_minutes = statistics.mean(minutes_series) if minutes_series else 0
        avg_daily_steps = statistics.mean(steps_series) if steps_series else 0
        
        # Analyze trend
        trend_analysis = self.trend.analyze(minutes_series)
        activity_trend = trend_analysis["trend"]
        
        # Calculate consistency
        if len(minutes_series) > 1:
            consistency_score = max(0, 100 - (statistics.stdev(minutes_series) / 
                                              (avg_daily_minutes + 1) * 100))
        else:
            consistency_score = 50.0
        
        # Detect patterns
        day_pattern = self.pattern.detect_day_of_week_pattern(data_points)
        time_pattern = self.pattern.detect_time_of_day_pattern(
            [{"date": dp.date, "mood": dp.mood} for dp in data_points]
        )
        
        # Detect anomalies
        anomalies = self.anomaly.detect(minutes_series)
        anomaly_details = []
        for a in anomalies:
            if a["index"] < len(data_points):
                anomaly_details.append({
                    "date": data_points[a["index"]].date,
                    "type": a["type"],
                    "actual_minutes": a["value"],
                    "expected_minutes": avg_daily_minutes,
                    "deviation": f"{a['deviation_pct']:.1f}%"
                })
        
        # Generate forecasts
        forecasts = self._generate_forecast(
            minutes_series, 
            avg_daily_minutes, 
            trend_analysis,
            forecast_days
        )
        
        # Generate recommendations
        recommendations = self._generate_recommendations(
            activity_trend,
            consistency_score,
            day_pattern,
            anomalies
        )
        
        return ActivityForecast(
            dog_id=dog_id,
            dog_name=dog_name,
            generated_at=datetime.utcnow(),
            days_analyzed=days_analyzed,
            avg_daily_minutes=round(avg_daily_minutes, 1),
            avg_daily_steps=round(avg_daily_steps, 0),
            activity_trend=activity_trend,
            consistency_score=round(consistency_score, 1),
            best_day=day_pattern.get("best_day", "Unknown"),
            best_time=time_pattern.get("preferred_time", "morning"),
            cycle_detected="weekly" if day_pattern.get("detected") else None,
            forecast=forecasts,
            forecast_days=forecast_days,
            anomalies=anomaly_details,
            anomaly_count=len(anomaly_details),
            recommendations=recommendations
        )
    
    def _generate_forecast(
        self,
        series: List[float],
        baseline: float,
        trend_analysis: Dict,
        days: int
    ) -> List[ForecastResult]:
        """Generate daily forecasts."""
        
        forecasts = []
        
        # Use exponential smoothing for base prediction
        smoothed, predicted, confidence = self.exp_smooth.calculate(series)
        
        # Apply trend adjustment
        slope = trend_analysis.get("slope", 0)
        trend_strength = trend_analysis.get("strength", 0)
        
        for i in range(days):
            forecast_date = date.today() + timedelta(days=i + 1)
            
            # Predicted value with trend
            daily_change = slope * trend_strength
            pred_minutes = max(0, predicted + (daily_change * i))
            
            # Confidence decreases with distance
            distance_confidence = max(50, confidence - (i * 5))
            
            # Determine trend direction
            if i == 0:
                comparison = series[-1] if series else pred_minutes
            else:
                comparison = forecasts[i-1].predicted_minutes
            
            if pred_minutes > comparison * 1.05:
                trend = "increasing"
            elif pred_minutes < comparison * 0.95:
                trend = "decreasing"
            else:
                trend = "stable"
            
            # Factors influencing prediction
            factors = []
            if trend_analysis["trend"] == "increasing":
                factors.append("Historical upward trend")
            elif trend_analysis["trend"] == "decreasing":
                factors.append("Historical downward trend")
            if i > 0:
                factors.append(f"Day {i+1} forecast")
            
            forecasts.append(ForecastResult(
                date=forecast_date.isoformat(),
                predicted_minutes=round(pred_minutes),
                confidence=round(distance_confidence, 1),
                trend=trend,
                factors=factors
            ))
        
        return forecasts
    
    def _generate_recommendations(
        self,
        trend: str,
        consistency: float,
        day_pattern: Dict,
        anomalies: List[Dict]
    ) -> List[str]:
        """Generate actionable recommendations."""
        
        recommendations = []
        
        # Trend-based recommendations
        if trend == "decreasing":
            recommendations.append(
                "Activity has been declining. Consider increasing walk duration or frequency."
            )
        elif trend == "increasing":
            recommendations.append(
                "Great progress! Keep up the momentum with consistent activity."
            )
        else:
            recommendations.append(
                "Activity is stable. Try introducing new activities to boost engagement."
            )
        
        # Consistency-based recommendations
        if consistency < 60:
            recommendations.append(
                "Activity varies significantly day-to-day. Try to establish a more consistent routine."
            )
        
        # Day pattern recommendations
        if day_pattern.get("detected"):
            best = day_pattern.get("best_day", "weekends")
            recommendations.append(
                f"{best}s show highest activity. Schedule important activities on {best}."
            )
        
        # Anomaly-based recommendations
        if len(anomalies) > 2:
            recommendations.append(
                f"Multiple activity anomalies detected ({len(anomalies)} unusual days). "
                "Review what caused these variations."
            )
        
        return recommendations[:3]  # Return top 3

# ============== Recovery Forecaster ==============

class RecoveryForecaster:
    """
    Forecasts recovery time after illness/injury.
    
    Uses historical wellness data to estimate recovery timelines.
    """
    
    def estimate_recovery(
        self,
        dog_age: float,
        previous_recovery_days: List[int],
        current_health_score: float
    ) -> Dict:
        """
        Estimate recovery time based on age and history.
        
        Args:
            dog_age: Age in years
            previous_recovery_days: List of previous recovery periods
            current_health_score: Current healthspan score (0-100)
        
        Returns:
            Dictionary with recovery estimate
        """
        
        # Base recovery time by age
        if dog_age < 2:
            base_days = 5
        elif dog_age < 7:
            base_days = 7
        elif dog_age < 10:
            base_days = 10
        else:
            base_days = 14
        
        # Adjust based on health score
        health_factor = current_health_score / 100
        adjusted_days = base_days / health_factor
        
        # Adjust based on history
        if previous_recovery_days:
            avg_historical = statistics.mean(previous_recovery_days)
            adjusted_days = (adjusted_days + avg_historical) / 2
        
        return {
            "estimated_days": round(adjusted_days),
            "confidence": "high" if previous_recovery_days else "medium",
            "factors": [
                f"Age-based: {base_days} days",
                f"Health score adjustment: {'+' if health_factor > 1 else '-'}{abs(1-health_factor)*100:.0f}%"
            ],
            "recommendations": self._get_recovery_recommendations(adjusted_days)
        }
    
    def _get_recovery_recommendations(self, days: float) -> List[str]:
        """Get recommendations for recovery period."""
        
        recommendations = []
        
        if days <= 5:
            recommendations.append("Light activity only - short, gentle walks")
            recommendations.append("Monitor energy levels closely")
        elif days <= 10:
            recommendations.append("Gradual return to normal activity")
            recommendations.append("Avoid strenuous exercise for first half of recovery")
        else:
            recommendations.append("Extended rest period recommended")
            recommendations.append("Consider veterinary follow-up if no improvement in 7 days")
        
        return recommendations

# ============== ruv-FANN Bridge (for future integration) ==============

class RuvFannBridge:
    """
    Bridge to ruv-FANN for advanced neural forecasting.
    
    When ruv-FANN is available, this enables:
    - LSTM-based long-term predictions
    - Multi-variate forecasting
    - Complex pattern recognition
    
    Currently falls back to statistical methods.
    """
    
    def __init__(self):
        self.enabled = False
        self.available = self._check_availability()
    
    def _check_availability(self) -> bool:
        """Check if ruv-FANN is available."""
        try:
            # Try to import ruv-FANN if available
            # import ruv_fann  # Future: enable when available
            return False
        except ImportError:
            logger.info("ruv-FANN not available, using statistical forecasting")
            return False
    
    async def predict_with_ruffann(
        self,
        data: List[float],
        forecast_days: int
    ) -> Dict:
        """
        Use ruv-FANN for advanced forecasting.
        
        Returns neural network predictions when available.
        """
        
        if not self.available:
            return {
                "using_fallback": True,
                "reason": "ruv-FANN not installed"
            }
        
        # Future: Implement actual ruv-FANN integration
        # For now, this is a placeholder for when ruv-FANN is available
        pass

# ============== Factory Functions ==============

def create_forecaster() -> ActivityForecaster:
    """Create a configured activity forecaster."""
    return ActivityForecaster()

def create_recovery_forecaster() -> RecoveryForecaster:
    """Create a recovery forecaster."""
    return RecoveryForecaster()

# ============== Data Conversion Helpers ==============

def logs_to_datapoints(logs: List[Dict]) -> List[ActivityDataPoint]:
    """Convert database logs to ActivityDataPoint format."""
    
    data_points = []
    for log in logs:
        # Calculate quality score from available data
        quality = 70.0  # Base quality
        
        if log.get('active_minutes', 0) > 60:
            quality += 10
        if log.get('mood') in ['happy', 'excited', 'energetic']:
            quality += 10
        if log.get('steps', 0) > 5000:
            quality += 10
        
        data_points.append(ActivityDataPoint(
            date=log.get('logged_at', '')[:10],  # Just date part
            active_minutes=log.get('active_minutes', 0),
            steps=log.get('steps', 0),
            walks=log.get('walks', 1),
            mood=log.get('mood', 'neutral'),
            quality_score=min(100, quality)
        ))
    
    return data_points
