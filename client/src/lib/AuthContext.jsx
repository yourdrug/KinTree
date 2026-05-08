/**
 * lib/AuthContext.jsx
 */

import React, {
  createContext,
  useState,
  useContext,
  useEffect,
  useCallback,
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
  const [isLoadingAuth,   setIsLoadingAuth]   = useState(true);
  const [authError,       setAuthError]       = useState(null);

  const [sessions,          setSessions]          = useState([]);
  const [isLoadingSessions, setIsLoadingSessions] = useState(false);
  const [sessionsError,     setSessionsError]     = useState(null);

  // ── Internal clear ─────────────────────────────────────────────────────────
  const _clearSession = useCallback(() => {
    setUser(null);
    setIsAuthenticated(false);
    setSessions([]);
  }, []);

  useEffect(() => {
    _logoutRef.current = _clearSession;
  }, [_clearSession]);

  // ── Restore on mount ───────────────────────────────────────────────────────
  const checkUserAuth = useCallback(async () => {
    try {
      setIsLoadingAuth(true);
      const res = await http.get(EP.auth.me());
      setUser(res.data);
      setIsAuthenticated(true);
    } catch {
      _clearSession();
    } finally {
      setIsLoadingAuth(false);
    }
  }, [_clearSession]);

  useEffect(() => {
    checkUserAuth();
  }, [checkUserAuth]);

  // ── Login ──────────────────────────────────────────────────────────────────
  const login = useCallback(async (email, password) => {
    try {
      setIsLoadingAuth(true);
      setAuthError(null);
      const res = await http.post(EP.auth.login(), { email, password });
      setUser(res.data);
      setIsAuthenticated(true);
      return { ok: true };
    } catch (err) {
      const message = _extractError(err, "Login failed");
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
      const message = _extractError(err, "Registration failed");
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
  // Редирект на Google через бэкенд — бэкенд сам формирует consent URL
  const loginWithGoogle = useCallback(() => {
    window.location.href = `${appParams.apiUrl}/auth/oauth/google`;
  }, []);

  // ── OAuth: Telegram ────────────────────────────────────────────────────────
  // Telegram Login Widget вызывает этот callback с данными пользователя
  const loginWithTelegram = useCallback(async (telegramData) => {
    try {
      setIsLoadingAuth(true);
      setAuthError(null);
      const params = new URLSearchParams(telegramData).toString();
      const res = await http.get(`${EP.auth.telegramCallback()}?${params}`);
      setUser(res.data);
      setIsAuthenticated(true);
      return { ok: true };
    } catch (err) {
      const message = _extractError(err, "Telegram login failed");
      setAuthError(message);
      return { ok: false, message };
    } finally {
      setIsLoadingAuth(false);
    }
  }, []);

  // ── Handle OAuth redirect result (вызывается на странице /oauth/callback) ──
  // После редиректа от Google бэкенд ставит cookie — нужно только обновить user
  const handleOAuthCallback = useCallback(async () => {
    await checkUserAuth();
  }, [checkUserAuth]);

  // ── Email verification ─────────────────────────────────────────────────────
  const verifyEmail = useCallback(async (token) => {
    try {
      await http.post(EP.auth.verifyEmail(), { token });
      // Обновляем user — is_verified изменился
      await checkUserAuth();
      return { ok: true };
    } catch (err) {
      return { ok: false, message: _extractError(err, "Verification failed") };
    }
  }, [checkUserAuth]);

  const resendVerification = useCallback(async () => {
    try {
      await http.post(EP.auth.resendVerification());
      return { ok: true };
    } catch (err) {
      return { ok: false, message: _extractError(err, "Failed to resend") };
    }
  }, []);

  // ── Password reset ─────────────────────────────────────────────────────────
  const forgotPassword = useCallback(async (email) => {
    try {
      await http.post(EP.auth.forgotPassword(), { email });
      return { ok: true };
    } catch (err) {
      return { ok: false, message: _extractError(err, "Failed to send reset email") };
    }
  }, []);

  const resetPassword = useCallback(async (token, newPassword) => {
    try {
      await http.post(EP.auth.resetPassword(), { token, new_password: newPassword });
      return { ok: true };
    } catch (err) {
      return { ok: false, message: _extractError(err, "Failed to reset password") };
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
      setSessionsError(_extractError(err, "Failed to load sessions"));
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
      return { ok: false, message: _extractError(err, "Failed to revoke session") };
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
  const data = err.response?.data;
  if (typeof data?.message === "string") return data.message;
  if (typeof data?.detail === "string") return data.detail;
  if (Array.isArray(data?.detail)) return data.detail.map((d) => d.msg).join("; ");
  return err.message || fallback;
}
