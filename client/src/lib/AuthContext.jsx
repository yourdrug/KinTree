/**
 * lib/AuthContext.jsx
 *
 * Cookie-based аутентификация.
 * Axios instance и интерцептор живут в api/client.js — не здесь.
 * URL эндпоинтов — в api/endpoints.js — не здесь.
 *
 * Этот файл отвечает только за:
 *  - React-состояние аутентификации (user, isAuthenticated, ...)
 *  - Методы login / register / logout / logoutAll
 *  - Управление сессиями через useSession()
 *  - Регистрацию _logoutRef для интерцептора
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

  // Регистрируем callback для интерцептора в api/client.js
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
  // window.location.href — сознательный выбор: полный сброс React + query cache
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

// ─── Re-export http для обратной совместимости (api/index.js использует его) ──
export { http as authApi };

// ─── Internal ──────────────────────────────────────────────────────────────────

function _extractError(err, fallback) {
  const detail = err.response?.data?.detail;
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) return detail.map((d) => d.msg).join("; ");
  return err.message || fallback;
}
