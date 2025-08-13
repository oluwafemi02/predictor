import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL 
  ? `${process.env.REACT_APP_API_URL}/api/v1`
  : 'http://localhost:5000/api/v1';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor for auth
api.interceptors.request.use(
  (config) => {
    // Add auth token if available
    const token = localStorage.getItem('authToken');
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
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Handle unauthorized access
      localStorage.removeItem('authToken');
      window.location.href = '/login';
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
  const response = await api.get<{ predictions: any[] }>('/upcoming-predictions');
  return response.data.predictions;
};

export const getUpcomingMatches = async (limit?: number) => {
  const response = await api.get<{ matches: Match[] }>('/upcoming-matches', {
    params: { limit }
  });
  return response.data.matches;
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

export default api;