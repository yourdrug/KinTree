import { motion } from "framer-motion";
import { Leaf, ArrowRight, Eye } from "lucide-react";
import { Button } from "@/components/ui/button";
import { base44 } from "@/api/base44Client";
import Navbar from "../components/landing/Navbar";
import HeroTree from "../components/landing/HeroTree";
import FeatureCards from "../components/landing/FeatureCards";
import HowItWorks from "../components/landing/HowItWorks";
import Footer from "../components/landing/Footer";
import { Link } from "react-router-dom";

export default function Landing() {
  return (
    <div className="min-h-screen font-sans" style={{ background: "hsl(40,33%,98%)" }}>
      <Navbar />

      {/* Hero Section */}
      <section className="pt-28 pb-20 px-6 md:px-12">
        <div className="max-w-6xl mx-auto">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-16 items-center">
            {/* Left: Text */}
            <div>
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.6 }}
              >
                <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full text-sm font-medium mb-6"
                  style={{ background: "hsl(145,35%,92%)", color: "hsl(145,35%,28%)" }}>
                  <Leaf className="w-3.5 h-3.5" />
                  Сохраните наследие вашей семьи
                </div>
              </motion.div>

              <motion.h1
                initial={{ opacity: 0, y: 25 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.7, delay: 0.1 }}
                className="font-serif text-4xl md:text-5xl lg:text-6xl font-semibold text-foreground leading-[1.15] mb-6"
              >
                Сохрани историю своей семьи{" "}
                <span style={{ color: "hsl(145,35%,38%)" }}>в одном дереве</span>
              </motion.h1>

              <motion.p
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.7, delay: 0.2 }}
                className="text-lg text-muted-foreground leading-relaxed mb-10 max-w-xl"
              >
                KinTree — это платформа для создания, изучения и сохранения генеалогических деревьев.
                Соединяйте поколения, находите родственников и передавайте историю рода своим детям.
              </motion.p>

              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.7, delay: 0.3 }}
                className="flex flex-col sm:flex-row gap-3"
              >
                <Button
                  size="lg"
                  className="rounded-2xl px-8 py-6 text-base font-semibold shadow-lg gap-2 bg-primary text-primary-foreground hover:bg-primary/90"
                  style={{ boxShadow: "0 8px 30px hsla(145,35%,38%,0.3)" }}
                  onClick={() => base44.auth.redirectToLogin()}
                >
                  Создать фамильное дерево
                  <ArrowRight className="w-5 h-5" />
                </Button>

                <Button
                  size="lg"
                  variant="outline"
                  className="rounded-2xl px-8 py-6 text-base font-medium gap-2"
                  style={{ borderColor: "hsl(35,20%,82%)", color: "hsl(30,10%,30%)" }}
                  onClick={() => base44.auth.redirectToLogin()}
                >
                  Войти
                </Button>
              </motion.div>

              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: 0.5 }}
                className="mt-4"
              >
                <Link to="/explore">
                  <Button variant="ghost" className="gap-2 text-muted-foreground hover:text-foreground text-sm rounded-xl">
                    <Eye className="w-4 h-4" />
                    Продолжить как гость
                  </Button>
                </Link>
              </motion.div>

              {/* Social proof */}
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: 0.6 }}
                className="mt-10 flex items-center gap-4"
              >
                <div className="flex -space-x-2">
                  {[
                    "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=32&h=32&fit=crop&crop=face",
                    "https://images.unsplash.com/photo-1438761681033-6461ffad8d80?w=32&h=32&fit=crop&crop=face",
                    "https://images.unsplash.com/photo-1544005313-94ddf0286df2?w=32&h=32&fit=crop&crop=face",
                    "https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?w=32&h=32&fit=crop&crop=face",
                  ].map((src, i) => (
                    <img key={i} src={src} alt="" className="w-8 h-8 rounded-full border-2 border-white object-cover" />
                  ))}
                </div>
                <p className="text-sm text-muted-foreground">
                  <span className="font-semibold text-foreground">12 000+</span> семей уже хранят историю
                </p>
              </motion.div>
            </div>

            {/* Right: Tree Visual */}
            <motion.div
              initial={{ opacity: 0, x: 30 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.9, delay: 0.2 }}
              className="relative"
            >
              {/* Decorative blob */}
              <div className="absolute inset-0 -m-8 rounded-[50%]"
                style={{ background: "radial-gradient(ellipse, hsl(145,35%,92%) 0%, transparent 70%)", zIndex: 0 }} />
              <div className="relative z-10">
                <HeroTree />
              </div>
            </motion.div>
          </div>
        </div>
      </section>

      {/* Stats Strip */}
      <motion.section
        initial={{ opacity: 0 }}
        whileInView={{ opacity: 1 }}
        viewport={{ once: true }}
        className="py-12 px-6"
        style={{ background: "hsl(145,35%,38%)" }}
      >
        <div className="max-w-4xl mx-auto grid grid-cols-2 md:grid-cols-4 gap-8 text-center">
          {[
            { val: "12K+", label: "Семей" },
            { val: "240K+", label: "Людей в деревьях" },
            { val: "8", label: "Поколений в среднем" },
            { val: "99%", label: "Приватность данных" },
          ].map((s) => (
            <div key={s.label}>
              <div className="font-serif text-3xl font-bold text-white mb-1">{s.val}</div>
              <div className="text-sm" style={{ color: "hsl(145,40%,80%)" }}>{s.label}</div>
            </div>
          ))}
        </div>
      </motion.section>

      <FeatureCards />
      <HowItWorks />

      {/* Final CTA */}
      <section className="py-24 px-6">
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="max-w-2xl mx-auto text-center"
        >
          <div className="rounded-3xl p-12"
            style={{ background: "linear-gradient(135deg, hsl(145,35%,92%) 0%, hsl(30,50%,92%) 100%)", border: "1px solid hsl(35,20%,85%)" }}>
            <div className="text-5xl mb-5">🌳</div>
            <h2 className="font-serif text-3xl md:text-4xl font-semibold text-foreground mb-4">
              Начните сегодня
            </h2>
            <p className="text-muted-foreground mb-8 text-lg">
              Ваша семейная история заслуживает быть сохранённой
            </p>
            <Button
              size="lg"
              className="rounded-2xl px-10 py-6 text-base font-semibold gap-2"
              style={{ background: "hsl(145,35%,38%)", color: "white", boxShadow: "0 8px 30px hsla(145,35%,38%,0.35)" }}
              onClick={() => base44.auth.redirectToLogin()}
            >
              Создать бесплатно
              <ArrowRight className="w-5 h-5" />
            </Button>
          </div>
        </motion.div>
      </section>

      <Footer />
    </div>
  );
}