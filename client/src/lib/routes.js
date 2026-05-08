/**
 * lib/routes.js
 */

export const ROUTES = {
  // ── Public ──────────────────────────────────────────────────────────────────
  home:          () => "/",
  login:         () => "/login",
  explore:       () => "/explore",
  forgotPassword:() => "/forgot-password",
  resetPassword: () => "/reset-password",   // ?token=...
  verifyEmail:   () => "/verify-email",     // ?token=...

  // ── Protected ────────────────────────────────────────────────────────────────
  dashboard: () => "/dashboard",
  tree:      (familyId) => `/tree/${familyId}`,

  // ── Settings ─────────────────────────────────────────────────────────────────
  settings: {
    root:     () => "/settings",
    sessions: () => "/settings/sessions",
    profile:  () => "/settings/profile",
  },
};

export const PROTECTED_PATHS = [
  ROUTES.dashboard(),
  ROUTES.tree(":id"),
  ROUTES.settings.root(),
  ROUTES.settings.sessions(),
  ROUTES.settings.profile(),
];
