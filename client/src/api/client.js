/**
 * api/client.js
 *
 * Axios instance с silent-refresh интерцептором.
 * Вынесен из AuthContext чтобы:
 *  - api/index.js мог импортировать его без циклических зависимостей
 *  - AuthContext импортировал только http, не создавал свой instance
 *
 * Поток при 401:
 *  1. Запрос вернул 401
 *  2. Если это не /refresh и не /login — пробуем тихий refresh
 *  3. Параллельные 401 ставятся в очередь, refresh делается один раз
 *  4. После успешного refresh — повторяем все запросы из очереди
 *  5. Если refresh тоже 401 — вызываем _logoutRef.current() (устанавливает AuthContext)
 */

import axios from "axios";
import { appParams } from "@/lib/app-params";
import { ENDPOINTS as EP } from "@/api/endpoints";

export const http = axios.create({
  baseURL: appParams.apiUrl,
  withCredentials: true, // куки идут с каждым запросом автоматически
});

// ── Refresh queue ──────────────────────────────────────────────────────────────

let _isRefreshing = false;
let _refreshQueue = [];

function _processQueue(error) {
  _refreshQueue.forEach((p) => (error ? p.reject(error) : p.resolve()));
  _refreshQueue = [];
}

// Устанавливается из AuthContext после mount
// Ref-паттерн: интерцептор не захватывает устаревший closure
export const _logoutRef = { current: null };

// ── Interceptor ────────────────────────────────────────────────────────────────

http.interceptors.response.use(
  (res) => res,
  async (err) => {
    const original = err.config;

    const isAuthEndpoint =
      original.url?.includes(EP.auth.refresh()) ||
      original.url?.includes(EP.auth.login());

    if (err.response?.status !== 401 || original._retry || isAuthEndpoint) {
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
      _logoutRef.current?.();
      return Promise.reject(refreshErr);
    } finally {
      _isRefreshing = false;
    }
  }
);
