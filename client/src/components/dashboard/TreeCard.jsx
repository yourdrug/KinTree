/**
 * components/dashboard/TreeCard.jsx
 */

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Users, Lock, Globe, ArrowRight, TreePine, Eye, EyeOff, Loader2 } from "lucide-react";
import { Link } from "react-router-dom";
import { toast } from "@/components/ui/use-toast";
import { familiesApi } from "@/api";
import { ROUTES } from "@/lib/routes";

export default function TreeCard({ tree: initialTree, index, onUpdate }) {
  const [tree,    setTree]    = useState(initialTree);
  const [loading, setLoading] = useState(false);

  const togglePublic = async (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (loading) return;
    setLoading(true);
    try {
      const updated = await familiesApi.setPublic(tree.id, !tree.is_public);
      setTree(updated);
      onUpdate?.(updated);
      toast({
        title: updated.is_public ? "Дерево стало публичным" : "Дерево стало приватным",
        description: updated.is_public
          ? "Теперь любой может просмотреть его по ссылке."
          : "Дерево видно только вам.",
      });
    } catch {
      toast({ variant: "destructive", title: "Ошибка", description: "Не удалось изменить видимость." });
    } finally {
      setLoading(false);
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.08 }}
      whileHover={{ y: -4 }}
      className="group relative rounded-2xl overflow-hidden"
      style={{ border: "1px solid hsl(35,20%,88%)", background: "white" }}
    >
      {/* Cover */}
      <div
        className="h-36 relative overflow-hidden"
        style={{
          background: tree.cover_image
            ? `url(${tree.cover_image}) center/cover`
            : `linear-gradient(135deg, hsl(145,35%,${85 - index * 5}%) 0%, hsl(30,50%,${88 - index * 3}%) 100%)`,
        }}
      >
        <div
          className="absolute inset-0"
          style={{ background: "linear-gradient(to bottom, transparent 40%, hsla(30,10%,15%,0.3))" }}
        />
        <div className="absolute top-3 left-3">
          <div
            className="w-8 h-8 rounded-xl flex items-center justify-center"
            style={{ background: "hsla(255,255%,255%,0.2)", backdropFilter: "blur(8px)" }}
          >
            <TreePine className="w-4 h-4 text-white" />
          </div>
        </div>

        {/* Visibility badge + toggle */}
        <div className="absolute top-3 right-3 flex items-center gap-1.5">
          <div
            className="px-2 py-1 rounded-lg flex items-center gap-1 text-white text-xs"
            style={{ background: "hsla(255,255%,255%,0.2)", backdropFilter: "blur(8px)" }}
          >
            {tree.is_public ? <Globe className="w-3 h-3" /> : <Lock className="w-3 h-3" />}
            {tree.is_public ? "Публичное" : "Приватное"}
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="p-5">
        <h3 className="font-serif font-semibold text-lg text-foreground mb-1">{tree.name}</h3>
        {tree.description && (
          <p className="text-sm text-muted-foreground mb-4 line-clamp-2">{tree.description}</p>
        )}

        <div className="flex items-center justify-between mt-3 gap-2">
          <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
            <Users className="w-3.5 h-3.5" />
            <span>Семейное дерево</span>
          </div>

          <div className="flex items-center gap-2">
            {/* Toggle public/private button */}
            <motion.button
              whileTap={{ scale: 0.93 }}
              onClick={togglePublic}
              disabled={loading}
              title={tree.is_public ? "Сделать приватным" : "Сделать публичным"}
              className="flex items-center gap-1 px-2.5 py-1.5 rounded-xl text-xs font-medium transition-all"
              style={{
                background: tree.is_public ? "hsl(210,60%,95%)" : "hsl(35,30%,95%)",
                color:      tree.is_public ? "hsl(210,60%,38%)" : "hsl(30,10%,45%)",
                border:     tree.is_public ? "1px solid hsl(210,50%,82%)" : "1px solid hsl(35,20%,85%)",
              }}
            >
              <AnimatePresence mode="wait" initial={false}>
                {loading ? (
                  <motion.span key="spin" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
                    <Loader2 className="w-3 h-3 animate-spin" />
                  </motion.span>
                ) : tree.is_public ? (
                  <motion.span key="pub" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
                    className="flex items-center gap-1">
                    <EyeOff className="w-3 h-3" /> Скрыть
                  </motion.span>
                ) : (
                  <motion.span key="priv" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
                    className="flex items-center gap-1">
                    <Eye className="w-3 h-3" /> Открыть
                  </motion.span>
                )}
              </AnimatePresence>
            </motion.button>

            <Link to={ROUTES.tree(tree.id)}>
              <motion.div
                whileHover={{ x: 3 }}
                className="flex items-center gap-1 text-xs font-medium group-hover:text-primary transition-colors"
                style={{ color: "hsl(145,35%,38%)" }}
              >
                Открыть <ArrowRight className="w-3.5 h-3.5" />
              </motion.div>
            </Link>
          </div>
        </div>

        {/* Public link hint */}
        <AnimatePresence>
          {tree.is_public && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: "auto" }}
              exit={{ opacity: 0, height: 0 }}
              className="mt-3 overflow-hidden"
            >
              <div
                className="flex items-center gap-2 px-3 py-2 rounded-xl text-xs"
                style={{ background: "hsl(210,60%,96%)", border: "1px solid hsl(210,50%,86%)", color: "hsl(210,50%,38%)" }}
              >
                <Globe className="w-3 h-3 flex-shrink-0" />
                <span className="truncate">Доступно по прямой ссылке</span>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </motion.div>
  );
}
