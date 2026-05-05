/**
 * lib/navigation.js
 *
 * Обёртка над react-router useNavigate.
 * Даёт типобезопасную навигацию через ROUTES без прямых строк.
 *
 * Использование:
 *   const nav = useAppNavigate();
 *
 *   nav.toLogin()
 *   nav.toDashboard()
 *   nav.toTree(familyId)
 *   nav.toSessions()
 *   nav.back()
 *
 * Почему не просто useNavigate + ROUTES напрямую?
 *   - Централизует опции (replace, state) для каждого перехода
 *   - После логина делаем replace чтобы кнопка «назад» не вела на /login
 *   - Меньше шанс забыть { replace: true } в нужных местах
 *
 * ИСКЛЮЧЕНИЕ: logout использует window.location.href = ROUTES.home()
 * для полного сброса React-состояния, кешей и query client.
 * Это сознательное решение, не баг.
 */

import { useNavigate } from "react-router-dom";
import { ROUTES } from "@/lib/routes";

export function useAppNavigate() {
  const navigate = useNavigate();

  return {
    // ── Public ─────────────────────────────────────────────────────────────
    toHome:    (opts) => navigate(ROUTES.home(),    opts),
    toLogin:   (opts) => navigate(ROUTES.login(),   opts),
    toExplore: (opts) => navigate(ROUTES.explore(), opts),

    // ── После успешного логина — replace чтобы не вернуться на /login ────
    afterLogin: () => navigate(ROUTES.dashboard(), { replace: true }),

    // ── Protected ───────────────────────────────────────────────────────────
    toDashboard: (opts) => navigate(ROUTES.dashboard(), opts),
    toTree:  (familyId, opts) => navigate(ROUTES.tree(familyId), opts),

    // ── Settings ────────────────────────────────────────────────────────────
    toSettings:  (opts) => navigate(ROUTES.settings.root(),     opts),
    toSessions:  (opts) => navigate(ROUTES.settings.sessions(), opts),
    toProfile:   (opts) => navigate(ROUTES.settings.profile(),  opts),

    // ── Утилиты ─────────────────────────────────────────────────────────────
    back: () => navigate(-1),

    /**
     * Редирект на логин с сохранением текущего пути.
     * После логина можно восстановить: location.state?.from
     */
    toLoginFrom: (currentPath) =>
      navigate(ROUTES.login(), { state: { from: currentPath } }),
  };
}
