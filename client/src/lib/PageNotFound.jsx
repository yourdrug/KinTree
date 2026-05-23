import { Link } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { TreePine, ArrowLeft } from "lucide-react";
import {useAppNavigate} from "@/lib/navigation.js";

export default function PageNotFound() {
  const navigate = useAppNavigate()

  return (
    <div className="min-h-screen flex items-center justify-center bg-background px-6">
      <div className="text-center">
        <div className="w-20 h-20 rounded-3xl bg-primary/8 flex items-center justify-center mx-auto mb-6">
          <TreePine className="w-10 h-10 text-primary/30" />
        </div>
        <h1 className="text-6xl font-serif font-bold text-primary/20 mb-2">404</h1>
        <h2 className="text-xl font-semibold mb-2">Страница не найдена</h2>
        <p className="text-muted-foreground mb-8">Эта ветвь дерева ведёт в никуда</p>
        <Button className="rounded-full gap-2 px-6" onClick={() => nav.toHome()}>
          <ArrowLeft className="w-4 h-4" />
          На главную
        </Button>
      </div>
    </div>
  );
}
