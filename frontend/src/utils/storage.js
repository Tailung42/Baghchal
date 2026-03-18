const USER_STORAGE_KEY = "user";
const GUEST_STORAGE_KEY = "guest";
const GAME_STORAGE_KEY = "gameId";
const ACCESS_TOKEN_KEY = "access_token";
const REFRESH_TOKEN_KEY = "refresh_token";
import { generateUsername } from "unique-username-generator";

export const authStorage = {
  getToken: () => {
    const access = JSON.parse(localStorage.getItem(ACCESS_TOKEN_KEY));
    const refresh = JSON.parse(localStorage.getItem(REFRESH_TOKEN_KEY));
    return [access, refresh];
  },

  setToken: (access, refresh) => {
    localStorage.setItem(ACCESS_TOKEN_KEY, JSON.stringify(access));
    localStorage.setItem(REFRESH_TOKEN_KEY, JSON.stringify(refresh));
  },

  setUser: (user) => {
    localStorage.setItem(USER_STORAGE_KEY, JSON.stringify(user));
    localStorage.removeItem(GUEST_STORAGE_KEY);
    return user;
  },

  getUser: () => {
    const stored = localStorage.getItem(USER_STORAGE_KEY);
    if (!stored) return null;
    try {
      return JSON.parse(stored);
    } catch {
      return null;
    }
  },

  clearUser: () => {
    localStorage.removeItem(USER_STORAGE_KEY);
  },

  setGuest: (guest) => {
    localStorage.setItem(GUEST_STORAGE_KEY, JSON.stringify(guest));
    localStorage.removeItem(USER_STORAGE_KEY);
    return true;
  },

  getGuest: () => {
    const stored = localStorage.getItem(GUEST_STORAGE_KEY);
    if (!stored) return null;
    try {
      return JSON.parse(stored);
    } catch {
      return null;
    }
  },

  clearGuest: () => {
    localStorage.removeItem(GUEST_STORAGE_KEY);
  },

  clearAll: () => {
    localStorage.removeItem(USER_STORAGE_KEY);
    localStorage.removeItem(GUEST_STORAGE_KEY);
    localStorage.removeItem(ACCESS_TOKEN_KEY);
    localStorage.removeItem(REFRESH_TOKEN_KEY);
  },
};

export const gameStorage = {
  isInGame: sessionStorage.getItem(GAME_STORAGE_KEY, null) ? true : false,

  setGame: (gameId) => {
    sessionStorage.setItem(GAME_STORAGE_KEY, gameId);
  },

  removeGame: () => {
    sessionStorage.removeItem(GAME_STORAGE_KEY);
  },
};
