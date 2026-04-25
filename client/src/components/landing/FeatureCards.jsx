import { motion } from "framer-motion";
import { TreePine, Search, BookOpen, Shield, Globe } from "lucide-react";

const features = [
  {
    icon: TreePine,
    title: "Семейное дерево",
    desc: "Создавайте визуальные деревья поколений с фотографиями и датами",
    color: "hsl(145,35%,38%)",
    bg: "hsl(145,35%,95%)",
  },
  {
    icon: Search,
    title: "Поиск родственников",
    desc: "Находите связи между ветвями и исследуйте историю рода",
    color: "hsl(30,50%,50%)",
    bg: "hsl(30,50%,95%)",
  },
  {
    icon: BookOpen,
    title: "История поколений",
    desc: "Сохраняйте биографии, документы и воспоминания семьи",
    color: "hsl(200,40%,45%)",
    bg: "hsl(200,40%,95%)",
  },
  {
    icon: Shield,
    title: "Приватность",
    desc: "Полный контроль над доступом — делитесь только с теми, кому доверяете",
    color: "hsl(145,35%,38%)",
    bg: "hsl(145,35%,95%)",
  },
  {
    icon: Globe,
    title: "Публичные деревья",
    desc: "Исследуйте открытые деревья других семей и находите связи",
    color: "hsl(30,50%,50%)",
    bg: "hsl(30,50%,95%)",
  },
];

export default function FeatureCards() {
  return (
    <section id="features" className="py-24 px-6 md:px-12">
      <div className="max-w-6xl mx-auto">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6 }}
          className="text-center mb-16"
        >
          <span className="inline-block px-4 py-1.5 rounded-full text-sm font-medium mb-4"
            style={{ background: "hsl(145,35%,92%)", color: "hsl(145,35%,30%)" }}>
            Возможности
          </span>
          <h2 className="font-serif text-3xl md:text-4xl font-semibold text-foreground mb-4">
            Всё для вашей семейной истории
          </h2>
          <p className="text-muted-foreground text-lg max-w-xl mx-auto">
            KinTree объединяет инструменты для создания, изучения и сохранения истории вашего рода
          </p>
        </motion.div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
          {features.map((f, i) => {
            const Icon = f.icon;
            return (
              <motion.div
                key={f.title}
                initial={{ opacity: 0, y: 30 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: i * 0.1, duration: 0.5 }}
                whileHover={{ y: -4 }}
                className={`rounded-2xl p-6 cursor-default ${i === 4 ? "sm:col-span-2 lg:col-span-1" : ""}`}
                style={{ background: "hsl(40,30%,97%)", border: "1px solid hsl(35,20%,90%)" }}
              >
                <div
                  className="w-12 h-12 rounded-2xl flex items-center justify-center mb-5"
                  style={{ background: f.bg }}
                >
                  <Icon className="w-6 h-6" style={{ color: f.color }} />
                </div>
                <h3 className="font-semibold text-lg text-foreground mb-2">{f.title}</h3>
                <p className="text-muted-foreground text-sm leading-relaxed">{f.desc}</p>
              </motion.div>
            );
          })}
        </div>
      </div>
    </section>
  );
}