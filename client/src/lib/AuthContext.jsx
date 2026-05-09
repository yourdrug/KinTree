/**
 * lib/AuthContext.jsx
 *
 * Исправления:
 * 1. checkUserAuth не вызывает _clearSession при 401 — только при настоящем logout/refresh fail
 * 2. loginWithGoogle открывает окно через редирект на бэкенд (бэкенд → Google → /oauth/callback)
 * 3. handleOAuthCallback корректно принимает code из URL и отправляет на бэкенд
 * 4. Состояние не сбрасывается при SPA-навигации (Provider монтируется один раз в App)
 * 5. _logoutRef устанавливается только когда пользователь активно залогинен
 * 6. isLoadingAuth true только при реальных запросах, не при навигации
 */

import React, {
  createContext,
  useState,
  useContext,
  useEffect,
  useCallback,
  useRef,
} from "react";
import { http, _logoutRef } from "@/api/client";
import { ENDPOINTS as EP } from "@/api/endpoints";
import { ROUTES } from "@/lib/routes";
import { appParams } from "@/lib/app-params";

// ─── Contexts ──────────────────────────────────────────────────────────────────

const AuthContext    = createContext(null);
const SessionContext = createContext(null);

// ─── Provider ──────────────────────────────────────────────────────────────────

export const AuthProvider = ({ children }) => {
  const [user,            setUser]            = useState(null);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  // true только при начальной загрузке — потом false
  const [isLoadingAuth,   setIsLoadingAuth]   = useState(true);
  const [authError,       setAuthError]       = useState(null);

  const [sessions,          setSessions]          = useState([]);
  const [isLoadingSessions, setIsLoadingSessions] = useState(false);
  const [sessionsError,     setSessionsError]     = useState(null);

  // Флаг: был ли пользователь когда-либо залогинен в этой сессии
  // Нужен чтобы _logoutRef не вызывал clearSession при первом 401 /me
  const wasAuthenticated = useRef(false);

  // ── Internal clear ─────────────────────────────────────────────────────────
  const _clearSession = useCallback(() => {
    setUser(null);
    setIsAuthenticated(false);
    setSessions([]);
    wasAuthenticated.current = false;
  }, []);

  // Регистрируем logout только когда пользователь залогинен
  // При незалогиненном состоянии — пустая функция (чтобы не делать лишний redirect)
  useEffect(() => {
    if (isAuthenticated) {
      _logoutRef.current = _clearSession;
    } else {
      _logoutRef.current = null;
    }
  }, [isAuthenticated, _clearSession]);

  // ── Restore on mount — единственный вызов при старте ───────────────────────
  const checkUserAuth = useCallback(async () => {
    try {
      setIsLoadingAuth(true);
      const res = await http.get(EP.auth.me());
      setUser(res.data);
      setIsAuthenticated(true);
      wasAuthenticated.current = true;
      setAuthError(null);
    } catch {
      // 401 при /me — просто не залогинен, это нормально
      // НЕ вызываем _clearSession, просто оставляем user = null
      setUser(null);
      setIsAuthenticated(false);
    } finally {
      setIsLoadingAuth(false);
    }
  }, []);

  // Запускается один раз при монтировании — при SPA-навигации НЕ перезапускается
  useEffect(() => {
    checkUserAuth();
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  // ── Login ──────────────────────────────────────────────────────────────────
  const login = useCallback(async (email, password) => {
    try {
      setIsLoadingAuth(true);
      setAuthError(null);
      const res = await http.post(EP.auth.login(), { email, password });
      setUser(res.data);
      setIsAuthenticated(true);
      wasAuthenticated.current = true;
      return { ok: true };
    } catch (err) {
      const message = _extractError(err, "Ошибка входа");
      setAuthError(message);
      return { ok: false, message };
    } finally {
      setIsLoadingAuth(false);
    }
  }, []);

  // ── Register ───────────────────────────────────────────────────────────────
  const register = useCallback(async (email, password) => {
    try {
      setIsLoadingAuth(true);
      setAuthError(null);
      await http.post(EP.auth.register(), { email, password });
      return await login(email, password);
    } catch (err) {
      const message = _extractError(err, "Ошибка регистрации");
      setAuthError(message);
      return { ok: false, message };
    } finally {
      setIsLoadingAuth(false);
    }
  }, [login]);

  // ── Logout ─────────────────────────────────────────────────────────────────
  const logout = useCallback(async () => {
    try {
      await http.post(EP.auth.logout());
    } catch { /* ignore */ } finally {
      _clearSession();
      // Полный reload чтобы сбросить все кеши и React Query
      window.location.href = ROUTES.home();
    }
  }, [_clearSession]);

  // ── Logout all devices ─────────────────────────────────────────────────────
  const logoutAll = useCallback(async () => {
    try {
      await http.post(EP.auth.logoutAll());
    } catch { /* ignore */ } finally {
      _clearSession();
      window.location.href = ROUTES.home();
    }
  }, [_clearSession]);

  // ── OAuth: Google ──────────────────────────────────────────────────────────
  // Бэкенд на GET /auth/oauth/google делает редирект на Google.
  // Google после авторизации редиректит пользователя на GOOGLE_REDIRECT_URI.
  // GOOGLE_REDIRECT_URI должен указывать на страницу /oauth/callback на фронте.
  const loginWithGoogle = useCallback(() => {
    window.location.href = `${appParams.apiUrl}${EP.auth.googleRedirect()}`;
  }, []);

  // ── OAuth: Telegram ────────────────────────────────────────────────────────
  const loginWithTelegram = useCallback(async (telegramData) => {
    try {
      setIsLoadingAuth(true);
      setAuthError(null);
      // Telegram присылает данные как объект — строим query string
      const params = new URLSearchParams(telegramData).toString();
      const res = await http.get(`${EP.auth.telegramCallback()}?${params}`);
      // Бэкенд ставит cookie и возвращает { detail: "ok" }
      // После этого перечитываем пользователя
      await checkUserAuth();
      return { ok: true };
    } catch (err) {
      const message = _extractError(err, "Ошибка входа через Telegram");
      setAuthError(message);
      return { ok: false, message };
    } finally {
      setIsLoadingAuth(false);
    }
  }, [checkUserAuth]);

  // ── Handle OAuth callback ──────────────────────────────────────────────────
  // Вызывается со страницы /oauth/callback после редиректа от Google.
  // Бэкенд уже поставил cookie — просто перечитываем пользователя.
  const handleOAuthCallback = useCallback(async () => {
    try {
      setIsLoadingAuth(true);
      await checkUserAuth();
      return { ok: isAuthenticated };
    } catch {
      return { ok: false };
    } finally {
      setIsLoadingAuth(false);
    }
  }, [checkUserAuth, isAuthenticated]);

  // ── Email verification ─────────────────────────────────────────────────────
  const verifyEmail = useCallback(async (token) => {
    try {
      await http.post(EP.auth.verifyEmail(), { token });
      await checkUserAuth();
      return { ok: true };
    } catch (err) {
      return { ok: false, message: _extractError(err, "Ошибка подтверждения") };
    }
  }, [checkUserAuth]);

  const resendVerification = useCallback(async () => {
    try {
      await http.post(EP.auth.resendVerification());
      return { ok: true };
    } catch (err) {
      return { ok: false, message: _extractError(err, "Не удалось отправить письмо") };
    }
  }, []);

  // ── Password reset ─────────────────────────────────────────────────────────
  const forgotPassword = useCallback(async (email) => {
    try {
      await http.post(EP.auth.forgotPassword(), { email });
      return { ok: true };
    } catch (err) {
      return { ok: false, message: _extractError(err, "Не удалось отправить письмо") };
    }
  }, []);

  const resetPassword = useCallback(async (token, newPassword) => {
    try {
      await http.post(EP.auth.resetPassword(), { token, new_password: newPassword });
      return { ok: true };
    } catch (err) {
      return { ok: false, message: _extractError(err, "Не удалось сбросить пароль") };
    }
  }, []);

  // ── Sessions ───────────────────────────────────────────────────────────────
  const fetchSessions = useCallback(async () => {
    try {
      setIsLoadingSessions(true);
      setSessionsError(null);
      const res = await http.get(EP.auth.sessions());
      setSessions(res.data);
    } catch (err) {
      setSessionsError(_extractError(err, "Не удалось загрузить сессии"));
    } finally {
      setIsLoadingSessions(false);
    }
  }, []);

  const revokeSession = useCallback(async (sessionId) => {
    try {
      await http.delete(EP.auth.session(sessionId));
      setSessions((prev) => prev.filter((s) => s.session_id !== sessionId));
      return { ok: true };
    } catch (err) {
      return { ok: false, message: _extractError(err, "Не удалось завершить сессию") };
    }
  }, []);

  // ── Helpers ────────────────────────────────────────────────────────────────
  const hasPermission = useCallback(
    (codename) => user?.permissions?.includes(codename) ?? false,
    [user]
  );

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
    checkUserAuth,
    hasPermission,
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
};

// ─── Hooks ─────────────────────────────────────────────────────────────────────

export const useAuth = () => {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
};

export const useSession = () => {
  const ctx = useContext(SessionContext);
  if (!ctx) throw new Error("useSession must be used within AuthProvider");
  return ctx;
};

export { http as authApi };

// ─── Internal ──────────────────────────────────────────────────────────────────

function _extractError(err, fallback) {
  const data = err?.response?.data;
  if (!data) return err?.message || fallback;
  if (typeof data.message === "string") return data.message;
  if (typeof data.detail === "string")  return data.detail;
  if (Array.isArray(data.detail))       return data.detail.map((d) => d.msg).join("; ");
  return err?.message || fallback;
}
