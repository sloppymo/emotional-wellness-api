import axios from 'axios';

// Create axios instance with default config
const api = axios.create({
  baseURL: process.env.REACT_APP_API_URL || 'http://localhost:8000/api',
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor for adding auth token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor to handle common errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Handle unauthorized access
      localStorage.removeItem('token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// Auth service
export const authService = {
  login: async (email: string, password: string) => {
    const formData = new URLSearchParams();
    formData.append('username', email);
    formData.append('password', password);
    
    const response = await api.post('/v1/auth/login', formData, {
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
    });
    return response.data;
  },
  
  register: async (email: string, password: string, username: string) => {
    const response = await api.post('/v1/auth/register', {
      email,
      password,
      username,
    });
    return response.data;
  },
  
  getCurrentUser: async () => {
    const response = await api.get('/v1/auth/me');
    return response.data;
  },
};

// Game service
export const gameService = {
  createGame: async (scenarioId: string, factionId: string) => {
    const response = await api.post('/v1/games', {
      scenario_id: scenarioId,
      faction_id: factionId,
    });
    return response.data;
  },
  
  getGames: async () => {
    const response = await api.get('/v1/games');
    return response.data;
  },
  
  getGameById: async (gameId: string) => {
    const response = await api.get(`/v1/games/${gameId}`);
    return response.data;
  },
  
  advanceTurn: async (gameId: string) => {
    const response = await api.post(`/v1/games/${gameId}/turns`);
    return response.data;
  },
  
  performAction: async (gameId: string, action: any) => {
    const response = await api.post(`/v1/games/${gameId}/actions`, action);
    return response.data;
  },
  
  getGameEvents: async (gameId: string) => {
    const response = await api.get(`/v1/games/${gameId}/events`);
    return response.data;
  },
};

// Faction service
export const factionService = {
  getFactions: async (filters?: any) => {
    const response = await api.get('/v1/factions', { params: filters });
    return response.data;
  },
  
  getFactionById: async (factionId: string) => {
    const response = await api.get(`/v1/factions/${factionId}`);
    return response.data;
  },
  
  getFactionByGame: async (gameId: string) => {
    const response = await api.get(`/v1/games/${gameId}/factions`);
    return response.data;
  },
  
  getFactionRelationships: async (factionId: string, gameId?: string) => {
    const params = gameId ? { game_id: gameId } : {};
    const response = await api.get(`/v1/factions/${factionId}/relationships`, { params });
    return response.data;
  },
};

// Player character service
export const playerService = {
  getPlayerCharacters: async (gameId: string) => {
    const response = await api.get(`/v1/games/${gameId}/characters`);
    return response.data;
  },
  
  createPlayerCharacter: async (gameId: string, data: any) => {
    const response = await api.post(`/v1/games/${gameId}/characters`, data);
    return response.data;
  },
  
  getPlayerCharacter: async (gameId: string, characterId: string) => {
    const response = await api.get(`/v1/games/${gameId}/characters/${characterId}`);
    return response.data;
  },
  
  createCell: async (gameId: string, characterId: string, data: any) => {
    const response = await api.post(`/v1/games/${gameId}/characters/${characterId}/cells`, data);
    return response.data;
  },
  
  getJournalEntries: async (gameId: string, characterId: string) => {
    const response = await api.get(`/v1/games/${gameId}/characters/${characterId}/journal`);
    return response.data;
  },
  
  createJournalEntry: async (gameId: string, characterId: string, data: any) => {
    const response = await api.post(`/v1/games/${gameId}/characters/${characterId}/journal`, data);
    return response.data;
  },
};

export default api;
