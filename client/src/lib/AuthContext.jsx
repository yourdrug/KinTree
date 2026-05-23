/**
 * lib/AuthContext.jsx
 *
 * Единственный источник правды для состояния аутентификации.
 *
 * Архитектура:
 * - AuthProvider монтируется один раз в App (снаружи Routes)
 * - Состояние: user, isAuthenticated, isLoadingAuth
 * - При монтировании делает один GET /account/me (isInitial=true → без refresh при 401)
 * - После логина делает GET /account/me (isInitial=false → с refresh)
 * - authCallbacks.onUnauthenticated регистрируется когда пользователь залогинен
 *   и вызывается http.js при окончательном провале refresh
 *
 * Сессии вынесены в отдельный контекст SessionContext чтобы не перегружать AuthContext.
 *
 * НЕ содержит:
 * - Дублирующих axios instance (всё через api/http.js)
 * - Прямых вызовов axios (всё через api/auth.js)
 * - Логики refresh (она в api/http.js)
 */

import React, {
  createContext,
  useState,
  useContext,
  useEffect,
  useCallback,
  useRef,
} from "react";

import { authApi } from "@/api/auth";
import { authCallbacks, meCallState } from "@/api/http";
import { ROUTES } from "@/lib/routes";

// ── Contexts ───────────────────────────────────────────────────────────────────

const AuthContext    = createContext(null);
const SessionContext = createContext(null);

// ── AuthProvider ───────────────────────────────────────────────────────────────

export function AuthProvider({ children }) {
  const [user,          setUser]          = useState(null);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [isLoadingAuth, setIsLoadingAuth] = useState(true);   // true только при старте
  const [authError,     setAuthError]     = useState(null);

  // Sessions
  const [sessions,          setSessions]          = useState([]);
  const [isLoadingSessions, setIsLoadingSessions] = useState(false);
  const [sessionsError,     setSessionsError]     = useState(null);

  // ── Internal helpers ───────────────────────────────────────────────────────

  const _setLoggedIn = useCallback((userData) => {
    setUser(userData);
    setIsAuthenticated(true);
    setAuthError(null);
    // Регистрируем колбэк для http.js: вызовется если refresh окончательно провалится
    authCallbacks.onUnauthenticated = _clearSession;
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const _clearSession = useCallback(() => {
    setUser(null);
    setIsAuthenticated(false);
    setSessions([]);
    authCallbacks.onUnauthenticated = null;
  }, []);

  // ── fetchMe ────────────────────────────────────────────────────────────────
  /**
   * Загружает данные текущего пользователя через GET /account/me.
   *
   * isInitial=true  → первый старт приложения:
   *   401 = "не залогинен", refresh НЕ делается (через meCallState.isInitial)
   *
   * isInitial=false → после логина/OAuth/верификации:
   *   401 = "токен истёк", http.js сделает refresh автоматически
   */
  const fetchMe = useCallback(async (isInitial = false) => {
    try {
      setIsLoadingAuth(true);
      meCallState.isInitial = isInitial;

      const res = await authApi.me();
      _setLoggedIn(res.data);
    } catch {
      _clearSession();
    } finally {
      meCallState.isInitial = false;
      setIsLoadingAuth(false);
    }
  }, [_setLoggedIn, _clearSession]);

  // Единственный вызов при монтировании (isInitial=true)
  const didMount = useRef(false);
  useEffect(() => {
    if (didMount.current) return;
    didMount.current = true;
    fetchMe(true);
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  // ── Auth actions ───────────────────────────────────────────────────────────

  const login = useCallback(async (email, password) => {
    setIsLoadingAuth(true);
    setAuthError(null);
    try {
      const result = await authApi.login(email, password);
      if (!result.ok) {
        setAuthError(result.message);
        return result;
      }
      // Бэкенд поставил куки — загружаем профиль
      await fetchMe(false);
      return { ok: true };
    } finally {
      setIsLoadingAuth(false);
    }
  }, [fetchMe]);

  const register = useCallback(async (email, password) => {
    setIsLoadingAuth(true);
    setAuthError(null);
    try {
      const result = await authApi.register(email, password);
      if (!result.ok) {
        setAuthError(result.message);
        return result;
      }
      // После регистрации сразу логиним
      return login(email, password);
    } finally {
      setIsLoadingAuth(false);
    }
  }, [login]);

  const logout = useCallback(async () => {
    await authApi.logout();
    _clearSession();
    // Полный reload: сбрасываем все React-кеши и QueryClient
    window.location.href = ROUTES.home();
  }, [_clearSession]);

  const logoutAll = useCallback(async () => {
    await authApi.logoutAll();
    _clearSession();
    window.location.href = ROUTES.home();
  }, [_clearSession]);

  const loginWithGoogle = useCallback(() => {
    authApi.loginWithGoogle();
  }, []);

  const loginWithTelegram = useCallback(async (telegramData) => {
    setIsLoadingAuth(true);
    try {
      const result = await authApi.loginWithTelegram(telegramData);
      if (!result.ok) return result;
      await fetchMe(false);
      return { ok: true };
    } finally {
      setIsLoadingAuth(false);
    }
  }, [fetchMe]);

  // OAuth callback: бэкенд уже поставил куки, просто читаем профиль
  const handleOAuthCallback = useCallback(async () => {
    await fetchMe(false);
    return { ok: isAuthenticated };
  }, [fetchMe, isAuthenticated]);

  const verifyEmail = useCallback(async (token) => {
    const result = await authApi.verifyEmail(token);
    if (result.ok) await fetchMe(false);
    return result;
  }, [fetchMe]);

  const resendVerification = useCallback(() => authApi.resendVerification(), []);

  const forgotPassword = useCallback((email) => authApi.forgotPassword(email), []);

  const resetPassword  = useCallback((token, newPassword) =>
    authApi.resetPassword(token, newPassword), []);

  // ── Sessions ───────────────────────────────────────────────────────────────

  const fetchSessions = useCallback(async () => {
    setIsLoadingSessions(true);
    setSessionsError(null);
    try {
      const data = await authApi.getSessions();
      setSessions(data);
    } catch {
      setSessionsError("Не удалось загрузить сессии");
    } finally {
      setIsLoadingSessions(false);
    }
  }, []);

  const revokeSession = useCallback(async (sessionId) => {
    const result = await authApi.revokeSession(sessionId);
    if (result.ok) {
      setSessions((prev) => prev.filter((s) => s.session_id !== sessionId));
    }
    return result;
  }, []);

  // ── Values ─────────────────────────────────────────────────────────────────

  const authValue = {
    user,
    isAuthenticated,
    isLoadingAuth,
    authError,
    login,
    register,
    logout,
    logoutAll,
    loginWithGoogle,
    loginWithTelegram,
    handleOAuthCallback,
    verifyEmail,
    resendVerification,
    forgotPassword,
    resetPassword,
    fetchMe,
  };

  const sessionValue = {
    sessions,
    isLoadingSessions,
    sessionsError,
    fetchSessions,
    revokeSession,
  };

  return (
    <AuthContext.Provider value={authValue}>
      <SessionContext.Provider value={sessionValue}>
        {children}
      </SessionContext.Provider>
    </AuthContext.Provider>
  );
}

// ── Hooks ──────────────────────────────────────────────────────────────────────

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}

export function useSession() {
  const ctx = useContext(SessionContext);
  if (!ctx) throw new Error("useSession must be used within AuthProvider");
  return ctx;
}
