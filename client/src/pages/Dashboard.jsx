import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { Plus, TreePine, Leaf, Search, LogOut } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { base44 } from "@/api/base44Client";
import TreeCard from "../components/dashboard/TreeCard";
import { Link } from "react-router-dom";

export default function Dashboard() {
  const [user, setUser] = useState(null);
  const [trees, setTrees] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [creating, setCreating] = useState(false);
  const [newTreeName, setNewTreeName] = useState("");

  useEffect(() => {
    const load = async () => {
      const [me, treeList] = await Promise.all([
        base44.auth.me(),
        base44.entities.FamilyTree.list("-created_date"),
      ]);
      setUser(me);
      setTrees(treeList);
      setLoading(false);
    };
    load();
  }, []);

  const createTree = async () => {
    if (!newTreeName.trim()) return;
    const tree = await base44.entities.FamilyTree.create({ name: newTreeName.trim(), is_public: false });
    setTrees((t) => [tree, ...t]);
    setNewTreeName("");
    setCreating(false);
  };

  const filtered = trees.filter((t) => t.name.toLowerCase().includes(search.toLowerCase()));

  return (
    <div className="min-h-screen" style={{ background: "hsl(40,33%,98%)" }}>
      {/* Header */}
      <header className="px-6 md:px-10 py-5 flex items-center justify-between"
        style={{ borderBottom: "1px solid hsl(35,20%,88%)", background: "hsla(40,33%,98%,0.9)", backdropFilter: "blur(16px)", position: "sticky", top: 0, zIndex: 30 }}>
        <Link to="/" className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-xl bg-primary flex items-center justify-center">
            <Leaf className="w-4 h-4 text-primary-foreground" />
          </div>
          <span className="font-serif font-semibold text-xl text-foreground">KinTree</span>
        </Link>
        <div className="flex items-center gap-3">
          {user && (
            <div className="hidden md:flex items-center gap-2 text-sm text-muted-foreground">
              <div className="w-7 h-7 rounded-full bg-primary/20 flex items-center justify-center text-xs font-semibold text-primary">
                {user.full_name?.[0] || user.email?.[0] || "U"}
              </div>
              {user.full_name || user.email}
            </div>
          )}
          <Button
            variant="ghost"
            size="sm"
            className="text-muted-foreground gap-2"
            onClick={() => base44.auth.logout("/")}
          >
            <LogOut className="w-4 h-4" />
            <span className="hidden sm:inline">Выйти</span>
          </Button>
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-6 md:px-10 py-10">
        {/* Welcome */}
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="mb-10">
          <h1 className="font-serif text-3xl md:text-4xl font-semibold text-foreground mb-2">
            Мои деревья 🌳
          </h1>
          <p className="text-muted-foreground">
            Добро пожаловать{user?.full_name ? `, ${user.full_name}` : ""}! Управляйте вашими семейными историями
          </p>
        </motion.div>

        {/* Actions bar */}
        <div className="flex flex-col sm:flex-row gap-4 mb-8">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
            <Input
              placeholder="Поиск деревьев..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="pl-10 rounded-xl"
              style={{ background: "white", border: "1px solid hsl(35,20%,88%)" }}
            />
          </div>
          <Button
            className="rounded-xl gap-2 bg-primary text-primary-foreground hover:bg-primary/90 px-6"
            onClick={() => setCreating(true)}
          >
            <Plus className="w-4 h-4" />
            Новое дерево
          </Button>
        </div>

        {/* Create inline */}
        {creating && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            className="mb-6 p-5 rounded-2xl flex flex-col sm:flex-row gap-3 items-start sm:items-center"
            style={{ background: "hsl(145,35%,95%)", border: "1px solid hsl(145,35%,80%)" }}
          >
            <TreePine className="w-5 h-5 flex-shrink-0" style={{ color: "hsl(145,35%,38%)" }} />
            <Input
              autoFocus
              placeholder="Название дерева (например: Семья Ивановых)"
              value={newTreeName}
              onChange={(e) => setNewTreeName(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && createTree()}
              className="flex-1 rounded-xl"
              style={{ background: "white" }}
            />
            <div className="flex gap-2 w-full sm:w-auto">
              <Button size="sm" className="flex-1 sm:flex-none rounded-xl bg-primary text-primary-foreground" onClick={createTree}>
                Создать
              </Button>
              <Button size="sm" variant="outline" className="flex-1 sm:flex-none rounded-xl" onClick={() => setCreating(false)}>
                Отмена
              </Button>
            </div>
          </motion.div>
        )}

        {/* Trees Grid */}
        {loading ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
            {[...Array(3)].map((_, i) => (
              <div key={i} className="rounded-2xl h-52 animate-pulse" style={{ background: "hsl(35,25%,93%)" }} />
            ))}
          </div>
        ) : filtered.length === 0 ? (
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="text-center py-24">
            <div className="text-6xl mb-5">🌱</div>
            <h3 className="font-serif text-2xl font-semibold text-foreground mb-3">
              {search ? "Ничего не найдено" : "Нет деревьев"}
            </h3>
            <p className="text-muted-foreground mb-6">
              {search ? "Попробуйте другой запрос" : "Создайте своё первое семейное дерево"}
            </p>
            {!search && (
              <Button
                className="rounded-xl gap-2 bg-primary text-primary-foreground"
                onClick={() => setCreating(true)}
              >
                <Plus className="w-4 h-4" /> Создать дерево
              </Button>
            )}
          </motion.div>
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