import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL 
  ? `${process.env.REACT_APP_API_URL}/api/v1`
  : 'http://localhost:5000/api/v1';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: true, // Enable cookie support
});

// Token management
const tokenManager = {
  getAccessToken: () => localStorage.getItem('access_token'),
  getRefreshToken: () => localStorage.getItem('refresh_token'),
  setTokens: (tokens: { access_token: string; refresh_token: string }) => {
    localStorage.setItem('access_token', tokens.access_token);
    localStorage.setItem('refresh_token', tokens.refresh_token);
  },
  clearTokens: () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('user');
  }
};

// Request interceptor for auth
api.interceptors.request.use(
  (config) => {
    // Add auth token if available
    const token = tokenManager.getAccessToken();
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    
    // Add API key if available (for legacy support)
    const apiKey = localStorage.getItem('apiKey');
    if (apiKey) {
      config.headers['X-API-Key'] = apiKey;
    }
    
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor for error handling and token refresh
let isRefreshing = false;
let failedQueue: any[] = [];

const processQueue = (error: any, token: string | null = null) => {
  failedQueue.forEach(prom => {
    if (error) {
      prom.reject(error);
    } else {
      prom.resolve(token);
    }
  });
  
  failedQueue = [];
};

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    if (error.response?.status === 401 && !originalRequest._retry) {
      if (isRefreshing) {
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject });
        }).then(token => {
          originalRequest.headers.Authorization = `Bearer ${token}`;
          return api(originalRequest);
        }).catch(err => {
          return Promise.reject(err);
        });
      }

      originalRequest._retry = true;
      isRefreshing = true;

      const refreshToken = tokenManager.getRefreshToken();
      
      if (refreshToken) {
        try {
          const response = await api.post('/auth/refresh', {}, {
            headers: {
              Authorization: `Bearer ${refreshToken}`
            }
          });
          
          const { tokens } = response.data;
          tokenManager.setTokens(tokens);
          processQueue(null, tokens.access_token);
          
          originalRequest.headers.Authorization = `Bearer ${tokens.access_token}`;
          return api(originalRequest);
        } catch (err) {
          processQueue(err, null);
          tokenManager.clearTokens();
          window.location.href = '/login';
          return Promise.reject(err);
        } finally {
          isRefreshing = false;
        }
      } else {
        // No refresh token, redirect to login
        tokenManager.clearTokens();
        window.location.href = '/login';
      }
    }

    return Promise.reject(error);
  }
);

// Types
export interface Team {
  id: number;
  name: string;
  code: string;
  logo_url: string;
  stadium: string;
  founded: number;
}

export interface TeamWithStats extends Team {
  matches_played?: number;
  wins?: number;
  draws?: number;
  losses?: number;
  goals_for?: number;
  goals_against?: number;
  points?: number;
  form?: string | null;
}

export interface TeamStatistics {
  season: string;
  matches_played: number;
  wins: number;
  draws: number;
  losses: number;
  goals_for: number;
  goals_against: number;
  form: string;
  clean_sheets: number;
  home_record: {
    wins: number;
    draws: number;
    losses: number;
  };
  away_record: {
    wins: number;
    draws: number;
    losses: number;
  };
}

export interface Match {
  id: number;
  date: string;
  home_team: {
    id: number;
    name: string;
    logo_url: string;
  };
  away_team: {
    id: number;
    name: string;
    logo_url: string;
  };
  home_score: number | null;
  away_score: number | null;
  status: string;
  competition: string;
  venue: string;
  has_prediction: boolean;
}

export interface MatchDetails extends Match {
  home_score_halftime: number | null;
  away_score_halftime: number | null;
  referee: string;
  attendance: number;
}

export interface Prediction {
  home_win_probability: number;
  draw_probability: number;
  away_win_probability: number;
  predicted_home_score: number;
  predicted_away_score: number;
  over_2_5_probability: number;
  both_teams_score_probability: number;
  confidence_score: number;
  factors: Record<string, string>;
  created_at: string;
  model_version?: string;
}

export interface HeadToHead {
  total_matches: number;
  home_wins: number;
  away_wins: number;
  draws: number;
  last_5_results: Array<{
    date: string;
    result: string;
    score: string;
  }>;
}

export interface LeagueTableEntry {
  position: number;
  team: {
    id: number;
    name: string;
    logo_url: string;
  };
  played: number;
  won: number;
  drawn: number;
  lost: number;
  goals_for: number;
  goals_against: number;
  goal_difference: number;
  points: number;
  form: string;
}

export interface PaginationResponse<T> {
  items: T[];
  pagination: {
    page: number;
    pages: number;
    total: number;
    per_page: number;
  };
}

// Error response interface
export interface APIError {
  status: 'error';
  message: string;
  field?: string;
  code?: string;
}

// Success response wrapper
export interface APIResponse<T> {
  status: 'success';
  data: T;
  message?: string;
}

// API Functions

// Teams
export const getTeams = async (competition?: string): Promise<TeamWithStats[]> => {
  const response = await api.get<APIResponse<{ teams: TeamWithStats[] }>>('/teams', {
    params: { competition },
  });
  return response.data.data.teams;
};

export const getTeamDetails = async (teamId: number, season?: string) => {
  const response = await api.get<{
    team: Team;
    statistics: TeamStatistics;
    recent_matches: Match[];
    injured_players: any[];
  }>(`/teams/${teamId}`, {
    params: { season },
  });
  return response.data;
};

// Matches
export const getMatches = async (filters: {
  date_from?: string;
  date_to?: string;
  team_id?: number;
  competition?: string;
  status?: string;
  page?: number;
}) => {
  const response = await api.get<{
    matches: Match[];
    pagination: PaginationResponse<Match>['pagination'];
  }>('/matches', {
    params: filters,
  });
  return response.data;
};

export const getMatchDetails = async (matchId: number) => {
  const response = await api.get<{
    match: MatchDetails;
    head_to_head: HeadToHead | null;
    prediction: Prediction | null;
    team_form: {
      home_team: {
        form: string;
        recent_matches: number;
      };
      away_team: {
        form: string;
        recent_matches: number;
      };
    };
  }>(`/matches/${matchId}`);
  return response.data;
};

// Predictions
export const getPredictions = async (filters: {
  date_from?: string;
  date_to?: string;
  page?: number;
  competition?: string;
}) => {
  const response = await api.get<{
    predictions: any[];
    pagination: PaginationResponse<any>['pagination'];
  }>('/predictions', {
    params: filters,
  });
  return response.data;
};

export const createPrediction = async (matchId: number) => {
  const response = await api.post<any>(`/predictions/${matchId}`);
  return response.data;
};

export const getUpcomingPredictions = async () => {
  // Use SportMonks API endpoint for upcoming fixtures with predictions
  const days = 7; // Get fixtures for next 7 days
  const response = await axios.get<{ fixtures: any[] }>(
    `${process.env.REACT_APP_API_URL || 'http://localhost:5000'}/api/sportmonks/fixtures/upcoming`,
    {
      params: { days, predictions: true }
    }
  );
  
  // Transform SportMonks fixtures with predictions to match the expected format
  const predictions = response.data.fixtures
    .filter((fixture: any) => fixture.predictions) // Only include fixtures with predictions
    .map((fixture: any) => ({
      id: fixture.id,
      fixture_id: fixture.id,
      match: {
        homeTeam: fixture.home_team?.name || 'Unknown',
        awayTeam: fixture.away_team?.name || 'Unknown',
        date: fixture.date,
        competition: fixture.league?.name || 'Unknown League'
      },
      prediction: fixture.predictions?.match_winner,
      confidence: Math.max(
        fixture.predictions?.match_winner?.home_win || 0,
        fixture.predictions?.match_winner?.draw || 0,
        fixture.predictions?.match_winner?.away_win || 0
      ) / 100, // Convert percentage to decimal
      odds: fixture.predictions?.goals
    }));
  
  return predictions;
};

export const getUpcomingMatches = async (limit?: number) => {
  // Use SportMonks API endpoint for upcoming fixtures
  const days = 7; // Get fixtures for next 7 days
  const response = await axios.get<{ fixtures: any[] }>(
    `${process.env.REACT_APP_API_URL || 'http://localhost:5000'}/api/sportmonks/fixtures/upcoming`,
    {
      params: { days, predictions: false }
    }
  );
  
  // Transform SportMonks fixtures to match the expected format
  const matches = response.data.fixtures.slice(0, limit).map((fixture: any) => ({
    id: fixture.id,
    homeTeam: fixture.home_team?.name || 'Unknown',
    awayTeam: fixture.away_team?.name || 'Unknown',
    date: fixture.date,
    time: new Date(fixture.date).toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' }),
    competition: fixture.league?.name || 'Unknown League',
    venue: fixture.venue?.name || 'Unknown Venue',
    homeTeamLogo: fixture.home_team?.logo,
    awayTeamLogo: fixture.away_team?.logo
  }));
  
  return matches;
};

// Statistics
export const getCompetitions = async () => {
  const response = await api.get<{ competitions: string[] }>('/statistics/competitions');
  return response.data.competitions;
};

export const getLeagueTable = async (competition: string, season?: string) => {
  const response = await api.get<{
    competition: string;
    season: string;
    available_seasons: string[];
    table: LeagueTableEntry[];
    last_updated: string;
  }>('/statistics/league-table', {
    params: { competition, season },
  });
  return response.data;
};

// Team Players
export const getTeamPlayers = async (teamId: number) => {
  const response = await api.get<{
    players: Array<{
      id: number;
      name: string;
      position: string;
      number?: number;
      age?: number;
      nationality?: string;
      injured?: boolean;
    }>;
  }>(`/teams/${teamId}/players`);
  return response.data;
};

// Team Matches
export const getTeamMatches = async (teamId: number, limit: number = 20) => {
  const response = await api.get<{
    matches: Match[];
  }>('/matches', {
    params: {
      team_id: teamId,
      per_page: limit,
    },
  });
  return response.data;
};

// Team Statistics
export const getTeamStatistics = async (teamId: number, season?: string) => {
  const response = await api.get<{
    statistics: TeamStatistics & {
      position?: number;
      points?: number;
    };
  }>(`/teams/${teamId}`, {
    params: { season },
  });
  return response.data;
};

// Model
export const getModelStatus = async () => {
  const response = await api.get<{
    is_trained: boolean;
    model_version: string;
    features: string[];
    last_trained?: string;
    training_data?: {
      total_matches: number;
      finished_matches: number;
      validation_split: number;
    };
    performance?: {
      accuracy: number;
      precision: number;
      recall: number;
      f1_score: number;
      ready_for_predictions: boolean;
      confidence_calibrated: boolean;
    };
    model_insights?: {
      top_features: Array<{
        name: string;
        importance: number;
      }>;
      ensemble_weights: {
        xgboost: number;
        lightgbm: number;
        random_forest: number;
        gradient_boosting: number;
      };
    };
  }>('/model/status');
  return response.data;
};

export const trainModel = async () => {
  const response = await api.post<{ message: string }>('/model/train');
  return response.data;
};

// Sync
export const syncTeams = async (competitionId: number) => {
  const response = await api.post<{ message: string }>(`/sync/teams/${competitionId}`);
  return response.data;
};

export const syncMatches = async (competitionId: number, season?: string) => {
  const response = await api.post<{ message: string }>(`/sync/matches/${competitionId}`, {
    season,
  });
  return response.data;
};

// Authentication APIs
export const authAPI = {
  // Register new user
  register: async (data: {
    username: string;
    email: string;
    password: string;
  }) => {
    const response = await api.post('/auth/register', data);
    if (response.data.tokens) {
      tokenManager.setTokens(response.data.tokens);
      localStorage.setItem('user', JSON.stringify(response.data.user));
    }
    return response.data;
  },

  // Login
  login: async (data: {
    username: string;
    password: string;
  }) => {
    const response = await api.post('/auth/login', data);
    if (response.data.tokens) {
      tokenManager.setTokens(response.data.tokens);
      localStorage.setItem('user', JSON.stringify(response.data.user));
    }
    return response.data;
  },

  // Logout
  logout: async () => {
    try {
      await api.post('/auth/logout');
    } catch (error) {
      console.error('Logout error:', error);
    } finally {
      tokenManager.clearTokens();
      window.location.href = '/login';
    }
  },

  // Get current user
  getCurrentUser: async () => {
    const response = await api.get('/auth/me');
    return response.data;
  },

  // Generate API key
  generateApiKey: async () => {
    const response = await api.post('/auth/api-key');
    return response.data;
  },

  // Check if authenticated
  isAuthenticated: () => {
    return !!tokenManager.getAccessToken();
  },

  // Get stored user
  getStoredUser: () => {
    const userStr = localStorage.getItem('user');
    return userStr ? JSON.parse(userStr) : null;
  }
};

// Export everything
export { tokenManager, api };

export default api;