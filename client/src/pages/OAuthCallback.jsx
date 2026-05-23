/**
 * pages/OAuthCallback.jsx
 *
 * Обрабатывает редирект от Google OAuth.
 * Бэкенд уже поставил куки — просто читаем профиль через /account/me.
 */

import { useEffect, useRef, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { Leaf, Loader2, XCircle } from "lucide-react";
import { motion } from "framer-motion";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/lib/AuthContext";
import { ROUTES }  from "@/lib/routes";

export default function OAuthCallback() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const { fetchMe } = useAuth();

  const [status,   setStatus]   = useState("loading");
  const [errorMsg, setErrorMsg] = useState("");
  const called = useRef(false);

  useEffect(() => {
    if (called.current) return;
    called.current = true;

    const oauthError = searchParams.get("error");

    if (oauthError) {
      setErrorMsg(
        oauthError === "access_denied"
          ? "Вы отменили авторизацию через Google."
          : `Ошибка Google OAuth: ${oauthError}`
      );
      setStatus("error");
      return;
    }

    // Бэкенд уже поставил куки через Set-Cookie при редиректе.
    // Достаточно прочитать /account/me (isInitial=false → с поддержкой refresh).
    fetchMe(false)
      .then(() => {
        setStatus("success");
        setTimeout(() => navigate(ROUTES.dashboard(), { replace: true }), 700);
      })
      .catch(() => {
        setErrorMsg("Не удалось получить данные аккаунта. Попробуйте снова.");
        setStatus("error");
      });
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  return (
    <div className="min-h-screen flex flex-col items-center justify-center px-6"
      style={{ background: "hsl(40,33%,98%)" }}>

      <div className="flex items-center gap-2 mb-12">
        <div className="w-8 h-8 rounded-xl bg-primary flex items-center justify-center">
          <Leaf className="w-4 h-4 text-primary-foreground" />
        </div>
        <span className="font-serif font-semibold text-xl text-foreground">KinTree</span>
      </div>

      <motion.div initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }}
        className="w-full max-w-sm text-center">

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
            <div className="w-16 h-16 rounded-2xl flex items-center justify-center mx-auto mb-6"
              style={{ background: "hsl(145,35%,94%)" }}>
              <svg className="w-8 h-8" viewBox="0 0 24 24" fill="none">
                <path d="M5 13l4 4L19 7" stroke="hsl(145,35%,38%)"
                  strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" />
              </svg>
            </div>
            <h1 className="font-serif text-2xl font-semibold text-foreground mb-2">Вход выполнен!</h1>
            <p className="text-sm text-muted-foreground">Перенаправляем…</p>
          </>
        )}

        {status === "error" && (
          <>
            <div className="w-16 h-16 rounded-2xl flex items-center justify-center mx-auto mb-6"
              style={{ background: "hsl(0,60%,97%)" }}>
              <XCircle className="w-8 h-8" style={{ color: "hsl(0,60%,50%)" }} />
            </div>
            <h1 className="font-serif text-2xl font-semibold text-foreground mb-3">
              Не удалось войти
            </h1>
            <p className="text-sm text-muted-foreground mb-8">{errorMsg}</p>
            <Button
              className="w-full h-11 rounded-xl text-sm font-semibold"
              style={{ background: "hsl(145,35%,38%)", color: "white" }}
              onClick={() => navigate(ROUTES.login(), { replace: true })}
            >
              Вернуться к входу
            </Button>
          </>
        )}
      </motion.div>
    </div>
  );
}
