/**
 * api/endpoints.js
 *
 * Единственный источник правды для всех API URL.
 */

export const ENDPOINTS = {
  // ── Auth (cookie-based) ───────────────────────────────────────────────────
  auth: {
    me:                 () => "/account/me",
    login:              () => "/auth/cookie/login",
    register:           () => "/auth/register",
    logout:             () => "/auth/cookie/logout",
    logoutAll:          () => "/auth/cookie/logout-all",
    refresh:            () => "/auth/cookie/refresh",
    sessions:           () => "/auth/sessions",
    session:            (sessionId) => `/auth/sessions/${sessionId}`,

    // Email verification & password reset
    verifyEmail:        () => "/auth/verify-email",
    resendVerification: () => "/auth/resend-verification",
    forgotPassword:     () => "/auth/forgot-password",
    resetPassword:      () => "/account/reset-password",

    // OAuth — Google: бэкенд сам делает редирект на Google consent screen
    googleRedirect:     () => "/auth/oauth/google",
    // После Google редиректит обратно на фронт /oauth/callback?code=...
    // Фронт делает GET на этот эндпоинт с code из URL
    googleCallback:     () => "/auth/oauth/google/callback",

    // Telegram: GET с параметрами от виджета
    telegramCallback:   () => "/auth/oauth/cookie/telegram/callback",
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
    graph:             (familyId)          => `/relations/family-graph/${familyId}`,
    parentChild:       ()                  => "/relations/parent-child",
    removeParentChild: (parentId, childId) => `/relations/parent-child/${parentId}/${childId}`,
    spouses:           ()                  => "/relations/spouses",
    divorce:           ()                  => "/relations/spouses/divorce",
    removeSpouse:      (idA, idB)          => `/relations/spouses/${idA}/${idB}`,
  },
};
