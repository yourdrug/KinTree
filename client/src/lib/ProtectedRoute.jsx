/**
 * lib/ProtectedRoute.jsx
 *
 * Обёртка для защищённых маршрутов.
 *
 * Поведение:
 *  - isLoadingAuth  → спиннер (не редиректим пока не знаем статус)
 *  - !isAuthenticated → редирект на /login с сохранением текущего пути
 *  - isAuthenticated → рендерим children
 *
 * Сохранение пути (state.from) позволяет после логина вернуться
 * на страницу, с которой пришёл пользователь:
 *
 *   const location = useLocation();
 *   const from = location.state?.from || ROUTES.dashboard();
 *   navigate(from, { replace: true });
 */

import React from "react";
import { Navigate, useLocation } from "react-router-dom";
import { useAuth } from "@/lib/AuthContext";
import { ROUTES } from "@/lib/routes";

export default function ProtectedRoute({ children }) {
  const { isAuthenticated, isLoadingAuth } = useAuth();
  const location = useLocation();

  if (isLoadingAuth) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="w-6 h-6 border-2 border-primary/30 border-t-primary rounded-full animate-spin" />
      </div>
    );
  }

  if (!isAuthenticated) {
    return (
      <Navigate
        to={ROUTES.login()}
        state={{ from: location.pathname }}
        replace
      />
    );
  }

  return children;
}
