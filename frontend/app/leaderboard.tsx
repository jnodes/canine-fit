import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  FlatList,
  TouchableOpacity,
  ActivityIndicator,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { useRouter } from 'expo-router';
import { usePremium } from '../src/context/AuthContext';
import UpgradePrompt from '../src/components/UpgradePrompt';
import api from '../src/services/api';

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

interface LeaderboardEntry {
  rank: number;
  id: string;
  name: string;
  breed: string;
  avatar_url?: string;
  total_points: number;
  streak: number;
  score: number;
  is_ai: boolean;
}

export default function LeaderboardScreen() {
  const router = useRouter();
  const { isPremium } = usePremium();
  const [showUpgradeModal, setShowUpgradeModal] = useState(false);
  const [leaderboard, setLeaderboard] = useState<LeaderboardEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'global' | 'breed'>('global');
  const [selectedBreed, setSelectedBreed] = useState('Golden Retriever');

  useEffect(() => {
    if (!isPremium) {
      setShowUpgradeModal(true);
      setLoading(false);
      return;
    }
    fetchLeaderboard();
  }, [isPremium, activeTab, selectedBreed]);

  const fetchLeaderboard = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = activeTab === 'global' 
        ? await api.getGlobalLeaderboard()
        : await api.getBreedLeaderboard(selectedBreed);
      setLeaderboard(data);
    } catch (err: any) {
      if (err?.response?.data?.detail?.error === 'premium_required') {
        setShowUpgradeModal(true);
      } else {
        setError('Failed to load leaderboard');
      }
    } finally {
      setLoading(false);
    }
  };

  const getMedalColor = (rank: number) => {
    switch (rank) {
      case 1: return '#FFD700';
      case 2: return '#C0C0C0';
      case 3: return '#CD7F32';
      default: return COLORS.textSecondary;
    }
  };

  const renderItem = ({ item }: { item: LeaderboardEntry }) => (
    <View style={[styles.leaderboardItem, item.rank <= 3 && styles.topThreeItem]}>
      <View style={styles.rankContainer}>
        {item.rank <= 3 ? (
          <View style={[styles.medalBadge, { backgroundColor: getMedalColor(item.rank) }]}>
            <Text style={[styles.medalText, item.rank === 1 && styles.goldText]}>{item.rank}</Text>
          </View>
        ) : (
          <Text style={styles.rankText}>#{item.rank}</Text>
        )}
      </View>
      
      <View style={styles.dogInfo}>
        <Text style={styles.dogName}>{item.name}</Text>
        <Text style={styles.dogBreed}>{item.breed}</Text>
      </View>
      
      <View style={styles.statsContainer}>
        <Text style={styles.scoreText}>{item.score}</Text>
        <Text style={styles.pointsLabel}>pts</Text>
      </View>
    </View>
  );

  return (
    <SafeAreaView style={styles.container} edges={['top']}>
      {/* Header */}
      <View style={styles.header}>
        <TouchableOpacity onPress={() => router.back()} style={styles.backButton}>
          <Ionicons name="chevron-back" size={24} color={COLORS.text} />
        </TouchableOpacity>
        <Text style={styles.title}>Leaderboard</Text>
        <View style={styles.placeholder} />
      </View>

      {/* Tabs */}
      <View style={styles.tabs}>
        <TouchableOpacity
          style={[styles.tab, activeTab === 'global' && styles.activeTab]}
          onPress={() => setActiveTab('global')}
        >
          <Ionicons
            name="globe"
            size={18}
            color={activeTab === 'global' ? COLORS.primary : COLORS.textSecondary}
          />
          <Text style={[styles.tabText, activeTab === 'global' && styles.activeTabText]}>
            Global
          </Text>
        </TouchableOpacity>
        
        <TouchableOpacity
          style={[styles.tab, activeTab === 'breed' && styles.activeTab]}
          onPress={() => setActiveTab('breed')}
        >
          <Ionicons
            name="paw"
            size={18}
            color={activeTab === 'breed' ? COLORS.primary : COLORS.textSecondary}
          />
          <Text style={[styles.tabText, activeTab === 'breed' && styles.activeTabText]}>
            By Breed
          </Text>
        </TouchableOpacity>
      </View>

      {/* Breed Selector (if breed tab) */}
      {activeTab === 'breed' && (
        <View style={styles.breedSelector}>
          <TouchableOpacity style={styles.breedButton}>
            <Text style={styles.breedButtonText}>{selectedBreed}</Text>
            <Ionicons name="chevron-down" size={16} color={COLORS.textSecondary} />
          </TouchableOpacity>
        </View>
      )}

      {/* Leaderboard Content */}
      {loading ? (
        <View style={styles.centerContent}>
          <ActivityIndicator size="large" color={COLORS.primary} />
          <Text style={styles.loadingText}>Loading leaderboard...</Text>
        </View>
      ) : error ? (
        <View style={styles.centerContent}>
          <Ionicons name="alert-circle" size={48} color={COLORS.error} />
          <Text style={styles.errorText}>{error}</Text>
          <TouchableOpacity style={styles.retryButton} onPress={fetchLeaderboard}>
            <Text style={styles.retryButtonText}>Try Again</Text>
          </TouchableOpacity>
        </View>
      ) : (
        <FlatList
          data={leaderboard}
          renderItem={renderItem}
          keyExtractor={(item) => item.id}
          contentContainerStyle={styles.listContent}
          showsVerticalScrollIndicator={false}
          ListEmptyComponent={
            <View style={styles.centerContent}>
              <Ionicons name="trophy-outline" size={48} color={COLORS.textSecondary} />
              <Text style={styles.emptyText}>No entries yet</Text>
            </View>
          }
        />
      )}

      <UpgradePrompt
        visible={showUpgradeModal}
        onClose={() => {
          setShowUpgradeModal(false);
          if (!isPremium) {
            router.back();
          }
        }}
        feature="Leaderboard"
      />
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: COLORS.background,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 16,
    paddingVertical: 12,
  },
  backButton: {
    padding: 4,
  },
  title: {
    fontSize: 20,
    fontWeight: '700',
    color: COLORS.text,
  },
  placeholder: {
    width: 32,
  },
  tabs: {
    flexDirection: 'row',
    paddingHorizontal: 16,
    marginBottom: 16,
    gap: 12,
  },
  tab: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 12,
    borderRadius: 12,
    backgroundColor: COLORS.card,
    gap: 8,
  },
  activeTab: {
    backgroundColor: COLORS.primary + '20',
  },
  tabText: {
    fontSize: 14,
    fontWeight: '600',
    color: COLORS.textSecondary,
  },
  activeTabText: {
    color: COLORS.primary,
  },
  breedSelector: {
    paddingHorizontal: 16,
    marginBottom: 16,
  },
  breedButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 10,
    paddingHorizontal: 16,
    backgroundColor: COLORS.card,
    borderRadius: 8,
    alignSelf: 'center',
    gap: 6,
  },
  breedButtonText: {
    color: COLORS.text,
    fontSize: 14,
    fontWeight: '500',
  },
  listContent: {
    paddingHorizontal: 16,
    paddingBottom: 20,
  },
  leaderboardItem: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 14,
    paddingHorizontal: 16,
    backgroundColor: COLORS.card,
    borderRadius: 12,
    marginBottom: 8,
  },
  topThreeItem: {
    borderWidth: 1,
    borderColor: COLORS.border,
  },
  rankContainer: {
    width: 40,
    alignItems: 'center',
  },
  medalBadge: {
    width: 28,
    height: 28,
    borderRadius: 14,
    justifyContent: 'center',
    alignItems: 'center',
  },
  medalText: {
    fontSize: 12,
    fontWeight: '700',
    color: '#000',
  },
  goldText: {
    color: '#000',
  },
  rankText: {
    fontSize: 14,
    fontWeight: '600',
    color: COLORS.textSecondary,
  },
  dogInfo: {
    flex: 1,
    marginLeft: 12,
  },
  dogName: {
    fontSize: 15,
    fontWeight: '600',
    color: COLORS.text,
  },
  dogBreed: {
    fontSize: 12,
    color: COLORS.textSecondary,
    marginTop: 2,
  },
  statsContainer: {
    alignItems: 'flex-end',
  },
  scoreText: {
    fontSize: 18,
    fontWeight: '700',
    color: COLORS.primary,
  },
  pointsLabel: {
    fontSize: 10,
    color: COLORS.textSecondary,
  },
  centerContent: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 40,
  },
  loadingText: {
    marginTop: 12,
    color: COLORS.textSecondary,
    fontSize: 14,
  },
  errorText: {
    marginTop: 12,
    color: COLORS.error,
    fontSize: 14,
    textAlign: 'center',
  },
  retryButton: {
    marginTop: 16,
    paddingVertical: 10,
    paddingHorizontal: 24,
    backgroundColor: COLORS.primary,
    borderRadius: 8,
  },
  retryButtonText: {
    color: COLORS.text,
    fontWeight: '600',
  },
  emptyText: {
    marginTop: 12,
    color: COLORS.textSecondary,
    fontSize: 14,
  },
});
