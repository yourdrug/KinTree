import React from 'react';
import { motion } from 'framer-motion';
import { TreePine, Search, History, Shield, Users } from 'lucide-react';

const features = [
  {
    icon: TreePine,
    title: 'Создание семейного дерева',
    description: 'Интуитивный визуальный редактор для построения генеалогического дерева любой сложности',
  },
  {
    icon: Search,
    title: 'Поиск родственников',
    description: 'Находите связи между людьми и откройте неизвестные ветви вашей семьи',
  },
  {
    icon: History,
    title: 'Сохранение истории',
    description: 'Прикрепляйте фотографии, документы и истории к каждому члену семьи',
  },
  {
    icon: Shield,
    title: 'Приватность и контроль',
    description: 'Полный контроль доступа — делитесь деревом только с теми, кому доверяете',
  },
  {
    icon: Users,
    title: 'Совместная работа',
    description: 'Приглашайте родственников для совместного заполнения семейного дерева',
  },
];

export default function FeaturesSection() {
  return (
    <section id="features" className="py-28 relative">
      <div className="absolute inset-0 bg-gradient-to-b from-transparent via-secondary/30 to-transparent pointer-events-none" />

      <div className="max-w-7xl mx-auto px-6 relative z-10">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6 }}
          className="text-center mb-16"
        >
          <span className="text-sm font-medium text-primary tracking-wide uppercase">Возможности</span>
          <h2 className="text-3xl md:text-4xl font-serif font-bold mt-3">
            Всё для вашей семейной истории
          </h2>
          <p className="text-muted-foreground mt-4 max-w-2xl mx-auto text-lg">
            Мощные инструменты, обёрнутые в простой и тёплый интерфейс
          </p>
        </motion.div>

        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
          {features.map((feature, i) => (
            <motion.div
              key={feature.title}
              initial={{ opacity: 0, y: 30 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.5, delay: i * 0.1 }}
              className="group p-8 rounded-2xl bg-card/80 backdrop-blur-sm border border-border/50 hover:border-primary/20 hover:shadow-xl hover:shadow-primary/5 transition-all duration-500"
            >
              <div className="w-12 h-12 rounded-xl bg-primary/8 flex items-center justify-center mb-5 group-hover:bg-primary/15 transition-colors">
                <feature.icon className="w-6 h-6 text-primary" />
              </div>
              <h3 className="text-lg font-semibold mb-2">{feature.title}</h3>
              <p className="text-muted-foreground leading-relaxed">{feature.description}</p>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}