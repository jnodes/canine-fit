import AsyncStorage from '@react-native-async-storage/async-storage';

const API_BASE_URL = process.env.EXPO_PUBLIC_BACKEND_URL || '';

class ApiService {
  private token: string | null = null;

  async init() {
    try {
      this.token = await AsyncStorage.getItem('auth_token');
    } catch (e) {
      // Silent fail in production
    }
  }

  setToken(token: string | null) {
    this.token = token;
    if (token) {
      AsyncStorage.setItem('auth_token', token).catch(() => {});
    } else {
      AsyncStorage.removeItem('auth_token').catch(() => {});
    }
  }

  getToken() {
    return this.token;
  }

  private async request(endpoint: string, options: RequestInit = {}) {
    const url = `${API_BASE_URL}/api/v1${endpoint}`;
    
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      ...(options.headers as Record<string, string> || {}),
    };

    if (this.token) {
      headers['Authorization'] = `Bearer ${this.token}`;
    }

    try {
      const response = await fetch(url, {
        ...options,
        headers,
      });

      if (!response.ok) {
        const error = await response.json().catch(() => ({ detail: 'Request failed' }));
        throw new Error(error.detail || `HTTP error ${response.status}`);
      }

      return response.json();
    } catch (error) {
      console.error(`API Error [${endpoint}]:`, error);
      throw error;
    }
  }

  // Auth
  async signup(email: string, password: string, name: string) {
    const data = await this.request('/auth/signup', {
      method: 'POST',
      body: JSON.stringify({ email, password, name }),
    });
    this.setToken(data.access_token);
    return data;
  }

  async login(email: string, password: string) {
    const data = await this.request('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    });
    this.setToken(data.access_token);
    return data;
  }

  async logout() {
    try {
      await this.request('/auth/logout', { method: 'POST' });
    } finally {
      this.setToken(null);
    }
  }

  // Dogs
  async getDogs() {
    return this.request('/dogs');
  }

  async createDog(dogData: {
    name: string;
    breed: string;
    date_of_birth?: string;
    weight_lbs?: number;
    sex?: string;
    activity_level?: string;
  }) {
    return this.request('/dogs', {
      method: 'POST',
      body: JSON.stringify(dogData),
    });
  }

  async updateDog(dogId: string, dogData: Partial<{
    name: string;
    breed: string;
    avatar_url: string;
    date_of_birth: string;
    weight_lbs: number;
    sex: string;
    activity_level: string;
  }>) {
    return this.request(`/dogs/${dogId}`, {
      method: 'PUT',
      body: JSON.stringify(dogData),
    });
  }

  async uploadDogPhoto(dogId: string, imageBase64: string) {
    return this.request(`/dogs/${dogId}/photo`, {
      method: 'POST',
      body: JSON.stringify({ image_base64: imageBase64 }),
    });
  }

  async deleteDog(dogId: string) {
    return this.request(`/dogs/${dogId}`, { method: 'DELETE' });
  }

  // Daily Logs
  async getDailyLogs(dogId: string) {
    return this.request(`/daily-logs/${dogId}`);
  }

  async getTodayLog(dogId: string) {
    return this.request(`/daily-logs/${dogId}/today`);
  }

  async createDailyLog(logData: {
    dog_id: string;
    mood: string;
    exercise_level: string;
    nutrition_quality: string;
    notes?: string;
  }) {
    return this.request('/daily-logs', {
      method: 'POST',
      body: JSON.stringify(logData),
    });
  }

  // Healthspan
  async getHealthspan(dogId: string) {
    return this.request(`/healthspan/${dogId}`);
  }

  // Lilo AI
  async getLiloReports(dogId: string) {
    return this.request(`/lilo-ai/${dogId}`);
  }

  async generateLiloReport(dogId: string) {
    return this.request(`/lilo-ai/${dogId}`, { method: 'POST' });
  }

  // Dog Breeds
  async getDogBreeds() {
    return this.request('/dog-breeds');
  }

  // Food Safety
  async searchFood(query: string) {
    return this.request(`/food-search?query=${encodeURIComponent(query)}`);
  }

  // Subscription
  async getSubscriptionPlans() {
    return this.request('/subscription/plans');
  }

  async createCheckoutSession(planId: string, originUrl: string) {
    return this.request('/subscription/checkout', {
      method: 'POST',
      body: JSON.stringify({ plan_id: planId, origin_url: originUrl }),
    });
  }

  async getCheckoutStatus(sessionId: string) {
    return this.request(`/subscription/status/${sessionId}`);
  }

  async getCurrentSubscription() {
    return this.request('/subscription/current');
  }

  async getMe() {
    return this.request('/auth/me');
  }

  // Leaderboard (Premium)
  async getGlobalLeaderboard() {
    return this.request('/leaderboard');
  }

  async getBreedLeaderboard(breed: string) {
    return this.request(`/leaderboard/${encodeURIComponent(breed)}`);
  }

  // Weather (Free - value-add feature)
  async getWeather(lat: number, lon: number) {
    return this.request(`/weather/current?lat=${lat}&lon=${lon}`);
  }

  async getWeatherForecast(lat: number, lon: number, hours: number = 24) {
    return this.request(`/weather/forecast?lat=${lat}&lon=${lon}&hours=${hours}`);
  }

  // Breeds (Free)
  async searchBreeds(query: string, limit: number = 10) {
    return this.request(`/breeds/search?q=${encodeURIComponent(query)}&limit=${limit}`);
  }

  async getBreedInsights(breedId: string) {
    return this.request(`/breeds/${encodeURIComponent(breedId)}/insights`);
  }

  // Foods (Premium)
  async searchFoods(query: string, limit: number = 10) {
    return this.request(`/foods/search?query=${encodeURIComponent(query)}&limit=${limit}`);
  }

  async getFoodDetails(fdcId: string) {
    return this.request(`/foods/${fdcId}`);
  }

  // Air Quality (Premium)
  async getAirQuality(zipCode: string) {
    return this.request(`/air-quality?zip_code=${zipCode}`);
  }

  // Healthspan Calculation
  async calculateHealthspan(
    activityScore: number,
    nutritionScore: number,
    environmentalScore: number,
    breedBaseline: number = 85.0
  ) {
    return this.request('/healthspan/calculate', {
      method: 'POST',
      body: JSON.stringify({
        activity_score: activityScore,
        nutrition_score: nutritionScore,
        environmental_score: environmentalScore,
        breed_baseline: breedBaseline
      })
    });
  }
}

export const api = new ApiService();
export default api;
