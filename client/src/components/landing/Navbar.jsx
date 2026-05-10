/**
 * components/landing/Navbar.jsx
 *
 * Исправлено: адаптируется под авторизованного пользователя.
 */

import { motion } from "framer-motion";
import { Leaf, LayoutDashboard } from "lucide-react";
import { Button }         from "@/components/ui/button";
import { useAppNavigate } from "@/lib/navigation";
import { useAuth }        from "@/lib/AuthContext";

export default function Navbar() {
  const nav = useAppNavigate();
  const { isAuthenticated, user } = useAuth();

  const initial = (user?.full_name?.[0] || user?.email?.[0] || "").toUpperCase();

  return (
    <motion.nav
      initial={{ y: -20, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      transition={{ duration: 0.6 }}
      className="fixed top-0 left-0 right-0 z-50 flex items-center justify-between px-6 md:px-12 py-4"
      style={{
        background: "hsla(40,33%,98%,0.85)",
        backdropFilter: "blur(20px)",
        borderBottom: "1px solid hsla(35,20%,88%,0.6)",
      }}
    >
      {/* Лого */}
      <div className="flex items-center gap-2">
        <div className="w-8 h-8 rounded-xl bg-primary flex items-center justify-center">
          <Leaf className="w-4 h-4 text-primary-foreground" />
        </div>
        <span className="font-serif font-semibold text-xl text-foreground">KinTree</span>
      </div>

      {/* Центральные ссылки */}
      <div className="hidden md:flex items-center gap-8 text-sm text-muted-foreground">
        <a href="#features" className="hover:text-foreground transition-colors">Возможности</a>
        <a href="#how"      className="hover:text-foreground transition-colors">Как работает</a>
        <a href="#"         className="hover:text-foreground transition-colors">Цены</a>
      </div>

      {/* Правая часть */}
      <div className="flex items-center gap-3">
        {isAuthenticated ? (
          <>
            {/* Аватар с инициалом */}
            {initial && (
              <div className="w-8 h-8 rounded-full bg-primary/15 flex items-center justify-center text-xs font-semibold text-primary">
                {initial}
              </div>
            )}
            <Button
              size="sm"
              className="bg-primary text-primary-foreground hover:bg-primary/90 rounded-xl px-5 gap-1.5"
              onClick={() => nav.toDashboard()}
            >
              <LayoutDashboard className="w-3.5 h-3.5" />
              Мои деревья
            </Button>
          </>
        ) : (
          <>
            <Button
              variant="ghost"
              size="sm"
              className="text-muted-foreground hover:text-foreground"
              onClick={() => nav.toLogin()}
            >
              Войти
            </Button>
            <Button
              size="sm"
              className="bg-primary text-primary-foreground hover:bg-primary/90 rounded-xl px-5"
              onClick={() => nav.toLogin()}
            >
              Начать
            </Button>
          </>
        )}
      </div>
    </motion.nav>
  );
}
