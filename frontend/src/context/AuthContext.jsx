import { createContext, useContext, useState, useEffect } from "react";
import { authApi } from "../api/client";
import { authStorage } from "../utils/storage";
import { generateUsername } from "unique-username-generator";

const AuthContext = createContext(undefined);

export function AuthProvider({ children }) {
  const [auth, setAuth] = useState({ user: null, guest: null });
  const [isLoading, setIsLoading] = useState(true);
  const user = authStorage.getUser();
  const guest = authStorage.getGuest();

  // # load stored user on mount
  useEffect(() => {
    if (user) {
      setAuth((prev) => ({ ...prev, user: user, guest: guest }));
    } else if (guest) {
      setAuth((prev) => ({ ...prev, user: null, guest: guest }));
    } else {
      loginAsGuest();
    }
    setIsLoading(false);
  }, []);

  const login = async (username, password) => {
    const response = await authApi.login(username, password);
    handleLoginResponse(response);
  };

  const signup = async (formData) => {
    const response = await authApi.signup(formData);
    handleLoginResponse(response);
  };

  const googleAuth = async (token, mode) => {
    const response = await authApi.googleAuth(token, mode);
    handleLoginResponse(response);
  };

  const loginAsGuest = async () => {
    const guestId = generateUsername();
    const promise = await authApi.guestLogin(guestId);
    const data = promise.data;
    const guest_user = data.user_data;
    authStorage.setGuest(guest_user);
    authStorage.setToken(data.access, data.refresh);
    setAuth((prev) => ({ ...prev, user: null, guest: guest_user }));
  };

  const handleLoginResponse = (response) => {
    const data = response.data;
    const user = data.user_data;
    authStorage.setToken(data.access, data.refresh);
    authStorage.setUser(user);
    setAuth((prev) => ({ ...prev, user: user, guest: null }));
  };
  const logout = () => {
    authStorage.clearAll();
    setAuth({ user: null, guest: null });
  };

  return (
    <AuthContext.Provider
      value={{
        auth,
        isLoading,
        login,
        signup,
        googleAuth,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}
