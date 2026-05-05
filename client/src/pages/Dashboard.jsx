/**
 * pages/Dashboard.jsx
 *
 * Изменения:
 *  - window.location.href → useAppNavigate
 *  - <Link> использует ROUTES
 *  - UserMenu ссылки через ROUTES
 */

import { useState, useEffect, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Plus, TreePine, Leaf, Search, LogOut, Shield, ChevronDown } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input }  from "@/components/ui/input";
import TreeCard    from "../components/dashboard/TreeCard";
import { Link }           from "react-router-dom";
import { familiesApi }    from "@/api";
import { useAuth }        from "@/lib/AuthContext";
import { useAppNavigate } from "@/lib/navigation";
import { ROUTES }         from "@/lib/routes";

// ─── User menu ─────────────────────────────────────────────────────────────────

function UserMenu({ user, onLogout }) {
  const nav   = useAppNavigate();
  const [open, setOpen] = useState(false);
  const ref   = useRef(null);

  useEffect(() => {
    const handler = (e) => {
      if (ref.current && !ref.current.contains(e.target)) setOpen(false);
    };
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, []);

  const initial = (user?.full_name?.[0] || user?.email?.[0] || "U").toUpperCase();

  return (
    <div ref={ref} className="relative">
      <button
        onClick={() => setOpen((v) => !v)}
        className="flex items-center gap-2 rounded-xl px-3 py-2 text-sm transition-colors hover:bg-black/5"
      >
        <div className="w-7 h-7 rounded-full bg-primary/20 flex items-center justify-center text-xs font-semibold text-primary">
          {initial}
        </div>
        <span className="hidden md:block text-muted-foreground max-w-32 truncate">
          {user?.full_name || user?.email}
        </span>
        <ChevronDown className="w-3.5 h-3.5 text-muted-foreground" />
      </button>

      <AnimatePresence>
        {open && (
          <motion.div
            initial={{ opacity: 0, y: 6, scale: 0.97 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 6, scale: 0.97 }}
            transition={{ duration: 0.12 }}
            className="absolute right-0 top-full mt-1.5 w-52 rounded-2xl overflow-hidden z-50"
            style={{
              background: "white",
              border: "1px solid hsl(35,20%,88%)",
              boxShadow: "0 8px 32px hsla(30,10%,15%,0.12)",
            }}
          >
            <div className="px-4 py-3 border-b" style={{ borderColor: "hsl(35,20%,92%)" }}>
              <p className="text-xs text-muted-foreground">Вы вошли как</p>
              <p className="text-sm font-medium text-foreground truncate mt-0.5">{user?.email}</p>
            </div>
            <div className="py-1.5">
              <Link
                to={ROUTES.settings.sessions()}
                onClick={() => setOpen(false)}
                className="flex items-center gap-3 px-4 py-2.5 text-sm text-foreground hover:bg-muted/50 transition-colors"
              >
                <Shield className="w-4 h-4 text-muted-foreground" />
                Активные сессии
              </Link>
              <button
                onClick={() => { setOpen(false); onLogout(); }}
                className="flex w-full items-center gap-3 px-4 py-2.5 text-sm transition-colors hover:bg-muted/50"
                style={{ color: "hsl(0,60%,45%)" }}
              >
                <LogOut className="w-4 h-4" />
                Выйти
              </button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

// ─── Dashboard ─────────────────────────────────────────────────────────────────

export default function Dashboard() {
  const { user, logout } = useAuth();
  const nav = useAppNavigate();

  const [trees,       setTrees]       = useState([]);
  const [loading,     setLoading]     = useState(true);
  const [search,      setSearch]      = useState("");
  const [creating,    setCreating]    = useState(false);
  const [newTreeName, setNewTreeName] = useState("");

  useEffect(() => { loadTrees(); }, []);

  const loadTrees = async () => {
    try {
      setLoading(true);
      const page = await familiesApi.list({ owner_id: user?.id, limit: 100 });
      setTrees(page.result ?? []);
    } catch (err) {
      console.error("Failed to load families:", err.message);
    } finally {
      setLoading(false);
    }
  };

  const createTree = async () => {
    if (!newTreeName.trim()) return;
    try {
      const family = await familiesApi.create({ name: newTreeName.trim() });
      setTrees((prev) => [family, ...prev]);
      setNewTreeName("");
      setCreating(false);
    } catch (err) {
      console.error("Create family failed:", err.message);
    }
  };

  const filtered = trees.filter((t) =>
    t.name.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="min-h-screen" style={{ background: "hsl(40,33%,98%)" }}>
      {/* Header */}
      <header
        className="px-6 md:px-10 py-5 flex items-center justify-between sticky top-0 z-30"
        style={{
          borderBottom: "1px solid hsl(35,20%,88%)",
          background: "hsla(40,33%,98%,0.9)",
          backdropFilter: "blur(16px)",
        }}
      >
        <Link to={ROUTES.home()} className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-xl bg-primary flex items-center justify-center">
            <Leaf className="w-4 h-4 text-primary-foreground" />
          </div>
          <span className="font-serif font-semibold text-xl text-foreground">KinTree</span>
        </Link>

        <UserMenu user={user} onLogout={logout} />
      </header>

      <main className="max-w-6xl mx-auto px-6 md:px-10 py-10">
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="mb-10">
          <h1 className="font-serif text-3xl md:text-4xl font-semibold text-foreground mb-2">
            Мои деревья 🌳
          </h1>
          <p className="text-muted-foreground">
            Добро пожаловать{user?.full_name ? `, ${user.full_name}` : ""}! Управляйте вашими семейными историями
          </p>
        </motion.div>

        <div className="flex flex-col sm:flex-row gap-4 mb-8">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
            <Input
              placeholder="Поиск деревьев..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="pl-10 rounded-xl"
            />
          </div>
          <Button className="rounded-xl gap-2" onClick={() => setCreating(true)}>
            <Plus className="w-4 h-4" /> Новое дерево
          </Button>
        </div>

        {creating && (
          <motion.div
            initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }}
            className="mb-6 p-5 rounded-2xl flex flex-col sm:flex-row gap-3"
            style={{ background: "white", border: "1px solid hsl(35,20%,88%)" }}
          >
            <TreePine className="w-5 h-5 text-muted-foreground mt-2.5 flex-shrink-0" />
            <Input
              autoFocus
              placeholder="Название дерева"
              value={newTreeName}
              onChange={(e) => setNewTreeName(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && createTree()}
              className="flex-1"
            />
            <Button onClick={createTree}>Создать</Button>
            <Button variant="outline" onClick={() => setCreating(false)}>Отмена</Button>
          </motion.div>
        )}

        {loading ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
            {[1, 2, 3].map((i) => (
              <div key={i} className="h-40 rounded-2xl animate-pulse"
                style={{ background: "hsl(35,25%,93%)" }} />
            ))}
          </div>
        ) : filtered.length === 0 ? (
          <div className="text-center py-20 text-muted-foreground">
            {search ? "Ничего не найдено" : "Нет деревьев — создайте первое!"}
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
            {filtered.map((tree, i) => (
              <TreeCard key={tree.id} tree={tree} index={i} />
            ))}
          </div>
        )}
      </main>
    </div>
  );
}
