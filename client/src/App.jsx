/**
 * App.jsx  (или router.jsx — в зависимости от вашей структуры)
 *
 * Весь роутинг приложения в одном месте.
 * Маршруты берутся из ROUTES — нет ни одной строки URL вручную.
 *
 * Структура:
 *   Public  — доступны всем
 *   Protected — требуют авторизации, оборачиваются ProtectedRoute
 *   Fallback  — 404
 */

import React from "react";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";

import { AuthProvider } from "@/lib/AuthContext";
import ProtectedRoute   from "@/lib/ProtectedRoute";
import { ROUTES }       from "@/lib/routes";

// Pages — public
import Landing      from "@/pages/Landing";
import Login        from "@/pages/Login";
import Explore      from "@/pages/Explore";
import PageNotFound from "@/lib/PageNotFound";

// Pages — protected
import Dashboard from "@/pages/Dashboard";
import TreeView  from "@/pages/TreeView";
import Sessions  from "@/pages/Sessions";

// QueryClient (если используете react-query)
import { QueryClientProvider } from "@tanstack/react-query";
import { queryClientInstance } from "@/lib/query-client";

export default function App() {
  return (
    <QueryClientProvider client={queryClientInstance}>
      <BrowserRouter>
        <AuthProvider>
          <Routes>

            {/* ── Public ──────────────────────────────────────────────── */}
            <Route path={ROUTES.home()}    element={<Landing />} />
            <Route path={ROUTES.login()}   element={<Login />} />
            <Route path={ROUTES.explore()} element={<Explore />} />

            {/* ── Protected ────────────────────────────────────────────── */}
            <Route
              path={ROUTES.dashboard()}
              element={<ProtectedRoute><Dashboard /></ProtectedRoute>}
            />
            <Route
              path={ROUTES.tree(":id")}
              element={<ProtectedRoute><TreeView /></ProtectedRoute>}
            />

            {/* Settings — группируем под /settings/* */}
            <Route
              path={ROUTES.settings.sessions()}
              element={<ProtectedRoute><Sessions /></ProtectedRoute>}
            />

            {/* Редирект /settings → /settings/sessions как index */}
            <Route
              path={ROUTES.settings.root()}
              element={<Navigate to={ROUTES.settings.sessions()} replace />}
            />

            {/* ── 404 ─────────────────────────────────────────────────── */}
            <Route path="*" element={<PageNotFound />} />

          </Routes>
        </AuthProvider>
      </BrowserRouter>
    </QueryClientProvider>
  );
}
