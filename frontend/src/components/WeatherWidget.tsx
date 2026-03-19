import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ActivityIndicator,
  RefreshControl,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import * as Location from 'expo-location';
import api from '../services/api';

const COLORS = {
  primary: '#FF6B00',
  secondary: '#00BFA5',
  background: '#0A0E17',
  card: '#141B2D',
  cardLight: '#1C2438',
  text: '#FFFFFF',
  textSecondary: '#8892A6',
  border: '#1F2937',
  success: '#10B981',
  warning: '#F59E0B',
  error: '#EF4444',
};

interface WeatherData {
  temperature: number;
  feels_like: number;
  condition: string;
  description: string;
  icon: string;
  humidity: number;
  wind_speed: number;
  walk_score: number;
  recommendations: string[];
  issues: string[];
}

interface BestWalkTime {
  hour: number;
  temp: number;
  condition: string;
  icon: string;
  score: number;
  label: string;
}

export default function WeatherWidget() {
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [weather, setWeather] = useState<WeatherData | null>(null);
  const [bestTimes, setBestTimes] = useState<BestWalkTime[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [expanded, setExpanded] = useState(false);

  useEffect(() => {
    fetchWeather();
  }, []);

  const fetchWeather = async () => {
    try {
      setLoading(true);
      setError(null);

      const { status } = await Location.requestForegroundPermissionsAsync();
      if (status !== 'granted') {
        setError('Location permission denied');
        return;
      }

      const location = await Location.getCurrentPositionAsync({
        accuracy: Location.Accuracy.Balanced,
      });

      const { latitude, longitude } = location.coords;

      const [weatherData, forecastData] = await Promise.all([
        api.getWeather(latitude, longitude),
        api.getWeatherForecast(latitude, longitude, 24),
      ]);

      setWeather(weatherData.walk_analysis);
      setBestTimes(forecastData.best_walk_times || []);
    } catch (err: any) {
      setError(err.message || 'Failed to load weather');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  const onRefresh = () => {
    setRefreshing(true);
    fetchWeather();
  };

  const getWeatherIcon = (condition: string): string => {
    const iconMap: Record<string, string> = {
      'Clear': 'sunny',
      'Clouds': 'cloudy',
      'Rain': 'rainy',
      'Drizzle': 'rainy-outline',
      'Thunderstorm': 'thunderstorm',
      'Snow': 'snow',
      'Mist': 'water-outline',
      'Fog': 'cloudy-outline',
    };
    return iconMap[condition] || 'cloudy';
  };

  const getScoreColor = (score: number): string => {
    if (score >= 80) return COLORS.success;
    if (score >= 60) return COLORS.warning;
    return COLORS.error;
  };

  const getScoreLabel = (score: number): string => {
    if (score >= 80) return 'Great for walking!';
    if (score >= 60) return 'Okay for walking';
    return 'Stay indoors';
  };

  if (loading) {
    return (
      <View style={styles.container}>
        <View style={styles.header}>
          <Ionicons name="partly-sunny" size={20} color={COLORS.primary} />
          <Text style={styles.title}>Walk Weather</Text>
        </View>
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="small" color={COLORS.primary} />
          <Text style={styles.loadingText}>Getting weather...</Text>
        </View>
      </View>
    );
  }

  if (error) {
    return (
      <View style={styles.container}>
        <View style={styles.header}>
          <Ionicons name="partly-sunny" size={20} color={COLORS.primary} />
          <Text style={styles.title}>Walk Weather</Text>
        </View>
        <TouchableOpacity style={styles.errorContainer} onPress={fetchWeather}>
          <Ionicons name="location" size={24} color={COLORS.textSecondary} />
          <Text style={styles.errorText}>{error}</Text>
          <Text style={styles.retryText}>Tap to retry</Text>
        </TouchableOpacity>
      </View>
    );
  }

  if (!weather) return null;

  return (
    <View style={styles.container}>
      <TouchableOpacity 
        style={styles.header} 
        onPress={() => setExpanded(!expanded)}
        activeOpacity={0.7}
      >
        <View style={styles.headerLeft}>
          <Ionicons 
            name={getWeatherIcon(weather.condition) as any} 
            size={24} 
            color={COLORS.primary} 
          />
          <Text style={styles.title}>Walk Weather</Text>
        </View>
        <View style={styles.headerRight}>
          <Text style={styles.temperature}>{weather.temperature}°F</Text>
          <Ionicons 
            name={expanded ? 'chevron-up' : 'chevron-down'} 
            size={20} 
            color={COLORS.textSecondary} 
          />
        </View>
      </TouchableOpacity>

      {/* Walk Score Badge */}
      <View style={styles.scoreContainer}>
        <View style={[styles.scoreBadge, { backgroundColor: getScoreColor(weather.walk_score) + '20' }]}>
          <Text style={[styles.scoreValue, { color: getScoreColor(weather.walk_score) }]}>
            {weather.walk_score}
          </Text>
          <Text style={styles.scoreLabel}>{getScoreLabel(weather.walk_score)}</Text>
        </View>
        <View style={styles.conditionBadge}>
          <Text style={styles.conditionText}>{weather.description}</Text>
        </View>
      </View>

      {/* Expanded Details */}
      {expanded && (
        <View style={styles.expandedContent}>
          {/* Quick Stats */}
          <View style={styles.statsRow}>
            <View style={styles.stat}>
              <Ionicons name="thermometer" size={16} color={COLORS.textSecondary} />
              <Text style={styles.statLabel}>Feels like</Text>
              <Text style={styles.statValue}>{weather.feels_like}°F</Text>
            </View>
            <View style={styles.stat}>
              <Ionicons name="water" size={16} color={COLORS.textSecondary} />
              <Text style={styles.statLabel}>Humidity</Text>
              <Text style={styles.statValue}>{weather.humidity}%</Text>
            </View>
            <View style={styles.stat}>
              <Ionicons name="speedometer" size={16} color={COLORS.textSecondary} />
              <Text style={styles.statLabel}>Wind</Text>
              <Text style={styles.statValue}>{weather.wind_speed} mph</Text>
            </View>
          </View>

          {/* Recommendations */}
          {weather.recommendations.length > 0 && (
            <View style={styles.recommendations}>
              {weather.recommendations.slice(0, 3).map((rec, index) => (
                <View key={index} style={styles.recommendationItem}>
                  <Text style={styles.recommendationText}>{rec}</Text>
                </View>
              ))}
            </View>
          )}

          {/* Best Walk Times */}
          {bestTimes.length > 0 && (
            <View style={styles.bestTimes}>
              <Text style={styles.bestTimesTitle}>Best times to walk:</Text>
              <View style={styles.timesRow}>
                {bestTimes.slice(0, 4).map((time, index) => (
                  <View key={index} style={styles.timeSlot}>
                    <Text style={styles.timeLabel}>{time.label}</Text>
                    <Text style={styles.timeTemp}>{time.temp}°</Text>
                  </View>
                ))}
              </View>
            </View>
          )}

          {/* Refresh */}
          <TouchableOpacity style={styles.refreshButton} onPress={onRefresh}>
            <Ionicons name="refresh" size={16} color={COLORS.textSecondary} />
            <Text style={styles.refreshText}>Refresh</Text>
          </TouchableOpacity>
        </View>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    backgroundColor: COLORS.card,
    borderRadius: 16,
    padding: 16,
    marginHorizontal: 16,
    marginBottom: 16,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  headerLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  headerRight: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  title: {
    fontSize: 16,
    fontWeight: '600',
    color: COLORS.text,
  },
  temperature: {
    fontSize: 20,
    fontWeight: '700',
    color: COLORS.text,
  },
  loadingContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 20,
    gap: 10,
  },
  loadingText: {
    color: COLORS.textSecondary,
    fontSize: 14,
  },
  errorContainer: {
    alignItems: 'center',
    paddingVertical: 16,
  },
  errorText: {
    color: COLORS.textSecondary,
    fontSize: 14,
    marginTop: 8,
    textAlign: 'center',
  },
  retryText: {
    color: COLORS.primary,
    fontSize: 12,
    marginTop: 4,
  },
  scoreContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
  },
  scoreBadge: {
    paddingHorizontal: 16,
    paddingVertical: 10,
    borderRadius: 12,
    alignItems: 'center',
  },
  scoreValue: {
    fontSize: 28,
    fontWeight: '800',
  },
  scoreLabel: {
    fontSize: 10,
    fontWeight: '600',
    marginTop: 2,
    opacity: 0.8,
  },
  conditionBadge: {
    flex: 1,
    backgroundColor: COLORS.cardLight,
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderRadius: 8,
  },
  conditionText: {
    color: COLORS.text,
    fontSize: 14,
    fontWeight: '500',
    textTransform: 'capitalize',
  },
  expandedContent: {
    marginTop: 16,
    borderTopWidth: 1,
    borderTopColor: COLORS.border,
    paddingTop: 16,
  },
  statsRow: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    marginBottom: 16,
  },
  stat: {
    alignItems: 'center',
    gap: 4,
  },
  statLabel: {
    fontSize: 11,
    color: COLORS.textSecondary,
  },
  statValue: {
    fontSize: 14,
    fontWeight: '600',
    color: COLORS.text,
  },
  recommendations: {
    marginBottom: 16,
  },
  recommendationItem: {
    backgroundColor: COLORS.cardLight,
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderRadius: 8,
    marginBottom: 6,
  },
  recommendationText: {
    fontSize: 13,
    color: COLORS.text,
    lineHeight: 18,
  },
  bestTimes: {
    marginBottom: 16,
  },
  bestTimesTitle: {
    fontSize: 13,
    fontWeight: '600',
    color: COLORS.textSecondary,
    marginBottom: 8,
  },
  timesRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  timeSlot: {
    backgroundColor: COLORS.cardLight,
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderRadius: 8,
    alignItems: 'center',
    flex: 1,
    marginHorizontal: 2,
  },
  timeLabel: {
    fontSize: 12,
    fontWeight: '600',
    color: COLORS.text,
  },
  timeTemp: {
    fontSize: 11,
    color: COLORS.textSecondary,
    marginTop: 2,
  },
  refreshButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 6,
    paddingVertical: 8,
  },
  refreshText: {
    fontSize: 12,
    color: COLORS.textSecondary,
  },
});
