/**
 * components/common/PageHeader.jsx
 *
 * Sticky-шапка страниц приложения.
 *
 * Props:
 *   backTo    — путь для кнопки «Назад» (если не передан — кнопки нет)
 *   backLabel — подпись кнопки, по умолчанию «Назад»
 *   actions   — ReactNode справа (кнопки, меню)
 */

import { Link } from "react-router-dom";
import { Leaf, ChevronLeft } from "lucide-react";
import { Button } from "@/components/ui/button";
import { ROUTES } from "@/lib/routes";

export default function PageHeader({ backTo, backLabel = "Назад", actions }) {
  return (
    <header
      className="px-6 md:px-10 py-5 flex items-center justify-between sticky top-0 z-30"
      style={{
        borderBottom:   "1px solid hsl(35,20%,88%)",
        background:     "hsla(40,33%,98%,0.9)",
        backdropFilter: "blur(16px)",
      }}
    >
      <div className="flex items-center gap-3">
        {backTo && (
          <>
            <Link to={backTo}>
              <Button variant="ghost" size="sm" className="rounded-xl gap-1.5 text-muted-foreground">
                <ChevronLeft className="w-4 h-4" />
                {backLabel}
              </Button>
            </Link>
            <div className="w-px h-5 bg-border" />
          </>
        )}

        <Link to={ROUTES.home()} className="flex items-center gap-2">
          <div className="w-7 h-7 rounded-lg bg-primary flex items-center justify-center">
            <Leaf className="w-3.5 h-3.5 text-primary-foreground" />
          </div>
          <span className="font-serif font-semibold text-foreground">KinTree</span>
        </Link>
      </div>

      {actions && <div className="flex items-center gap-2">{actions}</div>}
    </header>
  );
}
