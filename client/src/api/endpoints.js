/**
 * api/endpoints.js
 *
 * Единственный источник правды для всех API URL.
 *
 * Правила:
 *  - Каждый эндпоинт — функция, параметры явные
 *  - Функции возвращают только строки — без axios, без логики
 *  - Реальные вызовы живут в api/index.js
 *
 * Использование:
 *   import { ENDPOINTS as EP } from "@/api/endpoints";
 *
 *   http.get(EP.families.get(id))
 *   http.post(EP.auth.login())
 */

export const ENDPOINTS = {
  // ── Auth (cookie-based) ───────────────────────────────────────────────────
  auth: {
    me:        () => "/auth/cookie/me",
    login:     () => "/auth/cookie/login",
    register:  () => "/auth/cookie/register",
    logout:    () => "/auth/cookie/logout",
    logoutAll: () => "/auth/cookie/logout-all",
    refresh:   () => "/auth/cookie/refresh",
    sessions:  () => "/auth/cookie/sessions",
    session:   (sessionId) => `/auth/cookie/sessions/${sessionId}`,
  },

  // ── Families ──────────────────────────────────────────────────────────────
  families: {
    list:   ()   => "/families/",
    get:    (id) => `/families/${id}`,
    create: ()   => "/families/",
    update: (id) => `/families/${id}`,
    patch:  (id) => `/families/${id}`,
    delete: (id) => `/families/${id}`,
  },

  // ── Persons ───────────────────────────────────────────────────────────────
  persons: {
    list:   ()   => "/persons/",
    get:    (id) => `/persons/${id}`,
    create: ()   => "/persons/",
    update: (id) => `/persons/${id}`,
    patch:  (id) => `/persons/${id}`,
    delete: (id) => `/persons/${id}`,
  },

  // ── Relations ─────────────────────────────────────────────────────────────
  relations: {
    graph:        (familyId) => `/relations/graph/${familyId}`,

    parentChild:        ()                   => "/relations/parent-child",
    removeParentChild:  (parentId, childId)  => `/relations/parent-child/${parentId}/${childId}`,

    spouses:      ()           => "/relations/spouses",
    divorce:      ()           => "/relations/spouses/divorce",
    removeSpouse: (idA, idB)   => `/relations/spouses/${idA}/${idB}`,
  },
};
