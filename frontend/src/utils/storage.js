const AUTH_STORAGE_KEY = "auth";
const GUEST_STORAGE_KEY = "guestAuth";
const GAME_STORAGE_KEY = "gameId";
import { generateUsername } from "unique-username-generator";

export const authStorage = {
  setUserAuth: (user) => {
    localStorage.setItem(
      AUTH_STORAGE_KEY,
      JSON.stringify({ isLoggedIn: true, user }),
    );
    localStorage.removeItem(GUEST_STORAGE_KEY);
    return user;
  },

  getUserAuth: () => {
    const stored = localStorage.getItem(AUTH_STORAGE_KEY);
    if (!stored) return null;
    try {
      return JSON.parse(stored);
    } catch {
      return null;
    }
  },

  clearUserAuth: () => {
    localStorage.removeItem(AUTH_STORAGE_KEY);
  },

  setGuestAuth: () => {
    const guestId = generateUsername();
    localStorage.setItem(GUEST_STORAGE_KEY, JSON.stringify({ guestId }));
    localStorage.removeItem(AUTH_STORAGE_KEY);
    return guestId;
  },

  getGuestAuth: () => {
    const stored = localStorage.getItem(GUEST_STORAGE_KEY);
    if (!stored) return null;
    try {
      return JSON.parse(stored);
    } catch {
      return null;
    }
  },

  clearGuestAuth: () => {
    localStorage.removeItem(GUEST_STORAGE_KEY);
  },

  clearAll: () => {
    localStorage.removeItem(AUTH_STORAGE_KEY);
    localStorage.removeItem(GUEST_STORAGE_KEY);
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
