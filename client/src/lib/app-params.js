/**
 * lib/app-params.js
 *
 * Параметры приложения.
 * Токены не хранятся нигде на клиенте — только httpOnly-куки на сервере.
 */

export const appParams = {
  apiUrl: import.meta.env.VITE_API_URL || "http://localhost:8000",
};
