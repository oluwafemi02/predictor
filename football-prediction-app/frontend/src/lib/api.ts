import axios from 'axios';
import type { AxiosError, AxiosRequestConfig } from 'axios';

// Get API base URL from environment variable or use relative URLs
// In production, if no env var is set, use relative URLs (same domain)
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 
  (import.meta.env.PROD ? '' : 'http://localhost:5000');

// Create axios instance with defaults
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor for auth tokens if needed
apiClient.interceptors.request.use(
  (config) => {
    // Add auth token if available
    const token = localStorage.getItem('auth_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor for error handling
apiClient.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config as AxiosRequestConfig & { _retry?: boolean };
    
    // Retry on 5xx errors
    if (error.response?.status && error.response.status >= 500 && !originalRequest._retry) {
      originalRequest._retry = true;
      await new Promise(resolve => setTimeout(resolve, 1000)); // Wait 1 second
      return apiClient(originalRequest);
    }
    
    // Transform error to consistent format
    const message = (error.response?.data as any)?.message || error.message || 'An error occurred';
    const status = error.response?.status || 500;
    
    return Promise.reject({
      message,
      status,
      data: error.response?.data,
    });
  }
);

// API types
export interface Team {
  id: number;
  name: string;
  code?: string;
  logo_url?: string;
  stadium?: string;
  founded?: number;
}

export interface Match {
  id: number;
  home_team: Team;
  away_team: Team;
  match_date: string;
  venue?: string;
  competition?: string;
  season?: string;
  round?: string;
  home_score?: number;
  away_score?: number;
  home_score_halftime?: number;
  away_score_halftime?: number;
  status?: string;
  referee?: string;
  attendance?: number;
}

export interface Prediction {
  id: number;
  match_id: number;
  match?: Match;
  prediction_type: string;
  predicted_outcome?: string;
  home_win_probability?: number;
  draw_probability?: number;
  away_win_probability?: number;
  confidence?: number;
  created_at: string;
}

export interface Player {
  id: number;
  name: string;
  position?: string;
  jersey_number?: number;
  age?: number;
  nationality?: string;
  photo_url?: string;
  team_id: number;
}

export interface PaginatedResponse<T> {
  data: T[];
  page: number;
  page_size: number;
  total: number;
  total_pages: number;
}

// API endpoints
export const api = {
  // Fixtures
  async getFixtures(params?: {
    date_from?: string;
    date_to?: string;
    page?: number;
    page_size?: number;
    league_id?: number;
  }): Promise<PaginatedResponse<Match>> {
    const response = await apiClient.get('/api/v1/fixtures', { params });
    return response.data;
  },

  // Predictions
  async getPredictions(params?: {
    date_from?: string;
    date_to?: string;
    page?: number;
    page_size?: number;
  }): Promise<PaginatedResponse<Prediction>> {
    const response = await apiClient.get('/api/v1/predictions', { params });
    return response.data;
  },

  // Teams
  async getTeams(params?: {
    search?: string;
    page?: number;
    page_size?: number;
  }): Promise<PaginatedResponse<Team>> {
    const response = await apiClient.get('/api/v1/teams', { params });
    return response.data;
  },

  async getTeamSquad(teamId: number): Promise<Player[]> {
    const response = await apiClient.get(`/api/v1/teams/${teamId}/squad`);
    return response.data.data;
  },

  // Match details
  async getMatchDetails(matchId: number): Promise<Match> {
    const response = await apiClient.get(`/api/v1/matches/${matchId}`);
    return response.data.data;
  },

  // Health check
  async healthCheck(): Promise<{ status: string }> {
    const response = await apiClient.get('/healthz');
    return response.data;
  },

  // Version info
  async getVersion(): Promise<{
    version: string;
    git_commit: string;
    deployment_time: string;
    environment: string;
    features: Record<string, boolean>;
  }> {
    const response = await apiClient.get('/api/version');
    return response.data;
  },
};

// Export for testing
export { apiClient };