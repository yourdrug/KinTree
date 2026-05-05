/**
 * lib/routes.js
 *
 * Единственный источник правды для всех маршрутов приложения.
 *
 * Правила:
 *  - Каждый маршрут — функция, даже без параметров. Это даёт
 *    единообразный вызов: ROUTES.login() вместо ROUTES.login
 *  - Параметры явные — TypeScript подсветит если забыл передать id
 *  - Для навигации использовать useAppNavigate() из lib/navigation.js,
 *    не window.location.href (кроме logout — там нужен полный сброс)
 *
 * Использование:
 *   import { ROUTES } from "@/lib/routes";
 *
 *   <Link to={ROUTES.tree(family.id)}>...</Link>
 *   navigate(ROUTES.settings.sessions())
 */

export const ROUTES = {
  // ── Public ──────────────────────────────────────────────────────────────────
  home:    () => "/",
  login:   () => "/login",
  explore: () => "/explore",

  // ── Protected ────────────────────────────────────────────────────────────────
  dashboard: () => "/dashboard",

  /** Просмотр / редактирование конкретного дерева */
  tree: (familyId) => `/tree/${familyId}`,

  // ── Settings (вложенные) ─────────────────────────────────────────────────────
  settings: {
    /** Корень настроек — можно использовать как index */
    root:     () => "/settings",
    sessions: () => "/settings/sessions",
    profile:  () => "/settings/profile",
  },
};

/**
 * Все защищённые маршруты для ProtectedRoute.
 * Если маршрут есть здесь — компонент требует авторизации.
 */
export const PROTECTED_PATHS = [
  ROUTES.dashboard(),
  ROUTES.tree(":id"),
  ROUTES.settings.root(),
  ROUTES.settings.sessions(),
  ROUTES.settings.profile(),
];
