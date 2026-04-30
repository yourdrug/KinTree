/**
 * client/src/lib/AuthContext.jsx
 *
 * Cookie-based авторизация.
 * - Токены хранятся в httpOnly-куках (бэкенд их ставит / удаляет)
 * - Фронт НИКОГДА не видит и не хранит access/refresh токены
 * - При старте: GET /auth/cookie/me — если кука жива, юзер восстанавливается
 * - axios автоматически отправляет куки при withCredentials: true
 * - При 401 — один тихий retry через POST /auth/cookie/refresh
 */

import React, {
  createContext,
  useState,
  useContext,
  useEffect,
  useRef,
  useCallback,
} from "react";
import axios from "axios";
import { appParams } from "@/lib/app-params";

// ─── Axios instance ────────────────────────────────────────────────────────────

const api = axios.create({
  baseURL: appParams.apiUrl,
  withCredentials: true, // ← куки идут с каждым запросом автоматически
});

// ─── Silent refresh ────────────────────────────────────────────────────────────
// Если бэкенд вернул 401 — один раз пробуем обновить токен через куку.
// Если refresh тоже упал — разлогиниваем.

let _isRefreshing = false;
let _refreshQueue = []; // очередь запросов, ждущих пока refresh завершится

function _processQueue(error) {
  _refreshQueue.forEach((p) => (error ? p.reject(error) : p.resolve()));
  _refreshQueue = [];
}

// authLogout хранится в ref чтобы интерцептор мог его вызвать
// без захвата устаревшего closure
const _logoutRef = { current: null };

api.interceptors.response.use(
  (res) => res,
  async (err) => {
    const original = err.config;

    if (
      err.response?.status === 401 &&
      !original._retry &&
      !original.url?.includes("/auth/cookie/refresh") &&
      !original.url?.includes("/auth/cookie/login")
    ) {
      original._retry = true;

      if (_isRefreshing) {
        // Уже рефрешим — ставим в очередь
        return new Promise((resolve, reject) => {
          _refreshQueue.push({ resolve, reject });
        }).then(() => api(original));
      }

      _isRefreshing = true;

      try {
        await api.post("/auth/cookie/refresh");
        _processQueue(null);
        return api(original); // повторяем исходный запрос
      } catch (refreshErr) {
        _processQueue(refreshErr);
        _logoutRef.current?.(); // разлогиниваем
        return Promise.reject(refreshErr);
      } finally {
        _isRefreshing = false;
      }
    }

    return Promise.reject(err);
  }
);

// ─── Context ───────────────────────────────────────────────────────────────────

const AuthContext = createContext();

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);          // AccountResponse | null
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [isLoadingAuth, setIsLoadingAuth] = useState(true);
  const [authError, setAuthError] = useState(null);

  // ── Внутренний logout (без редиректа) ─────────────────────────────────────
  const _clearSession = useCallback(() => {
    setUser(null);
    setIsAuthenticated(false);
  }, []);

  // Регистрируем в ref для интерцептора
  useEffect(() => {
    _logoutRef.current = _clearSession;
  }, [_clearSession]);

  // ── Автологин при старте / рефреше страницы ───────────────────────────────
  const checkUserAuth = useCallback(async () => {
    try {
      setIsLoadingAuth(true);
      // access_token кука жива → получаем профиль
      const res = await api.get("/auth/cookie/me");
      setUser(res.data);
      setIsAuthenticated(true);
    } catch {
      // access_token протух → интерцептор уже попробовал refresh
      // Если и refresh упал — _clearSession вызван из интерцептора
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

      // Бэкенд ставит куки и возвращает AccountResponse (без токенов)
      const res = await api.post("/auth/cookie/login", { email, password });

      setUser(res.data);
      setIsAuthenticated(true);
      return { ok: true };
    } catch (err) {
      const message =
        err.response?.data?.detail || err.message || "Login failed";
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

      await api.post("/auth/cookie/register", { email, password });
      // После регистрации сразу логиним
      return await login(email, password);
    } catch (err) {
      const detail = err.response?.data?.detail;
      const message =
        typeof detail === "string"
          ? detail
          : Array.isArray(detail)
          ? detail.map((d) => d.msg).join("; ")
          : "Registration failed";

      setAuthError(message);
      return { ok: false, message };
    } finally {
      setIsLoadingAuth(false);
    }
  }, [login]);

  // ── Logout ─────────────────────────────────────────────────────────────────
  const logout = useCallback(async () => {
    try {
      // Бэкенд инвалидирует refresh-токен и удаляет куки
      await api.post("/auth/cookie/logout");
    } catch {
      // Даже если запрос упал — чистим состояние на фронте
    } finally {
      _clearSession();
      window.location.href = "/";
    }
  }, [_clearSession]);

  // ── Helpers ────────────────────────────────────────────────────────────────
  const navigateToLogin = useCallback(() => {
    window.location.href = "/login";
  }, []);

  /**
   * Проверить, есть ли у пользователя право.
   * Permissions приходят в TokenResponse и хранятся в user.permissions.
   * @param {string} codename  напр. "family:create"
   */
  const hasPermission = useCallback(
    (codename) => user?.permissions?.includes(codename) ?? false,
    [user]
  );

  return (
    <AuthContext.Provider
      value={{
        user,
        isAuthenticated,
        isLoadingAuth,
        authError,
        login,
        register,
        logout,
        navigateToLogin,
        checkUserAuth,
        hasPermission,
        // Экспортируем api-инстанс чтобы другие модули могли его переиспользовать
        api,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within AuthProvider");
  }
  return context;
};

/**
 * Экспортируем api отдельно — для использования в api/index.js
 * вместо создания нового инстанса там.
 * Так интерцептор с auto-refresh будет работать для всех запросов.
 */
export { api as authApi };