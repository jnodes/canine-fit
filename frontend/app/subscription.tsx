import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ScrollView,
  ActivityIndicator,
  Alert,
  Linking,
  Platform,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { LinearGradient } from 'expo-linear-gradient';
import { useRouter, useLocalSearchParams } from 'expo-router';
import { useAuth } from '../src/context/AuthContext';
import api from '../src/services/api';

const COLORS = {
  primary: '#FF6B00',
  secondary: '#00BFA5',
  navy: '#1E3A8A',
  background: '#0A0E17',
  card: '#141B2D',
  text: '#FFFFFF',
  textSecondary: '#8892A6',
  border: '#1F2937',
  success: '#10B981',
  warning: '#F59E0B',
  gold: '#FFD700',
};

interface Plan {
  name: string;
  price: number;
  period: string;
  description: string;
}

export default function SubscriptionScreen() {
  const router = useRouter();
  const params = useLocalSearchParams();
  const { user, isAuthenticated } = useAuth();
  const [plans, setPlans] = useState<Record<string, Plan>>({});
  const [selectedPlan, setSelectedPlan] = useState<string>('annual');
  const [isLoading, setIsLoading] = useState(true);
  const [isCheckingOut, setIsCheckingOut] = useState(false);
  const [checkingStatus, setCheckingStatus] = useState(false);

  useEffect(() => {
    loadPlans();
    
    // Check for session_id from Stripe redirect
    if (params.session_id) {
      checkPaymentStatus(params.session_id as string);
    }
  }, [params.session_id]);

  const loadPlans = async () => {
    try {
      const plansData = await api.getSubscriptionPlans();
      setPlans(plansData);
    } catch (error) {
      console.error('Failed to load plans:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const checkPaymentStatus = async (sessionId: string) => {
    setCheckingStatus(true);
    let attempts = 0;
    const maxAttempts = 5;
    
    const poll = async () => {
      try {
        const status = await api.getCheckoutStatus(sessionId);
        
        if (status.payment_status === 'paid') {
          Alert.alert(
            'Welcome to Premium! 🎉',
            'Your subscription is now active. Enjoy all the premium features!',
            [{ text: 'Start Exploring', onPress: () => router.replace('/(tabs)') }]
          );
          setCheckingStatus(false);
          return;
        } else if (status.status === 'expired') {
          Alert.alert('Payment Expired', 'Your payment session expired. Please try again.');
          setCheckingStatus(false);
          return;
        }
        
        attempts++;
        if (attempts < maxAttempts) {
          setTimeout(poll, 2000);
        } else {
          setCheckingStatus(false);
          Alert.alert(
            'Processing',
            'Your payment is being processed. Please check back in a moment.',
            [{ text: 'OK' }]
          );
        }
      } catch (error) {
        setCheckingStatus(false);
        console.error('Error checking status:', error);
      }
    };
    
    poll();
  };

  const handleSubscribe = async () => {
    if (!isAuthenticated) {
      router.push('/auth');
      return;
    }

    setIsCheckingOut(true);
    try {
      const originUrl = Platform.OS === 'web' 
        ? window.location.origin 
        : process.env.EXPO_PUBLIC_BACKEND_URL || 'https://dog-fitness-hub.preview.emergentagent.com';
      
      const result = await api.createCheckoutSession(selectedPlan, originUrl);
      
      if (result.checkout_url) {
        if (Platform.OS === 'web') {
          window.location.href = result.checkout_url;
        } else {
          await Linking.openURL(result.checkout_url);
        }
      }
    } catch (error: any) {
      Alert.alert('Error', error.message || 'Failed to start checkout');
    } finally {
      setIsCheckingOut(false);
    }
  };

  const features = [
    { icon: 'sparkles', text: 'AI-Powered Health Insights', premium: true },
    { icon: 'analytics', text: 'Advanced Analytics & Trends', premium: true },
    { icon: 'trophy', text: 'Breed Leaderboard Access', premium: true },
    { icon: 'restaurant', text: 'Food Safety Database', premium: true },
    { icon: 'notifications', text: 'Smart Health Reminders', premium: true },
    { icon: 'cloud-upload', text: 'Unlimited Cloud Backup', premium: true },
    { icon: 'people', text: 'Multi-Pet Support', premium: true },
    { icon: 'medical', text: 'Vet Visit Tracking', premium: true },
  ];

  if (isLoading || checkingStatus) {
    return (
      <SafeAreaView style={[styles.container, styles.centered]}>
        <ActivityIndicator size="large" color={COLORS.primary} />
        <Text style={styles.loadingText}>
          {checkingStatus ? 'Verifying your payment...' : 'Loading plans...'}
        </Text>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.container} edges={['top']}>
      <ScrollView showsVerticalScrollIndicator={false} contentContainerStyle={styles.scrollContent}>
        {/* Header */}
        <View style={styles.header}>
          <TouchableOpacity style={styles.closeBtn} onPress={() => router.back()}>
            <Ionicons name="close" size={24} color={COLORS.text} />
          </TouchableOpacity>
          
          <View style={styles.headerIcon}>
            <LinearGradient
              colors={[COLORS.gold, '#FFA500']}
              style={styles.crownBg}
            >
              <Ionicons name="diamond" size={32} color="#000" />
            </LinearGradient>
          </View>
          
          <Text style={styles.title}>Unlock Premium</Text>
          <Text style={styles.subtitle}>
            Give your dog the healthiest life possible with AI-powered insights and advanced tracking
          </Text>
        </View>

        {/* Plan Selection */}
        <View style={styles.plansContainer}>
          {Object.entries(plans).map(([planId, plan]) => (
            <TouchableOpacity
              key={planId}
              style={[
                styles.planCard,
                selectedPlan === planId && styles.planCardSelected,
              ]}
              onPress={() => setSelectedPlan(planId)}
              activeOpacity={0.7}
            >
              {planId === 'annual' && (
                <View style={styles.bestValueBadge}>
                  <Text style={styles.bestValueText}>BEST VALUE</Text>
                </View>
              )}
              
              <View style={styles.planRadio}>
                <View style={[
                  styles.radioOuter,
                  selectedPlan === planId && styles.radioOuterSelected
                ]}>
                  {selectedPlan === planId && <View style={styles.radioInner} />}
                </View>
              </View>
              
              <View style={styles.planInfo}>
                <Text style={styles.planName}>{plan.name}</Text>
                <Text style={styles.planDescription}>{plan.description}</Text>
              </View>
              
              <View style={styles.planPrice}>
                <Text style={styles.priceAmount}>${plan.price}</Text>
                <Text style={styles.pricePeriod}>/{plan.period === 'month' ? 'mo' : 'yr'}</Text>
              </View>
            </TouchableOpacity>
          ))}
        </View>

        {/* Features List */}
        <View style={styles.featuresContainer}>
          <Text style={styles.featuresTitle}>What's included</Text>
          
          {features.map((feature, index) => (
            <View key={index} style={styles.featureRow}>
              <View style={[styles.featureIcon, { backgroundColor: COLORS.secondary + '20' }]}>
                <Ionicons name={feature.icon as any} size={18} color={COLORS.secondary} />
              </View>
              <Text style={styles.featureText}>{feature.text}</Text>
              <Ionicons name="checkmark-circle" size={20} color={COLORS.success} />
            </View>
          ))}
        </View>

        {/* Subscribe Button */}
        <TouchableOpacity
          style={styles.subscribeBtn}
          onPress={handleSubscribe}
          disabled={isCheckingOut}
          activeOpacity={0.8}
        >
          <LinearGradient
            colors={[COLORS.primary, '#FF8533']}
            start={{ x: 0, y: 0 }}
            end={{ x: 1, y: 0 }}
            style={styles.subscribeGradient}
          >
            {isCheckingOut ? (
              <ActivityIndicator color={COLORS.text} />
            ) : (
              <>
                <Ionicons name="lock-open" size={20} color={COLORS.text} />
                <Text style={styles.subscribeText}>
                  Start Premium — ${plans[selectedPlan]?.price}/{plans[selectedPlan]?.period === 'month' ? 'mo' : 'yr'}
                </Text>
              </>
            )}
          </LinearGradient>
        </TouchableOpacity>

        {/* Terms */}
        <Text style={styles.termsText}>
          Cancel anytime. By subscribing, you agree to our{" "}
          <Text style={styles.link} onPress={() => Linking.openURL('https://canine.fit/terms')}>
            Terms of Service
          </Text>{" "}
          and{" "}
          <Text style={styles.link} onPress={() => Linking.openURL('https://canine.fit/privacy')}>
            Privacy Policy
          </Text>
          .
        </Text>

        {/* Guarantee */}
        <View style={styles.guaranteeContainer}>
          <Ionicons name="shield-checkmark" size={24} color={COLORS.success} />
          <Text style={styles.guaranteeText}>7-day money-back guarantee</Text>
        </View>
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
  loadingText: {
    marginTop: 16,
    fontSize: 16,
    color: COLORS.textSecondary,
  },
  scrollContent: {
    paddingHorizontal: 24,
    paddingBottom: 40,
  },
  header: {
    alignItems: 'center',
    paddingTop: 20,
    paddingBottom: 32,
  },
  closeBtn: {
    position: 'absolute',
    top: 20,
    right: 0,
    width: 44,
    height: 44,
    borderRadius: 22,
    backgroundColor: COLORS.card,
    justifyContent: 'center',
    alignItems: 'center',
  },
  headerIcon: {
    marginBottom: 20,
  },
  crownBg: {
    width: 72,
    height: 72,
    borderRadius: 24,
    justifyContent: 'center',
    alignItems: 'center',
  },
  title: {
    fontSize: 28,
    fontWeight: '800',
    color: COLORS.text,
    marginBottom: 12,
  },
  subtitle: {
    fontSize: 15,
    color: COLORS.textSecondary,
    textAlign: 'center',
    lineHeight: 22,
    paddingHorizontal: 20,
  },
  plansContainer: {
    marginBottom: 32,
    gap: 12,
  },
  planCard: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: COLORS.card,
    borderRadius: 16,
    padding: 16,
    borderWidth: 2,
    borderColor: 'transparent',
    position: 'relative',
  },
  planCardSelected: {
    borderColor: COLORS.primary,
    backgroundColor: COLORS.primary + '10',
  },
  bestValueBadge: {
    position: 'absolute',
    top: -10,
    right: 16,
    backgroundColor: COLORS.primary,
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 8,
  },
  bestValueText: {
    fontSize: 10,
    fontWeight: '700',
    color: COLORS.text,
  },
  planRadio: {
    marginRight: 14,
  },
  radioOuter: {
    width: 24,
    height: 24,
    borderRadius: 12,
    borderWidth: 2,
    borderColor: COLORS.textSecondary,
    justifyContent: 'center',
    alignItems: 'center',
  },
  radioOuterSelected: {
    borderColor: COLORS.primary,
  },
  radioInner: {
    width: 12,
    height: 12,
    borderRadius: 6,
    backgroundColor: COLORS.primary,
  },
  planInfo: {
    flex: 1,
  },
  planName: {
    fontSize: 17,
    fontWeight: '600',
    color: COLORS.text,
  },
  planDescription: {
    fontSize: 13,
    color: COLORS.textSecondary,
    marginTop: 2,
  },
  planPrice: {
    flexDirection: 'row',
    alignItems: 'baseline',
  },
  priceAmount: {
    fontSize: 24,
    fontWeight: '700',
    color: COLORS.text,
  },
  pricePeriod: {
    fontSize: 14,
    color: COLORS.textSecondary,
  },
  featuresContainer: {
    marginBottom: 32,
  },
  featuresTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: COLORS.text,
    marginBottom: 16,
  },
  featureRow: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: COLORS.border,
  },
  featureIcon: {
    width: 36,
    height: 36,
    borderRadius: 10,
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 14,
  },
  featureText: {
    flex: 1,
    fontSize: 15,
    color: COLORS.text,
  },
  subscribeBtn: {
    borderRadius: 16,
    overflow: 'hidden',
    marginBottom: 16,
  },
  subscribeGradient: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 18,
    gap: 10,
  },
  subscribeText: {
    fontSize: 17,
    fontWeight: '700',
    color: COLORS.text,
  },
  termsText: {
    fontSize: 12,
    color: COLORS.textSecondary,
    textAlign: 'center',
    marginBottom: 20,
    lineHeight: 18,
  },
  link: {
    color: COLORS.primary,
    textDecorationLine: 'underline',
  },
  guaranteeContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
  },
  guaranteeText: {
    fontSize: 14,
    fontWeight: '600',
    color: COLORS.success,
  },
});
