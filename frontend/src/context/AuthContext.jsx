import { createContext, useContext, useState, useEffect } from 'react';
import { authApi } from '../api/client';
import { authStorage } from '../utils/storage';

const AuthContext = createContext(undefined);

export function AuthProvider({ children }) {
  const [auth, setAuth] = useState({ isLoggedIn: false });
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const userAuth = authStorage.getUserAuth();
    const guestAuth = authStorage.getGuestAuth();

    if (userAuth?.isLoggedIn && userAuth.user) {
      setAuth({ isLoggedIn: true, user: userAuth.user });
    } else if (guestAuth?.guestId) {
      setAuth({ isLoggedIn: false, guestId: guestAuth.guestId });
    } else {
      setAuth({ isLoggedIn: false });
    }
    setIsLoading(false);
  }, []);

  const login = async (username, password) => {
    const response = await authApi.login(username, password);
    const userData = response.data.user_data;
    authStorage.setUserAuth(userData);
    setAuth({ isLoggedIn: true, user: userData });
  };

  const signup = async (formData) => {
    await authApi.signup(formData);
  };

  const googleAuth = async (token, mode) => {
    const response = await authApi.googleAuth(token, mode);
    const userData = response.data.user_data;
    authStorage.setUserAuth(userData);
    setAuth({ isLoggedIn: true, user: userData });
  };

  const setGuestId = (guestId) => {
    authStorage.setGuestAuth(guestId);
    setAuth({ isLoggedIn: false, guestId });
  };

  const logout = () => {
    authStorage.clearAll();
    setAuth({ isLoggedIn: false });
  };

  return (
    <AuthContext.Provider value={{ auth, isLoading, login, signup, googleAuth, setGuestId, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
