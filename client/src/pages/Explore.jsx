/**
 * pages/Explore.jsx
 */

import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { Search, Globe, TreePine, Info } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input }  from "@/components/ui/input";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Link }   from "react-router-dom";
import PageHeader from "@/components/common/PageHeader";
import EmptyState from "@/components/common/EmptyState";
import { useAppNavigate } from "@/lib/navigation";
import { ROUTES }         from "@/lib/routes";

export default function Explore() {
  const nav = useAppNavigate();

  const [trees,   setTrees]   = useState([]);
  const [loading, setLoading] = useState(true);
  const [search,  setSearch]  = useState("");

  useEffect(() => {
    // TODO: загрузить публичные деревья через API
    setTrees([]);
    setLoading(false);
  }, []);

  const filtered = trees.filter((t) =>
    t.name.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="min-h-screen" style={{ background: "hsl(40,33%,98%)" }}>
      <PageHeader
        backTo={ROUTES.home()}
        backLabel="На главную"
        actions={
          <Button size="sm" className="rounded-xl gap-2 bg-primary text-primary-foreground"
            onClick={() => nav.toLogin()}>
            Войти и создать дерево
          </Button>
        }
      />

      <main className="max-w-5xl mx-auto px-6 md:px-10 py-10">
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="mb-10">
          <div className="flex items-center gap-2 mb-3">
            <Globe className="w-5 h-5 text-primary" />
            <span className="text-sm font-medium text-primary">Публичные деревья</span>
          </div>
          <h1 className="font-serif text-3xl md:text-4xl font-semibold text-foreground mb-3">
            Исследуйте семейные истории
          </h1>
          <p className="text-muted-foreground text-lg">
            Просматривайте деревья других семей в режиме гостя.
          </p>
        </motion.div>

        <div className="relative mb-6">
          <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-muted-foreground" />
          <Input
            placeholder="Поиск публичных деревьев..."
            value={search} onChange={(e) => setSearch(e.target.value)}
            className="pl-12 py-6 text-base rounded-2xl"
            style={{ background: "white", border: "1px solid hsl(35,20%,88%)" }}
          />
        </div>

        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.15 }} className="mb-8">
          <Alert className="rounded-2xl border" style={{ borderColor: "hsl(30,40%,88%)", background: "hsl(30,50%,96%)" }}>
            <Info className="h-4 w-4" style={{ color: "hsl(30,50%,50%)" }} />
            <AlertDescription style={{ color: "hsl(30,20%,35%)" }}>
              <strong>Режим гостя:</strong> вы можете просматривать публичные деревья, но не можете их редактировать.{" "}
              <button onClick={() => nav.toLogin()}
                className="underline font-medium hover:no-underline" style={{ color: "hsl(145,35%,38%)" }}>
                Войдите
              </button>
              , чтобы создать своё дерево.
            </AlertDescription>
          </Alert>
        </motion.div>

        {loading ? (
          <SkeletonGrid />
        ) : filtered.length === 0 ? (
          <EmptyState
            emoji={search ? "🔍" : "🌳"}
            title={search ? "Ничего не найдено" : "Нет публичных деревьев"}
            description={search ? "Попробуйте другой запрос" : "Будьте первым — создайте своё дерево!"}
          />
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
            {filtered.map((tree, i) => (
              <PublicTreeCard key={tree.id} tree={tree} index={i} />
            ))}
          </div>
        )}
      </main>
    </div>
  );
}

function PublicTreeCard({ tree, index }) {
  return (
    <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.06 }} whileHover={{ y: -4 }}>
      <Link to={ROUTES.tree(tree.id)} className="block rounded-2xl overflow-hidden"
        style={{ border: "1px solid hsl(35,20%,88%)", background: "white" }}>
        <div className="h-32 relative flex items-center justify-center"
          style={{
            background: `linear-gradient(135deg,
              hsl(145,35%,${82 - index * 3}%) 0%,
              hsl(30,50%,${88 - index * 2}%) 100%)`,
          }}>
          <TreePine className="w-12 h-12 text-white/50" />
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
  );
}

function SkeletonGrid() {
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
      {[...Array(6)].map((_, i) => (
        <div key={i} className="rounded-2xl h-44 animate-pulse" style={{ background: "hsl(35,25%,93%)" }} />
      ))}
    </div>
  );
}
