import React from 'react';
import { Outlet, Link, useLocation } from 'react-router-dom';
import { TreePine, LayoutDashboard, Globe, LogOut, User } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { base44 } from '@/api/base44Client';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { useAuth } from '@/lib/AuthContext';

export default function AppLayout() {
  const location = useLocation();
  const { user } = useAuth();

  const navItems = [
    { path: '/dashboard', label: 'Мои деревья', icon: LayoutDashboard },
    { path: '/explore', label: 'Публичные деревья', icon: Globe },
  ];

  return (
    <div className="min-h-screen bg-background">
      <nav className="fixed top-0 left-0 right-0 z-50 backdrop-blur-xl bg-background/80 border-b border-border/50">
        <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-8">
            <Link to="/dashboard" className="flex items-center gap-2.5 group">
              <div className="w-9 h-9 rounded-xl bg-primary/10 flex items-center justify-center group-hover:bg-primary/20 transition-colors">
                <TreePine className="w-5 h-5 text-primary" />
              </div>
              <span className="text-xl font-semibold tracking-tight">KinTree</span>
            </Link>

            <div className="hidden md:flex items-center gap-1">
              {navItems.map(item => (
                <Link key={item.path} to={item.path}>
                  <Button
                    variant={location.pathname === item.path ? "secondary" : "ghost"}
                    size="sm"
                    className="rounded-full gap-2 text-sm"
                  >
                    <item.icon className="w-4 h-4" />
                    {item.label}
                  </Button>
                </Link>
              ))}
            </div>
          </div>

          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" size="sm" className="rounded-full gap-2">
                <div className="w-7 h-7 rounded-full bg-primary/10 flex items-center justify-center">
                  <User className="w-4 h-4 text-primary" />
                </div>
                <span className="hidden md:inline text-sm">{user?.full_name || 'Пользователь'}</span>
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end" className="w-48">
              <DropdownMenuItem className="text-sm text-muted-foreground" disabled>
                {user?.email}
              </DropdownMenuItem>
              <DropdownMenuSeparator />
              <DropdownMenuItem onClick={() => base44.auth.logout()}>
                <LogOut className="w-4 h-4 mr-2" />
                Выйти
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </nav>

      <main className="pt-16">
        <Outlet />
      </main>
    </div>
  );
}