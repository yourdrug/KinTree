/**
 * pages/ResetPassword.jsx
 *
 * Страница установки нового пароля.
 * Открывается по ссылке из письма: /reset-password?token=...
 *
 * Состояния:
 *  - idle    → форма ввода нового пароля
 *  - loading → запрос к API
 *  - success → пароль изменён, кнопка перехода к логину
 *  - error   → токен истёк или невалиден
 */

import { useState } from "react";
import { useSearchParams, Link } from "react-router-dom";
import { motion, AnimatePresence } from "framer-motion";
import { Lock, Eye, EyeOff, CheckCircle2, XCircle, ArrowRight, Leaf } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input }  from "@/components/ui/input";
import { Label }  from "@/components/ui/label";
import { useAuth }        from "@/lib/AuthContext";
import { useAppNavigate } from "@/lib/navigation";
import { ROUTES }         from "@/lib/routes";

export default function ResetPassword() {
  const { resetPassword } = useAuth();
  const nav = useAppNavigate();
  const [searchParams] = useSearchParams();
  const token = searchParams.get("token") || "";

  const [password,     setPassword]     = useState("");
  const [confirm,      setConfirm]      = useState("");
  const [showPass,     setShowPass]     = useState(false);
  const [showConfirm,  setShowConfirm]  = useState(false);
  const [status,       setStatus]       = useState("idle"); // idle | loading | success | error
  const [errorMsg,     setErrorMsg]     = useState("");

  // Нет токена в URL — сразу показываем ошибку
  if (!token) {
    return <_ErrorScreen message="Ссылка недействительна. Запросите новую." />;
  }

  const handleSubmit = async (e) => {
    e.preventDefault();
    setErrorMsg("");

    if (!password) { setErrorMsg("Введите новый пароль"); return; }
    if (password !== confirm) { setErrorMsg("Пароли не совпадают"); return; }

    setStatus("loading");
    const result = await resetPassword(token, password);

    if (result?.ok) {
      setStatus("success");
    } else {
      setStatus("error");
      setErrorMsg(result?.message || "Токен недействителен или устарел");
    }
  };

  if (status === "success") {
    return (
      <_CenteredLayout>
        <div className="w-16 h-16 rounded-2xl flex items-center justify-center mx-auto mb-6"
          style={{ background: "hsl(145,35%,94%)" }}>
          <CheckCircle2 className="w-8 h-8" style={{ color: "hsl(145,35%,38%)" }} />
        </div>
        <h1 className="font-serif text-2xl font-semibold text-foreground mb-3">
          Пароль изменён
        </h1>
        <p className="text-sm text-muted-foreground mb-8">
          Новый пароль установлен. Все активные сессии завершены.
        </p>
        <Button onClick={() => nav.to(ROUTES.login())}
          className="w-full h-12 rounded-xl text-sm font-semibold gap-2"
          style={{ background: "hsl(145,35%,38%)", color: "white" }}>
          Войти в аккаунт <ArrowRight className="w-4 h-4" />
        </Button>
      </_CenteredLayout>
    );
  }

  if (status === "error") {
    return <_ErrorScreen message={errorMsg} />;
  }

  return (
    <_CenteredLayout>
      <h1 className="font-serif text-3xl font-semibold text-foreground mb-2">
        Новый пароль
      </h1>
      <p className="text-sm text-muted-foreground mb-8">
        Придумайте надёжный пароль для вашего аккаунта.
      </p>

      <form onSubmit={handleSubmit} className="space-y-5">
        {/* Новый пароль */}
        <div className="space-y-1.5">
          <Label htmlFor="password" className="text-xs font-medium text-muted-foreground">
            Новый пароль
            <span className="ml-2 font-normal text-muted-foreground/70">
              (мин. 8 симв., заглавная, цифра)
            </span>
          </Label>
          <div className="relative">
            <Lock className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
            <Input id="password" type={showPass ? "text" : "password"}
              value={password} onChange={(e) => setPassword(e.target.value)}
              placeholder="Придумайте пароль" autoComplete="new-password"
              className="pl-10 pr-12 h-12 rounded-xl text-sm"
              style={{ background: "white", border: "1.5px solid hsl(35,20%,88%)" }} />
            <button type="button" tabIndex={-1}
              onClick={() => setShowPass((v) => !v)}
              className="absolute right-3.5 top-1/2 -translate-y-1/2 w-7 h-7 flex items-center justify-center rounded-lg hover:bg-muted transition-colors">
              {showPass ? <EyeOff className="w-4 h-4 text-muted-foreground" /> : <Eye className="w-4 h-4 text-muted-foreground" />}
            </button>
          </div>
        </div>

        {/* Подтверждение */}
        <div className="space-y-1.5">
          <Label htmlFor="confirm" className="text-xs font-medium text-muted-foreground">
            Повторите пароль
          </Label>
          <div className="relative">
            <Lock className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
            <Input id="confirm" type={showConfirm ? "text" : "password"}
              value={confirm} onChange={(e) => setConfirm(e.target.value)}
              placeholder="Введите пароль ещё раз" autoComplete="new-password"
              className="pl-10 pr-12 h-12 rounded-xl text-sm"
              style={{ background: "white", border: "1.5px solid hsl(35,20%,88%)" }} />
            <button type="button" tabIndex={-1}
              onClick={() => setShowConfirm((v) => !v)}
              className="absolute right-3.5 top-1/2 -translate-y-1/2 w-7 h-7 flex items-center justify-center rounded-lg hover:bg-muted transition-colors">
              {showConfirm ? <EyeOff className="w-4 h-4 text-muted-foreground" /> : <Eye className="w-4 h-4 text-muted-foreground" />}
            </button>
          </div>
        </div>

        <AnimatePresence>
          {errorMsg && (
            <motion.div initial={{ opacity: 0, y: -8, height: 0 }}
              animate={{ opacity: 1, y: 0, height: "auto" }}
              exit={{ opacity: 0, y: -8, height: 0 }}
              className="px-4 py-3 rounded-xl text-sm"
              style={{ background: "hsl(0,60%,97%)", border: "1px solid hsl(0,60%,90%)", color: "hsl(0,60%,45%)" }}>
              {errorMsg}
            </motion.div>
          )}
        </AnimatePresence>

        <Button type="submit" disabled={status === "loading"}
          className="w-full h-12 rounded-xl text-sm font-semibold gap-2"
          style={{ background: "hsl(145,35%,38%)", color: "white", boxShadow: "0 4px 20px hsla(145,35%,38%,0.4)" }}>
          {status === "loading"
            ? <div className="w-5 h-5 border-2 border-white/40 border-t-white rounded-full animate-spin" />
            : <>Сохранить пароль <ArrowRight className="w-4 h-4" /></>}
        </Button>
      </form>
    </_CenteredLayout>
  );
}

// ── Вспомогательные компоненты ────────────────────────────────────────────────

function _CenteredLayout({ children }) {
  return (
    <div className="min-h-screen flex flex-col items-center justify-center px-6"
      style={{ background: "hsl(40,33%,98%)" }}>
      <Link to={ROUTES.home()} className="flex items-center gap-2 mb-10">
        <div className="w-8 h-8 rounded-xl bg-primary flex items-center justify-center">
          <Leaf className="w-4 h-4 text-primary-foreground" />
        </div>
        <span className="font-serif font-semibold text-xl text-foreground">KinTree</span>
      </Link>
      <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}
        className="w-full max-w-[420px]">
        {children}
      </motion.div>
    </div>
  );
}

function _ErrorScreen({ message }) {
  return (
    <_CenteredLayout>
      <div className="w-16 h-16 rounded-2xl flex items-center justify-center mx-auto mb-6"
        style={{ background: "hsl(0,60%,97%)" }}>
        <XCircle className="w-8 h-8" style={{ color: "hsl(0,60%,50%)" }} />
      </div>
      <h1 className="font-serif text-2xl font-semibold text-foreground mb-3 text-center">
        Ссылка недействительна
      </h1>
      <p className="text-sm text-muted-foreground mb-8 text-center">{message}</p>
      <Link to={ROUTES.login()}>
        <Button variant="outline" className="w-full h-11 rounded-xl text-sm"
          style={{ borderColor: "hsl(35,20%,85%)" }}>
          Запросить новую ссылку
        </Button>
      </Link>
    </_CenteredLayout>
  );
}
