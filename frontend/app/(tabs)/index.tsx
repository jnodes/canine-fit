import React, { useEffect, useRef, useCallback } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  Dimensions,
  Animated,
  Platform,
  RefreshControl,
  ActivityIndicator,
  Image,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { LinearGradient } from 'expo-linear-gradient';
import { useRouter, useFocusEffect } from 'expo-router';
import { useAuth } from '../../src/context/AuthContext';
import { useHealthspan, useLiloReports, useDailyLog } from '../../src/hooks/useHealthData';

// Lilo AI companion image
const LILO_IMAGE = require('../../assets/lilo.jpg');

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
};

export default function HomeScreen() {
  const router = useRouter();
  const { user, currentDog, isAuthenticated, isLoading: authLoading } = useAuth();
  const { healthspan, isLoading: healthLoading, refresh: refreshHealthspan } = useHealthspan();
  const { reports, refresh: refreshReports } = useLiloReports();
  const { todayLog, refresh: refreshTodayLog } = useDailyLog();
  
  const [refreshing, setRefreshing] = React.useState(false);
  
  const fadeAnim = useRef(new Animated.Value(0)).current;
  const slideAnim = useRef(new Animated.Value(30)).current;
  const scaleAnim = useRef(new Animated.Value(0.9)).current;

  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      router.replace('/auth');
    }
  }, [authLoading, isAuthenticated]);

  useEffect(() => {
    Animated.parallel([
      Animated.timing(fadeAnim, {
        toValue: 1,
        duration: 600,
        useNativeDriver: true,
      }),
      Animated.timing(slideAnim, {
        toValue: 0,
        duration: 600,
        useNativeDriver: true,
      }),
      Animated.spring(scaleAnim, {
        toValue: 1,
        tension: 50,
        friction: 7,
        useNativeDriver: true,
      }),
    ]).start();
  }, []);

  useFocusEffect(
    useCallback(() => {
      refreshHealthspan();
      refreshTodayLog();
    }, [])
  );

  const onRefresh = async () => {
    setRefreshing(true);
    await Promise.all([refreshHealthspan(), refreshTodayLog(), refreshReports()]);
    setRefreshing(false);
  };

  const getGreeting = () => {
    const hour = new Date().getHours();
    if (hour < 12) return 'Good Morning!';
    if (hour < 17) return 'Good Afternoon!';
    return 'Good Evening!';
  };

  const calculateAge = (dob?: string) => {
    if (!dob) return null;
    const birthDate = new Date(dob);
    const today = new Date();
    let age = today.getFullYear() - birthDate.getFullYear();
    const monthDiff = today.getMonth() - birthDate.getMonth();
    if (monthDiff < 0 || (monthDiff === 0 && today.getDate() < birthDate.getDate())) {
      age--;
    }
    return age;
  };

  if (authLoading) {
    return (
      <View style={[styles.container, styles.centered]}>
        <ActivityIndicator size="large" color={COLORS.primary} />
      </View>
    );
  }

  if (!currentDog) {
    return (
      <SafeAreaView style={styles.container} edges={['top']}>
        <View style={styles.emptyState}>
          <Ionicons name="paw" size={64} color={COLORS.primary} />
          <Text style={styles.emptyTitle}>No Dog Profile Yet</Text>
          <Text style={styles.emptySubtitle}>Add your first dog to start tracking their health</Text>
          <TouchableOpacity
            style={styles.addDogBtn}
            onPress={() => router.push('/onboarding')}
          >
            <LinearGradient
              colors={[COLORS.primary, '#FF8533']}
              style={styles.addDogGradient}
            >
              <Ionicons name="add" size={24} color={COLORS.text} />
              <Text style={styles.addDogText}>Add Your Dog</Text>
            </LinearGradient>
          </TouchableOpacity>
        </View>
      </SafeAreaView>
    );
  }

  const dogAge = calculateAge(currentDog.date_of_birth);
  const latestReport = reports[0];

  const quickStats = [
    { icon: 'flame', label: 'Streak', value: `${healthspan?.streak || 0} days`, color: COLORS.primary },
    { icon: 'star', label: 'Points', value: healthspan?.total_points?.toLocaleString() || '0', color: COLORS.secondary },
    { icon: 'trophy', label: 'Rank', value: `#${healthspan?.breed_rank || '-'}`, color: COLORS.warning },
    { icon: 'checkmark-circle', label: 'Today', value: todayLog ? 'Done' : 'Pending', color: todayLog ? COLORS.success : COLORS.textSecondary },
  ];

  return (
    <SafeAreaView style={styles.container} edges={['top']}>
      <ScrollView 
        showsVerticalScrollIndicator={false} 
        contentContainerStyle={styles.scrollContent}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor={COLORS.primary} />
        }
      >
        {/* Header */}
        <Animated.View style={[styles.header, { opacity: fadeAnim, transform: [{ translateY: slideAnim }] }]}>
          <View>
            <Text style={styles.greeting}>{getGreeting()}</Text>
            <Text style={styles.subtitle}>
              {currentDog.name} is {todayLog ? 'doing great' : 'waiting for today\'s log'}
            </Text>
          </View>
          <TouchableOpacity style={styles.notificationBtn}>
            <Ionicons name="notifications" size={24} color={COLORS.text} />
            <View style={styles.notificationBadge} />
          </TouchableOpacity>
        </Animated.View>

        {/* Healthspan Score Card */}
        <Animated.View style={{ opacity: fadeAnim, transform: [{ scale: scaleAnim }] }}>
          <LinearGradient
            colors={['#FF6B00', '#FF8533']}
            start={{ x: 0, y: 0 }}
            end={{ x: 1, y: 1 }}
            style={styles.scoreCard}
          >
            <View style={styles.scoreHeader}>
              <View style={styles.dogAvatar}>
                <Ionicons name="paw" size={28} color={COLORS.primary} />
              </View>
              <View style={styles.scoreInfo}>
                <Text style={styles.dogName}>{currentDog.name}</Text>
                <Text style={styles.breedText}>
                  {currentDog.breed} {dogAge ? `• ${dogAge} years` : ''}
                </Text>
              </View>
              <TouchableOpacity style={styles.editBtn} onPress={() => router.push('/profile')}>
                <Ionicons name="chevron-forward" size={20} color="rgba(255,255,255,0.8)" />
              </TouchableOpacity>
            </View>
            
            <View style={styles.scoreBody}>
              <View style={styles.mainScore}>
                <Text style={styles.scoreLabel}>Healthspan Score</Text>
                <View style={styles.scoreRow}>
                  <Text style={styles.scoreValue}>{healthspan?.score || 85}</Text>
                  <View style={styles.scoreTrend}>
                    <Ionicons name="trending-up" size={16} color="#10B981" />
                    <Text style={styles.trendText}>+3</Text>
                  </View>
                </View>
                <View style={styles.scoreBar}>
                  <View style={[styles.scoreProgress, { width: `${healthspan?.score || 85}%` }]} />
                </View>
              </View>
              
              <View style={styles.scoreRank}>
                <Ionicons name="trophy" size={20} color="#FFD700" />
                <Text style={styles.rankText}>#{healthspan?.breed_rank || '-'} in {currentDog.breed}s</Text>
              </View>
            </View>
          </LinearGradient>
        </Animated.View>

        {/* Quick Stats */}
        <Animated.View style={[styles.statsContainer, { opacity: fadeAnim, transform: [{ translateY: slideAnim }] }]}>
          <Text style={styles.sectionTitle}>Today's Overview</Text>
          <View style={styles.statsGrid}>
            {quickStats.map((stat, index) => (
              <TouchableOpacity key={index} style={styles.statCard}>
                <View style={[styles.statIcon, { backgroundColor: `${stat.color}20` }]}>
                  <Ionicons name={stat.icon as any} size={20} color={stat.color} />
                </View>
                <Text style={styles.statValue}>{stat.value}</Text>
                <Text style={styles.statLabel}>{stat.label}</Text>
              </TouchableOpacity>
            ))}
          </View>
        </Animated.View>

        {/* Daily Ritual CTA */}
        {!todayLog && (
          <Animated.View style={{ opacity: fadeAnim }}>
            <TouchableOpacity 
              style={styles.ritualCard}
              onPress={() => router.push('/log')}
              activeOpacity={0.8}
            >
              <LinearGradient
                colors={['#00BFA5', '#00D9B8']}
                start={{ x: 0, y: 0 }}
                end={{ x: 1, y: 0 }}
                style={styles.ritualGradient}
              >
                <View style={styles.ritualContent}>
                  <View style={styles.ritualIcon}>
                    <Ionicons name="checkmark-circle" size={32} color={COLORS.text} />
                  </View>
                  <View style={styles.ritualText}>
                    <Text style={styles.ritualTitle}>Complete Daily Ritual</Text>
                    <Text style={styles.ritualSubtitle}>Log {currentDog.name}'s health in under 15 seconds</Text>
                  </View>
                  <Ionicons name="chevron-forward" size={24} color="rgba(255,255,255,0.8)" />
                </View>
              </LinearGradient>
            </TouchableOpacity>
          </Animated.View>
        )}

        {/* Lilo AI Tip */}
        {latestReport && (
          <Animated.View style={[styles.liloCard, { opacity: fadeAnim }]}>
            <View style={styles.liloHeader}>
              <Image source={LILO_IMAGE} style={styles.liloAvatar} />
              <View>
                <Text style={styles.liloName}>Lilo AI</Text>
                <Text style={styles.liloLabel}>Your Dog's Companion</Text>
              </View>
            </View>
            <Text style={styles.liloMessage}>
              "{latestReport.summary}"
            </Text>
            {latestReport.insights[0] && (
              <Text style={styles.liloInsight}>
                💡 {latestReport.insights[0]}
              </Text>
            )}
            <TouchableOpacity style={styles.liloBtn} onPress={() => router.push('/insights')}>
              <Text style={styles.liloBtnText}>View Full Insights</Text>
              <Ionicons name="arrow-forward" size={16} color={COLORS.secondary} />
            </TouchableOpacity>
          </Animated.View>
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
  centered: {
    justifyContent: 'center',
    alignItems: 'center',
  },
  scrollContent: {
    paddingHorizontal: 20,
    paddingBottom: 100,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 20,
  },
  greeting: {
    fontSize: 28,
    fontWeight: '700',
    color: COLORS.text,
  },
  subtitle: {
    fontSize: 14,
    color: COLORS.textSecondary,
    marginTop: 4,
  },
  notificationBtn: {
    width: 44,
    height: 44,
    borderRadius: 22,
    backgroundColor: COLORS.card,
    justifyContent: 'center',
    alignItems: 'center',
  },
  notificationBadge: {
    position: 'absolute',
    top: 10,
    right: 12,
    width: 8,
    height: 8,
    borderRadius: 4,
    backgroundColor: COLORS.primary,
  },
  emptyState: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingHorizontal: 40,
  },
  emptyTitle: {
    fontSize: 24,
    fontWeight: '700',
    color: COLORS.text,
    marginTop: 24,
    marginBottom: 8,
  },
  emptySubtitle: {
    fontSize: 15,
    color: COLORS.textSecondary,
    textAlign: 'center',
    marginBottom: 32,
  },
  addDogBtn: {
    borderRadius: 16,
    overflow: 'hidden',
  },
  addDogGradient: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 16,
    paddingHorizontal: 32,
    gap: 8,
  },
  addDogText: {
    fontSize: 17,
    fontWeight: '700',
    color: COLORS.text,
  },
  scoreCard: {
    borderRadius: 24,
    padding: 20,
    marginBottom: 20,
  },
  scoreHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 20,
  },
  dogAvatar: {
    width: 56,
    height: 56,
    borderRadius: 28,
    backgroundColor: 'rgba(255,255,255,0.95)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  scoreInfo: {
    flex: 1,
    marginLeft: 14,
  },
  dogName: {
    fontSize: 22,
    fontWeight: '700',
    color: COLORS.text,
  },
  breedText: {
    fontSize: 13,
    color: 'rgba(255,255,255,0.8)',
    marginTop: 2,
  },
  editBtn: {
    width: 36,
    height: 36,
    borderRadius: 18,
    backgroundColor: 'rgba(255,255,255,0.2)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  scoreBody: {
    backgroundColor: 'rgba(255,255,255,0.15)',
    borderRadius: 16,
    padding: 16,
  },
  mainScore: {
    marginBottom: 12,
  },
  scoreLabel: {
    fontSize: 13,
    color: 'rgba(255,255,255,0.8)',
    fontWeight: '500',
  },
  scoreRow: {
    flexDirection: 'row',
    alignItems: 'flex-end',
    marginTop: 4,
  },
  scoreValue: {
    fontSize: 48,
    fontWeight: '800',
    color: COLORS.text,
    lineHeight: 52,
  },
  scoreTrend: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: 'rgba(16,185,129,0.2)',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 12,
    marginLeft: 12,
    marginBottom: 8,
  },
  trendText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#10B981',
    marginLeft: 4,
  },
  scoreBar: {
    height: 6,
    backgroundColor: 'rgba(255,255,255,0.3)',
    borderRadius: 3,
    marginTop: 8,
  },
  scoreProgress: {
    height: 6,
    backgroundColor: COLORS.text,
    borderRadius: 3,
  },
  scoreRank: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingTop: 12,
    borderTopWidth: 1,
    borderTopColor: 'rgba(255,255,255,0.2)',
  },
  rankText: {
    fontSize: 14,
    color: COLORS.text,
    fontWeight: '600',
    marginLeft: 8,
  },
  statsContainer: {
    marginBottom: 20,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: COLORS.text,
    marginBottom: 14,
  },
  statsGrid: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  statCard: {
    flex: 1,
    backgroundColor: COLORS.card,
    borderRadius: 16,
    padding: 12,
    marginHorizontal: 4,
    alignItems: 'center',
  },
  statIcon: {
    width: 40,
    height: 40,
    borderRadius: 12,
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 8,
  },
  statValue: {
    fontSize: 14,
    fontWeight: '700',
    color: COLORS.text,
  },
  statLabel: {
    fontSize: 11,
    color: COLORS.textSecondary,
    marginTop: 2,
  },
  ritualCard: {
    marginBottom: 24,
    borderRadius: 20,
    overflow: 'hidden',
  },
  ritualGradient: {
    padding: 20,
  },
  ritualContent: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  ritualIcon: {
    width: 52,
    height: 52,
    borderRadius: 26,
    backgroundColor: 'rgba(255,255,255,0.2)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  ritualText: {
    flex: 1,
    marginLeft: 14,
  },
  ritualTitle: {
    fontSize: 17,
    fontWeight: '700',
    color: COLORS.text,
  },
  ritualSubtitle: {
    fontSize: 13,
    color: 'rgba(255,255,255,0.8)',
    marginTop: 2,
  },
  liloCard: {
    backgroundColor: COLORS.card,
    borderRadius: 20,
    padding: 20,
    borderWidth: 1,
    borderColor: COLORS.secondary + '30',
  },
  liloHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 14,
  },
  liloAvatar: {
    width: 48,
    height: 48,
    borderRadius: 24,
    marginRight: 12,
  },
  liloEmoji: {
    fontSize: 22,
  },
  liloName: {
    fontSize: 16,
    fontWeight: '700',
    color: COLORS.secondary,
  },
  liloLabel: {
    fontSize: 12,
    color: COLORS.textSecondary,
  },
  liloMessage: {
    fontSize: 14,
    color: COLORS.text,
    lineHeight: 22,
    fontStyle: 'italic',
  },
  liloInsight: {
    fontSize: 13,
    color: COLORS.textSecondary,
    marginTop: 10,
    lineHeight: 20,
  },
  liloBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    marginTop: 14,
    paddingTop: 14,
    borderTopWidth: 1,
    borderTopColor: COLORS.border,
  },
  liloBtnText: {
    fontSize: 14,
    fontWeight: '600',
    color: COLORS.secondary,
    marginRight: 6,
  },
});
