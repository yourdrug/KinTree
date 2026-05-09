/**
 * App.jsx
 *
 * Исправления:
 *  - Добавлен маршрут /oauth/callback для обработки Google OAuth редиректа
 *  - AuthProvider и QueryClientProvider монтируются один раз — снаружи Router
 *    чтобы состояние не сбрасывалось при навигации
 */

import React from "react";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";

import { AuthProvider }  from "@/lib/AuthContext";
import ProtectedRoute    from "@/lib/ProtectedRoute";
import { ROUTES }        from "@/lib/routes";
import { Toaster }       from "@/components/ui/toaster";
import { QueryClientProvider } from "@tanstack/react-query";
import { queryClientInstance } from "@/lib/query-client";

// Pages — public
import Landing       from "@/pages/Landing";
import Login         from "@/pages/Login";
import Explore       from "@/pages/Explore";
import OAuthCallback from "@/pages/OAuthCallback";
import ResetPassword from "@/pages/ResetPassword";
import VerifyEmail   from "@/pages/VerifyEmail";
import PageNotFound  from "@/lib/PageNotFound";

// Pages — protected
import Dashboard from "@/pages/Dashboard";
import TreeView  from "@/pages/TreeView";
import Sessions  from "@/pages/Sessions";

export default function App() {
  return (
    <QueryClientProvider client={queryClientInstance}>
      <BrowserRouter>
        {/*
          AuthProvider внутри BrowserRouter (нужны хуки роутера),
          но снаружи Routes — монтируется один раз на всё время жизни приложения.
          Состояние авторизации живёт здесь и не сбрасывается при смене маршрута.
        */}
        <AuthProvider>
          <Routes>
            {/* ── Public ──────────────────────────────────────────────── */}
            <Route path={ROUTES.home()}          element={<Landing />} />
            <Route path={ROUTES.login()}         element={<Login />} />
            <Route path={ROUTES.explore()}       element={<Explore />} />
            <Route path={ROUTES.oauthCallback()} element={<OAuthCallback />} />
            <Route path={ROUTES.resetPassword()} element={<ResetPassword />} />
            <Route path={ROUTES.verifyEmail()}   element={<VerifyEmail />} />

            {/* ── Protected ────────────────────────────────────────────── */}
            <Route
              path={ROUTES.dashboard()}
              element={<ProtectedRoute><Dashboard /></ProtectedRoute>}
            />
            <Route
              path={ROUTES.tree(":id")}
              element={<ProtectedRoute><TreeView /></ProtectedRoute>}
            />
            <Route
              path={ROUTES.settings.sessions()}
              element={<ProtectedRoute><Sessions /></ProtectedRoute>}
            />
            <Route
              path={ROUTES.settings.root()}
              element={<Navigate to={ROUTES.settings.sessions()} replace />}
            />

            {/* ── 404 ─────────────────────────────────────────────────── */}
            <Route path="*" element={<PageNotFound />} />
          </Routes>

          <Toaster />
        </AuthProvider>
      </BrowserRouter>
    </QueryClientProvider>
  );
}
