/**
 * api/auth.js
 *
 * Все API-вызовы связанные с аутентификацией.
 * Использует единственный http-клиент из api/http.js.
 */

import { http, extractErrorMessage } from "./http";
import { ENDPOINTS as EP } from "./endpoints";

/**
 * Обёртка для безопасного вызова API.
 * Возвращает { ok: true, data } или { ok: false, message }.
 */
async function safeCall(fn, fallback) {
  try {
    const res = await fn();
    return { ok: true, data: res.data };
  } catch (error) {
    return { ok: false, message: extractErrorMessage(error, fallback) };
  }
}

export const authApi = {
  /** Получить текущего пользователя */
  me: () => http.get(EP.auth.me()),

  /** Войти через email/password */
  login: (email, password) =>
    safeCall(
      () => http.post(EP.auth.login(), { email, password }),
      "Ошибка входа"
    ),

  /** Зарегистрироваться */
  register: (email, password) =>
    safeCall(
      () => http.post(EP.auth.register(), { email, password }),
      "Ошибка регистрации"
    ),

  /** Выйти из текущей сессии */
  logout: () => http.post(EP.auth.logout()).catch(() => {}),

  /** Выйти из всех сессий */
  logoutAll: () => http.post(EP.auth.logoutAll()).catch(() => {}),

  /** Подтвердить email */
  verifyEmail: (token) =>
    safeCall(
      () => http.post(EP.auth.verifyEmail(), { token }),
      "Ошибка подтверждения"
    ),

  /** Повторно отправить письмо подтверждения */
  resendVerification: () =>
    safeCall(
      () => http.post(EP.auth.resendVerification()),
      "Не удалось отправить письмо"
    ),

  /** Запросить сброс пароля */
  forgotPassword: (email) =>
    safeCall(
      () => http.post(EP.auth.forgotPassword(), { email }),
      "Не удалось отправить письмо"
    ),

  /** Установить новый пароль */
  resetPassword: (token, newPassword) =>
    safeCall(
      () => http.post(EP.auth.resetPassword(), { token, new_password: newPassword }),
      "Не удалось сбросить пароль"
    ),

  /** Войти через Google (редирект) */
  loginWithGoogle: () => {
    window.location.href = `${import.meta.env.VITE_API_URL ?? ""}${EP.auth.googleRedirect()}`;
  },

  /** Войти через Telegram */
  loginWithTelegram: (telegramData) =>
    safeCall(
      () => http.get(`${EP.auth.telegramCallback()}?${new URLSearchParams(telegramData)}`),
      "Ошибка входа через Telegram"
    ),

  /** Получить список активных сессий */
  getSessions: () =>
    http.get(EP.auth.sessions()).then((r) => r.data),

  /** Завершить сессию по ID */
  revokeSession: (sessionId) =>
    safeCall(
      () => http.delete(EP.auth.session(sessionId)),
      "Не удалось завершить сессию"
    ),
};
