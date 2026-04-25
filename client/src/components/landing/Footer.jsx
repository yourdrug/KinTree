import { Leaf } from "lucide-react";

export default function Footer() {
  return (
    <footer className="py-12 px-6 md:px-12" style={{ borderTop: "1px solid hsl(35,20%,88%)" }}>
      <div className="max-w-6xl mx-auto flex flex-col md:flex-row items-center justify-between gap-6">
        <div className="flex items-center gap-2">
          <div className="w-7 h-7 rounded-lg bg-primary flex items-center justify-center">
            <Leaf className="w-3.5 h-3.5 text-primary-foreground" />
          </div>
          <span className="font-serif font-semibold text-foreground">KinTree</span>
        </div>
        <p className="text-sm text-muted-foreground text-center">
          © 2026 KinTree — Платформа для семейных историй и генеалогических деревьев
        </p>
        <div className="flex gap-6 text-sm text-muted-foreground">
          <a href="#" className="hover:text-foreground transition-colors">Конфиденциальность</a>
          <a href="#" className="hover:text-foreground transition-colors">Условия</a>
          <a href="#" className="hover:text-foreground transition-colors">Помощь</a>
        </div>
      </div>
    </footer>
  );
}