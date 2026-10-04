import React, { createContext, useContext, useState, useEffect } from 'react';
import { User } from '../types/auth';
import { getMe, revokeSession } from '../api/auth';
import { clearAuthTokens } from '../api/client';

interface AuthContextType {
  user: User | null;
  isLoading: boolean;
  loginUser: (token: string, refresh: string) => void;
  logoutUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{children: React.ReactNode}> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem('access_token');
    if (!token) {
      setIsLoading(false);
      return;
    }
    getMe()
      .then(setUser)
      .catch(() => {
        clearAuthTokens();
        setUser(null);
      })
      .finally(() => setIsLoading(false));
  }, []);

  const loginUser = (token: string, refresh: string) => {
    localStorage.setItem('access_token', token);
    localStorage.setItem('refresh_token', refresh);
    setIsLoading(true);
    getMe()
      .then(setUser)
      .catch(() => {
        clearAuthTokens();
        setUser(null);
      })
      .finally(() => setIsLoading(false));
  };

  const logoutUser = async () => {
    const refreshToken = localStorage.getItem('refresh_token');
    clearAuthTokens();
    setUser(null);
    if (refreshToken) {
      try {
        await revokeSession(refreshToken);
      } catch {
        // Local credentials are already cleared; remote logout is best effort.
      }
    }
  };

  return <AuthContext.Provider value={{ user, isLoading, loginUser, logoutUser }}>{children}</AuthContext.Provider>;
};

export const useAuthContext = () => {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuthContext must be used within an AuthProvider");
  return ctx;
};
