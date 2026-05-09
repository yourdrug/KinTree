/**
 * App.jsx
 *
 * Изменения:
 *  - Добавлен <Toaster /> — теперь toast() работает глобально
 */

import React from "react";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";

import { AuthProvider }  from "@/lib/AuthContext";
import ProtectedRoute    from "@/lib/ProtectedRoute";
import { ROUTES }        from "@/lib/routes";
import { Toaster }       from "@/components/ui/toaster";

// Pages — public
import Landing      from "@/pages/Landing";
import Login        from "@/pages/Login";
import Explore      from "@/pages/Explore";
import PageNotFound from "@/lib/PageNotFound";

// Pages — protected
import Dashboard from "@/pages/Dashboard";
import TreeView  from "@/pages/TreeView";
import Sessions  from "@/pages/Sessions";

import { QueryClientProvider } from "@tanstack/react-query";
import { queryClientInstance } from "@/lib/query-client";
import ResetPassword from "@/pages/ResetPassword.jsx";
import VerifyEmail   from "@/pages/VerifyEmail.jsx";

export default function App() {
  return (
    <QueryClientProvider client={queryClientInstance}>
      <BrowserRouter>
        <AuthProvider>
          <Routes>
            {/* ── Public ──────────────────────────────────────────────── */}
            <Route path={ROUTES.home()}          element={<Landing />} />
            <Route path={ROUTES.login()}         element={<Login />} />
            <Route path={ROUTES.explore()}       element={<Explore />} />
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
