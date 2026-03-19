import React, { useRef, useEffect, useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  Animated,
  Dimensions,
  Image,
  Alert,
  ActivityIndicator,
  Platform,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { LinearGradient } from 'expo-linear-gradient';
import { useRouter } from 'expo-router';
import * as ImagePicker from 'expo-image-picker';
import { useAuth } from '../../src/context/AuthContext';
import { useHealthspan } from '../../src/hooks/useHealthData';
import api from '../../src/services/api';

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

export default function ProfileScreen() {
  const router = useRouter();
  const { currentDog, user, refreshDogs, logout } = useAuth();
  const { healthspan } = useHealthspan();
  const [uploading, setUploading] = useState(false);
  
  const fadeAnim = useRef(new Animated.Value(0)).current;
  const slideAnim = useRef(new Animated.Value(30)).current;
  const scaleAnim = useRef(new Animated.Value(0.9)).current;

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

  const pickImage = async () => {
    // Request permissions
    const { status } = await ImagePicker.requestMediaLibraryPermissionsAsync();
    
    if (status !== 'granted') {
      Alert.alert('Permission Required', 'Please allow access to your photo library to upload a profile photo.');
      return;
    }

    try {
      const result = await ImagePicker.launchImageLibraryAsync({
        mediaTypes: ImagePicker.MediaTypeOptions.Images,
        allowsEditing: true,
        aspect: [1, 1],
        quality: 0.5,
        base64: true,
      });

      if (!result.canceled && result.assets[0].base64) {
        await uploadPhoto(result.assets[0].base64);
      }
    } catch (error) {
      Alert.alert('Error', 'Failed to pick image');
    }
  };

  const takePhoto = async () => {
    const { status } = await ImagePicker.requestCameraPermissionsAsync();
    
    if (status !== 'granted') {
      Alert.alert('Permission Required', 'Please allow camera access to take a profile photo.');
      return;
    }

    try {
      const result = await ImagePicker.launchCameraAsync({
        allowsEditing: true,
        aspect: [1, 1],
        quality: 0.5,
        base64: true,
      });

      if (!result.canceled && result.assets[0].base64) {
        await uploadPhoto(result.assets[0].base64);
      }
    } catch (error) {
      Alert.alert('Error', 'Failed to take photo');
    }
  };

  const uploadPhoto = async (base64: string) => {
    if (!currentDog) return;
    
    setUploading(true);
    try {
      await api.uploadDogPhoto(currentDog.id, base64);
      await refreshDogs();
      Alert.alert('Success', 'Photo uploaded successfully!');
    } catch (error: any) {
      Alert.alert('Error', error.message || 'Failed to upload photo');
    } finally {
      setUploading(false);
    }
  };

  const showPhotoOptions = () => {
    Alert.alert(
      'Update Profile Photo',
      'Choose an option',
      [
        { text: 'Take Photo', onPress: takePhoto },
        { text: 'Choose from Library', onPress: pickImage },
        { text: 'Cancel', style: 'cancel' },
      ]
    );
  };

  const handleLogout = () => {
    Alert.alert(
      'Logout',
      'Are you sure you want to logout?',
      [
        { text: 'Cancel', style: 'cancel' },
        { 
          text: 'Logout', 
          style: 'destructive',
          onPress: async () => {
            await logout();
            router.replace('/auth');
          }
        },
      ]
    );
  };

  if (!currentDog) {
    return (
      <SafeAreaView style={[styles.container, styles.centered]}>
        <ActivityIndicator size="large" color={COLORS.primary} />
      </SafeAreaView>
    );
  }

  const dogAge = calculateAge(currentDog.date_of_birth);

  const stats = [
    { label: 'Total Days Logged', value: healthspan?.total_points ? Math.floor(healthspan.total_points / 10).toString() : '0', icon: 'calendar' },
    { label: 'Current Streak', value: healthspan?.streak?.toString() || '0', icon: 'flame' },
    { label: 'Healthspan Points', value: healthspan?.total_points?.toLocaleString() || '0', icon: 'star' },
    { label: 'Breed Rank', value: `#${healthspan?.breed_rank || '-'}`, icon: 'trophy' },
  ];

  const healthInfo = [
    { label: 'Last Vet Visit', value: 'Not recorded', icon: 'medical' },
    { label: 'Vaccinations', value: 'Not recorded', icon: 'shield-checkmark', status: 'pending' },
    { label: 'Medications', value: 'None', icon: 'medkit' },
    { label: 'Allergies', value: 'None known', icon: 'alert-circle' },
  ];

  const settingsOptions = [
    { label: 'Edit Dog Profile', icon: 'create', color: COLORS.primary, onPress: () => {} },
    { label: 'Notifications', icon: 'notifications', color: COLORS.secondary, onPress: () => {} },
    { label: 'Premium Subscription', icon: 'diamond', color: COLORS.warning, onPress: () => router.push('/subscription') },
    { label: 'Help & Support', icon: 'help-circle', color: COLORS.textSecondary, onPress: () => {} },
    { label: 'Logout', icon: 'log-out', color: COLORS.error, onPress: handleLogout },
  ];

  return (
    <SafeAreaView style={styles.container} edges={['top']}>
      <ScrollView showsVerticalScrollIndicator={false} contentContainerStyle={styles.scrollContent}>
        {/* Header */}
        <Animated.View style={[styles.header, { opacity: fadeAnim }]}>
          <Text style={styles.title}>Profile</Text>
          <TouchableOpacity style={styles.settingsBtn}>
            <Ionicons name="settings-outline" size={24} color={COLORS.text} />
          </TouchableOpacity>
        </Animated.View>

        {/* Dog Profile Card */}
        <Animated.View style={{ opacity: fadeAnim, transform: [{ scale: scaleAnim }] }}>
          <LinearGradient
            colors={['#FF6B00', '#FF8533']}
            start={{ x: 0, y: 0 }}
            end={{ x: 1, y: 1 }}
            style={styles.profileCard}
          >
            <View style={styles.profileHeader}>
              <TouchableOpacity style={styles.avatarContainer} onPress={showPhotoOptions} disabled={uploading}>
                {currentDog.avatar_url ? (
                  <Image 
                    source={{ uri: currentDog.avatar_url }} 
                    style={styles.avatarImage}
                  />
                ) : (
                  <View style={styles.avatar}>
                    <Ionicons name="paw" size={40} color={COLORS.primary} />
                  </View>
                )}
                <View style={styles.editAvatarBtn}>
                  {uploading ? (
                    <ActivityIndicator size="small" color={COLORS.text} />
                  ) : (
                    <Ionicons name="camera" size={14} color={COLORS.text} />
                  )}
                </View>
              </TouchableOpacity>
              
              <View style={styles.profileInfo}>
                <Text style={styles.dogName}>{currentDog.name}</Text>
                <Text style={styles.breedText}>{currentDog.breed}</Text>
                <View style={styles.tagRow}>
                  {dogAge && (
                    <View style={styles.tag}>
                      <Ionicons name="calendar" size={12} color={COLORS.text} />
                      <Text style={styles.tagText}>{dogAge} years</Text>
                    </View>
                  )}
                  {currentDog.weight_lbs && (
                    <View style={styles.tag}>
                      <Ionicons name="fitness" size={12} color={COLORS.text} />
                      <Text style={styles.tagText}>{currentDog.weight_lbs} lbs</Text>
                    </View>
                  )}
                </View>
              </View>
            </View>
            
            <TouchableOpacity style={styles.editProfileBtn} onPress={showPhotoOptions}>
              <Ionicons name="camera" size={18} color={COLORS.primary} />
              <Text style={styles.editProfileText}>Change Photo</Text>
            </TouchableOpacity>
          </LinearGradient>
        </Animated.View>

        {/* User Info */}
        <Animated.View style={[styles.userInfoCard, { opacity: fadeAnim }]}>
          <View style={styles.userInfoRow}>
            <Ionicons name="person" size={20} color={COLORS.secondary} />
            <View style={styles.userInfoText}>
              <Text style={styles.userInfoLabel}>Owner</Text>
              <Text style={styles.userInfoValue}>{user?.name || 'User'}</Text>
            </View>
          </View>
          <View style={styles.userInfoRow}>
            <Ionicons name="mail" size={20} color={COLORS.secondary} />
            <View style={styles.userInfoText}>
              <Text style={styles.userInfoLabel}>Email</Text>
              <Text style={styles.userInfoValue}>{user?.email || 'Not set'}</Text>
            </View>
          </View>
        </Animated.View>

        {/* Stats Grid */}
        <Animated.View style={[styles.statsContainer, { opacity: fadeAnim, transform: [{ translateY: slideAnim }] }]}>
          <Text style={styles.sectionTitle}>Achievements</Text>
          <View style={styles.statsGrid}>
            {stats.map((stat, index) => (
              <View key={index} style={styles.statCard}>
                <View style={styles.statIconContainer}>
                  <Ionicons name={stat.icon as any} size={20} color={COLORS.primary} />
                </View>
                <Text style={styles.statValue}>{stat.value}</Text>
                <Text style={styles.statLabel}>{stat.label}</Text>
              </View>
            ))}
          </View>
        </Animated.View>

        {/* Health Information */}
        <Animated.View style={[styles.healthContainer, { opacity: fadeAnim }]}>
          <Text style={styles.sectionTitle}>Health Information</Text>
          <View style={styles.healthCard}>
            {healthInfo.map((info, index) => (
              <View 
                key={index} 
                style={[
                  styles.healthRow,
                  index !== healthInfo.length - 1 && styles.healthRowBorder
                ]}
              >
                <View style={styles.healthIcon}>
                  <Ionicons name={info.icon as any} size={20} color={COLORS.secondary} />
                </View>
                <View style={styles.healthInfo}>
                  <Text style={styles.healthLabel}>{info.label}</Text>
                  <Text style={[
                    styles.healthValue,
                    info.status === 'good' && { color: COLORS.success }
                  ]}>{info.value}</Text>
                </View>
                <Ionicons name="chevron-forward" size={20} color={COLORS.textSecondary} />
              </View>
            ))}
          </View>
        </Animated.View>

        {/* Dog Details */}
        <Animated.View style={[styles.detailsContainer, { opacity: fadeAnim }]}>
          <Text style={styles.sectionTitle}>Dog Details</Text>
          <View style={styles.detailsCard}>
            <View style={styles.detailRow}>
              <Text style={styles.detailLabel}>Birthday</Text>
              <Text style={styles.detailValue}>
                {currentDog.date_of_birth 
                  ? new Date(currentDog.date_of_birth).toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' })
                  : 'Not set'}
              </Text>
            </View>
            <View style={styles.detailRow}>
              <Text style={styles.detailLabel}>Sex</Text>
              <Text style={styles.detailValue}>{currentDog.sex ? currentDog.sex.charAt(0).toUpperCase() + currentDog.sex.slice(1) : 'Not set'}</Text>
            </View>
            <View style={styles.detailRow}>
              <Text style={styles.detailLabel}>Activity Level</Text>
              <Text style={styles.detailValue}>{currentDog.activity_level ? currentDog.activity_level.charAt(0).toUpperCase() + currentDog.activity_level.slice(1) : 'Not set'}</Text>
            </View>
          </View>
        </Animated.View>

        {/* Settings Options */}
        <Animated.View style={[styles.settingsContainer, { opacity: fadeAnim }]}>
          <Text style={styles.sectionTitle}>Settings</Text>
          <View style={styles.settingsCard}>
            {settingsOptions.map((option, index) => (
              <TouchableOpacity 
                key={index} 
                style={[
                  styles.settingsRow,
                  index !== settingsOptions.length - 1 && styles.settingsRowBorder
                ]}
                onPress={option.onPress}
              >
                <View style={[styles.settingsIcon, { backgroundColor: option.color + '15' }]}>
                  <Ionicons name={option.icon as any} size={20} color={option.color} />
                </View>
                <Text style={[styles.settingsLabel, option.label === 'Logout' && { color: COLORS.error }]}>
                  {option.label}
                </Text>
                <Ionicons name="chevron-forward" size={20} color={COLORS.textSecondary} />
              </TouchableOpacity>
            ))}
          </View>
        </Animated.View>

        {/* App Version */}
        <View style={styles.versionContainer}>
          <Text style={styles.versionText}>Canine.Fit v1.0.0</Text>
          <Text style={styles.copyrightText}>Made with love for dogs everywhere</Text>
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
  title: {
    fontSize: 32,
    fontWeight: '800',
    color: COLORS.text,
  },
  settingsBtn: {
    width: 44,
    height: 44,
    borderRadius: 22,
    backgroundColor: COLORS.card,
    justifyContent: 'center',
    alignItems: 'center',
  },
  profileCard: {
    borderRadius: 24,
    padding: 20,
    marginBottom: 16,
  },
  profileHeader: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  avatarContainer: {
    position: 'relative',
  },
  avatar: {
    width: 80,
    height: 80,
    borderRadius: 40,
    backgroundColor: 'rgba(255,255,255,0.95)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  avatarImage: {
    width: 80,
    height: 80,
    borderRadius: 40,
  },
  editAvatarBtn: {
    position: 'absolute',
    bottom: 0,
    right: 0,
    width: 28,
    height: 28,
    borderRadius: 14,
    backgroundColor: COLORS.secondary,
    justifyContent: 'center',
    alignItems: 'center',
    borderWidth: 2,
    borderColor: COLORS.primary,
  },
  profileInfo: {
    flex: 1,
    marginLeft: 16,
  },
  dogName: {
    fontSize: 26,
    fontWeight: '800',
    color: COLORS.text,
  },
  breedText: {
    fontSize: 14,
    color: 'rgba(255,255,255,0.85)',
    marginTop: 2,
  },
  tagRow: {
    flexDirection: 'row',
    marginTop: 10,
  },
  tag: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: 'rgba(255,255,255,0.2)',
    paddingHorizontal: 10,
    paddingVertical: 5,
    borderRadius: 12,
    marginRight: 8,
  },
  tagText: {
    fontSize: 12,
    fontWeight: '600',
    color: COLORS.text,
    marginLeft: 4,
  },
  editProfileBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: 'rgba(255,255,255,0.95)',
    borderRadius: 14,
    paddingVertical: 12,
    marginTop: 16,
  },
  editProfileText: {
    fontSize: 15,
    fontWeight: '700',
    color: COLORS.primary,
    marginLeft: 8,
  },
  userInfoCard: {
    backgroundColor: COLORS.card,
    borderRadius: 18,
    padding: 16,
    marginBottom: 24,
  },
  userInfoRow: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 8,
  },
  userInfoText: {
    marginLeft: 14,
  },
  userInfoLabel: {
    fontSize: 12,
    color: COLORS.textSecondary,
  },
  userInfoValue: {
    fontSize: 15,
    fontWeight: '600',
    color: COLORS.text,
    marginTop: 2,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: COLORS.text,
    marginBottom: 14,
  },
  statsContainer: {
    marginBottom: 24,
  },
  statsGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    marginHorizontal: -6,
  },
  statCard: {
    width: (width - 52) / 2,
    backgroundColor: COLORS.card,
    borderRadius: 18,
    padding: 16,
    marginHorizontal: 3,
    marginBottom: 12,
  },
  statIconContainer: {
    width: 44,
    height: 44,
    borderRadius: 14,
    backgroundColor: COLORS.primary + '15',
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 12,
  },
  statValue: {
    fontSize: 24,
    fontWeight: '800',
    color: COLORS.text,
  },
  statLabel: {
    fontSize: 12,
    color: COLORS.textSecondary,
    marginTop: 4,
  },
  healthContainer: {
    marginBottom: 24,
  },
  healthCard: {
    backgroundColor: COLORS.card,
    borderRadius: 18,
    overflow: 'hidden',
  },
  healthRow: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 16,
  },
  healthRowBorder: {
    borderBottomWidth: 1,
    borderBottomColor: COLORS.border,
  },
  healthIcon: {
    width: 40,
    height: 40,
    borderRadius: 12,
    backgroundColor: COLORS.secondary + '15',
    justifyContent: 'center',
    alignItems: 'center',
  },
  healthInfo: {
    flex: 1,
    marginLeft: 14,
  },
  healthLabel: {
    fontSize: 13,
    color: COLORS.textSecondary,
  },
  healthValue: {
    fontSize: 15,
    fontWeight: '600',
    color: COLORS.text,
    marginTop: 2,
  },
  detailsContainer: {
    marginBottom: 24,
  },
  detailsCard: {
    backgroundColor: COLORS.card,
    borderRadius: 18,
    padding: 16,
  },
  detailRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 8,
  },
  detailLabel: {
    fontSize: 14,
    color: COLORS.textSecondary,
  },
  detailValue: {
    fontSize: 14,
    fontWeight: '600',
    color: COLORS.text,
  },
  settingsContainer: {
    marginBottom: 24,
  },
  settingsCard: {
    backgroundColor: COLORS.card,
    borderRadius: 18,
    overflow: 'hidden',
  },
  settingsRow: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 16,
  },
  settingsRowBorder: {
    borderBottomWidth: 1,
    borderBottomColor: COLORS.border,
  },
  settingsIcon: {
    width: 40,
    height: 40,
    borderRadius: 12,
    justifyContent: 'center',
    alignItems: 'center',
  },
  settingsLabel: {
    flex: 1,
    fontSize: 15,
    fontWeight: '500',
    color: COLORS.text,
    marginLeft: 14,
  },
  versionContainer: {
    alignItems: 'center',
    paddingVertical: 20,
  },
  versionText: {
    fontSize: 13,
    color: COLORS.textSecondary,
  },
  copyrightText: {
    fontSize: 12,
    color: COLORS.textSecondary,
    marginTop: 4,
  },
});
