/**
 * lib/routes.js
 */

export const ROUTES = {
  home:           () => "/",
  login:          () => "/login",
  explore:        () => "/explore",
  forgotPassword: () => "/forgot-password",
  resetPassword:  () => "/reset-password",
  verifyEmail:    () => "/verify-email",
  oauthCallback:  () => "/oauth/callback",

  dashboard: () => "/dashboard",
  tree:      (familyId) => `/tree/${familyId}`,

  settings: {
    root:     () => "/settings",
    sessions: () => "/settings/sessions",
    profile:  () => "/settings/profile",
  },
};
