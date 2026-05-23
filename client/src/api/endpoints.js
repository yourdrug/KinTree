/**
 * api/endpoints.js
 *
 * Единственный источник правды для всех API URL.
 * Импортируется из http.js и всех api-модулей.
 */

export const ENDPOINTS = {
  auth: {
    me:                 () => "/account/me",
    login:              () => "/auth/cookie/login",
    register:           () => "/auth/register",
    logout:             () => "/auth/cookie/logout",
    logoutAll:          () => "/auth/cookie/logout-all",
    refresh:            () => "/auth/cookie/refresh",
    sessions:           () => "/auth/sessions",
    session:            (id) => `/auth/sessions/${id}`,
    verifyEmail:        () => "/auth/verify-email",
    resendVerification: () => "/auth/resend-verification",
    forgotPassword:     () => "/auth/forgot-password",
    resetPassword:      () => "/account/reset-password",
    googleRedirect:     () => "/auth/oauth/google",
    telegramCallback:   () => "/auth/oauth/cookie/telegram/callback",
  },

  families: {
    list:   ()    => "/families/",
    detail: (id)  => `/families/${id}`,
    create: ()    => "/families/",
    patch:  (id)  => `/families/${id}`,
    delete: (id)  => `/families/${id}`,
  },

  persons: {
    list:   ()    => "/persons/",
    detail: (id)  => `/persons/${id}`,
    create: ()    => "/persons/",
    patch:  (id)  => `/persons/${id}`,
    delete: (id)  => `/persons/${id}`,
  },

  relations: {
    graph:             (familyId)            => `/relations/family-graph/${familyId}`,
    addParentChild:    ()                    => "/relations/parent-child",
    removeParentChild: (parentId, childId)   => `/relations/parent-child/${parentId}/${childId}`,
    addSpouse:         ()                    => "/relations/spouse",
    removeSpouse:      (idA, idB)            => `/relations/spouse/${idA}/${idB}`,
  },
};
