import React, { useState, useRef, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  Animated,
  Dimensions,
  Alert,
  ActivityIndicator,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { LinearGradient } from 'expo-linear-gradient';
import { useRouter } from 'expo-router';
import { useAuth } from '../../src/context/AuthContext';
import { useDailyLog } from '../../src/hooks/useHealthData';

const { width } = Dimensions.get('window');

const COLORS = {
  primary: '#FF6B00',
  secondary: '#00BFA5',
  navy: '#1E3A8A',
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

type MoodType = 'great' | 'good' | 'okay' | 'tired' | 'unwell' | null;
type ExerciseType = 'none' | 'light' | 'moderate' | 'active' | 'intense' | null;
type NutritionType = 'poor' | 'fair' | 'good' | 'excellent' | null;

export default function LogScreen() {
  const router = useRouter();
  const { currentDog } = useAuth();
  const { todayLog, submitLog, isLoading } = useDailyLog();
  
  const [mood, setMood] = useState<MoodType>(null);
  const [exercise, setExercise] = useState<ExerciseType>(null);
  const [nutrition, setNutrition] = useState<NutritionType>(null);
  const [submitting, setSubmitting] = useState(false);
  
  const fadeAnim = useRef(new Animated.Value(0)).current;
  const slideAnim = useRef(new Animated.Value(20)).current;
  const progressAnim = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    Animated.parallel([
      Animated.timing(fadeAnim, {
        toValue: 1,
        duration: 500,
        useNativeDriver: true,
      }),
      Animated.timing(slideAnim, {
        toValue: 0,
        duration: 500,
        useNativeDriver: true,
      }),
    ]).start();
  }, []);

  useEffect(() => {
    const completedSteps = [mood, exercise, nutrition].filter(v => v !== null).length;
    Animated.timing(progressAnim, {
      toValue: completedSteps / 3,
      duration: 300,
      useNativeDriver: false,
    }).start();
  }, [mood, exercise, nutrition]);

  // If already logged today, show completion message
  if (todayLog) {
    return (
      <SafeAreaView style={styles.container} edges={['top']}>
        <View style={styles.completedContainer}>
          <View style={styles.completedIcon}>
            <Ionicons name="checkmark-circle" size={80} color={COLORS.success} />
          </View>
          <Text style={styles.completedTitle}>All Done for Today!</Text>
          <Text style={styles.completedSubtitle}>
            You've already logged {currentDog?.name}'s health for today. Come back tomorrow!
          </Text>
          <View style={styles.completedStats}>
            <View style={styles.completedStat}>
              <Text style={styles.completedStatLabel}>Mood</Text>
              <Text style={styles.completedStatValue}>{todayLog.mood}</Text>
            </View>
            <View style={styles.completedStat}>
              <Text style={styles.completedStatLabel}>Exercise</Text>
              <Text style={styles.completedStatValue}>{todayLog.exercise_level}</Text>
            </View>
            <View style={styles.completedStat}>
              <Text style={styles.completedStatLabel}>Nutrition</Text>
              <Text style={styles.completedStatValue}>{todayLog.nutrition_quality}</Text>
            </View>
          </View>
          <TouchableOpacity
            style={styles.homeBtn}
            onPress={() => router.push('/')}
          >
            <Text style={styles.homeBtnText}>Back to Home</Text>
          </TouchableOpacity>
        </View>
      </SafeAreaView>
    );
  }

  const moodOptions = [
    { id: 'great', emoji: '😄', label: 'Great', color: COLORS.success },
    { id: 'good', emoji: '🙂', label: 'Good', color: COLORS.secondary },
    { id: 'okay', emoji: '😐', label: 'Okay', color: COLORS.warning },
    { id: 'tired', emoji: '😴', label: 'Tired', color: COLORS.navy },
    { id: 'unwell', emoji: '🤒', label: 'Unwell', color: COLORS.error },
  ];

  const exerciseOptions = [
    { id: 'none', icon: 'bed', label: 'Rest Day', value: '0 min', color: COLORS.textSecondary },
    { id: 'light', icon: 'walk', label: 'Light', value: '15-30 min', color: COLORS.secondary },
    { id: 'moderate', icon: 'fitness', label: 'Moderate', value: '30-60 min', color: COLORS.success },
    { id: 'active', icon: 'bicycle', label: 'Active', value: '60-90 min', color: COLORS.primary },
    { id: 'intense', icon: 'flame', label: 'Intense', value: '90+ min', color: COLORS.warning },
  ];

  const nutritionOptions = [
    { id: 'poor', icon: 'alert-circle', label: 'Poor', desc: 'Skipped meals', color: COLORS.error },
    { id: 'fair', icon: 'remove-circle', label: 'Fair', desc: 'Irregular eating', color: COLORS.warning },
    { id: 'good', icon: 'checkmark-circle', label: 'Good', desc: 'Regular meals', color: COLORS.secondary },
    { id: 'excellent', icon: 'star', label: 'Excellent', desc: 'Perfect nutrition', color: COLORS.success },
  ];

  const isComplete = mood && exercise && nutrition;

  const handleSubmit = async () => {
    if (!isComplete || !currentDog) return;
    
    setSubmitting(true);
    try {
      await submitLog({
        mood,
        exercise_level: exercise,
        nutrition_quality: nutrition,
      });
      Alert.alert(
        'Success! 🎉',
        `You earned 10 Healthspan Points for logging ${currentDog.name}'s health today!`,
        [{ text: 'Awesome!', onPress: () => router.push('/') }]
      );
    } catch (error: any) {
      Alert.alert('Error', error.message || 'Failed to submit log');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <SafeAreaView style={styles.container} edges={['top']}>
      <ScrollView showsVerticalScrollIndicator={false} contentContainerStyle={styles.scrollContent}>
        {/* Header */}
        <Animated.View style={[styles.header, { opacity: fadeAnim, transform: [{ translateY: slideAnim }] }]}>
          <Text style={styles.title}>Daily Ritual</Text>
          <Text style={styles.subtitle}>Log {currentDog?.name}'s health in under 15 seconds</Text>
          
          {/* Progress Bar */}
          <View style={styles.progressContainer}>
            <View style={styles.progressBar}>
              <Animated.View 
                style={[
                  styles.progressFill, 
                  { 
                    width: progressAnim.interpolate({
                      inputRange: [0, 1],
                      outputRange: ['0%', '100%'],
                    })
                  }
                ]} 
              />
            </View>
            <Text style={styles.progressText}>
              {[mood, exercise, nutrition].filter(v => v !== null).length}/3 completed
            </Text>
          </View>
        </Animated.View>

        {/* Mood Section */}
        <Animated.View style={[styles.section, { opacity: fadeAnim }]}>
          <View style={styles.sectionHeader}>
            <View style={[styles.sectionIcon, { backgroundColor: COLORS.primary + '20' }]}>
              <Ionicons name="happy" size={20} color={COLORS.primary} />
            </View>
            <Text style={styles.sectionTitle}>How is {currentDog?.name} feeling today?</Text>
          </View>
          
          <View style={styles.moodGrid}>
            {moodOptions.map((option) => (
              <TouchableOpacity
                key={option.id}
                style={[
                  styles.moodCard,
                  mood === option.id && { borderColor: option.color, backgroundColor: option.color + '15' }
                ]}
                onPress={() => setMood(option.id as MoodType)}
                activeOpacity={0.7}
              >
                <Text style={styles.moodEmoji}>{option.emoji}</Text>
                <Text style={[
                  styles.moodLabel,
                  mood === option.id && { color: option.color }
                ]}>{option.label}</Text>
                {mood === option.id && (
                  <View style={[styles.selectedCheck, { backgroundColor: option.color }]}>
                    <Ionicons name="checkmark" size={12} color={COLORS.text} />
                  </View>
                )}
              </TouchableOpacity>
            ))}
          </View>
        </Animated.View>

        {/* Exercise Section */}
        <Animated.View style={[styles.section, { opacity: fadeAnim }]}>
          <View style={styles.sectionHeader}>
            <View style={[styles.sectionIcon, { backgroundColor: COLORS.secondary + '20' }]}>
              <Ionicons name="fitness" size={20} color={COLORS.secondary} />
            </View>
            <Text style={styles.sectionTitle}>Exercise Level</Text>
          </View>
          
          <View style={styles.exerciseGrid}>
            {exerciseOptions.map((option) => (
              <TouchableOpacity
                key={option.id}
                style={[
                  styles.exerciseCard,
                  exercise === option.id && { borderColor: option.color, backgroundColor: option.color + '15' }
                ]}
                onPress={() => setExercise(option.id as ExerciseType)}
                activeOpacity={0.7}
              >
                <View style={[styles.exerciseIcon, { backgroundColor: option.color + '20' }]}>
                  <Ionicons name={option.icon as any} size={22} color={option.color} />
                </View>
                <Text style={[
                  styles.exerciseLabel,
                  exercise === option.id && { color: option.color }
                ]}>{option.label}</Text>
                <Text style={styles.exerciseValue}>{option.value}</Text>
                {exercise === option.id && (
                  <View style={[styles.selectedIndicator, { backgroundColor: option.color }]} />
                )}
              </TouchableOpacity>
            ))}
          </View>
        </Animated.View>

        {/* Nutrition Section */}
        <Animated.View style={[styles.section, { opacity: fadeAnim }]}>
          <View style={styles.sectionHeader}>
            <View style={[styles.sectionIcon, { backgroundColor: COLORS.warning + '20' }]}>
              <Ionicons name="restaurant" size={20} color={COLORS.warning} />
            </View>
            <Text style={styles.sectionTitle}>Nutrition Quality</Text>
          </View>
          
          <View style={styles.nutritionGrid}>
            {nutritionOptions.map((option) => (
              <TouchableOpacity
                key={option.id}
                style={[
                  styles.nutritionCard,
                  nutrition === option.id && { borderColor: option.color, backgroundColor: option.color + '15' }
                ]}
                onPress={() => setNutrition(option.id as NutritionType)}
                activeOpacity={0.7}
              >
                <View style={styles.nutritionContent}>
                  <View style={[styles.nutritionIcon, { backgroundColor: option.color + '20' }]}>
                    <Ionicons name={option.icon as any} size={22} color={option.color} />
                  </View>
                  <View style={styles.nutritionText}>
                    <Text style={[
                      styles.nutritionLabel,
                      nutrition === option.id && { color: option.color }
                    ]}>{option.label}</Text>
                    <Text style={styles.nutritionDesc}>{option.desc}</Text>
                  </View>
                </View>
                {nutrition === option.id && (
                  <View style={[styles.checkCircle, { backgroundColor: option.color }]}>
                    <Ionicons name="checkmark" size={14} color={COLORS.text} />
                  </View>
                )}
              </TouchableOpacity>
            ))}
          </View>
        </Animated.View>

        {/* Submit Button */}
        <TouchableOpacity
          style={[styles.submitBtn, !isComplete && styles.submitBtnDisabled]}
          onPress={handleSubmit}
          disabled={!isComplete || submitting}
          activeOpacity={0.8}
        >
          <LinearGradient
            colors={isComplete ? ['#FF6B00', '#FF8533'] : [COLORS.card, COLORS.card]}
            start={{ x: 0, y: 0 }}
            end={{ x: 1, y: 0 }}
            style={styles.submitGradient}
          >
            {submitting ? (
              <ActivityIndicator color={COLORS.text} />
            ) : (
              <>
                <Ionicons 
                  name={isComplete ? 'checkmark-circle' : 'time'} 
                  size={22} 
                  color={isComplete ? COLORS.text : COLORS.textSecondary} 
                />
                <Text style={[
                  styles.submitText,
                  !isComplete && styles.submitTextDisabled
                ]}>
                  {isComplete ? 'Complete Ritual +10 pts' : 'Complete all sections'}
                </Text>
              </>
            )}
          </LinearGradient>
        </TouchableOpacity>

        {/* Points Preview */}
        {isComplete && (
          <View style={styles.pointsPreview}>
            <Ionicons name="star" size={16} color={COLORS.warning} />
            <Text style={styles.pointsText}>You'll earn 10 Healthspan Points!</Text>
          </View>
        )}
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: COLORS.background,
  },
  scrollContent: {
    paddingHorizontal: 20,
    paddingBottom: 100,
  },
  header: {
    paddingVertical: 24,
  },
  title: {
    fontSize: 32,
    fontWeight: '800',
    color: COLORS.text,
  },
  subtitle: {
    fontSize: 15,
    color: COLORS.textSecondary,
    marginTop: 6,
  },
  progressContainer: {
    marginTop: 20,
  },
  progressBar: {
    height: 8,
    backgroundColor: COLORS.card,
    borderRadius: 4,
    overflow: 'hidden',
  },
  progressFill: {
    height: '100%',
    backgroundColor: COLORS.primary,
    borderRadius: 4,
  },
  progressText: {
    fontSize: 13,
    color: COLORS.textSecondary,
    marginTop: 8,
  },
  section: {
    marginBottom: 28,
  },
  sectionHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 16,
  },
  sectionIcon: {
    width: 36,
    height: 36,
    borderRadius: 12,
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 12,
  },
  sectionTitle: {
    fontSize: 17,
    fontWeight: '700',
    color: COLORS.text,
  },
  moodGrid: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  moodCard: {
    flex: 1,
    backgroundColor: COLORS.card,
    borderRadius: 16,
    padding: 10,
    marginHorizontal: 3,
    alignItems: 'center',
    borderWidth: 2,
    borderColor: 'transparent',
  },
  moodEmoji: {
    fontSize: 28,
    marginBottom: 6,
  },
  moodLabel: {
    fontSize: 11,
    fontWeight: '600',
    color: COLORS.textSecondary,
  },
  selectedCheck: {
    position: 'absolute',
    top: -6,
    right: -6,
    width: 20,
    height: 20,
    borderRadius: 10,
    justifyContent: 'center',
    alignItems: 'center',
  },
  exerciseGrid: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  exerciseCard: {
    flex: 1,
    backgroundColor: COLORS.card,
    borderRadius: 16,
    padding: 10,
    marginHorizontal: 3,
    alignItems: 'center',
    borderWidth: 2,
    borderColor: 'transparent',
  },
  exerciseIcon: {
    width: 44,
    height: 44,
    borderRadius: 14,
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 8,
  },
  exerciseLabel: {
    fontSize: 12,
    fontWeight: '600',
    color: COLORS.text,
    textAlign: 'center',
  },
  exerciseValue: {
    fontSize: 10,
    color: COLORS.textSecondary,
    marginTop: 2,
    textAlign: 'center',
  },
  selectedIndicator: {
    position: 'absolute',
    bottom: 0,
    left: '20%',
    right: '20%',
    height: 3,
    borderRadius: 2,
  },
  nutritionGrid: {
    gap: 10,
  },
  nutritionCard: {
    backgroundColor: COLORS.card,
    borderRadius: 16,
    padding: 16,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    borderWidth: 2,
    borderColor: 'transparent',
  },
  nutritionContent: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  nutritionIcon: {
    width: 44,
    height: 44,
    borderRadius: 14,
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 14,
  },
  nutritionText: {
    flex: 1,
  },
  nutritionLabel: {
    fontSize: 15,
    fontWeight: '600',
    color: COLORS.text,
  },
  nutritionDesc: {
    fontSize: 12,
    color: COLORS.textSecondary,
    marginTop: 2,
  },
  checkCircle: {
    width: 26,
    height: 26,
    borderRadius: 13,
    justifyContent: 'center',
    alignItems: 'center',
  },
  submitBtn: {
    marginTop: 10,
    borderRadius: 16,
    overflow: 'hidden',
  },
  submitBtnDisabled: {
    opacity: 0.6,
  },
  submitGradient: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 18,
  },
  submitText: {
    fontSize: 17,
    fontWeight: '700',
    color: COLORS.text,
    marginLeft: 10,
  },
  submitTextDisabled: {
    color: COLORS.textSecondary,
  },
  pointsPreview: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    marginTop: 16,
  },
  pointsText: {
    fontSize: 14,
    color: COLORS.warning,
    fontWeight: '600',
    marginLeft: 8,
  },
  // Completed state styles
  completedContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingHorizontal: 40,
  },
  completedIcon: {
    marginBottom: 24,
  },
  completedTitle: {
    fontSize: 28,
    fontWeight: '700',
    color: COLORS.text,
    marginBottom: 12,
  },
  completedSubtitle: {
    fontSize: 15,
    color: COLORS.textSecondary,
    textAlign: 'center',
    marginBottom: 32,
  },
  completedStats: {
    flexDirection: 'row',
    marginBottom: 32,
  },
  completedStat: {
    alignItems: 'center',
    marginHorizontal: 16,
  },
  completedStatLabel: {
    fontSize: 12,
    color: COLORS.textSecondary,
    marginBottom: 4,
  },
  completedStatValue: {
    fontSize: 16,
    fontWeight: '600',
    color: COLORS.text,
    textTransform: 'capitalize',
  },
  homeBtn: {
    backgroundColor: COLORS.card,
    paddingVertical: 16,
    paddingHorizontal: 32,
    borderRadius: 16,
  },
  homeBtnText: {
    fontSize: 16,
    fontWeight: '600',
    color: COLORS.primary,
  },
});
