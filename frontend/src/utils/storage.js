const AUTH_STORAGE_KEY = 'auth';
const GUEST_STORAGE_KEY = 'guestAuth';

export const authStorage = {
  setUserAuth: (user) => {
    localStorage.setItem(AUTH_STORAGE_KEY, JSON.stringify({ isLoggedIn: true, user }));
    sessionStorage.removeItem(GUEST_STORAGE_KEY);
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

  setGuestAuth: (guestId) => {
    sessionStorage.setItem(GUEST_STORAGE_KEY, JSON.stringify({ guestId }));
    localStorage.removeItem(AUTH_STORAGE_KEY);
  },

  getGuestAuth: () => {
    const stored = sessionStorage.getItem(GUEST_STORAGE_KEY);
    if (!stored) return null;
    try {
      return JSON.parse(stored);
    } catch {
      return null;
    }
  },

  clearGuestAuth: () => {
    sessionStorage.removeItem(GUEST_STORAGE_KEY);
  },

  clearAll: () => {
    localStorage.removeItem(AUTH_STORAGE_KEY);
    sessionStorage.removeItem(GUEST_STORAGE_KEY);
  },
};
