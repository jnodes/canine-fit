import React, { useRef, useEffect, useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  Dimensions,
  Animated,
  Image,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { useRouter } from 'expo-router';
import { LinearGradient } from 'expo-linear-gradient';
import { usePremium } from '../../src/context/AuthContext';
import UpgradePrompt from '../../src/components/UpgradePrompt';

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
  error: '#EF4444',
};

export default function InsightsScreen() {
  const router = useRouter();
  const fadeAnim = useRef(new Animated.Value(0)).current;
  const slideAnim = useRef(new Animated.Value(30)).current;
  const { isPremium } = usePremium();
  const [showUpgradeModal, setShowUpgradeModal] = useState(false);
  const [lockedFeature, setLockedFeature] = useState('');

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
    ]).start();
  }, []);

  const handlePremiumAction = (feature: string) => {
    setLockedFeature(feature);
    setShowUpgradeModal(true);
  };

  const weeklyData = [
    { day: 'Mon', score: 88, height: 75 },
    { day: 'Tue', score: 92, height: 85 },
    { day: 'Wed', score: 85, height: 70 },
    { day: 'Thu', score: 94, height: 90 },
    { day: 'Fri', score: 90, height: 80 },
    { day: 'Sat', score: 96, height: 95 },
    { day: 'Sun', score: 94, height: 90 },
  ];

  const insights = [
    {
      id: 1,
      type: 'positive',
      icon: 'trending-up',
      title: 'Activity Up 15%',
      description: 'Max is more active this week compared to last week. Great job!',
      color: COLORS.success,
    },
    {
      id: 2,
      type: 'warning',
      icon: 'water',
      title: 'Hydration Reminder',
      description: 'Ensure Max drinks enough water after walks on hot days.',
      color: COLORS.warning,
    },
    {
      id: 3,
      type: 'tip',
      icon: 'bulb',
      title: 'Pro Tip',
      description: 'Golden Retrievers benefit from swimming - consider pool time!',
      color: COLORS.navy,
    },
  ];

  const whatIfScenarios = [
    {
      id: 1,
      scenario: '+10 min daily walk',
      impact: '+2.3 months lifespan',
      icon: 'walk',
      color: COLORS.secondary,
    },
    {
      id: 2,
      scenario: 'Add fish oil supplement',
      impact: '+1.8 months lifespan',
      icon: 'fish',
      color: COLORS.primary,
    },
    {
      id: 3,
      scenario: 'Reduce treats by 20%',
      impact: '+3.1 months lifespan',
      icon: 'remove-circle',
      color: COLORS.success,
    },
  ];

  const breedLeaderboard = [
    { rank: 1, name: 'Bella', score: 98, isYou: false },
    { rank: 2, name: 'Charlie', score: 97, isYou: false },
    { rank: 3, name: 'Luna', score: 96, isYou: false },
    { rank: 12, name: 'Max', score: 94, isYou: true },
  ];

  return (
    <SafeAreaView style={styles.container} edges={['top']}>
      <ScrollView showsVerticalScrollIndicator={false} contentContainerStyle={styles.scrollContent}>
        {/* Header */}
        <Animated.View style={[styles.header, { opacity: fadeAnim, transform: [{ translateY: slideAnim }] }]}>
          <Text style={styles.title}>Insights</Text>
          <Text style={styles.subtitle}>AI-powered health analysis for Max</Text>
        </Animated.View>

        {/* Weekly Score Chart */}
        <Animated.View style={[styles.chartCard, { opacity: fadeAnim }]}>
          <View style={styles.chartHeader}>
            <Text style={styles.chartTitle}>Weekly Healthspan</Text>
            <View style={styles.chartBadge}>
              <Ionicons name="trending-up" size={14} color={COLORS.success} />
              <Text style={styles.chartBadgeText}>+6%</Text>
            </View>
          </View>
          
          <View style={styles.chartContainer}>
            {weeklyData.map((item, index) => (
              <View key={index} style={styles.barContainer}>
                <View style={styles.barWrapper}>
                  <LinearGradient
                    colors={[COLORS.primary, COLORS.primary + '80']}
                    style={[styles.bar, { height: item.height }]}
                  />
                </View>
                <Text style={styles.barLabel}>{item.day}</Text>
              </View>
            ))}
          </View>
          
          <View style={styles.chartFooter}>
            <View style={styles.avgScore}>
              <Text style={styles.avgLabel}>Weekly Average</Text>
              <Text style={styles.avgValue}>91.3</Text>
            </View>
            <TouchableOpacity style={styles.detailsBtn}>
              <Text style={styles.detailsBtnText}>View Details</Text>
              <Ionicons name="chevron-forward" size={16} color={COLORS.primary} />
            </TouchableOpacity>
          </View>
        </Animated.View>

        {/* AI Insights */}
        <Animated.View style={{ opacity: fadeAnim }}>
          <View style={styles.sectionHeader}>
            <Image source={LILO_IMAGE} style={styles.liloSectionImage} />
            <Text style={styles.sectionTitle}>Lilo's Insights</Text>
          </View>
          
          {insights.map((insight) => (
            <TouchableOpacity key={insight.id} style={styles.insightCard}>
              <View style={[styles.insightIcon, { backgroundColor: insight.color + '20' }]}>
                <Ionicons name={insight.icon as any} size={22} color={insight.color} />
              </View>
              <View style={styles.insightContent}>
                <Text style={styles.insightTitle}>{insight.title}</Text>
                <Text style={styles.insightDesc}>{insight.description}</Text>
              </View>
              <Ionicons name="chevron-forward" size={20} color={COLORS.textSecondary} />
            </TouchableOpacity>
          ))}
        </Animated.View>

        {/* What-If Simulator */}
        <Animated.View style={{ opacity: fadeAnim }}>
          <View style={styles.sectionHeader}>
            <View style={[styles.sectionIcon, { backgroundColor: COLORS.primary + '20' }]}>
              <Ionicons name="flash" size={18} color={COLORS.primary} />
            </View>
            <Text style={styles.sectionTitle}>What-If Simulator</Text>
          </View>
          
          <View style={styles.scenariosContainer}>
            {whatIfScenarios.map((scenario) => (
              <TouchableOpacity key={scenario.id} style={styles.scenarioCard}>
                <View style={[styles.scenarioIcon, { backgroundColor: scenario.color + '15' }]}>
                  <Ionicons name={scenario.icon as any} size={24} color={scenario.color} />
                </View>
                <Text style={styles.scenarioText}>{scenario.scenario}</Text>
                <View style={styles.scenarioImpact}>
                  <Ionicons name="add" size={14} color={COLORS.success} />
                  <Text style={styles.impactText}>{scenario.impact}</Text>
                </View>
              </TouchableOpacity>
            ))}
          </View>
        </Animated.View>

        {/* Breed Leaderboard - Premium */}
        <Animated.View style={[styles.leaderboardCard, { opacity: fadeAnim }]}>
          <View style={styles.leaderboardHeader}>
            <View style={styles.leaderboardTitle}>
              <Ionicons name="trophy" size={20} color={COLORS.warning} />
              <Text style={styles.leaderboardTitleText}>Golden Retriever Leaderboard</Text>
              {!isPremium && (
                <View style={styles.premiumBadge}>
                  <Ionicons name="diamond" size={10} color={COLORS.warning} />
                </View>
              )}
            </View>
            <TouchableOpacity onPress={() => isPremium ? router.push('/leaderboard') : handlePremiumAction('Breed Leaderboard')}>
              <Text style={[styles.viewAllBtn, !isPremium && styles.viewAllBtnLocked]}>View All</Text>
            </TouchableOpacity>
          </View>
          
          {!isPremium ? (
            <TouchableOpacity style={styles.lockedContent} onPress={() => handlePremiumAction('Breed Leaderboard')}>
              <Ionicons name="lock-closed" size={32} color={COLORS.textSecondary} />
              <Text style={styles.lockedText}>Upgrade to Premium to view leaderboard</Text>
              <View style={styles.upgradeCta}>
                <Ionicons name="sparkles" size={14} color={COLORS.warning} />
                <Text style={styles.upgradeCtaText}>Unlock with Premium</Text>
              </View>
            </TouchableOpacity>
          ) : (
            breedLeaderboard.map((dog) => (
            <View 
              key={dog.rank} 
              style={[
                styles.leaderboardItem,
                dog.isYou && styles.leaderboardItemHighlight
              ]}
            >
              <View style={styles.rankContainer}>
                {dog.rank <= 3 ? (
                  <View style={[
                    styles.medalBadge,
                    { backgroundColor: dog.rank === 1 ? '#FFD700' : dog.rank === 2 ? '#C0C0C0' : '#CD7F32' }
                  ]}>
                    <Text style={styles.medalText}>{dog.rank}</Text>
                  </View>
                ) : (
                  <Text style={styles.rankText}>#{dog.rank}</Text>
                )}
              </View>
              <Text style={[styles.dogName, dog.isYou && styles.dogNameHighlight]}>
                {dog.name} {dog.isYou && '(You)'}
              </Text>
              <Text style={[styles.dogScore, dog.isYou && styles.dogScoreHighlight]}>
                {dog.score} pts
              </Text>
            </View>
          )))}
        </Animated.View>

        {/* Food Safety Quick Check - Premium */}
        <Animated.View style={{ opacity: fadeAnim }}>
          <TouchableOpacity 
            style={styles.foodCheckCard}
            onPress={() => isPremium ? null : handlePremiumAction('Food Safety Database')}
          >
            <LinearGradient
              colors={[isPremium ? COLORS.navy : COLORS.cardLight, isPremium ? '#2563EB' : '#374151']}
              start={{ x: 0, y: 0 }}
              end={{ x: 1, y: 0 }}
              style={styles.foodCheckGradient}
            >
              <View style={styles.foodCheckIcon}>
                <Ionicons name="search" size={24} color={COLORS.text} />
              </View>
              <View style={styles.foodCheckContent}>
                <Text style={styles.foodCheckTitle}>Food Safety Checker</Text>
                <Text style={styles.foodCheckSubtitle}>Is this food safe for Max?</Text>
              </View>
              <Ionicons name="chevron-forward" size={24} color="rgba(255,255,255,0.7)" />
            </LinearGradient>
          </TouchableOpacity>
        </Animated.View>
      </ScrollView>
      
      <UpgradePrompt
        visible={showUpgradeModal}
        onClose={() => setShowUpgradeModal(false)}
        feature={lockedFeature}
      />
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
  chartCard: {
    backgroundColor: COLORS.card,
    borderRadius: 24,
    padding: 20,
    marginBottom: 24,
  },
  chartHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 20,
  },
  chartTitle: {
    fontSize: 17,
    fontWeight: '700',
    color: COLORS.text,
  },
  chartBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: COLORS.success + '20',
    paddingHorizontal: 10,
    paddingVertical: 5,
    borderRadius: 12,
  },
  chartBadgeText: {
    fontSize: 13,
    fontWeight: '600',
    color: COLORS.success,
    marginLeft: 4,
  },
  chartContainer: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-end',
    height: 120,
    paddingHorizontal: 5,
  },
  barContainer: {
    alignItems: 'center',
    flex: 1,
  },
  barWrapper: {
    height: 100,
    width: 28,
    justifyContent: 'flex-end',
  },
  bar: {
    width: '100%',
    borderRadius: 8,
  },
  barLabel: {
    fontSize: 11,
    color: COLORS.textSecondary,
    marginTop: 8,
    fontWeight: '500',
  },
  chartFooter: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginTop: 20,
    paddingTop: 16,
    borderTopWidth: 1,
    borderTopColor: COLORS.border,
  },
  avgScore: {},
  avgLabel: {
    fontSize: 12,
    color: COLORS.textSecondary,
  },
  avgValue: {
    fontSize: 24,
    fontWeight: '700',
    color: COLORS.text,
    marginTop: 2,
  },
  detailsBtn: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  detailsBtnText: {
    fontSize: 14,
    fontWeight: '600',
    color: COLORS.primary,
    marginRight: 4,
  },
  sectionHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 16,
  },
  sectionIcon: {
    width: 32,
    height: 32,
    borderRadius: 10,
    backgroundColor: COLORS.secondary + '20',
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 10,
  },
  liloSectionImage: {
    width: 36,
    height: 36,
    borderRadius: 18,
    marginRight: 10,
  },
  sectionTitle: {
    fontSize: 17,
    fontWeight: '700',
    color: COLORS.text,
  },
  insightCard: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: COLORS.card,
    borderRadius: 16,
    padding: 16,
    marginBottom: 10,
  },
  insightIcon: {
    width: 48,
    height: 48,
    borderRadius: 14,
    justifyContent: 'center',
    alignItems: 'center',
  },
  insightContent: {
    flex: 1,
    marginLeft: 14,
  },
  insightTitle: {
    fontSize: 15,
    fontWeight: '600',
    color: COLORS.text,
  },
  insightDesc: {
    fontSize: 13,
    color: COLORS.textSecondary,
    marginTop: 3,
    lineHeight: 18,
  },
  scenariosContainer: {
    flexDirection: 'row',
    marginBottom: 24,
    marginHorizontal: -5,
  },
  scenarioCard: {
    flex: 1,
    backgroundColor: COLORS.card,
    borderRadius: 16,
    padding: 14,
    marginHorizontal: 5,
    alignItems: 'center',
  },
  scenarioIcon: {
    width: 50,
    height: 50,
    borderRadius: 16,
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 10,
  },
  scenarioText: {
    fontSize: 12,
    fontWeight: '600',
    color: COLORS.text,
    textAlign: 'center',
    marginBottom: 8,
    minHeight: 32,
  },
  scenarioImpact: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: COLORS.success + '15',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 8,
  },
  impactText: {
    fontSize: 10,
    fontWeight: '600',
    color: COLORS.success,
    marginLeft: 2,
  },
  leaderboardCard: {
    backgroundColor: COLORS.card,
    borderRadius: 20,
    padding: 18,
    marginBottom: 20,
  },
  leaderboardHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 16,
  },
  leaderboardTitle: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  premiumBadge: {
    marginLeft: 8,
    backgroundColor: 'rgba(245, 158, 11, 0.2)',
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: 4,
  },
  viewAllBtnLocked: {
    color: COLORS.warning,
  },
  lockedContent: {
    alignItems: 'center',
    paddingVertical: 32,
  },
  lockedText: {
    color: COLORS.textSecondary,
    fontSize: 14,
    marginTop: 12,
    textAlign: 'center',
  },
  upgradeCta: {
    flexDirection: 'row',
    alignItems: 'center',
    marginTop: 12,
    backgroundColor: 'rgba(245, 158, 11, 0.1)',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 16,
    gap: 4,
  },
  upgradeCtaText: {
    color: COLORS.warning,
    fontSize: 12,
    fontWeight: '600',
  },
  leaderboardTitleText: {
    fontSize: 15,
    fontWeight: '700',
    color: COLORS.text,
    marginLeft: 8,
  },
  viewAllBtn: {
    fontSize: 13,
    color: COLORS.primary,
    fontWeight: '600',
  },
  leaderboardItem: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: COLORS.border,
  },
  leaderboardItemHighlight: {
    backgroundColor: COLORS.primary + '10',
    marginHorizontal: -18,
    paddingHorizontal: 18,
    borderRadius: 12,
    borderBottomWidth: 0,
  },
  rankContainer: {
    width: 40,
  },
  medalBadge: {
    width: 26,
    height: 26,
    borderRadius: 13,
    justifyContent: 'center',
    alignItems: 'center',
  },
  medalText: {
    fontSize: 12,
    fontWeight: '700',
    color: '#000',
  },
  rankText: {
    fontSize: 14,
    fontWeight: '600',
    color: COLORS.textSecondary,
  },
  dogName: {
    flex: 1,
    fontSize: 15,
    fontWeight: '500',
    color: COLORS.text,
  },
  dogNameHighlight: {
    fontWeight: '700',
    color: COLORS.primary,
  },
  dogScore: {
    fontSize: 14,
    fontWeight: '600',
    color: COLORS.textSecondary,
  },
  dogScoreHighlight: {
    color: COLORS.primary,
  },
  foodCheckCard: {
    borderRadius: 20,
    overflow: 'hidden',
    marginBottom: 20,
  },
  foodCheckGradient: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 20,
  },
  foodCheckIcon: {
    width: 52,
    height: 52,
    borderRadius: 16,
    backgroundColor: 'rgba(255,255,255,0.15)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  foodCheckContent: {
    flex: 1,
    marginLeft: 14,
  },
  foodCheckTitle: {
    fontSize: 17,
    fontWeight: '700',
    color: COLORS.text,
  },
  foodCheckSubtitle: {
    fontSize: 13,
    color: 'rgba(255,255,255,0.7)',
    marginTop: 2,
  },
});
