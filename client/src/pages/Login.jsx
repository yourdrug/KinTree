/**
 * pages/Login.jsx
 *
 * ИСПРАВЛЕНИЯ:
 * 1. useEffect для редиректа авторизованного пользователя — nav добавлен в deps,
 *    используем useRef для nav чтобы не перезапускать effect при каждом рендере.
 * 2. Telegram widget: убрана зависимость от изменяемой функции onAuth без useCallback.
 * 3. handleSubmit и handleForgotSubmit стабилизированы через useCallback.
 */

import { useState, useEffect, useRef, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Leaf, Eye, EyeOff, ArrowRight, TreePine,
  Mail, Lock, ArrowLeft, CheckCircle2,
} from "lucide-react";
import { Button }            from "@/components/ui/button";
import { Input }             from "@/components/ui/input";
import { Label }             from "@/components/ui/label";
import { Link, useLocation } from "react-router-dom";
import { useAuth }           from "@/lib/AuthContext";
import { useAppNavigate }    from "@/lib/navigation";
import { ROUTES }            from "@/lib/routes";

// ── Декоративное дерево ───────────────────────────────────────────────────────

const MiniTree = () => (
  <svg viewBox="0 0 220 320" className="w-full h-full opacity-90" fill="none">
    <defs>
      <radialGradient id="glow" cx="50%" cy="50%" r="50%">
        <stop offset="0%" stopColor="hsl(145,35%,38%)" stopOpacity="0.15" />
        <stop offset="100%" stopColor="hsl(145,35%,38%)" stopOpacity="0" />
      </radialGradient>
    </defs>
    <ellipse cx="110" cy="160" rx="100" ry="140" fill="url(#glow)" />
    {[
      { x1: 110, y1: 58,  x2: 60,  y2: 110 },
      { x1: 110, y1: 58,  x2: 160, y2: 110 },
      { x1: 60,  y1: 148, x2: 35,  y2: 200 },
      { x1: 60,  y1: 148, x2: 85,  y2: 200 },
      { x1: 160, y1: 148, x2: 135, y2: 200 },
      { x1: 160, y1: 148, x2: 185, y2: 200 },
      { x1: 60,  y1: 238, x2: 45,  y2: 285 },
      { x1: 85,  y1: 238, x2: 95,  y2: 285 },
    ].map((l, i) => (
      <motion.line key={i} x1={l.x1} y1={l.y1} x2={l.x2} y2={l.y2}
        stroke="hsl(145,35%,55%)" strokeWidth="1.5" strokeDasharray="4 3" opacity="0.5"
        initial={{ pathLength: 0, opacity: 0 }} animate={{ pathLength: 1, opacity: 0.5 }}
        transition={{ delay: 0.3 + i * 0.08, duration: 0.6 }} />
    ))}
    {[
      { cx: 110, cy: 38,  r: 18, label: "Пр.",  delay: 0 },
      { cx: 60,  cy: 128, r: 16, label: "Дед",  delay: 0.15 },
      { cx: 160, cy: 128, r: 16, label: "Баб.", delay: 0.2 },
      { cx: 35,  cy: 218, r: 13, label: "Дядя", delay: 0.3 },
      { cx: 85,  cy: 218, r: 13, label: "Папа", delay: 0.35 },
      { cx: 135, cy: 218, r: 13, label: "Мама", delay: 0.4 },
      { cx: 185, cy: 218, r: 13, label: "Тётя", delay: 0.45 },
      { cx: 60,  cy: 290, r: 11, label: "Брат", delay: 0.55 },
      { cx: 110, cy: 290, r: 14, label: "Вы",   delay: 0.6, isYou: true },
    ].map((n, i) => (
      <motion.g key={i} initial={{ scale: 0, opacity: 0 }} animate={{ scale: 1, opacity: 1 }}
        transition={{ delay: n.delay, type: "spring", stiffness: 200 }}>
        <circle cx={n.cx} cy={n.cy} r={n.r + 4}
          fill={n.isYou ? "hsl(145,35%,38%)" : "hsl(40,33%,98%)"}
          stroke={n.isYou ? "hsl(145,35%,30%)" : "hsl(35,20%,82%)"} strokeWidth="1.5" />
        <circle cx={n.cx} cy={n.cy} r={n.r}
          fill={n.isYou ? "hsl(145,35%,45%)" : "hsl(35,40%,92%)"} />
        <text x={n.cx} y={n.cy + 4} fontSize={n.r < 13 ? 6 : 7} fontWeight="600"
          fill={n.isYou ? "white" : "hsl(30,10%,30%)"} textAnchor="middle">
          {n.label}
        </text>
      </motion.g>
    ))}
  </svg>
);

// ── Иконка Google ─────────────────────────────────────────────────────────────

const GoogleIcon = () => (
  <svg viewBox="0 0 24 24" className="w-4 h-4" fill="none">
    <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" fill="#4285F4"/>
    <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853"/>
    <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" fill="#FBBC05"/>
    <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335"/>
  </svg>
);

// ── Иконка Telegram ───────────────────────────────────────────────────────────

const TelegramIcon = () => (
  <svg viewBox="0 0 24 24" className="w-4 h-4" fill="#229ED9">
    <path d="M12 0C5.373 0 0 5.373 0 12s5.373 12 12 12 12-5.373 12-12S18.627 0 12 0zm5.894 8.221-1.97 9.28c-.145.658-.537.818-1.084.508l-3-2.21-1.447 1.394c-.16.16-.295.295-.605.295l.213-3.053 5.56-5.023c.242-.213-.054-.333-.373-.12L7.17 13.667l-2.96-.924c-.643-.204-.657-.643.136-.953l11.57-4.461c.537-.194 1.006.131.978.892z"/>
  </svg>
);

// ── Telegram Widget Hook ───────────────────────────────────────────────────────

function useTelegramWidget(onAuth, enabled) {
  const containerRef = useRef(null);
  // Храним колбэк в ref чтобы не пересоздавать виджет при каждом рендере
  const onAuthRef = useRef(onAuth);
  useEffect(() => { onAuthRef.current = onAuth; }, [onAuth]);

  useEffect(() => {
    if (!enabled || !containerRef.current) return;
    containerRef.current.innerHTML = "";

    window._tgAuthCallback = (user) => { onAuthRef.current(user); };

    const botName = import.meta.env.VITE_TELEGRAM_BOT_NAME;
    if (!botName) return;

    const script = document.createElement("script");
    script.src = "https://telegram.org/js/telegram-widget.js?22";
    script.setAttribute("data-telegram-login", botName);
    script.setAttribute("data-size", "large");
    script.setAttribute("data-onauth", "_tgAuthCallback(user)");
    script.setAttribute("data-request-access", "write");
    script.async = true;

    containerRef.current.appendChild(script);

    return () => { delete window._tgAuthCallback; };
  }, [enabled]); // onAuth намеренно исключён — используем ref

  return containerRef;
}

// ─── Main ──────────────────────────────────────────────────────────────────────

export default function Login() {
  const {
    login, register, loginWithGoogle, loginWithTelegram,
    forgotPassword, isLoadingAuth, authError, isAuthenticated,
  } = useAuth();
  const nav      = useAppNavigate();
  const location = useLocation();
  const from     = location.state?.from || null;

  // FIX: стабилизируем nav в ref чтобы не перезапускать effect
  const navRef = useRef(nav);
  useEffect(() => { navRef.current = nav; }, [nav]);

  // Если уже залогинен — сразу на dashboard
  useEffect(() => {
    if (isAuthenticated) {
      navRef.current.afterLogin();
    }
  }, [isAuthenticated]);

  const [view,          setView]          = useState("login");
  const [showPassword,  setShowPassword]  = useState(false);
  const [form,          setForm]          = useState({ email: "", password: "" });
  const [forgotEmail,   setForgotEmail]   = useState("");
  const [localError,    setLocalError]    = useState("");
  const [forgotLoading, setForgotLoading] = useState(false);

  const showTgWidget = view === "login" || view === "register";

  const handleTelegramAuth = useCallback(async (telegramData) => {
    const result = await loginWithTelegram(telegramData);
    if (result?.ok) {
      from ? (window.location.href = from) : navRef.current.afterLogin();
    } else {
      setLocalError(result?.message || "Ошибка входа через Telegram");
    }
  }, [loginWithTelegram, from]);

  const tgContainerRef = useTelegramWidget(handleTelegramAuth, showTgWidget);

  const set = (k, v) => setForm((f) => ({ ...f, [k]: v }));
  const clearError = () => setLocalError("");

  const handleSubmit = useCallback(async (e) => {
    e.preventDefault();
    clearError();

    if (!form.email.trim() || !form.password.trim()) {
      setLocalError("Заполните все поля");
      return;
    }

    const result = await (view === "login"
      ? login(form.email, form.password)
      : register(form.email, form.password));

    if (result?.ok) {
      from ? (window.location.href = from) : navRef.current.afterLogin();
    } else {
      setLocalError(result?.message || "Ошибка авторизации");
    }
  }, [form, view, login, register, from]);

  const handleForgotSubmit = useCallback(async (e) => {
    e.preventDefault();
    clearError();
    if (!forgotEmail.trim()) { setLocalError("Введите email"); return; }

    setForgotLoading(true);
    const result = await forgotPassword(forgotEmail.trim());
    setForgotLoading(false);

    if (result?.ok) {
      setView("forgot-sent");
    } else {
      setLocalError(result?.message || "Ошибка отправки");
    }
  }, [forgotEmail, forgotPassword]);

  const error = localError || (typeof authError === "string" ? authError : "");

  // ── Экран «Письмо отправлено» ─────────────────────────────────────────────
  if (view === "forgot-sent") {
    return (
      <div className="min-h-screen flex items-center justify-center px-6" style={{ background: "hsl(40,33%,98%)" }}>
        <motion.div initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }}
          className="w-full max-w-[420px] text-center">
          <div className="w-16 h-16 rounded-2xl flex items-center justify-center mx-auto mb-6"
            style={{ background: "hsl(145,35%,94%)" }}>
            <CheckCircle2 className="w-8 h-8" style={{ color: "hsl(145,35%,38%)" }} />
          </div>
          <h1 className="font-serif text-2xl font-semibold text-foreground mb-3">Проверьте почту</h1>
          <p className="text-sm text-muted-foreground mb-2">
            Если аккаунт с адресом <strong>{forgotEmail}</strong> существует —
            мы отправили ссылку для сброса пароля.
          </p>
          <p className="text-xs text-muted-foreground mb-8">
            Ссылка действительна 15 минут. Проверьте папку «Спам».
          </p>
          <Button variant="outline" onClick={() => { setView("login"); setForgotEmail(""); clearError(); }}
            className="w-full h-11 rounded-xl text-sm gap-2"
            style={{ borderColor: "hsl(35,20%,85%)" }}>
            <ArrowLeft className="w-4 h-4" />
            Вернуться к входу
          </Button>
        </motion.div>
      </div>
    );
  }

  // ── Экран «Забыли пароль?» ────────────────────────────────────────────────
  if (view === "forgot") {
    return (
      <div className="min-h-screen flex items-center justify-center px-6" style={{ background: "hsl(40,33%,98%)" }}>
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}
          className="w-full max-w-[420px]">
          <button onClick={() => { setView("login"); clearError(); }}
            className="flex items-center gap-1.5 text-sm text-muted-foreground mb-8 hover:text-foreground transition-colors">
            <ArrowLeft className="w-4 h-4" /> Вернуться к входу
          </button>
          <h1 className="font-serif text-3xl font-semibold text-foreground mb-2">Сброс пароля</h1>
          <p className="text-sm text-muted-foreground mb-8">
            Введите email — мы пришлём ссылку для создания нового пароля.
          </p>
          <form onSubmit={handleForgotSubmit} className="space-y-5">
            <div className="space-y-1.5">
              <Label htmlFor="forgot-email" className="text-xs font-medium text-muted-foreground">Email</Label>
              <div className="relative">
                <Mail className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                <Input id="forgot-email" type="email" value={forgotEmail}
                  onChange={(e) => { setForgotEmail(e.target.value); clearError(); }}
                  placeholder="ivan@example.com" autoComplete="email"
                  className="pl-10 h-12 rounded-xl text-sm"
                  style={{ background: "white", border: "1.5px solid hsl(35,20%,88%)" }} />
              </div>
            </div>
            <AnimatePresence>
              {error && <ErrorBox message={error} />}
            </AnimatePresence>
            <Button type="submit" disabled={forgotLoading}
              className="w-full h-12 rounded-xl text-sm font-semibold gap-2"
              style={{ background: "hsl(145,35%,38%)", color: "white", boxShadow: "0 4px 20px hsla(145,35%,38%,0.4)" }}>
              {forgotLoading
                ? <div className="w-5 h-5 border-2 border-white/40 border-t-white rounded-full animate-spin" />
                : <><Mail className="w-4 h-4" />Отправить ссылку</>}
            </Button>
          </form>
        </motion.div>
      </div>
    );
  }

  // ── Основной экран: login / register ──────────────────────────────────────
  return (
    <div className="min-h-screen flex" style={{ background: "hsl(40,33%,98%)" }}>

      {/* Left panel */}
      <motion.div
        initial={{ opacity: 0, x: -40 }} animate={{ opacity: 1, x: 0 }}
        transition={{ duration: 0.8 }}
        className="hidden lg:flex flex-col justify-between w-[44%] relative overflow-hidden p-12"
        style={{ background: "hsl(145,35%,38%)" }}
      >
        <div className="absolute inset-0 opacity-10"
          style={{ backgroundImage: "radial-gradient(hsl(145,35%,60%) 1px, transparent 1px)", backgroundSize: "28px 28px" }} />

        <div className="relative z-10 flex items-center gap-3">
          <div className="w-10 h-10 rounded-2xl flex items-center justify-center"
            style={{ background: "hsla(40,33%,98%,0.2)" }}>
            <Leaf className="w-5 h-5 text-white" />
          </div>
          <span className="font-serif text-2xl font-semibold text-white">KinTree</span>
        </div>

        <div className="relative z-10 flex-1 flex flex-col items-center justify-center">
          <div className="w-56 h-80"><MiniTree /></div>
          <motion.p initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.6 }}
            className="text-center mt-6 font-serif text-xl font-medium leading-relaxed"
            style={{ color: "hsla(40,33%,98%,0.9)" }}>
            «Семья — это то, что остаётся,&nbsp;когда всё остальное уходит»
          </motion.p>
        </div>

        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.8 }}
          className="relative z-10 grid grid-cols-3 gap-4">
          {[{ val: "12K+", label: "семей" }, { val: "240K+", label: "людей" }, { val: "8", label: "поколений" }]
            .map((s) => (
              <div key={s.label} className="text-center">
                <div className="font-serif text-2xl font-bold text-white">{s.val}</div>
                <div className="text-xs mt-0.5" style={{ color: "hsla(40,33%,98%,0.6)" }}>{s.label}</div>
              </div>
            ))}
        </motion.div>
      </motion.div>

      {/* Right panel */}
      <div className="flex-1 flex flex-col items-center justify-center px-6 py-12">

        <Link to={ROUTES.home()} className="flex items-center gap-2 mb-10 lg:hidden">
          <div className="w-8 h-8 rounded-xl bg-primary flex items-center justify-center">
            <Leaf className="w-4 h-4 text-primary-foreground" />
          </div>
          <span className="font-serif font-semibold text-xl text-foreground">KinTree</span>
        </Link>

        <motion.div initial={{ opacity: 0, y: 30 }} animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.2 }} className="w-full max-w-[420px]">

          {/* Tabs */}
          <div className="flex rounded-2xl p-1 mb-8" style={{ background: "hsl(35,25%,93%)" }}>
            {["login", "register"].map((m) => (
              <button key={m} onClick={() => { setView(m); clearError(); }}
                className="flex-1 py-2.5 rounded-xl text-sm font-medium transition-all duration-200"
                style={{
                  background: view === m ? "white" : "transparent",
                  color: view === m ? "hsl(30,10%,15%)" : "hsl(30,8%,50%)",
                  boxShadow: view === m ? "0 1px 8px hsla(30,10%,15%,0.1)" : "none",
                }}>
                {m === "login" ? "Войти" : "Регистрация"}
              </button>
            ))}
          </div>

          {/* Heading */}
          <AnimatePresence mode="wait">
            <motion.div key={view}
              initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }} transition={{ duration: 0.2 }} className="mb-6">
              <h1 className="font-serif text-3xl font-semibold text-foreground mb-2">
                {view === "login" ? "Добро пожаловать" : "Создать аккаунт"}
              </h1>
              <p className="text-sm text-muted-foreground">
                {view === "login"
                  ? "Войдите, чтобы продолжить работу с вашим деревом"
                  : "Зарегистрируйтесь — это бесплатно и займёт минуту"}
              </p>
            </motion.div>
          </AnimatePresence>

          {/* OAuth кнопки */}
          <div className="grid grid-cols-2 gap-3 mb-5">
            <OAuthButton icon={<GoogleIcon />} label="Google" onClick={loginWithGoogle} />
            <OAuthButton
              icon={<TelegramIcon />}
              label="Telegram"
              onClick={() => {
                const btn = tgContainerRef.current?.querySelector("iframe,a,button");
                if (btn) btn.click();
              }}
              disabled={!import.meta.env.VITE_TELEGRAM_BOT_NAME}
            />
          </div>

          {/* Скрытый Telegram widget */}
          <div
            ref={tgContainerRef}
            className="overflow-hidden"
            style={{ height: 0, visibility: "hidden" }}
            aria-hidden="true"
          />

          <Divider />

          {/* Email + Password */}
          <form onSubmit={handleSubmit} className="space-y-5">
            <div className="space-y-1.5">
              <Label htmlFor="email" className="text-xs font-medium text-muted-foreground">Email</Label>
              <div className="relative">
                <Mail className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                <Input id="email" type="email" value={form.email}
                  onChange={(e) => { set("email", e.target.value); clearError(); }}
                  placeholder="ivan@example.com" autoComplete="email"
                  className="pl-10 h-12 rounded-xl text-sm"
                  style={{ background: "white", border: "1.5px solid hsl(35,20%,88%)" }} />
              </div>
            </div>

            <div className="space-y-1.5">
              <div className="flex items-center justify-between">
                <Label htmlFor="password" className="text-xs font-medium text-muted-foreground">
                  Пароль
                  {view === "register" && (
                    <span className="ml-2 font-normal text-muted-foreground/70">(мин. 8 симв., заглавная, цифра)</span>
                  )}
                </Label>
                {view === "login" && (
                  <button type="button"
                    onClick={() => { setView("forgot"); clearError(); }}
                    className="text-xs transition-colors hover:underline"
                    style={{ color: "hsl(145,35%,38%)" }}>
                    Забыли пароль?
                  </button>
                )}
              </div>
              <div className="relative">
                <Lock className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                <Input id="password" type={showPassword ? "text" : "password"}
                  value={form.password}
                  onChange={(e) => { set("password", e.target.value); clearError(); }}
                  placeholder={view === "register" ? "Придумайте пароль" : "Введите пароль"}
                  autoComplete={view === "login" ? "current-password" : "new-password"}
                  className="pl-10 pr-12 h-12 rounded-xl text-sm"
                  style={{ background: "white", border: "1.5px solid hsl(35,20%,88%)" }} />
                <button type="button" tabIndex={-1}
                  onClick={() => setShowPassword((v) => !v)}
                  className="absolute right-3.5 top-1/2 -translate-y-1/2 w-7 h-7 flex items-center justify-center rounded-lg transition-colors hover:bg-muted">
                  {showPassword
                    ? <EyeOff className="w-4 h-4 text-muted-foreground" />
                    : <Eye className="w-4 h-4 text-muted-foreground" />}
                </button>
              </div>
            </div>

            <AnimatePresence>
              {error && <ErrorBox message={error} />}
            </AnimatePresence>

            <Button type="submit" disabled={isLoadingAuth}
              className="w-full h-12 rounded-xl text-sm font-semibold gap-2"
              style={{ background: "hsl(145,35%,38%)", color: "white", boxShadow: "0 4px 20px hsla(145,35%,38%,0.4)" }}>
              {isLoadingAuth
                ? <div className="w-5 h-5 border-2 border-white/40 border-t-white rounded-full animate-spin" />
                : <>{view === "login" ? "Войти в аккаунт" : "Создать аккаунт"}<ArrowRight className="w-4 h-4" /></>}
            </Button>
          </form>

          <Divider />

          <Link to={ROUTES.explore()}>
            <Button variant="outline" className="w-full h-11 rounded-xl text-sm gap-2"
              style={{ borderColor: "hsl(35,20%,85%)" }}>
              <TreePine className="w-4 h-4 text-muted-foreground" />
              Продолжить как гость
            </Button>
          </Link>

          <p className="text-center text-sm text-muted-foreground mt-6">
            {view === "login" ? "Нет аккаунта? " : "Уже есть аккаунт? "}
            <button type="button"
              onClick={() => { setView(view === "login" ? "register" : "login"); clearError(); }}
              className="font-medium underline underline-offset-2 hover:no-underline transition-all"
              style={{ color: "hsl(145,35%,38%)" }}>
              {view === "login" ? "Зарегистрироваться" : "Войти"}
            </button>
          </p>

          <div className="text-center mt-4">
            <Link to={ROUTES.home()}
              className="text-xs text-muted-foreground/70 hover:text-muted-foreground transition-colors">
              ← На главную
            </Link>
          </div>
        </motion.div>
      </div>
    </div>
  );
}

// ─── Вспомогательные компоненты ────────────────────────────────────────────────

function OAuthButton({ icon, label, onClick, disabled }) {
  return (
    <button
      type="button"
      onClick={onClick}
      disabled={disabled}
      className="flex items-center justify-center gap-2.5 h-11 rounded-xl text-sm font-medium transition-all duration-200 hover:shadow-md active:scale-[0.98] disabled:opacity-40 disabled:cursor-not-allowed"
      style={{
        background: "white",
        border: "1.5px solid hsl(35,20%,88%)",
        color: "hsl(30,10%,20%)",
      }}
    >
      {icon}
      {label}
    </button>
  );
}

function Divider() {
  return (
    <div className="flex items-center gap-4 my-5">
      <div className="flex-1 h-px" style={{ background: "hsl(35,20%,88%)" }} />
      <span className="text-xs text-muted-foreground">или</span>
      <div className="flex-1 h-px" style={{ background: "hsl(35,20%,88%)" }} />
    </div>
  );
}

function ErrorBox({ message }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: -8, height: 0 }}
      animate={{ opacity: 1, y: 0, height: "auto" }}
      exit={{ opacity: 0, y: -8, height: 0 }}
      className="px-4 py-3 rounded-xl text-sm"
      style={{ background: "hsl(0,60%,97%)", border: "1px solid hsl(0,60%,90%)", color: "hsl(0,60%,45%)" }}
    >
      {message}
    </motion.div>
  );
}
