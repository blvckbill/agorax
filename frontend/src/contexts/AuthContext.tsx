import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { User } from '@/types/auth.types';
import { authApi } from '@/services/authApi';

interface AuthContextType {
  user: User | null;
  setUser: (user: User | null) => void;
  isAuthenticated: boolean;
  isLoading: boolean;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    // Check for existing token on mount
    const token = authApi.getToken();
    if (token) {
      // Set a temporary user - in production, validate token with backend
      setUser({ 
        id: 0, 
        email: '', 
        token,
        is_verified: true 
      });
      
      // TODO: Fetch actual user data from backend
      // authApi.getUser(userId).then(userData => setUser(userData));
    }
    setIsLoading(false);
  }, []);

  const logout = () => {
    authApi.clearToken();
    setUser(null);
  };

  const value = {
    user,
    setUser,
    isAuthenticated: !!user,
    isLoading,
    logout,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuthContext() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuthContext must be used within an AuthProvider');
  }
  return context;
}