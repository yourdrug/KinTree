/**
 * api/client.js
 *
 * Axios instance с silent-refresh интерцептором.
 *
 * Поток при 401:
 *  1. Запрос вернул 401
 *  2. Если это не /refresh и не /login — пробуем тихий refresh
 *  3. Параллельные 401 ставятся в очередь, refresh делается один раз
 *  4. После успешного refresh — повторяем все запросы из очереди
 *  5. Если refresh тоже 401 — вызываем _logoutRef.current()
 *
 * ИСПРАВЛЕНИЕ:
 *  - /account/me больше не исключён из refresh глобально.
 *    Вместо этого AuthContext помечает "начальный" вызов /me через
 *    _meCallState.isInitial = true, чтобы при первом старте приложения
 *    401 не вызвал refresh (пользователь просто не залогинен).
 *    Все последующие вызовы /me (после логина, OAuth и т.д.)
 *    идут через refresh как обычно.
 *  - _logoutRef вызывается только если пользователь был залогинен.
 */

import axios from "axios";
import { appParams } from "@/lib/app-params";
import { ENDPOINTS as EP } from "@/api/endpoints";

export const http = axios.create({
  baseURL: appParams.apiUrl,
  withCredentials: true,
});

// ── Refresh queue ──────────────────────────────────────────────────────────────

let _isRefreshing = false;
let _refreshQueue = [];

function _processQueue(error) {
  _refreshQueue.forEach((p) => (error ? p.reject(error) : p.resolve()));
  _refreshQueue = [];
}

// Устанавливается из AuthContext после mount
export const _logoutRef = { current: null };

/**
 * Флаг: идёт ли прямо сейчас начальный вызов /account/me при старте приложения.
 * AuthContext устанавливает его в true перед checkUserAuth() при монтировании,
 * и сбрасывает в false сразу после завершения.
 *
 * Это нужно чтобы 401 на /me при первом старте (пользователь просто не залогинен)
 * не триггерил refresh. При всех последующих вызовах /me (после логина,
 * OAuth callback и т.д.) refresh работает как обычно.
 */
export const _meCallState = { isInitial: false };

// ── Interceptor ────────────────────────────────────────────────────────────────

http.interceptors.response.use(
  (res) => res,
  async (err) => {
    const original = err.config;
    const status   = err.response?.status;
    const url      = original?.url ?? "";

    // Эндпоинты, которые никогда не должны триггерить refresh —
    // они сами являются частью процесса аутентификации.
    const isHardSkipUrl =
      url.includes(EP.auth.refresh()) ||
      url.includes(EP.auth.login());

    // /account/me при начальной проверке (старт приложения) тоже пропускаем —
    // 401 здесь означает просто "не залогинен", а не "токен истёк".
    const isInitialMeCall =
      url.includes(EP.auth.me()) && _meCallState.isInitial;

    if (status !== 401 || original._retry || isHardSkipUrl || isInitialMeCall) {
      return Promise.reject(err);
    }

    original._retry = true;

    if (_isRefreshing) {
      return new Promise((resolve, reject) => {
        _refreshQueue.push({ resolve, reject });
      }).then(() => http(original));
    }

    _isRefreshing = true;

    try {
      await http.post(EP.auth.refresh());
      _processQueue(null);
      return http(original);
    } catch (refreshErr) {
      _processQueue(refreshErr);
      // Вызываем logout только если пользователь был залогинен
      _logoutRef.current?.();
      return Promise.reject(refreshErr);
    } finally {
      _isRefreshing = false;
    }
  }
);
