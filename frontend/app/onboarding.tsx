import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TextInput,
  TouchableOpacity,
  ScrollView,
  ActivityIndicator,
  Alert,
  KeyboardAvoidingView,
  Platform,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { LinearGradient } from 'expo-linear-gradient';
import { useRouter } from 'expo-router';
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
};

const DOG_BREEDS = [
  'Golden Retriever', 'Labrador Retriever', 'German Shepherd', 'French Bulldog',
  'Bulldog', 'Poodle', 'Beagle', 'Rottweiler', 'Yorkshire Terrier', 'Boxer',
  'Dachshund', 'Siberian Husky', 'Great Dane', 'Border Collie', 'Australian Shepherd',
  'Mixed Breed', 'Other',
];

export default function OnboardingScreen() {
  const router = useRouter();
  const { addDog, refreshDogs } = useAuth();
  const [step, setStep] = useState(1);
  const [isLoading, setIsLoading] = useState(false);
  
  const [dogName, setDogName] = useState('');
  const [selectedBreed, setSelectedBreed] = useState('');
  const [weight, setWeight] = useState('');
  const [birthYear, setBirthYear] = useState('');
  const [sex, setSex] = useState<'male' | 'female' | ''>('');
  const [activityLevel, setActivityLevel] = useState<'low' | 'medium' | 'high' | ''>('');

  const handleNext = () => {
    if (step === 1 && !dogName.trim()) {
      Alert.alert('Error', 'Please enter your dog\'s name');
      return;
    }
    if (step === 2 && !selectedBreed) {
      Alert.alert('Error', 'Please select a breed');
      return;
    }
    setStep(step + 1);
  };

  const handleFinish = async () => {
    setIsLoading(true);
    try {
      const birthDate = birthYear ? `${birthYear}-01-01` : undefined;
      await addDog({
        name: dogName.trim(),
        breed: selectedBreed,
        weight_lbs: weight ? parseFloat(weight) : undefined,
        date_of_birth: birthDate,
        sex: sex || undefined,
        activity_level: activityLevel || undefined,
      });
      await refreshDogs();
      router.replace('/(tabs)');
    } catch (error: any) {
      Alert.alert('Error', error.message || 'Failed to create dog profile');
    } finally {
      setIsLoading(false);
    }
  };

  const renderStep1 = () => (
    <View style={styles.stepContent}>
      <Text style={styles.stepTitle}>What's your dog's name?</Text>
      <Text style={styles.stepSubtitle}>Let's get to know your furry friend</Text>
      
      <View style={styles.inputContainer}>
        <Ionicons name="paw" size={24} color={COLORS.primary} style={styles.inputIcon} />
        <TextInput
          style={styles.input}
          placeholder="e.g., Max, Bella, Charlie"
          placeholderTextColor={COLORS.textSecondary}
          value={dogName}
          onChangeText={setDogName}
          autoCapitalize="words"
          autoFocus
        />
      </View>
    </View>
  );

  const renderStep2 = () => (
    <View style={styles.stepContent}>
      <Text style={styles.stepTitle}>What breed is {dogName}?</Text>
      <Text style={styles.stepSubtitle}>This helps us provide breed-specific insights</Text>
      
      <ScrollView style={styles.breedList} showsVerticalScrollIndicator={false}>
        {DOG_BREEDS.map((breed) => (
          <TouchableOpacity
            key={breed}
            style={[
              styles.breedItem,
              selectedBreed === breed && styles.breedItemSelected,
            ]}
            onPress={() => setSelectedBreed(breed)}
          >
            <Text style={[
              styles.breedText,
              selectedBreed === breed && styles.breedTextSelected,
            ]}>
              {breed}
            </Text>
            {selectedBreed === breed && (
              <Ionicons name="checkmark-circle" size={24} color={COLORS.primary} />
            )}
          </TouchableOpacity>
        ))}
      </ScrollView>
    </View>
  );

  const renderStep3 = () => (
    <View style={styles.stepContent}>
      <Text style={styles.stepTitle}>Tell us more about {dogName}</Text>
      <Text style={styles.stepSubtitle}>Optional details for better tracking</Text>
      
      <View style={styles.optionalFields}>
        {/* Weight */}
        <View style={styles.fieldGroup}>
          <Text style={styles.fieldLabel}>Weight (lbs)</Text>
          <View style={styles.inputContainer}>
            <TextInput
              style={styles.input}
              placeholder="e.g., 65"
              placeholderTextColor={COLORS.textSecondary}
              value={weight}
              onChangeText={setWeight}
              keyboardType="numeric"
            />
          </View>
        </View>

        {/* Birth Year */}
        <View style={styles.fieldGroup}>
          <Text style={styles.fieldLabel}>Birth Year</Text>
          <View style={styles.inputContainer}>
            <TextInput
              style={styles.input}
              placeholder="e.g., 2022"
              placeholderTextColor={COLORS.textSecondary}
              value={birthYear}
              onChangeText={setBirthYear}
              keyboardType="numeric"
              maxLength={4}
            />
          </View>
        </View>

        {/* Sex */}
        <View style={styles.fieldGroup}>
          <Text style={styles.fieldLabel}>Sex</Text>
          <View style={styles.toggleRow}>
            <TouchableOpacity
              style={[styles.toggleBtn, sex === 'male' && styles.toggleBtnActive]}
              onPress={() => setSex('male')}
            >
              <Ionicons name="male" size={20} color={sex === 'male' ? COLORS.text : COLORS.textSecondary} />
              <Text style={[styles.toggleText, sex === 'male' && styles.toggleTextActive]}>Male</Text>
            </TouchableOpacity>
            <TouchableOpacity
              style={[styles.toggleBtn, sex === 'female' && styles.toggleBtnActive]}
              onPress={() => setSex('female')}
            >
              <Ionicons name="female" size={20} color={sex === 'female' ? COLORS.text : COLORS.textSecondary} />
              <Text style={[styles.toggleText, sex === 'female' && styles.toggleTextActive]}>Female</Text>
            </TouchableOpacity>
          </View>
        </View>

        {/* Activity Level */}
        <View style={styles.fieldGroup}>
          <Text style={styles.fieldLabel}>Activity Level</Text>
          <View style={styles.toggleRow}>
            {(['low', 'medium', 'high'] as const).map((level) => (
              <TouchableOpacity
                key={level}
                style={[styles.toggleBtn, styles.toggleBtnSmall, activityLevel === level && styles.toggleBtnActive]}
                onPress={() => setActivityLevel(level)}
              >
                <Text style={[styles.toggleText, activityLevel === level && styles.toggleTextActive]}>
                  {level.charAt(0).toUpperCase() + level.slice(1)}
                </Text>
              </TouchableOpacity>
            ))}
          </View>
        </View>
      </View>
    </View>
  );

  return (
    <SafeAreaView style={styles.container}>
      <KeyboardAvoidingView
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
        style={styles.keyboardView}
      >
        {/* Progress Bar */}
        <View style={styles.progressContainer}>
          <View style={styles.progressBar}>
            <View style={[styles.progressFill, { width: `${(step / 3) * 100}%` }]} />
          </View>
          <Text style={styles.progressText}>Step {step} of 3</Text>
        </View>

        {/* Content */}
        <View style={styles.content}>
          {step === 1 && renderStep1()}
          {step === 2 && renderStep2()}
          {step === 3 && renderStep3()}
        </View>

        {/* Navigation */}
        <View style={styles.navigation}>
          {step > 1 && (
            <TouchableOpacity
              style={styles.backBtn}
              onPress={() => setStep(step - 1)}
            >
              <Ionicons name="arrow-back" size={24} color={COLORS.text} />
            </TouchableOpacity>
          )}
          
          <TouchableOpacity
            style={styles.nextBtn}
            onPress={step === 3 ? handleFinish : handleNext}
            disabled={isLoading}
            activeOpacity={0.8}
          >
            <LinearGradient
              colors={[COLORS.primary, '#FF8533']}
              start={{ x: 0, y: 0 }}
              end={{ x: 1, y: 0 }}
              style={styles.nextGradient}
            >
              {isLoading ? (
                <ActivityIndicator color={COLORS.text} />
              ) : (
                <>
                  <Text style={styles.nextText}>
                    {step === 3 ? 'Get Started' : 'Continue'}
                  </Text>
                  <Ionicons name="arrow-forward" size={20} color={COLORS.text} />
                </>
              )}
            </LinearGradient>
          </TouchableOpacity>
        </View>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: COLORS.background,
  },
  keyboardView: {
    flex: 1,
  },
  progressContainer: {
    paddingHorizontal: 24,
    paddingTop: 20,
  },
  progressBar: {
    height: 6,
    backgroundColor: COLORS.card,
    borderRadius: 3,
    overflow: 'hidden',
  },
  progressFill: {
    height: '100%',
    backgroundColor: COLORS.primary,
    borderRadius: 3,
  },
  progressText: {
    fontSize: 13,
    color: COLORS.textSecondary,
    marginTop: 8,
  },
  content: {
    flex: 1,
    paddingHorizontal: 24,
    paddingTop: 40,
  },
  stepContent: {
    flex: 1,
  },
  stepTitle: {
    fontSize: 28,
    fontWeight: '700',
    color: COLORS.text,
    marginBottom: 8,
  },
  stepSubtitle: {
    fontSize: 15,
    color: COLORS.textSecondary,
    marginBottom: 32,
  },
  inputContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: COLORS.card,
    borderRadius: 16,
    paddingHorizontal: 16,
    borderWidth: 1,
    borderColor: COLORS.border,
  },
  inputIcon: {
    marginRight: 12,
  },
  input: {
    flex: 1,
    height: 56,
    fontSize: 16,
    color: COLORS.text,
  },
  breedList: {
    flex: 1,
  },
  breedItem: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    backgroundColor: COLORS.card,
    borderRadius: 12,
    padding: 16,
    marginBottom: 8,
    borderWidth: 2,
    borderColor: 'transparent',
  },
  breedItemSelected: {
    borderColor: COLORS.primary,
    backgroundColor: COLORS.primary + '10',
  },
  breedText: {
    fontSize: 16,
    color: COLORS.text,
  },
  breedTextSelected: {
    fontWeight: '600',
    color: COLORS.primary,
  },
  optionalFields: {
    gap: 24,
  },
  fieldGroup: {
    gap: 8,
  },
  fieldLabel: {
    fontSize: 14,
    fontWeight: '600',
    color: COLORS.textSecondary,
  },
  toggleRow: {
    flexDirection: 'row',
    gap: 12,
  },
  toggleBtn: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    backgroundColor: COLORS.card,
    borderRadius: 12,
    paddingVertical: 14,
    borderWidth: 2,
    borderColor: 'transparent',
  },
  toggleBtnSmall: {
    paddingVertical: 12,
  },
  toggleBtnActive: {
    borderColor: COLORS.primary,
    backgroundColor: COLORS.primary + '15',
  },
  toggleText: {
    fontSize: 15,
    color: COLORS.textSecondary,
  },
  toggleTextActive: {
    color: COLORS.text,
    fontWeight: '600',
  },
  navigation: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 24,
    paddingVertical: 20,
    gap: 12,
  },
  backBtn: {
    width: 56,
    height: 56,
    borderRadius: 16,
    backgroundColor: COLORS.card,
    justifyContent: 'center',
    alignItems: 'center',
  },
  nextBtn: {
    flex: 1,
    borderRadius: 16,
    overflow: 'hidden',
  },
  nextGradient: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 18,
    gap: 8,
  },
  nextText: {
    fontSize: 17,
    fontWeight: '700',
    color: COLORS.text,
  },
});
