/**
 * pages/Dashboard.jsx
 *
 * ИСПРАВЛЕНИЕ:
 * - loadTrees вызывается только когда user уже загружен (не null).
 *   Раньше при первом рендере user?.id был undefined — список грузился без фильтра.
 * - useEffect зависит от user?.id, а не от user целиком — нет лишних ре-запросов.
 */

import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { Plus, TreePine, Search } from "lucide-react";
import { Button }    from "@/components/ui/button";
import { Input }     from "@/components/ui/input";
import { toast }     from "@/components/ui/use-toast";
import TreeCard      from "@/components/dashboard/TreeCard";
import UserMenu      from "@/components/dashboard/UserMenu";
import PageHeader    from "@/components/common/PageHeader";
import EmptyState    from "@/components/common/EmptyState";
import { familiesApi } from "@/api";
import { useAuth }     from "@/lib/AuthContext";

export default function Dashboard() {
  const { user, logout } = useAuth();

  const [trees,       setTrees]       = useState([]);
  const [loading,     setLoading]     = useState(true);
  const [search,      setSearch]      = useState("");
  const [creating,    setCreating]    = useState(false);
  const [newTreeName, setNewTreeName] = useState("");

  // FIX: загружаем только когда user.id доступен
  useEffect(() => {
    if (!user?.id) return;
    loadTrees();
  }, [user?.id]); // eslint-disable-line react-hooks/exhaustive-deps

  const loadTrees = async () => {
    try {
      setLoading(true);
      const page = await familiesApi.list({ owner_id: user.id, limit: 100 });
      setTrees(page.result ?? []);
    } catch {
      toast({
        variant: "destructive",
        title: "Ошибка загрузки",
        description: "Не удалось загрузить список деревьев.",
      });
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
      toast({ title: "Дерево создано", description: `«${family.name}» готово к заполнению.` });
    } catch {
      toast({
        variant: "destructive",
        title: "Ошибка создания",
        description: "Не удалось создать дерево. Попробуйте ещё раз.",
      });
    }
  };

  const filtered = trees.filter((t) =>
    t.name.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="min-h-screen" style={{ background: "hsl(40,33%,98%)" }}>
      <PageHeader actions={<UserMenu user={user} onLogout={logout} />} />

      <main className="max-w-6xl mx-auto px-6 md:px-10 py-10">
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="mb-10">
          <h1 className="font-serif text-3xl md:text-4xl font-semibold text-foreground mb-2">
            Мои деревья 🌳
          </h1>
          <p className="text-muted-foreground">
            Добро пожаловать{user?.full_name ? `, ${user.full_name}` : ""}!
            Управляйте вашими семейными историями
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
          <SkeletonGrid />
        ) : filtered.length === 0 ? (
          <EmptyState
            emoji={search ? "🔍" : "🌱"}
            title={search ? "Ничего не найдено" : "Нет деревьев"}
            description={search ? "Попробуйте другой запрос" : "Создайте ваше первое семейное дерево!"}
          />
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

function SkeletonGrid() {
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
      {[1, 2, 3].map((i) => (
        <div key={i} className="h-40 rounded-2xl animate-pulse"
          style={{ background: "hsl(35,25%,93%)" }} />
      ))}
    </div>
  );
}
