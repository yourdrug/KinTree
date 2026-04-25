import React from 'react';
import { TreePine, Heart } from 'lucide-react';
import { Link } from 'react-router-dom';

export default function FooterSection() {
  return (
    <footer className="border-t border-border/50 bg-card/50">
      <div className="max-w-7xl mx-auto px-6 py-12">
        <div className="flex flex-col md:flex-row items-center justify-between gap-6">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-primary/10 flex items-center justify-center">
              <TreePine className="w-4 h-4 text-primary" />
            </div>
            <span className="font-semibold">KinTree</span>
          </div>

          <div className="flex items-center gap-8 text-sm text-muted-foreground">
            <Link to="/explore" className="hover:text-foreground transition-colors">Публичные деревья</Link>
            <a href="#features" className="hover:text-foreground transition-colors">Возможности</a>
            <a href="#how-it-works" className="hover:text-foreground transition-colors">Как это работает</a>
          </div>

          <p className="text-sm text-muted-foreground flex items-center gap-1">
            Создано с <Heart className="w-3.5 h-3.5 text-destructive fill-destructive" /> для семей
          </p>
        </div>
      </div>
    </footer>
  );
}