/**
 * pages/OAuthCallback.jsx
 *
 * Страница-обработчик OAuth редиректа от Google.
 *
 * Флоу:
 *   1. Пользователь нажимает "Войти через Google"
 *   2. Фронт делает window.location.href = /auth/oauth/google (бэкенд)
 *   3. Бэкенд редиректит на Google consent screen
 *   4. Google редиректит на GOOGLE_REDIRECT_URI = бэкенд /auth/oauth/google/callback
 *   5. Бэкенд обменивает code → токены, ставит cookie, редиректит на /oauth/callback (фронт)
 *   6. Эта страница вызывает checkUserAuth() — cookie уже есть, просто читаем /me
 *   7. Редиректим на dashboard
 */

import { useEffect, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { Leaf, Loader2, XCircle } from "lucide-react";
import { motion } from "framer-motion";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/lib/AuthContext";
import { http } from "@/api/client";
import { ENDPOINTS as EP } from "@/api/endpoints";
import { ROUTES } from "@/lib/routes";
import { appParams } from "@/lib/app-params";

export default function OAuthCallback() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const { checkUserAuth } = useAuth();

  const [status, setStatus] = useState("loading"); // loading | success | error
  const [errorMsg, setErrorMsg] = useState("");

  useEffect(() => {
    handleCallback();
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const handleCallback = async () => {
    try {
      const code  = searchParams.get("code");
      const error = searchParams.get("error");

      if (error) {
        setStatus("error");
        setErrorMsg(
          error === "access_denied"
            ? "Вы отменили авторизацию через Google."
            : `Ошибка OAuth: ${error}`
        );
        return;
      }

      if (code) {
        // Если бэкенд настроен так, что GOOGLE_REDIRECT_URI указывает на фронт —
        // передаём code на бэкенд, он поставит cookie
        await http.get(`${EP.auth.googleCallback()}?code=${encodeURIComponent(code)}`);
      }
      // Если code нет — бэкенд уже поставил cookie и сделал редирект на эту страницу

      // Перечитываем пользователя
      await checkUserAuth();

      setStatus("success");
      // Небольшая задержка для UX
      setTimeout(() => navigate(ROUTES.dashboard(), { replace: true }), 800);
    } catch (err) {
      const msg =
        err?.response?.data?.detail ||
        err?.response?.data?.message ||
        err?.message ||
        "Не удалось войти через Google";
      setStatus("error");
      setErrorMsg(typeof msg === "string" ? msg : "Не удалось войти через Google");
    }
  };

  return (
    <div
      className="min-h-screen flex flex-col items-center justify-center px-6"
      style={{ background: "hsl(40,33%,98%)" }}
    >
      {/* Лого */}
      <div className="flex items-center gap-2 mb-12">
        <div className="w-8 h-8 rounded-xl bg-primary flex items-center justify-center">
          <Leaf className="w-4 h-4 text-primary-foreground" />
        </div>
        <span className="font-serif font-semibold text-xl text-foreground">KinTree</span>
      </div>

      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        className="w-full max-w-sm text-center"
      >
        {status === "loading" && (
          <>
            <Loader2 className="w-12 h-12 mx-auto mb-6 animate-spin text-primary" />
            <h1 className="font-serif text-2xl font-semibold text-foreground mb-2">
              Входим через Google…
            </h1>
            <p className="text-sm text-muted-foreground">Подождите секунду</p>
          </>
        )}

        {status === "success" && (
          <>
            <div
              className="w-16 h-16 rounded-2xl flex items-center justify-center mx-auto mb-6"
              style={{ background: "hsl(145,35%,94%)" }}
            >
              <svg className="w-8 h-8" viewBox="0 0 24 24" fill="none">
                <path d="M5 13l4 4L19 7" stroke="hsl(145,35%,38%)" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" />
              </svg>
            </div>
            <h1 className="font-serif text-2xl font-semibold text-foreground mb-2">
              Вход выполнен!
            </h1>
            <p className="text-sm text-muted-foreground">Перенаправляем…</p>
          </>
        )}

        {status === "error" && (
          <>
            <div
              className="w-16 h-16 rounded-2xl flex items-center justify-center mx-auto mb-6"
              style={{ background: "hsl(0,60%,97%)" }}
            >
              <XCircle className="w-8 h-8" style={{ color: "hsl(0,60%,50%)" }} />
            </div>
            <h1 className="font-serif text-2xl font-semibold text-foreground mb-3">
              Не удалось войти
            </h1>
            <p className="text-sm text-muted-foreground mb-8">{errorMsg}</p>
            <div className="space-y-3">
              <Button
                className="w-full h-11 rounded-xl text-sm font-semibold"
                style={{ background: "hsl(145,35%,38%)", color: "white" }}
                onClick={() => navigate(ROUTES.login(), { replace: true })}
              >
                Вернуться к входу
              </Button>
              <Button
                variant="outline"
                className="w-full h-11 rounded-xl text-sm"
                onClick={() => {
                  setStatus("loading");
                  setErrorMsg("");
                  handleCallback();
                }}
              >
                Попробовать снова
              </Button>
            </div>
          </>
        )}
      </motion.div>
    </div>
  );
}
