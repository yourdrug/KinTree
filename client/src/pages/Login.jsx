// client/src/pages/Login.jsx

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Leaf, Eye, EyeOff, ArrowRight, TreePine, Mail, Lock } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Link } from "react-router-dom";
import { useAuth } from "@/lib/AuthContext";

// ── Декоративное дерево поколений ────────────────────────────────────────────

const MiniTree = () => (
  <svg viewBox="0 0 220 320" className="w-full h-full opacity-90" fill="none">
    <defs>
      <radialGradient id="glow" cx="50%" cy="50%" r="50%">
        <stop offset="0%" stopColor="hsl(145,35%,38%)" stopOpacity="0.15" />
        <stop offset="100%" stopColor="hsl(145,35%,38%)" stopOpacity="0" />
      </radialGradient>
    </defs>
    <ellipse cx="110" cy="160" rx="100" ry="140" fill="url(#glow)" />

    {/* Lines */}
    {[
      { x1: 110, y1: 58, x2: 60, y2: 110 },
      { x1: 110, y1: 58, x2: 160, y2: 110 },
      { x1: 60, y1: 148, x2: 35, y2: 200 },
      { x1: 60, y1: 148, x2: 85, y2: 200 },
      { x1: 160, y1: 148, x2: 135, y2: 200 },
      { x1: 160, y1: 148, x2: 185, y2: 200 },
      { x1: 60, y1: 238, x2: 45, y2: 285 },
      { x1: 85, y1: 238, x2: 95, y2: 285 },
    ].map((l, i) => (
      <motion.line
        key={i}
        x1={l.x1} y1={l.y1} x2={l.x2} y2={l.y2}
        stroke="hsl(145,35%,55%)"
        strokeWidth="1.5"
        strokeDasharray="4 3"
        opacity="0.5"
        initial={{ pathLength: 0, opacity: 0 }}
        animate={{ pathLength: 1, opacity: 0.5 }}
        transition={{ delay: 0.3 + i * 0.08, duration: 0.6 }}
      />
    ))}

    {/* Nodes */}
    {[
      { cx: 110, cy: 38, r: 18, label: "Пр.", delay: 0 },
      { cx: 60, cy: 128, r: 16, label: "Дед", delay: 0.15 },
      { cx: 160, cy: 128, r: 16, label: "Баб.", delay: 0.2 },
      { cx: 35, cy: 218, r: 13, label: "Дядя", delay: 0.3 },
      { cx: 85, cy: 218, r: 13, label: "Папа", delay: 0.35 },
      { cx: 135, cy: 218, r: 13, label: "Мама", delay: 0.4 },
      { cx: 185, cy: 218, r: 13, label: "Тётя", delay: 0.45 },
      { cx: 60, cy: 290, r: 11, label: "Брат", delay: 0.55 },
      { cx: 110, cy: 290, r: 14, label: "Вы", delay: 0.6, isYou: true },
    ].map((n, i) => (
      <motion.g key={i}
        initial={{ scale: 0, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        transition={{ delay: n.delay, type: "spring", stiffness: 200 }}>
        <circle
          cx={n.cx} cy={n.cy} r={n.r + 4}
          fill={n.isYou ? "hsl(145,35%,38%)" : "hsl(40,33%,98%)"}
          stroke={n.isYou ? "hsl(145,35%,30%)" : "hsl(35,20%,82%)"}
          strokeWidth="1.5"
          filter="url(#shadow)"
        />
        <circle
          cx={n.cx} cy={n.cy} r={n.r}
          fill={n.isYou ? "hsl(145,35%,45%)" : "hsl(35,40%,92%)"}
        />
        <text x={n.cx} y={n.cy + 4} fontSize={n.r < 13 ? 6 : 7}
          fontWeight="600" fill={n.isYou ? "white" : "hsl(30,10%,30%)"}
          textAnchor="middle">
          {n.label}
        </text>
      </motion.g>
    ))}
  </svg>
);

// ── Main component ────────────────────────────────────────────────────────────

export default function Login() {
  const { login, register, isLoadingAuth, authError } = useAuth();

  const [mode, setMode] = useState("login"); // "login" | "register"
  const [showPassword, setShowPassword] = useState(false);
  const [form, setForm] = useState({ email: "", password: "" });
  const [localError, setLocalError] = useState("");

  const set = (k, v) => setForm((f) => ({ ...f, [k]: v }));

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLocalError("");

    if (!form.email.trim() || !form.password.trim()) {
      setLocalError("Заполните все поля");
      return;
    }

    if (mode === "login") {
      const result = await login(form.email, form.password);
      if (!result?.ok && result !== true) {
        setLocalError(result?.message || "Неверный email или пароль");
      }
    } else {
      const result = await register(form.email, form.password);
      if (!result?.ok) {
        setLocalError(result?.message || "Ошибка регистрации");
      }
    }
  };

  const error = localError || (authError && typeof authError === "string" ? authError : "");

  return (
    <div
      className="min-h-screen flex"
      style={{ background: "hsl(40,33%,98%)" }}
    >
      {/* ── Left panel: decorative ───────────────────────────────────────── */}
      <motion.div
        initial={{ opacity: 0, x: -40 }}
        animate={{ opacity: 1, x: 0 }}
        transition={{ duration: 0.8 }}
        className="hidden lg:flex flex-col justify-between w-[44%] relative overflow-hidden p-12"
        style={{ background: "hsl(145,35%,38%)" }}
      >
        {/* Texture overlay */}
        <div className="absolute inset-0 opacity-10"
          style={{
            backgroundImage:
              "radial-gradient(hsl(145,35%,60%) 1px, transparent 1px)",
            backgroundSize: "28px 28px",
          }}
        />

        {/* Top: logo */}
        <div className="relative z-10 flex items-center gap-3">
          <div className="w-10 h-10 rounded-2xl flex items-center justify-center"
            style={{ background: "hsla(40,33%,98%,0.2)" }}>
            <Leaf className="w-5 h-5 text-white" />
          </div>
          <span className="font-serif text-2xl font-semibold text-white">KinTree</span>
        </div>

        {/* Center: mini tree */}
        <div className="relative z-10 flex-1 flex flex-col items-center justify-center">
          <div className="w-56 h-80">
            <MiniTree />
          </div>
          <motion.p
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.6 }}
            className="text-center mt-6 font-serif text-xl font-medium leading-relaxed"
            style={{ color: "hsla(40,33%,98%,0.9)" }}
          >
            «Семья — это то, что остаётся,&nbsp;когда всё остальное уходит»
          </motion.p>
        </div>

        {/* Bottom: stats */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.8 }}
          className="relative z-10 grid grid-cols-3 gap-4"
        >
          {[
            { val: "12K+", label: "семей" },
            { val: "240K+", label: "людей" },
            { val: "8", label: "поколений" },
          ].map((s) => (
            <div key={s.label} className="text-center">
              <div className="font-serif text-2xl font-bold text-white">{s.val}</div>
              <div className="text-xs mt-0.5" style={{ color: "hsla(40,33%,98%,0.6)" }}>
                {s.label}
              </div>
            </div>
          ))}
        </motion.div>
      </motion.div>

      {/* ── Right panel: form ────────────────────────────────────────────── */}
      <div className="flex-1 flex flex-col items-center justify-center px-6 py-12">

        {/* Mobile logo */}
        <Link to="/" className="flex items-center gap-2 mb-10 lg:hidden">
          <div className="w-8 h-8 rounded-xl bg-primary flex items-center justify-center">
            <Leaf className="w-4 h-4 text-primary-foreground" />
          </div>
          <span className="font-serif font-semibold text-xl text-foreground">KinTree</span>
        </Link>

        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.2 }}
          className="w-full max-w-[420px]"
        >
          {/* Tabs: login / register */}
          <div className="flex rounded-2xl p-1 mb-8"
            style={{ background: "hsl(35,25%,93%)" }}>
            {["login", "register"].map((m) => (
              <button
                key={m}
                onClick={() => { setMode(m); setLocalError(""); }}
                className="flex-1 py-2.5 rounded-xl text-sm font-medium transition-all duration-200"
                style={{
                  background: mode === m ? "white" : "transparent",
                  color: mode === m ? "hsl(30,10%,15%)" : "hsl(30,8%,50%)",
                  boxShadow: mode === m ? "0 1px 8px hsla(30,10%,15%,0.1)" : "none",
                }}
              >
                {m === "login" ? "Войти" : "Регистрация"}
              </button>
            ))}
          </div>

          {/* Heading */}
          <AnimatePresence mode="wait">
            <motion.div
              key={mode}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              transition={{ duration: 0.2 }}
              className="mb-8"
            >
              <h1 className="font-serif text-3xl font-semibold text-foreground mb-2">
                {mode === "login" ? "Добро пожаловать" : "Создать аккаунт"}
              </h1>
              <p className="text-sm text-muted-foreground">
                {mode === "login"
                  ? "Войдите, чтобы продолжить работу с вашим деревом"
                  : "Зарегистрируйтесь — это бесплатно и займёт минуту"}
              </p>
            </motion.div>
          </AnimatePresence>

          {/* Form */}
          <form onSubmit={handleSubmit} className="space-y-5">

            {/* Email */}
            <div className="space-y-1.5">
              <Label htmlFor="email" className="text-xs font-medium text-muted-foreground">
                Email
              </Label>
              <div className="relative">
                <Mail className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                <Input
                  id="email"
                  type="email"
                  value={form.email}
                  onChange={(e) => set("email", e.target.value)}
                  placeholder="ivan@example.com"
                  autoComplete="email"
                  className="pl-10 h-12 rounded-xl text-sm"
                  style={{ background: "white", border: "1.5px solid hsl(35,20%,88%)" }}
                />
              </div>
            </div>

            {/* Password */}
            <div className="space-y-1.5">
              <Label htmlFor="password" className="text-xs font-medium text-muted-foreground">
                Пароль
                {mode === "register" && (
                  <span className="ml-2 font-normal text-muted-foreground/70">
                    (мин. 8 симв., заглавная буква, цифра)
                  </span>
                )}
              </Label>
              <div className="relative">
                <Lock className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                <Input
                  id="password"
                  type={showPassword ? "text" : "password"}
                  value={form.password}
                  onChange={(e) => set("password", e.target.value)}
                  placeholder={mode === "register" ? "Придумайте пароль" : "Введите пароль"}
                  autoComplete={mode === "login" ? "current-password" : "new-password"}
                  className="pl-10 pr-12 h-12 rounded-xl text-sm"
                  style={{ background: "white", border: "1.5px solid hsl(35,20%,88%)" }}
                />
                <button
                  type="button"
                  tabIndex={-1}
                  onClick={() => setShowPassword((v) => !v)}
                  className="absolute right-3.5 top-1/2 -translate-y-1/2 w-7 h-7 flex items-center justify-center rounded-lg transition-colors hover:bg-muted"
                >
                  {showPassword
                    ? <EyeOff className="w-4 h-4 text-muted-foreground" />
                    : <Eye className="w-4 h-4 text-muted-foreground" />
                  }
                </button>
              </div>
            </div>

            {/* Error */}
            <AnimatePresence>
              {error && (
                <motion.div
                  initial={{ opacity: 0, y: -8, height: 0 }}
                  animate={{ opacity: 1, y: 0, height: "auto" }}
                  exit={{ opacity: 0, y: -8, height: 0 }}
                  className="px-4 py-3 rounded-xl text-sm"
                  style={{
                    background: "hsl(0,60%,97%)",
                    border: "1px solid hsl(0,60%,90%)",
                    color: "hsl(0,60%,45%)",
                  }}
                >
                  {error}
                </motion.div>
              )}
            </AnimatePresence>

            {/* Submit */}
            <Button
              type="submit"
              disabled={isLoadingAuth}
              className="w-full h-12 rounded-xl text-sm font-semibold gap-2 relative overflow-hidden"
              style={{
                background: "hsl(145,35%,38%)",
                color: "white",
                boxShadow: "0 4px 20px hsla(145,35%,38%,0.4)",
              }}
            >
              {isLoadingAuth ? (
                <div className="w-5 h-5 border-2 border-white/40 border-t-white rounded-full animate-spin" />
              ) : (
                <>
                  {mode === "login" ? "Войти в аккаунт" : "Создать аккаунт"}
                  <ArrowRight className="w-4 h-4" />
                </>
              )}
            </Button>
          </form>

          {/* Divider */}
          <div className="flex items-center gap-4 my-7">
            <div className="flex-1 h-px" style={{ background: "hsl(35,20%,88%)" }} />
            <span className="text-xs text-muted-foreground">или</span>
            <div className="flex-1 h-px" style={{ background: "hsl(35,20%,88%)" }} />
          </div>

          {/* Guest button */}
          <Link to="/explore">
            <Button
              variant="outline"
              className="w-full h-11 rounded-xl text-sm gap-2"
              style={{ borderColor: "hsl(35,20%,85%)" }}
            >
              <TreePine className="w-4 h-4 text-muted-foreground" />
              Продолжить как гость
            </Button>
          </Link>

          {/* Switch mode */}
          <p className="text-center text-sm text-muted-foreground mt-7">
            {mode === "login" ? "Нет аккаунта? " : "Уже есть аккаунт? "}
            <button
              type="button"
              onClick={() => { setMode(mode === "login" ? "register" : "login"); setLocalError(""); }}
              className="font-medium underline underline-offset-2 hover:no-underline transition-all"
              style={{ color: "hsl(145,35%,38%)" }}
            >
              {mode === "login" ? "Зарегистрироваться" : "Войти"}
            </button>
          </p>

          {/* Back link */}
          <div className="text-center mt-4">
            <Link to="/"
              className="text-xs text-muted-foreground/70 hover:text-muted-foreground transition-colors">
              ← На главную
            </Link>
          </div>
        </motion.div>
      </div>
    </div>
  );
}