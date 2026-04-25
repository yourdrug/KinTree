import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { Search, Globe, Leaf, ArrowLeft, TreePine, Lock } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { base44 } from "@/api/base44Client";
import { Link } from "react-router-dom";

export default function Explore() {
  const [trees, setTrees] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");

  useEffect(() => {
    const load = async () => {
      const all = await base44.entities.FamilyTree.filter({ is_public: true }, "-created_date", 50);
      setTrees(all || []);
      setLoading(false);
    };
    load();
  }, []);

  const filtered = trees.filter((t) => t.name.toLowerCase().includes(search.toLowerCase()));

  return (
    <div className="min-h-screen" style={{ background: "hsl(40,33%,98%)" }}>
      {/* Header */}
      <header className="px-6 md:px-10 py-5 flex items-center justify-between sticky top-0 z-20"
        style={{ borderBottom: "1px solid hsl(35,20%,88%)", background: "hsla(40,33%,98%,0.9)", backdropFilter: "blur(16px)" }}>
        <div className="flex items-center gap-3">
          <Link to="/">
            <Button variant="ghost" size="sm" className="rounded-xl gap-2 text-muted-foreground">
              <ArrowLeft className="w-4 h-4" /> На главную
            </Button>
          </Link>
          <div className="w-px h-5 bg-border" />
          <div className="flex items-center gap-2">
            <div className="w-7 h-7 rounded-lg bg-primary flex items-center justify-center">
              <Leaf className="w-3.5 h-3.5 text-primary-foreground" />
            </div>
            <span className="font-serif font-semibold text-foreground">KinTree</span>
          </div>
        </div>
        <Button
          size="sm"
          className="rounded-xl gap-2 bg-primary text-primary-foreground"
          onClick={() => base44.auth.redirectToLogin()}
        >
          Войти и создать дерево
        </Button>
      </header>

      <main className="max-w-5xl mx-auto px-6 md:px-10 py-10">
        {/* Hero */}
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="mb-10">
          <div className="flex items-center gap-2 mb-3">
            <Globe className="w-5 h-5 text-primary" />
            <span className="text-sm font-medium text-primary">Публичные деревья</span>
          </div>
          <h1 className="font-serif text-3xl md:text-4xl font-semibold text-foreground mb-3">
            Исследуйте семейные истории
          </h1>
          <p className="text-muted-foreground text-lg">
            Просматривайте деревья других семей в режиме гостя. Войдите, чтобы создать своё.
          </p>
        </motion.div>

        {/* Search */}
        <div className="relative mb-8">
          <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-muted-foreground" />
          <Input
            placeholder="Поиск публичных деревьев..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="pl-12 py-6 text-base rounded-2xl"
            style={{ background: "white", border: "1px solid hsl(35,20%,88%)" }}
          />
        </div>

        {/* Guest info banner */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.2 }}
          className="mb-8 p-4 rounded-2xl flex items-start gap-3"
          style={{ background: "hsl(30,50%,96%)", border: "1px solid hsl(30,40%,88%)" }}
        >
          <Lock className="w-4 h-4 mt-0.5 flex-shrink-0" style={{ color: "hsl(30,50%,50%)" }} />
          <div className="text-sm" style={{ color: "hsl(30,20%,35%)" }}>
            <strong>Режим гостя:</strong> вы можете просматривать публичные деревья, но не можете их редактировать.{" "}
            <button onClick={() => base44.auth.redirectToLogin()}
              className="underline font-medium hover:no-underline" style={{ color: "hsl(145,35%,38%)" }}>
              Войдите
            </button>{" "}
            чтобы создать своё дерево.
          </div>
        </motion.div>

        {/* Trees */}
        {loading ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
            {[...Array(6)].map((_, i) => (
              <div key={i} className="rounded-2xl h-44 animate-pulse" style={{ background: "hsl(35,25%,93%)" }} />
            ))}
          </div>
        ) : filtered.length === 0 ? (
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="text-center py-20">
            <div className="text-6xl mb-5">🔍</div>
            <h3 className="font-serif text-xl font-semibold text-foreground mb-2">
              {search ? "Ничего не найдено" : "Нет публичных деревьев"}
            </h3>
            <p className="text-muted-foreground">
              {search ? "Попробуйте другой запрос" : "Будьте первым — создайте своё дерево!"}
            </p>
          </motion.div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
            {filtered.map((tree, i) => (
              <motion.div
                key={tree.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.06 }}
                whileHover={{ y: -4 }}
              >
                <Link to={`/tree/${tree.id}`} className="block rounded-2xl overflow-hidden group"
                  style={{ border: "1px solid hsl(35,20%,88%)", background: "white" }}>
                  <div className="h-32 relative"
                    style={{
                      background: `linear-gradient(135deg, hsl(145,35%,${82 - i * 3}%) 0%, hsl(30,50%,${88 - i * 2}%) 100%)`
                    }}>
                    <div className="absolute inset-0 flex items-center justify-center">
                      <TreePine className="w-12 h-12 text-white/50" />
                    </div>
                  </div>
                  <div className="p-4">
                    <h3 className="font-serif font-semibold text-foreground mb-1">{tree.name}</h3>
                    {tree.description && (
                      <p className="text-xs text-muted-foreground line-clamp-2">{tree.description}</p>
                    )}
                    <div className="mt-3 flex items-center gap-1 text-xs font-medium"
                      style={{ color: "hsl(145,35%,38%)" }}>
                      <Globe className="w-3 h-3" /> Публичное
                    </div>
                  </div>
                </Link>
              </motion.div>
            ))}
          </div>
        )}
      </main>
    </div>
  );
}