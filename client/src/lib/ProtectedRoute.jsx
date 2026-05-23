/**
 * lib/ProtectedRoute.jsx
 *
 * Охраняет защищённые маршруты:
 * - isLoadingAuth  → спиннер (ждём результата /account/me при старте)
 * - !isAuthenticated → редирект на /login с сохранением текущего пути
 * - isAuthenticated → рендерим children
 *
 * Не вызывает повторно checkUserAuth при SPA-навигации —
 * AuthProvider монтируется один раз и хранит состояние в памяти.
 */

import { Navigate, useLocation } from "react-router-dom";
import { useAuth } from "@/lib/AuthContext";
import { ROUTES }  from "@/lib/routes";
import LoadingSpinner from "@/components/common/LoadingSpinner";

export default function ProtectedRoute({ children }) {
  const { isAuthenticated, isLoadingAuth } = useAuth();
  const location = useLocation();

  if (isLoadingAuth) return <LoadingSpinner fullScreen />;

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
