/**
 * pages/VerifyEmail.jsx
 *
 * Исправлено: nav.to() → nav.toDashboard() / nav.toLogin()
 * "Отправить повторно" использует resendVerification, а не verifyEmail(token)
 */

import { useEffect, useRef, useState } from "react";
import { useSearchParams, Link } from "react-router-dom";
import { motion } from "framer-motion";
import { CheckCircle2, XCircle, Loader2, Leaf } from "lucide-react";
import { Button }         from "@/components/ui/button";
import { useAuth }        from "@/lib/AuthContext";
import { useAppNavigate } from "@/lib/navigation";
import { ROUTES }         from "@/lib/routes";

export default function VerifyEmail() {
  const { verifyEmail, resendVerification, isAuthenticated } = useAuth();
  const nav = useAppNavigate();
  const [searchParams] = useSearchParams();
  const token = searchParams.get("token") || "";

  const [status,  setStatus]  = useState("loading");
  const [message, setMessage] = useState("");
  const [resent,  setResent]  = useState(false);
  const called = useRef(false);

  useEffect(() => {
    if (called.current) return;
    called.current = true;

    if (!token) {
      setStatus("error");
      setMessage("Токен не найден в ссылке.");
      return;
    }

    verifyEmail(token).then((result) => {
      if (result?.ok) {
        setStatus("success");
      } else {
        setStatus("error");
        setMessage(result?.message || "Ссылка недействительна или устарела.");
      }
    });
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const handleResend = async () => {
    const result = await resendVerification();
    if (result?.ok) setResent(true);
  };

  return (
    <div className="min-h-screen flex flex-col items-center justify-center px-6"
      style={{ background: "hsl(40,33%,98%)" }}>

      <Link to={ROUTES.home()} className="flex items-center gap-2 mb-12">
        <div className="w-8 h-8 rounded-xl bg-primary flex items-center justify-center">
          <Leaf className="w-4 h-4 text-primary-foreground" />
        </div>
        <span className="font-serif font-semibold text-xl text-foreground">KinTree</span>
      </Link>

      <motion.div initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }}
        className="w-full max-w-[420px] text-center">

        {status === "loading" && (
          <>
            <Loader2 className="w-12 h-12 mx-auto mb-6 animate-spin text-muted-foreground" />
            <h1 className="font-serif text-2xl font-semibold text-foreground mb-2">
              Подтверждение…
            </h1>
            <p className="text-sm text-muted-foreground">Проверяем ссылку, подождите.</p>
          </>
        )}

        {status === "success" && (
          <>
            <div className="w-16 h-16 rounded-2xl flex items-center justify-center mx-auto mb-6"
              style={{ background: "hsl(145,35%,94%)" }}>
              <CheckCircle2 className="w-8 h-8" style={{ color: "hsl(145,35%,38%)" }} />
            </div>
            <h1 className="font-serif text-2xl font-semibold text-foreground mb-3">
              Email подтверждён
            </h1>
            <p className="text-sm text-muted-foreground mb-8">
              Ваш адрес электронной почты успешно подтверждён.
            </p>
            <Button
              onClick={() => isAuthenticated ? nav.toDashboard() : nav.toLogin()}
              className="w-full h-12 rounded-xl text-sm font-semibold"
              style={{ background: "hsl(145,35%,38%)", color: "white" }}>
              {isAuthenticated ? "Перейти к дашборду" : "Войти в аккаунт"}
            </Button>
          </>
        )}

        {status === "error" && (
          <>
            <div className="w-16 h-16 rounded-2xl flex items-center justify-center mx-auto mb-6"
              style={{ background: "hsl(0,60%,97%)" }}>
              <XCircle className="w-8 h-8" style={{ color: "hsl(0,60%,50%)" }} />
            </div>
            <h1 className="font-serif text-2xl font-semibold text-foreground mb-3">
              Ссылка недействительна
            </h1>
            <p className="text-sm text-muted-foreground mb-8">{message}</p>
            <div className="space-y-3">
              {isAuthenticated && (
                <Button
                  onClick={handleResend}
                  disabled={resent}
                  className="w-full h-11 rounded-xl text-sm"
                  style={{ background: "hsl(145,35%,38%)", color: "white" }}>
                  {resent ? "Письмо отправлено" : "Отправить повторно"}
                </Button>
              )}
              <Link to={ROUTES.login()}>
                <Button variant="outline" className="w-full h-11 rounded-xl text-sm"
                  style={{ borderColor: "hsl(35,20%,85%)" }}>
                  На страницу входа
                </Button>
              </Link>
            </div>
          </>
        )}
      </motion.div>
    </div>
  );
}
