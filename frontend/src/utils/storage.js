const USER_STORAGE_KEY = "user";
const GUEST_STORAGE_KEY = "guest";
const GAME_STORAGE_KEY = "gameId";
const ACCESS_TOKEN_KEY = "access_token";
const REFRESH_TOKEN_KEY = "refresh_token";
import { generateUsername } from "unique-username-generator";

const _authStorage = {
  getToken: () => {
    const parseToken = (key) => {
      const raw = localStorage.getItem(key);
      if (!raw) return null;
      try {
        return JSON.parse(raw);
      } catch {
        // Corrupt stored value (e.g. literal "undefined" written by an old
        // bug). Clean it up so it cannot keep breaking API calls.
        localStorage.removeItem(key);
        return null;
      }
    };
    return [
      parseToken(ACCESS_TOKEN_KEY),
      parseToken(REFRESH_TOKEN_KEY),
    ];
  },

  setToken: (access, refresh) => {
    if (access) localStorage.setItem(ACCESS_TOKEN_KEY, JSON.stringify(access));
    if (refresh) localStorage.setItem(REFRESH_TOKEN_KEY, JSON.stringify(refresh));
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

export const authStorage = {
  ..._authStorage,
  getUsername: () => {
    const user = _authStorage.getUser();
    const guest = _authStorage.getGuest();
    if (user?.username) return user.username;
    if (guest?.username) return guest.username;
    return null;
  },
};

export const gameStorage = {
  isInGame: () => (!!sessionStorage.getItem(GAME_STORAGE_KEY)),

  setGame: (gameId) => {
    sessionStorage.setItem(GAME_STORAGE_KEY, gameId);
  },

  removeGame: () => {
    sessionStorage.removeItem(GAME_STORAGE_KEY);
  },
};
