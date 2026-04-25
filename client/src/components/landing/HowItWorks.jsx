import { motion } from "framer-motion";

const steps = [
  { num: "01", title: "Создайте дерево", desc: "Зарегистрируйтесь и дайте имя вашему семейному дереву. Это займёт меньше минуты." },
  { num: "02", title: "Добавьте людей", desc: "Вносите имена, даты, фотографии и истории членов вашей семьи." },
  { num: "03", title: "Стройте связи", desc: "Соединяйте родственников линиями — родители, дети, супруги." },
  { num: "04", title: "Делитесь памятью", desc: "Открывайте доступ родным или публикуйте дерево для всех желающих." },
];

export default function HowItWorks() {
  return (
    <section id="how" className="py-24 px-6 md:px-12" style={{ background: "hsl(35,30%,95%)" }}>
      <div className="max-w-5xl mx-auto">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="text-center mb-16"
        >
          <span className="inline-block px-4 py-1.5 rounded-full text-sm font-medium mb-4"
            style={{ background: "hsl(30,50%,88%)", color: "hsl(30,30%,30%)" }}>
            Как работает
          </span>
          <h2 className="font-serif text-3xl md:text-4xl font-semibold text-foreground mb-4">
            Начать просто
          </h2>
          <p className="text-muted-foreground text-lg">Четыре шага до вашего живого семейного архива</p>
        </motion.div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {steps.map((step, i) => (
            <motion.div
              key={step.num}
              initial={{ opacity: 0, y: 30 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: i * 0.12 }}
              className="relative"
            >
              {i < steps.length - 1 && (
                <div className="hidden lg:block absolute top-8 left-full w-full h-px"
                  style={{ background: "linear-gradient(to right, hsl(145,35%,65%), transparent)", zIndex: 0 }} />
              )}
              <div className="rounded-2xl p-6 h-full relative z-10" style={{ background: "white", border: "1px solid hsl(35,20%,90%)" }}>
                <div className="font-serif text-3xl font-bold mb-4" style={{ color: "hsl(145,35%,38%)" }}>
                  {step.num}
                </div>
                <h3 className="font-semibold text-foreground mb-2">{step.title}</h3>
                <p className="text-sm text-muted-foreground leading-relaxed">{step.desc}</p>
              </div>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}