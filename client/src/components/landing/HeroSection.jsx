import React from 'react';
import { Button } from '@/components/ui/button';
import { ArrowRight, Sparkles } from 'lucide-react';
import { motion } from 'framer-motion';
import { Link } from 'react-router-dom';
import HeroTreeVisual from './HeroTreeVisual';

export default function HeroSection() {
  return (
    <section className="relative min-h-screen flex items-center overflow-hidden pt-16">
      {/* Background organic shapes */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-20 -left-32 w-96 h-96 bg-primary/5 rounded-full blur-3xl" />
        <div className="absolute top-40 right-0 w-80 h-80 bg-accent/40 rounded-full blur-3xl" />
        <div className="absolute bottom-20 left-1/3 w-72 h-72 bg-secondary/60 rounded-full blur-3xl" />
      </div>

      <div className="max-w-7xl mx-auto px-6 w-full relative z-10">
        <div className="grid lg:grid-cols-2 gap-16 items-center">
          {/* Left: Text */}
          <motion.div
            initial={{ opacity: 0, x: -30 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.7, delay: 0.2 }}
            className="space-y-8"
          >
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.3 }}
              className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-primary/8 border border-primary/15 text-sm text-primary"
            >
              <Sparkles className="w-4 h-4" />
              Платформа генеалогических деревьев
            </motion.div>

            <h1 className="text-5xl md:text-6xl lg:text-7xl font-serif font-bold leading-tight tracking-tight">
              Сохрани историю{' '}
              <span className="text-primary">своей семьи</span>{' '}
              в одном дереве
            </h1>

            <p className="text-lg md:text-xl text-muted-foreground leading-relaxed max-w-lg">
              KinTree — современная платформа для создания, изучения и сохранения
              генеалогических деревьев. Откройте историю поколений и передайте её потомкам.
            </p>

            <div className="flex flex-col sm:flex-row gap-4">
              <Button
                size="lg"
                className="rounded-full px-8 h-13 text-base gap-2 shadow-lg shadow-primary/20"
                onClick={() => {window.location.href = '/login';}}
              >
                Создать фамильное дерево
                <ArrowRight className="w-4 h-4" />
              </Button>
              <Link to="/explore">
                <Button
                  variant="outline"
                  size="lg"
                  className="rounded-full px-8 h-13 text-base w-full sm:w-auto"
                >
                  Продолжить как гость
                </Button>
              </Link>
            </div>

            <div className="flex items-center gap-6 pt-2 text-sm text-muted-foreground">
              <div className="flex -space-x-2">
                {[1,2,3,4].map(i => (
                  <div key={i} className="w-8 h-8 rounded-full bg-accent border-2 border-background flex items-center justify-center text-xs font-medium text-accent-foreground">
                    {String.fromCharCode(64 + i)}
                  </div>
                ))}
              </div>
              <span>Более 2,000 семей уже строят деревья</span>
            </div>
          </motion.div>

          {/* Right: Tree Visual */}
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.8, delay: 0.4 }}
          >
            <HeroTreeVisual />
          </motion.div>
        </div>
      </div>
    </section>
  );
}
