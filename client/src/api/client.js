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
 * Важно: /account/me при первом запуске может вернуть 401 —
 * это НЕ должно вызывать logout (пользователь просто не залогинен).
 * Поэтому /account/me помечен как "auth endpoint" и не идёт через refresh.
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

// ── Interceptor ────────────────────────────────────────────────────────────────

http.interceptors.response.use(
  (res) => res,
  async (err) => {
    const original = err.config;
    const status   = err.response?.status;
    const url      = original?.url ?? "";

    // Эти эндпоинты не должны триггерить refresh — они сами про аутентификацию
    const isAuthUrl =
      url.includes(EP.auth.refresh()) ||
      url.includes(EP.auth.login())   ||
      url.includes(EP.auth.me());     // /account/me — начальная проверка

    if (status !== 401 || original._retry || isAuthUrl) {
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
      // (т.е. _logoutRef установлен и был активный пользователь)
      _logoutRef.current?.();
      return Promise.reject(refreshErr);
    } finally {
      _isRefreshing = false;
    }
  }
);
