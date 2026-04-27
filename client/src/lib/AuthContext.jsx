import React, { createContext, useState, useContext, useEffect } from 'react';
import axios from 'axios';
import { appParams } from '@/lib/app-params';

const AuthContext = createContext();

const api = axios.create({
  baseURL: appParams.apiUrl,
});

// interceptor для токена
api.interceptors.request.use((config) => {
  const token = appParams.getToken();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [isLoadingAuth, setIsLoadingAuth] = useState(true);
  const [authError, setAuthError] = useState(null);

  useEffect(() => {
    checkUserAuth();
  }, []);

  // 🔹 Проверка пользователя (GET /auth/me)
  const checkUserAuth = async () => {
    try {
      setIsLoadingAuth(true);

      const token = appParams.getToken();
      if (!token) {
        setIsAuthenticated(false);
        setIsLoadingAuth(false);
        return;
      }

      const res = await api.get('/auth/me');

      setUser(res.data);
      setIsAuthenticated(true);
    } catch (error) {
      console.error('Auth check failed:', error);

      appParams.removeToken();
      setUser(null);
      setIsAuthenticated(false);
      setAuthError('Session expired');
    } finally {
      setIsLoadingAuth(false);
    }
  };

  // 🔹 LOGIN (POST /auth/login)
  const login = async (email, password) => {
    try {
      setIsLoadingAuth(true);
      setAuthError(null);

      const res = await api.post('/auth/login', {
        email,
        password
      });

      const { access_token, user } = res.data;

      appParams.setToken(access_token);
      setUser(user);
      setIsAuthenticated(true);

      return true;
    } catch (error) {
      console.error('Login failed:', error);
      setAuthError(error.response?.data?.detail || 'Login failed');
      return false;
    } finally {
      setIsLoadingAuth(false);
    }
  };

  // 🔹 LOGOUT
  const logout = () => {
    appParams.removeToken();
    setUser(null);
    setIsAuthenticated(false);

    window.location.href = '/';
  };

  // 🔹 редирект на страницу логина
  const navigateToLogin = () => {
    window.location.href = '/login';
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        isAuthenticated,
        isLoadingAuth,
        authError,
        login,
        logout,
        navigateToLogin,
        checkUserAuth
      }}
    >
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
