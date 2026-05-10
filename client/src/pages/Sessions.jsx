/**
 * pages/Sessions.jsx
 *
 * ИСПРАВЛЕНИЕ:
 * - useEffect([fetchSessions]) — fetchSessions из useSession() должен быть стабильным.
 *   В AuthContext fetchSessions уже обёрнут в useCallback — это корректно.
 *   Но если AuthContext пересоздаёт функцию — добавлен guard через useRef.
 *   Теперь fetchSessions вызывается только при монтировании (один раз).
 */

import { useEffect, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Monitor, Smartphone, Globe,
  LogOut, Trash2, ShieldAlert, Clock, Wifi,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import PageHeader from "@/components/common/PageHeader";
import { useAuth, useSession } from "@/lib/AuthContext";
import { ROUTES } from "@/lib/routes";

// ─── UA parser ────────────────────────────────────────────────────────────────

function parseUA(ua) {
  if (!ua) return { name: "Неизвестное устройство", icon: "globe" };
  const s = ua.toLowerCase();
  const isMobile = /mobile|android|iphone|ipad/.test(s);

  let browser = "Браузер";
  if      (s.includes("chrome") && !s.includes("edg")) browser = "Chrome";
  else if (s.includes("firefox"))                       browser = "Firefox";
  else if (s.includes("safari") && !s.includes("chrome")) browser = "Safari";
  else if (s.includes("edg"))                           browser = "Edge";
  else if (s.includes("opera") || s.includes("opr"))   browser = "Opera";

  let os = "";
  if      (s.includes("windows")) os = "Windows";
  else if (s.includes("mac"))     os = "macOS";
  else if (s.includes("iphone"))  os = "iPhone";
  else if (s.includes("ipad"))    os = "iPad";
  else if (s.includes("android")) os = "Android";
  else if (s.includes("linux"))   os = "Linux";

  return {
    name: [browser, os].filter(Boolean).join(" · "),
    icon: isMobile ? "mobile" : "monitor",
  };
}

function DeviceIcon({ type }) {
  const cls = "w-5 h-5";
  if (type === "mobile")  return <Smartphone className={cls} />;
  if (type === "monitor") return <Monitor className={cls} />;
  return <Globe className={cls} />;
}

function formatDate(iso) {
  if (!iso) return "—";
  return new Date(iso).toLocaleString("ru-RU", {
    day: "numeric", month: "long", hour: "2-digit", minute: "2-digit",
  });
}

function formatExpiry(iso) {
  if (!iso) return "";
  const diff = new Date(iso) - Date.now();
  const days  = Math.floor(diff / 86400000);
  if (days > 1)  return `истекает через ${days} дн.`;
  const hours = Math.floor(diff / 3600000);
  if (hours > 0) return `истекает через ${hours} ч.`;
  return "истекает скоро";
}

// ─── SessionCard ──────────────────────────────────────────────────────────────

function SessionCard({ session, onRevoke }) {
  const { name, icon } = parseUA(session.user_agent);
  const isCurrent = session.is_current;

  return (
    <motion.div
      layout
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, x: -20, height: 0, marginBottom: 0 }}
      transition={{ duration: 0.2 }}
      className="flex items-start gap-4 p-4 rounded-2xl"
      style={{
        background: isCurrent ? "hsl(145,35%,96%)" : "white",
        border: isCurrent
          ? "1.5px solid hsl(145,35%,82%)"
          : "1px solid hsl(35,20%,90%)",
      }}
    >
      <div
        className="w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0 mt-0.5"
        style={{ background: isCurrent ? "hsl(145,35%,88%)" : "hsl(35,25%,93%)" }}
      >
        <DeviceIcon type={icon} />
      </div>

      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 mb-1">
          <span className="font-medium text-sm text-foreground truncate">{name}</span>
          {isCurrent && (
            <span
              className="text-xs px-2 py-0.5 rounded-full font-medium flex-shrink-0"
              style={{ background: "hsl(145,35%,82%)", color: "hsl(145,35%,28%)" }}
            >
              Текущая
            </span>
          )}
        </div>
        <div className="flex flex-wrap gap-x-4 gap-y-0.5 text-xs text-muted-foreground">
          {session.ip_address && (
            <span className="flex items-center gap-1">
              <Wifi className="w-3 h-3" />{session.ip_address}
            </span>
          )}
          {session.created_at && (
            <span className="flex items-center gap-1">
              <Clock className="w-3 h-3" />Создана {formatDate(session.created_at)}
            </span>
          )}
          {session.expires_at && (
            <span className="text-muted-foreground/60">{formatExpiry(session.expires_at)}</span>
          )}
        </div>
      </div>

      {!isCurrent && (
        <Button
          variant="ghost" size="sm"
          onClick={() => onRevoke(session.session_id)}
          className="flex-shrink-0 text-muted-foreground hover:text-destructive hover:bg-destructive/8 rounded-xl"
        >
          <Trash2 className="w-4 h-4" />
        </Button>
      )}
    </motion.div>
  );
}

// ─── Page ──────────────────────────────────────────────────────────────────────

export default function Sessions() {
  const { logoutAll } = useAuth();
  const { sessions, isLoadingSessions, sessionsError, fetchSessions, revokeSession } = useSession();

  // FIX: fetchSessions вызываем один раз при монтировании через ref-guard.
  // Это защищает от повторного вызова если AuthContext по какой-то причине
  // пересоздаст fetchSessions (хотя с useCallback это не должно происходить).
  const fetchedRef = useRef(false);
  useEffect(() => {
    if (fetchedRef.current) return;
    fetchedRef.current = true;
    fetchSessions();
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const currentSession = sessions.find((s) => s.is_current);
  const otherSessions  = sessions.filter((s) => !s.is_current);

  return (
    <div className="min-h-screen" style={{ background: "hsl(40,33%,98%)" }}>
      <PageHeader backTo={ROUTES.dashboard()} />

      <main className="max-w-2xl mx-auto px-6 md:px-10 py-10">
        <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} className="mb-8">
          <h1 className="font-serif text-3xl font-semibold text-foreground mb-2">
            Активные сессии
          </h1>
          <p className="text-muted-foreground">
            Управляйте устройствами, на которых вы вошли в KinTree.
            Если вы не узнаёте сессию — завершите её.
          </p>
        </motion.div>

        {sessions.length > 2 && (
          <motion.div
            initial={{ opacity: 0 }} animate={{ opacity: 1 }}
            className="mb-6 p-4 rounded-2xl flex items-start gap-3"
            style={{ background: "hsl(38,90%,96%)", border: "1px solid hsl(38,80%,86%)" }}
          >
            <ShieldAlert className="w-4 h-4 mt-0.5 flex-shrink-0" style={{ color: "hsl(38,80%,45%)" }} />
            <p className="text-sm" style={{ color: "hsl(38,40%,30%)" }}>
              У вас {sessions.length} активных сессий. Если не узнаёте некоторые —{" "}
              <button
                onClick={logoutAll}
                className="underline font-medium hover:no-underline"
                style={{ color: "hsl(145,35%,35%)" }}
              >
                выйдите со всех устройств
              </button>.
            </p>
          </motion.div>
        )}

        {isLoadingSessions && <SkeletonList />}

        {sessionsError && !isLoadingSessions && (
          <div
            className="p-4 rounded-2xl text-sm"
            style={{ background: "hsl(0,60%,97%)", border: "1px solid hsl(0,60%,90%)", color: "hsl(0,60%,45%)" }}
          >
            {sessionsError}
          </div>
        )}

        {!isLoadingSessions && !sessionsError && (
          <div className="space-y-3">
            {currentSession && (
              <SessionCard session={currentSession} onRevoke={revokeSession} />
            )}
            <AnimatePresence mode="popLayout">
              {otherSessions.map((s) => (
                <SessionCard key={s.session_id} session={s} onRevoke={revokeSession} />
              ))}
            </AnimatePresence>
            {sessions.length === 0 && (
              <p className="text-center py-10 text-muted-foreground text-sm">
                Нет активных сессий
              </p>
            )}
          </div>
        )}

        {sessions.length > 0 && !isLoadingSessions && (
          <motion.div
            initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.2 }}
            className="mt-8 pt-8" style={{ borderTop: "1px solid hsl(35,20%,88%)" }}
          >
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
              <div>
                <p className="font-medium text-sm text-foreground">Выйти со всех устройств</p>
                <p className="text-xs text-muted-foreground mt-0.5">
                  Завершит все {sessions.length} сессии, включая текущую
                </p>
              </div>
              <Button
                variant="outline" onClick={logoutAll}
                className="gap-2 rounded-xl text-sm flex-shrink-0"
                style={{ borderColor: "hsl(0,60%,88%)", color: "hsl(0,60%,45%)" }}
              >
                <LogOut className="w-4 h-4" />
                Выйти везде
              </Button>
            </div>
          </motion.div>
        )}
      </main>
    </div>
  );
}

function SkeletonList() {
  return (
    <div className="space-y-3">
      {[1, 2].map((i) => (
        <div key={i} className="h-20 rounded-2xl animate-pulse"
          style={{ background: "hsl(35,25%,93%)" }} />
      ))}
    </div>
  );
}
