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
    let cancelled = false;

    const finish = (nextAuth) => {
      if (!cancelled) {
        setAuth(nextAuth);
        setIsLoading(false);
      }
    };

    if (user) {
      finish({ ...auth, user, guest });
    } else if (guest && authStorage.getToken()[0]) {
      // Stored guest with a usable access token — trust the saved session.
      finish({ ...auth, user: null, guest });
    } else if (guest) {
      // Stored guest identity but no usable token (fresh or corrupted
      // storage). Re-authenticate as guest; loginAsGuest persists the tokens.
      loginAsGuest().then((guestUser) => {
        if (!cancelled) {
          authStorage.setGuest(guestUser);
          finish({ user: null, guest: guestUser });
        }
      });
    } else {
      loginAsGuest().then((guestUser) => {
        if (!cancelled) {
          // loginAsGuest already persisted the tokens; guestUser is only
          // the user_data payload (no access/refresh fields). Re-storing
          // undefined here would overwrite the real tokens with "undefined".
          authStorage.setGuest(guestUser);
          finish({ user: null, guest: guestUser });
        }
      });
    }

    return () => {
      cancelled = true;
    };
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

    // Show a provisional guest identity right away so the UI does not wait
    // on the network call just to display a username.
    const provisionalGuest = {
      username: guestId,
      is_guest: true,
    };

    authStorage.setGuest(provisionalGuest);
    setAuth((prev) => ({ ...prev, user: null, guest: provisionalGuest }));

    try {
      const response = await authApi.guestLogin(guestId);
      const data = response.data;
      const guest_user = data.user_data;

      authStorage.setGuest(guest_user);
      authStorage.setToken(data.access, data.refresh);

      setAuth((prev) => ({ ...prev, user: null, guest: guest_user }));

      return guest_user;
    } catch (error) {
      // If the backend call fails, keep the provisional guest identity so
      // the app is still usable with a generated username.
      console.warn("[Auth] guest login failed, keeping provisional guest:", error);
      return provisionalGuest;
    }
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
