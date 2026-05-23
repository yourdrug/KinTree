/**
 * api/http.js
 *
 * Единственный HTTP-клиент приложения.
 *
 * Особенности:
 * - Один axios instance для всего приложения
 * - Silent refresh с очередью параллельных запросов
 * - Поддержка ротации refresh-токенов (бэкенд может вернуть новый refresh в Set-Cookie)
 * - Различает "начальный" вызов /me (старт приложения) и повторные вызовы
 * - Вызывает onUnauthenticated() при окончательном провале refresh
 *
 * Поток при 401:
 *   1. Запрос → 401
 *   2. Если не refresh/login — ставим в очередь, делаем POST /auth/cookie/refresh
 *   3. Бэкенд обновляет куки (в т.ч. refresh при ротации) и отвечает 200
 *   4. Повторяем все запросы из очереди с оригинальными параметрами
 *   5. Если refresh → 401 — вызываем onUnauthenticated() и отклоняем все запросы
 *
 * Ротация refresh-токенов обрабатывается автоматически браузером через Set-Cookie.
 * Никакой ручной работы с токенами не требуется — всё через httpOnly куки.
 */

import axios from "axios";
import { ENDPOINTS } from "./endpoints";

// ── Callbacks ──────────────────────────────────────────────────────────────────
// Устанавливаются из AuthProvider при монтировании.
// Используем объект (не ref) чтобы не было циклических зависимостей.

export const authCallbacks = {
  /** Вызывается когда пользователь окончательно разлогинен (refresh не помог) */
  onUnauthenticated: null,
};

// ── Refresh state ──────────────────────────────────────────────────────────────

let isRefreshing = false;
let refreshQueue = []; // { resolve, reject }[]

function resolveQueue() {
  refreshQueue.forEach(({ resolve }) => resolve());
  refreshQueue = [];
}

function rejectQueue(error) {
  refreshQueue.forEach(({ reject }) => reject(error));
  refreshQueue = [];
}

// ── Initial-me flag ────────────────────────────────────────────────────────────
// При первом старте приложения вызов /me с 401 означает "не залогинен",
// а не "токен истёк" — refresh делать не нужно.

export const meCallState = { isInitial: false };

// ── Axios instance ─────────────────────────────────────────────────────────────

export const http = axios.create({
  baseURL: import.meta.env.VITE_API_URL ?? "",
  withCredentials: true,       // всегда отправляем куки
  timeout: 15_000,
});

// ── Response interceptor ───────────────────────────────────────────────────────

http.interceptors.response.use(
  (response) => response,

  async (error) => {
    const original = error.config;
    const status   = error.response?.status;
    const url      = original?.url ?? "";

    // Пропускаем refresh для служебных эндпоинтов
    const isAuthEndpoint =
      url.includes(ENDPOINTS.auth.refresh()) ||
      url.includes(ENDPOINTS.auth.login());

    // Пропускаем refresh для начального вызова /me (пользователь не залогинен)
    const isInitialMeCheck =
      url.includes(ENDPOINTS.auth.me()) && meCallState.isInitial;

    // Условия для пропуска refresh
    if (
      status !== 401 ||
      original._retry ||      // уже пробовали refresh для этого запроса
      isAuthEndpoint ||
      isInitialMeCheck
    ) {
      return Promise.reject(error);
    }

    // Помечаем запрос чтобы не попасть в бесконечный цикл
    original._retry = true;

    // Если refresh уже идёт — ставим в очередь
    if (isRefreshing) {
      return new Promise((resolve, reject) => {
        refreshQueue.push({ resolve, reject });
      }).then(() => http(original));
    }

    // Запускаем refresh
    isRefreshing = true;

    try {
      // POST /auth/cookie/refresh
      // Бэкенд обновляет access-токен (и refresh при ротации) через Set-Cookie.
      // Никаких токенов в теле ответа — всё прозрачно через куки.
      await http.post(ENDPOINTS.auth.refresh());

      resolveQueue();
      return http(original);
    } catch (refreshError) {
      rejectQueue(refreshError);

      // Вызываем колбэк только если он зарегистрирован
      // (пользователь был залогинен и теперь разлогинен)
      authCallbacks.onUnauthenticated?.();

      return Promise.reject(refreshError);
    } finally {
      isRefreshing = false;
    }
  }
);

// ── Error normalization ────────────────────────────────────────────────────────

/**
 * Извлекает читаемое сообщение об ошибке из ответа API.
 */
export function extractErrorMessage(error, fallback = "Произошла ошибка") {
  const data = error?.response?.data;
  if (!data) return error?.message || fallback;
  if (typeof data.message === "string") return data.message;
  if (typeof data.detail  === "string") return data.detail;
  if (Array.isArray(data.detail))       return data.detail.map((d) => d.msg).join("; ");
  return error?.message || fallback;
}
