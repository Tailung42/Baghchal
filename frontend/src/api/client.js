import axios from "axios";
import { authStorage } from "../utils/storage";

const API_BASE_URL =
  import.meta.env.VITE_BASE_HTTP_URL || "http://127.0.0.1:8000/";

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
});

// intercept the request to add authtoken
api.interceptors.request.use((config) => {
  const [access_token, _] = authStorage.getToken();
  if (access_token) {
    config.headers.Authorization = `Bearer ${access_token}`;
  }
  return config;
});

export const authApi = {
  login: (username, password) => api.post("login/", { username, password }),

  signup: (formData) =>
    api.post("signup/", formData, {
      headers: { "Content-Type": "multipart/form-data" },
    }),

  googleAuth: (token, mode) => api.post("auth/google", { token, mode }),

  guestLogin: (guestId) => api.post("guest-login/", { guest_id: guestId }),
};

export const gameApi = {
  create: (gameId, playerRole) =>
    api.post("game/create/", {
      game_id: gameId,
      player_role: playerRole,
    }),

  join: (gameId) => api.post("game/join/", { game_id: gameId }),

  rejoin: (gameId) => api.post("game/rejoin/", { game_id: gameId }),

  quickMatch: () => api.post("game/quick-match/"),
};

export const userApi = {
  getProfile: (username) => api.get(`users/${username}/`),
};

export default api;
