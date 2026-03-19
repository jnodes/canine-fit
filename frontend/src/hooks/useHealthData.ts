import { useState, useEffect, useCallback } from 'react';
import api from '../services/api';
import { useAuth } from '../context/AuthContext';

interface HealthspanData {
  score: number;
  streak: number;
  total_points: number;
  breed_rank: number;
  weekly_scores: { date: string; score: number }[];
}

interface LiloReport {
  id: string;
  dog_id: string;
  report_date: string;
  mood: string;
  summary: string;
  insights: string[];
  recommendation: string;
  healthspan_delta?: number;
}

export function useHealthspan() {
  const { currentDog } = useAuth();
  const [healthspan, setHealthspan] = useState<HealthspanData | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchHealthspan = useCallback(async () => {
    if (!currentDog) return;
    
    setIsLoading(true);
    setError(null);
    
    try {
      const data = await api.getHealthspan(currentDog.id);
      setHealthspan(data);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setIsLoading(false);
    }
  }, [currentDog]);

  useEffect(() => {
    fetchHealthspan();
  }, [fetchHealthspan]);

  return { healthspan, isLoading, error, refresh: fetchHealthspan };
}

export function useLiloReports() {
  const { currentDog } = useAuth();
  const [reports, setReports] = useState<LiloReport[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchReports = useCallback(async () => {
    if (!currentDog) return;
    
    setIsLoading(true);
    setError(null);
    
    try {
      const data = await api.getLiloReports(currentDog.id);
      setReports(data);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setIsLoading(false);
    }
  }, [currentDog]);

  const generateReport = useCallback(async () => {
    if (!currentDog) return null;
    
    setIsLoading(true);
    try {
      const newReport = await api.generateLiloReport(currentDog.id);
      setReports(prev => [newReport, ...prev]);
      return newReport;
    } catch (e: any) {
      setError(e.message);
      return null;
    } finally {
      setIsLoading(false);
    }
  }, [currentDog]);

  useEffect(() => {
    fetchReports();
  }, [fetchReports]);

  return { reports, isLoading, error, refresh: fetchReports, generateReport };
}

export function useDailyLog() {
  const { currentDog } = useAuth();
  const [todayLog, setTodayLog] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchTodayLog = useCallback(async () => {
    if (!currentDog) return;
    
    setIsLoading(true);
    setError(null);
    
    try {
      const data = await api.getTodayLog(currentDog.id);
      setTodayLog(data);
    } catch (e: any) {
      // No log for today is not an error
      setTodayLog(null);
    } finally {
      setIsLoading(false);
    }
  }, [currentDog]);

  const submitLog = useCallback(async (logData: {
    mood: string;
    exercise_level: string;
    nutrition_quality: string;
    notes?: string;
  }) => {
    if (!currentDog) return null;
    
    setIsLoading(true);
    setError(null);
    
    try {
      const newLog = await api.createDailyLog({
        dog_id: currentDog.id,
        ...logData,
      });
      setTodayLog(newLog);
      return newLog;
    } catch (e: any) {
      setError(e.message);
      throw e;
    } finally {
      setIsLoading(false);
    }
  }, [currentDog]);

  useEffect(() => {
    fetchTodayLog();
  }, [fetchTodayLog]);

  return { todayLog, isLoading, error, refresh: fetchTodayLog, submitLog };
}
