/**
 * lib/navigation.js
 *
 * Типизированные хелперы навигации.
 * Централизует replace/state опции — не надо помнить про { replace: true } на каждой странице.
 */

import { useNavigate } from "react-router-dom";
import { ROUTES } from "@/lib/routes";

export function useAppNavigate() {
  const navigate = useNavigate();

  return {
    toHome:      (opts) => navigate(ROUTES.home(),      opts),
    toLogin:     (opts) => navigate(ROUTES.login(),     opts),
    toExplore:   (opts) => navigate(ROUTES.explore(),   opts),
    toDashboard: (opts) => navigate(ROUTES.dashboard(), opts),
    toTree:      (id, opts) => navigate(ROUTES.tree(id), opts),
    toSettings:  (opts) => navigate(ROUTES.settings.root(),     opts),
    toSessions:  (opts) => navigate(ROUTES.settings.sessions(), opts),
    toProfile:   (opts) => navigate(ROUTES.settings.profile(),  opts),

    // После успешного логина — replace чтобы не вернуться на /login
    afterLogin: () => navigate(ROUTES.dashboard(), { replace: true }),

    // Редирект на логин с сохранением текущего пути
    toLoginFrom: (currentPath) =>
      navigate(ROUTES.login(), { state: { from: currentPath } }),

    back: () => navigate(-1),
  };
}
