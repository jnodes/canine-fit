import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import AsyncStorage from '@react-native-async-storage/async-storage';
import api from '../services/api';
import { supabase, getUserProfile, DogProfile } from '../services/supabase';

// Use Supabase User type
interface User {
  id: string;
  email: string;
  name: string;
  is_premium?: boolean;
  subscription_status?: string;
  subscription_plan?: string;
  subscription_expires?: string;
}

interface Dog {
  id: string;
  name: string;
  breed: string;
  avatar_url?: string;
  date_of_birth?: string;
  weight_lbs?: number;
  sex?: string;
  activity_level?: string;
  owner_id: string;
}

interface AuthContextType {
  user: User | null;
  dogs: Dog[];
  currentDog: Dog | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  login: (email: string, password: string) => Promise<void>;
  signup: (email: string, password: string, name: string) => Promise<void>;
  logout: () => Promise<void>;
  refreshDogs: () => Promise<void>;
  setCurrentDog: (dog: Dog) => void;
  addDog: (dogData: Omit<Dog, 'id' | 'owner_id'>) => Promise<Dog>;
  supabaseUser: any; // Supabase auth user
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [dogs, setDogs] = useState<Dog[]>([]);
  const [currentDog, setCurrentDog] = useState<Dog | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [supabaseUser, setSupabaseUser] = useState<any>(null);

  // Listen for Supabase auth changes
  useEffect(() => {
    // Check for existing Supabase session
    supabase.auth.getSession().then(({ data: { session } }: any) => {
      if (session) {
        setSupabaseUser(session.user);
        loadUserData(session.user.id);
      } else {
        // Fallback to stored backend auth
        loadStoredAuth();
      }
    });

    // Listen for auth changes
    const { data: { subscription } } = supabase.auth.onAuthStateChange(
      async (event: string, session: any) => {
        if (event === 'SIGNED_IN' && session) {
          setSupabaseUser(session.user);
          await loadUserData(session.user.id);
        } else if (event === 'SIGNED_OUT') {
          setSupabaseUser(null);
          setUser(null);
          setDogs([]);
          setCurrentDog(null);
        }
      }
    );

    return () => subscription.unsubscribe();
  }, []);

  const loadUserData = async (userId: string) => {
    try {
      // Get user profile from Supabase
      const profile = await getUserProfile();
      if (profile) {
        setUser({
          id: profile.id,
          email: profile.email,
          name: profile.name,
          is_premium: profile.is_premium,
          subscription_status: profile.subscription_status ?? undefined,
          subscription_plan: profile.subscription_plan ?? undefined,
          subscription_expires: profile.subscription_expires ?? undefined,
        });
        await AsyncStorage.setItem('user', JSON.stringify(profile));
      }
      
      // Also sync with backend API
      await api.init();
      await refreshDogs();
      
      // Load stored dog selection
      const storedDog = await AsyncStorage.getItem('current_dog');
      if (storedDog) {
        setCurrentDog(JSON.parse(storedDog));
      }
    } catch (error) {
      console.error('Failed to load user data:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const loadStoredAuth = async () => {
    try {
      await api.init();
      const storedUser = await AsyncStorage.getItem('user');
      const storedDog = await AsyncStorage.getItem('current_dog');
      
      if (storedUser && api.getToken()) {
        setUser(JSON.parse(storedUser));
        await refreshDogs();
        if (storedDog) {
          setCurrentDog(JSON.parse(storedDog));
        }
      } else {
        setIsLoading(false);
      }
    } catch (error) {
      console.error('Failed to load auth:', error);
      setIsLoading(false);
    }
  };

  const login = async (email: string, password: string) => {
    // Try Supabase Auth first
    try {
      const { data, error } = await supabase.auth.signInWithPassword({
        email,
        password,
      });
      
      if (error) throw error;
      
      // Sync with backend if needed
      await api.login(email, password);
      await loadUserData(data.user.id);
    } catch (supabaseError: any) {
      // Fallback to backend-only auth
      const data = await api.login(email, password);
      setUser(data.user);
      await AsyncStorage.setItem('user', JSON.stringify(data.user));
      await refreshDogs();
    }
  };

  const signup = async (email: string, password: string, name: string) => {
    // Use Supabase Auth
    const { data, error } = await supabase.auth.signUp({
      email,
      password,
      options: {
        data: { name },
      },
    });
    
    if (error) throw error;
    
    if (data.user) {
      setSupabaseUser(data.user);
      await loadUserData(data.user.id);
    }
    
    // Also create backend account
    try {
      const backendData = await api.signup(email, password, name);
      setUser(backendData.user);
    } catch (backendError) {
      console.log('Backend signup failed (may already exist):', backendError);
    }
  };

  const logout = async () => {
    try {
      await supabase.auth.signOut();
    } catch (e) {
      console.log('Supabase logout failed:', e);
    }
    
    try {
      await api.logout();
    } finally {
      setUser(null);
      setDogs([]);
      setCurrentDog(null);
      setSupabaseUser(null);
      await AsyncStorage.multiRemove(['user', 'current_dog', 'auth_token']);
    }
  };

  const refreshDogs = async () => {
    try {
      const dogsData = await api.getDogs();
      setDogs(dogsData);
      
      // Auto-select first dog if none selected
      if (dogsData.length > 0 && !currentDog) {
        const firstDog = dogsData[0];
        setCurrentDog(firstDog);
        await AsyncStorage.setItem('current_dog', JSON.stringify(firstDog));
      }
    } catch (error) {
      console.error('Failed to refresh dogs:', error);
    }
  };

  const handleSetCurrentDog = async (dog: Dog) => {
    setCurrentDog(dog);
    await AsyncStorage.setItem('current_dog', JSON.stringify(dog));
  };

  const addDog = async (dogData: Omit<Dog, 'id' | 'owner_id'>) => {
    const newDog = await api.createDog(dogData);
    setDogs(prev => [...prev, newDog]);
    if (!currentDog) {
      handleSetCurrentDog(newDog);
    }
    return newDog;
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        dogs,
        currentDog,
        isLoading,
        isAuthenticated: !!user || !!supabaseUser,
        login,
        signup,
        logout,
        refreshDogs,
        setCurrentDog: handleSetCurrentDog,
        addDog,
        supabaseUser,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}

export function usePremium() {
  const { user } = useAuth();
  return {
    isPremium: user?.is_premium ?? false,
    isFree: !user?.is_premium,
    canAccessPremium: user?.is_premium ?? false,
  };
}

export function isPremiumError(error: any): boolean {
  if (!error) return false;
  const detail = error?.response?.data?.detail;
  if (typeof detail === 'object') {
    return detail?.error === 'premium_required' || detail?.error === 'dog_limit_reached';
  }
  return error?.response?.data?.detail === 'premium_required';
}
