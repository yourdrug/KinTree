/**
 * lib/TreeRoute.jsx
 *
 * Маршрут для страницы дерева:
 * - Если пользователь авторизован — рендерим сразу (isLoadingAuth ждём).
 * - Если не авторизован — всё равно рендерим TreeView (он сам определит
 *   что дерево публичное и покажет его в read-only режиме).
 *
 * Это позволяет делиться ссылками на публичные деревья без регистрации.
 */

import { useAuth } from "@/lib/AuthContext";
import LoadingSpinner from "@/components/common/LoadingSpinner";

export default function TreeRoute({ children }) {
  const { isLoadingAuth } = useAuth();

  // Ждём завершения проверки авторизации чтобы TreeView знал user или null
  if (isLoadingAuth) return <LoadingSpinner fullScreen />;

  return children;
}
