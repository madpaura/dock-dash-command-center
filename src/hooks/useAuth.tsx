
import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { authApi } from '../lib/api';

interface User {
  id: number;
  name: string;
  email: string;
  role: 'admin' | 'user';
  token: string;
}

interface AuthContextType {
  user: User | null;
  login: (email: string, password: string) => Promise<{ success: boolean; error?: string }>;
  logout: () => Promise<void>;
  isAuthenticated: boolean;
  isLoading: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // Check for existing session on mount
  useEffect(() => {
    const validateSession = async () => {
      const savedUser = localStorage.getItem('dockerManager_user');

      if (savedUser) {
        try {
          const userData = JSON.parse(savedUser);

          if (userData && userData.token) {
            setUser(userData);

            const response = await authApi.validateSession(userData.token);

            if (!response.success || !response.data?.valid) {
              setUser(null);
            }
          } else {
            localStorage.removeItem('dockerManager_user');
          }
        } catch (error) {
          localStorage.removeItem('dockerManager_user');
        }
      }

      setIsLoading(false);
    };

    validateSession();
  }, []);

  const login = async (email: string, password: string): Promise<{ success: boolean; error?: string }> => {
    try {
      const response = await authApi.login(email, password);

      if (response.success && response.data) {
        const userData = {
          id: response.data.user_id,
          name: response.data.name,
          email: response.data.email,
          role: response.data.role as 'admin' | 'user',
          token: response.data.token
        };

        // Update state and localStorage
        setUser(userData);
        localStorage.setItem('dockerManager_user', JSON.stringify(userData));

        return { success: true };
      }

      console.error('Login failed:', response.error || 'Unknown error');
      return {
        success: false,
        error: response.error || 'Invalid credentials'
      };
    } catch (error) {
      console.error('Login exception:', error);
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Login failed'
      };
    }
  };

  const logout = async () => {
    if (user?.token) {
      try {
        await authApi.logout(user.token);
      } catch (error) {
        console.error('Logout error:', error);
      }
    }

    setUser(null);
    localStorage.removeItem('dockerManager_user');
  };

  return (
    <AuthContext.Provider value={{
      user,
      login,
      logout,
      isAuthenticated: !!user,
      isLoading
    }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
};
