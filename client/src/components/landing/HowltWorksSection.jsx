import React from 'react';
import { motion } from 'framer-motion';
import { UserPlus, GitBranch, Share2 } from 'lucide-react';

const steps = [
  {
    icon: UserPlus,
    step: '01',
    title: 'Создайте аккаунт',
    description: 'Зарегистрируйтесь за секунды и начните строить ваше семейное дерево',
  },
  {
    icon: GitBranch,
    step: '02',
    title: 'Добавьте семью',
    description: 'Добавляйте родственников, связи, фотографии и истории жизни',
  },
  {
    icon: Share2,
    step: '03',
    title: 'Делитесь и исследуйте',
    description: 'Поделитесь деревом с семьёй или исследуйте публичные деревья',
  },
];

export default function HowItWorksSection() {
  return (
    <section id="how-it-works" className="py-28">
      <div className="max-w-7xl mx-auto px-6">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6 }}
          className="text-center mb-16"
        >
          <span className="text-sm font-medium text-primary tracking-wide uppercase">Как это работает</span>
          <h2 className="text-3xl md:text-4xl font-serif font-bold mt-3">
            Три простых шага
          </h2>
        </motion.div>

        <div className="grid md:grid-cols-3 gap-8 md:gap-12">
          {steps.map((step, i) => (
            <motion.div
              key={step.step}
              initial={{ opacity: 0, y: 30 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.5, delay: i * 0.15 }}
              className="text-center relative"
            >
              {i < steps.length - 1 && (
                <div className="hidden md:block absolute top-12 left-[60%] w-[80%] h-px border-t-2 border-dashed border-border" />
              )}
              <div className="w-24 h-24 rounded-3xl bg-gradient-to-br from-primary/10 to-accent/20 flex items-center justify-center mx-auto mb-6 relative">
                <step.icon className="w-10 h-10 text-primary" />
                <span className="absolute -top-2 -right-2 w-7 h-7 rounded-full bg-primary text-primary-foreground text-xs font-bold flex items-center justify-center">
                  {step.step}
                </span>
              </div>
              <h3 className="text-xl font-semibold mb-3">{step.title}</h3>
              <p className="text-muted-foreground leading-relaxed max-w-xs mx-auto">{step.description}</p>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}