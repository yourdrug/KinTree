/**
 * components/dashboard/UserMenu.jsx
 */

import { Link } from "react-router-dom";
import { Shield, LogOut, ChevronDown } from "lucide-react";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { ROUTES } from "@/lib/routes";

export default function UserMenu({ user, onLogout }) {
  const initial = (user?.email?.[0] || "U").toUpperCase();

  return (
    <DropdownMenu>
      <DropdownMenuTrigger
        className="flex items-center gap-2 rounded-xl px-3 py-2 text-sm transition-colors hover:bg-black/5 outline-none"
      >
        <div className="w-7 h-7 rounded-full bg-primary/20 flex items-center justify-center text-xs font-semibold text-primary">
          {initial}
        </div>
        <span className="hidden md:block text-muted-foreground max-w-32 truncate">
          {user?.email}
        </span>
        <ChevronDown className="w-3.5 h-3.5 text-muted-foreground" />
      </DropdownMenuTrigger>

      <DropdownMenuContent
        align="end"
        className="w-52 rounded-2xl"
        style={{ border: "1px solid hsl(35,20%,88%)" }}
      >
        <DropdownMenuLabel className="font-normal">
          <p className="text-xs text-muted-foreground">Вы вошли как</p>
          <p className="text-sm font-medium text-foreground truncate mt-0.5">{user?.email}</p>
        </DropdownMenuLabel>

        <DropdownMenuSeparator />

        <DropdownMenuItem asChild>
          <Link to={ROUTES.settings.sessions()} className="flex items-center gap-3 cursor-pointer">
            <Shield className="w-4 h-4 text-muted-foreground" />
            Активные сессии
          </Link>
        </DropdownMenuItem>

        <DropdownMenuItem
          onClick={onLogout}
          className="flex items-center gap-3 cursor-pointer"
          style={{ color: "hsl(0,60%,45%)" }}
        >
          <LogOut className="w-4 h-4" />
          Выйти
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
