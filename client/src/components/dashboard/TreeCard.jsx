import { motion } from "framer-motion";
import { Users, Lock, Globe, ArrowRight, TreePine } from "lucide-react";
import { Link } from "react-router-dom";

export default function TreeCard({ tree, index }) {
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
      <div className="h-36 relative overflow-hidden"
        style={{
          background: tree.cover_image
            ? `url(${tree.cover_image}) center/cover`
            : `linear-gradient(135deg, hsl(145,35%,${85 - index * 5}%) 0%, hsl(30,50%,${88 - index * 3}%) 100%)`
        }}>
        <div className="absolute inset-0" style={{ background: "linear-gradient(to bottom, transparent 40%, hsla(30,10%,15%,0.3))" }} />
        <div className="absolute top-3 left-3">
          <div className="w-8 h-8 rounded-xl flex items-center justify-center"
            style={{ background: "hsla(255,255%,255%,0.2)", backdropFilter: "blur(8px)" }}>
            <TreePine className="w-4 h-4 text-white" />
          </div>
        </div>
        <div className="absolute top-3 right-3">
          <div className="px-2 py-1 rounded-lg flex items-center gap-1 text-white text-xs"
            style={{ background: "hsla(255,255%,255%,0.2)", backdropFilter: "blur(8px)" }}>
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
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
            <Users className="w-3.5 h-3.5" />
            <span>Семейное дерево</span>
          </div>
          <Link to={`/tree/${tree.id}`}>
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
    </motion.div>
  );
}