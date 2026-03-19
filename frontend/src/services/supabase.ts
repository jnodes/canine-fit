/**
 * Supabase Client for Canine.Fit
 * Handles authentication and real-time database subscriptions
 */

import { createClient, SupabaseClient, RealtimeChannel } from '@supabase/supabase-js';

// Supabase configuration
const SUPABASE_URL = process.env.EXPO_PUBLIC_SUPABASE_URL || 'https://your-project.supabase.co';
const SUPABASE_ANON_KEY = process.env.EXPO_PUBLIC_SUPABASE_ANON_KEY || 'your-anon-key';

// Create Supabase client
export const supabase: SupabaseClient = createClient(SUPABASE_URL, SUPABASE_ANON_KEY, {
  auth: {
    persistSession: true,
    autoRefreshToken: true,
    detectSessionInUrl: false,
  },
  realtime: {
    params: {
      eventsPerSecond: 10,
    },
  },
});

// Types for our database tables
export interface DogProfile {
  id: string;
  owner_id: string;
  name: string;
  breed: string;
  date_of_birth: string | null;
  weight_lbs: number | null;
  sex: string | null;
  activity_level: string | null;
  avatar_url: string | null;
  healthspan_score: number;
  created_at: string;
  updated_at: string;
}

export interface DailyLog {
  id: string;
  dog_id: string;
  date: string;
  mood: string;
  energy_level: number;
  appetite: number;
  sleep_quality: number;
  exercise_level: number;
  nutrition_quality: number;
  water_intake: number;
  notes: string | null;
  logged_at: string;
}

export interface UserProfile {
  id: string;
  email: string;
  name: string;
  is_premium: boolean;
  subscription_status: string | null;
  subscription_plan: string | null;
  subscription_expires: string | null;
  created_at: string;
}

export interface HealthspanStats {
  id: string;
  dog_id: string;
  current_score: number;
  total_points: number;
  streak: number;
  last_activity_date: string;
  calculated_at: string;
}

// Auth functions
export async function signUp(email: string, password: string, name: string) {
  const { data, error } = await supabase.auth.signUp({
    email,
    password,
    options: {
      data: {
        name,
      },
    },
  });
  
  if (error) throw error;
  return data;
}

export async function signIn(email: string, password: string) {
  const { data, error } = await supabase.auth.signInWithPassword({
    email,
    password,
  });
  
  if (error) throw error;
  return data;
}

export async function signOut() {
  const { error } = await supabase.auth.signOut();
  if (error) throw error;
}

export async function getCurrentUser() {
  const { data: { user }, error } = await supabase.auth.getUser();
  if (error) throw error;
  return user;
}

export async function resetPassword(email: string) {
  const { error } = await supabase.auth.resetPasswordForEmail(email);
  if (error) throw error;
}

export async function updatePassword(newPassword: string) {
  const { error } = await supabase.auth.updateUser({
    password: newPassword,
  });
  if (error) throw error;
}

// Dog profile functions
export async function getDogs() {
  const { data, error } = await supabase
    .from('dogs')
    .select('*')
    .order('created_at', { ascending: false });
  
  if (error) throw error;
  return data as DogProfile[];
}

export async function getDog(dogId: string) {
  const { data, error } = await supabase
    .from('dogs')
    .select('*')
    .eq('id', dogId)
    .single();
  
  if (error) throw error;
  return data as DogProfile;
}

export async function createDog(dog: Partial<DogProfile>) {
  const { data, error } = await supabase
    .from('dogs')
    .insert(dog)
    .select()
    .single();
  
  if (error) throw error;
  return data as DogProfile;
}

export async function updateDog(dogId: string, updates: Partial<DogProfile>) {
  const { data, error } = await supabase
    .from('dogs')
    .update({ ...updates, updated_at: new Date().toISOString() })
    .eq('id', dogId)
    .select()
    .single();
  
  if (error) throw error;
  return data as DogProfile;
}

export async function deleteDog(dogId: string) {
  const { error } = await supabase
    .from('dogs')
    .delete()
    .eq('id', dogId);
  
  if (error) throw error;
}

// Daily log functions
export async function getDailyLogs(dogId: string, days: number = 30) {
  const startDate = new Date();
  startDate.setDate(startDate.getDate() - days);
  
  const { data, error } = await supabase
    .from('daily_logs')
    .select('*')
    .eq('dog_id', dogId)
    .gte('date', startDate.toISOString().split('T')[0])
    .order('date', { ascending: false });
  
  if (error) throw error;
  return data as DailyLog[];
}

export async function getTodayLog(dogId: string) {
  const today = new Date().toISOString().split('T')[0];
  
  const { data, error } = await supabase
    .from('daily_logs')
    .select('*')
    .eq('dog_id', dogId)
    .eq('date', today)
    .single();
  
  if (error && error.code !== 'PGRST116') throw error; // Ignore "no rows" error
  return data as DailyLog | null;
}

export async function createDailyLog(log: Partial<DailyLog>) {
  const { data, error } = await supabase
    .from('daily_logs')
    .insert(log)
    .select()
    .single();
  
  if (error) throw error;
  return data as DailyLog;
}

export async function updateDailyLog(logId: string, updates: Partial<DailyLog>) {
  const { data, error } = await supabase
    .from('daily_logs')
    .update(updates)
    .eq('id', logId)
    .select()
    .single();
  
  if (error) throw error;
  return data as DailyLog;
}

// Healthspan stats functions
export async function getHealthspanStats(dogId: string) {
  const { data, error } = await supabase
    .from('healthspan_stats')
    .select('*')
    .eq('dog_id', dogId)
    .single();
  
  if (error && error.code !== 'PGRST116') throw error;
  return data as HealthspanStats | null;
}

// Real-time subscriptions
export function subscribeToDogUpdates(
  dogId: string,
  callback: (payload: any) => void
): RealtimeChannel {
  return supabase
    .channel(`dog:${dogId}`)
    .on(
      'postgres_changes',
      {
        event: '*',
        schema: 'public',
        table: 'dogs',
        filter: `id=eq.${dogId}`,
      },
      callback
    )
    .subscribe();
}

export function subscribeToDailyLogs(
  dogId: string,
  callback: (payload: any) => void
): RealtimeChannel {
  return supabase
    .channel(`logs:${dogId}`)
    .on(
      'postgres_changes',
      {
        event: '*',
        schema: 'public',
        table: 'daily_logs',
        filter: `dog_id=eq.${dogId}`,
      },
      callback
    )
    .subscribe();
}

export function subscribeToHealthspan(
  dogId: string,
  callback: (payload: any) => void
): RealtimeChannel {
  return supabase
    .channel(`healthspan:${dogId}`)
    .on(
      'postgres_changes',
      {
        event: 'UPDATE',
        schema: 'public',
        table: 'healthspan_stats',
        filter: `dog_id=eq.${dogId}`,
      },
      callback
    )
    .subscribe();
}

// User profile functions
export async function getUserProfile() {
  const { data: { user }, error: authError } = await supabase.auth.getUser();
  if (authError) throw authError;
  if (!user) return null;
  
  const { data, error } = await supabase
    .from('user_profiles')
    .select('*')
    .eq('id', user.id)
    .single();
  
  if (error && error.code !== 'PGRST116') throw error;
  return data as UserProfile | null;
}

export async function updateUserProfile(updates: Partial<UserProfile>) {
  const { data: { user }, error: authError } = await supabase.auth.getUser();
  if (authError) throw authError;
  if (!user) throw new Error('Not authenticated');
  
  const { data, error } = await supabase
    .from('user_profiles')
    .update(updates)
    .eq('id', user.id)
    .select()
    .single();
  
  if (error) throw error;
  return data as UserProfile;
}

// Export supabase client for direct access if needed
export default supabase;
