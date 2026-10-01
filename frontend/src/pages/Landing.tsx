import React from 'react';
import { useNavigate } from 'react-router-dom';
import { motion, useScroll, useTransform } from 'framer-motion';
import { Button } from '../components/ui/Button';
import { SereneMoonBackground } from '../components/ui/SereneMoonBackground';
import { Brain, Mic, ClipboardList, ArrowRight, ShieldCheck, Sparkles } from 'lucide-react';

export default function Landing() {
  const navigate = useNavigate();
  const { scrollY } = useScroll();

  // Scroll animations for editorial hero
  const titleOpacity = useTransform(scrollY, [30, 280], [0.5, 1]);
  const titleScale   = useTransform(scrollY, [30, 360], [0.92, 1.02]);
  const titleY       = useTransform(scrollY, [30, 360], [30, -5]);
  const scrollPromptOpacity = useTransform(scrollY, [0, 120], [1, 0]);

  return (
    <div className="min-h-screen bg-[#1B1622] text-[#E8B4B8] overflow-x-hidden relative font-sans selection:bg-[#81B29A]/30 selection:text-[#FFE8C2]">
      {/* Golden Celestial Ambient Background */}
      <SereneMoonBackground />

      {/* ── MINIMAL EDITORIAL NAVBAR ── */}
      <nav className="fixed top-0 left-0 right-0 z-50 glass-nav px-6 sm:px-12 py-4 flex items-center justify-between">
        <div 
          className="flex items-center gap-3 cursor-pointer group" 
          onClick={() => window.scrollTo({ top: 0, behavior: 'smooth' })}
        >
          <div className="w-8 h-8 rounded-full bg-[#81B29A]/15 border border-[#81B29A]/30 flex items-center justify-center transition-transform group-hover:scale-105">
            <Brain className="w-4 h-4 text-[#94D2BD]" />
          </div>
          <span className="font-serif-title text-xl font-bold tracking-widest text-[#FFE8C2] uppercase">
            MindScreen
          </span>
        </div>

        <div className="flex items-center gap-4">
          <Button 
            onClick={() => navigate('/dashboard')}
            className="bg-[#81B29A] hover:bg-[#94D2BD] text-slate-950 font-bold text-xs tracking-wider uppercase px-5 py-2.5 rounded-full shadow-[0_0_20px_rgba(129,178,154,0.3)] transition-all flex items-center gap-2"
          >
            Enter Sanctuary <ArrowRight className="w-3.5 h-3.5" />
          </Button>
        </div>
      </nav>

      <main className="relative z-10 max-w-6xl mx-auto px-6">
        {/* ── HERO SECTION: TIMELESS & REFINED ── */}
        <section className="min-h-screen flex flex-col justify-between pt-24 pb-12 relative">
          
          {/* Subtle Tagline */}
          <div className="text-center pt-8 z-20">
            <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-[#241D2B]/80 border border-[#81B29A]/25 backdrop-blur-md">
              <Sparkles className="w-3 h-3 text-[#94D2BD]" />
              <span className="text-[11px] font-semibold tracking-widest text-[#94D2BD] uppercase">
                Multimodal Mental Health Screening
              </span>
            </div>
          </div>

          {/* Editorial Title Card */}
          <motion.div
            style={{
              opacity: titleOpacity,
              scale: titleScale,
              y: titleY,
            }}
            className="text-center my-auto z-20 py-4"
          >
            <div className="max-w-2xl mx-auto p-8 sm:p-12 rounded-[2rem] bg-[#1B1622]/85 border border-[#81B29A]/30 backdrop-blur-2xl shadow-[0_20px_50px_rgba(0,0,0,0.65)]">
              <h1 className="font-serif-title text-6xl sm:text-7xl md:text-8xl italic font-semibold tracking-tight leading-[0.92] mb-4 text-[#FFE8C2]">
                MindScreen
              </h1>
              
              <p className="text-sm sm:text-base text-[#F0C0C6] font-medium leading-relaxed mb-7 max-w-lg mx-auto">
                A quiet screening sanctuary integrating standardized PHQ-9 metrics, MentalBERT semantics, and voice acoustic biomarkers.
              </p>

              <div className="flex items-center justify-center">
                <Button 
                  onClick={() => navigate('/dashboard')}
                  className="bg-[#81B29A] hover:bg-[#94D2BD] text-slate-950 font-bold text-sm px-8 py-3.5 rounded-full shadow-[0_0_25px_rgba(129,178,154,0.4)] transition-all flex items-center justify-center gap-2"
                >
                  Begin Screening <ArrowRight className="w-4 h-4" />
                </Button>
              </div>
            </div>
          </motion.div>

          {/* Gentle Scroll Cue */}
          <motion.div
            style={{ opacity: scrollPromptOpacity }}
            className="text-center z-30 pb-2 flex flex-col items-center justify-center"
          >
            <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-[#241D2B]/80 border border-[#81B29A]/30 backdrop-blur-xl">
              <span className="text-[10px] font-bold tracking-widest text-[#94D2BD] uppercase">
                Explore The Sanctuary
              </span>
              <motion.div
                animate={{ y: [0, 3, 0] }}
                transition={{ duration: 1.5, repeat: Infinity, ease: 'easeInOut' }}
                className="w-1.5 h-1.5 rounded-full bg-[#81B29A]"
              />
            </div>
          </motion.div>
        </section>

        {/* ── TRI-MODAL METHODOLOGY: CLEAN 3-COLUMN CARDS ── */}
        <section className="py-16 relative z-20">
          <div className="text-center mb-14">
            <h2 className="font-serif-title text-3xl sm:text-5xl italic font-normal tracking-tight mb-3 text-[#FFE8C2]">
              A Calibrated Tri-Modal Pipeline
            </h2>
            <p className="text-[#E8B4B8]/90 max-w-xl mx-auto text-sm font-medium leading-relaxed">
              Combining standardized self-reports, contextual language patterns, and vocal biomarkers for clinical-grade insight.
            </p>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {[
              {
                icon: ClipboardList,
                title: 'Clinical PHQ-9',
                weight: '20% Weight',
                desc: 'Standardized 9-question depression severity metric calibrated to international diagnostic criteria.',
              },
              {
                icon: Brain,
                title: 'MentalBERT NLP',
                weight: '50% Weight',
                desc: 'Domain-adapted transformer analyzing semantic sentiment, cognitive distortions, and journal reflections.',
              },
              {
                icon: Mic,
                title: 'Vocal Acoustics',
                weight: '30% Weight',
                desc: 'Acoustic feature extraction isolating pitch variation, energy contours, and MFCC biomarkers.',
              }
            ].map((feature, i) => (
              <motion.div 
                key={i}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5, delay: i * 0.12 }}
                viewport={{ once: true }}
                className="glass-card p-7 hover:-translate-y-1.5 transition-all duration-300 relative group border-[#81B29A]/20 hover:border-[#81B29A]/45"
              >
                <div className="flex items-center justify-between mb-5">
                  <div className="w-11 h-11 rounded-xl bg-[#81B29A]/15 border border-[#81B29A]/30 flex items-center justify-center">
                    <feature.icon className="w-5 h-5 text-[#94D2BD]" />
                  </div>
                  <span className="text-[10px] uppercase tracking-wider text-[#94D2BD] font-semibold px-2.5 py-1 rounded-full bg-[#81B29A]/10 border border-[#81B29A]/20">
                    {feature.weight}
                  </span>
                </div>
                <h3 className="font-serif-title text-2xl font-semibold mb-2 text-[#FFE8C2]">{feature.title}</h3>
                <p className="text-[#F0C0C6]/90 text-xs sm:text-sm leading-relaxed">{feature.desc}</p>
              </motion.div>
            ))}
          </div>
        </section>

        {/* ── SAATHI WELLBEING COMPANION SHOWCASE (REFINED PALETTE) ── */}
        <section className="py-14 relative z-20">
          <div className="glass-card p-8 sm:p-12 border-[#81B29A]/30 relative overflow-hidden bg-gradient-to-br from-[#241D2B] via-[#1B1622] to-[#251A2A]">
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-center">
              
              {/* Left Column: Native Twilight Chat Cards Preview */}
              <div className="lg:col-span-6 space-y-3.5">
                
                {/* User Message Bubble */}
                <motion.div
                  initial={{ opacity: 0, x: -15 }}
                  whileInView={{ opacity: 1, x: 0 }}
                  transition={{ duration: 0.4 }}
                  viewport={{ once: true }}
                  className="p-4 rounded-2xl bg-[#81B29A] text-slate-950 shadow-lg max-w-sm ml-auto space-y-1"
                >
                  <p className="text-xs font-bold text-slate-900/70">You</p>
                  <p className="text-xs sm:text-sm font-semibold leading-relaxed">
                    I get so stressed talking to my family. It always ends in an argument.
                  </p>
                </motion.div>

                {/* Saathi Companion Message Bubble */}
                <motion.div
                  initial={{ opacity: 0, x: -15 }}
                  whileInView={{ opacity: 1, x: 0 }}
                  transition={{ duration: 0.4, delay: 0.15 }}
                  viewport={{ once: true }}
                  className="p-4 rounded-2xl bg-[#1B1622] border border-[#81B29A]/30 shadow-lg max-w-sm space-y-1.5"
                >
                  <div className="flex items-center gap-1.5 text-xs font-bold text-[#94D2BD]">
                    <span>🌿 Saathi</span>
                  </div>
                  <p className="text-xs sm:text-sm text-[#F0C0C6] leading-relaxed">
                    It's so tough when the people closest to us don't seem to understand. Setting gentle emotional boundaries is a quiet act of self-care.
                  </p>
                </motion.div>

                {/* Grounding Exercise Card */}
                <motion.div
                  initial={{ opacity: 0, y: 10 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.4, delay: 0.3 }}
                  viewport={{ once: true }}
                  className="p-3.5 rounded-xl bg-[#241D2B] border border-[#81B29A]/35 shadow-md max-w-sm flex items-center justify-between gap-3"
                >
                  <div className="flex items-center gap-2.5">
                    <div className="w-8 h-8 rounded-lg bg-[#81B29A]/20 flex items-center justify-center">
                      <Sparkles className="w-4 h-4 text-[#94D2BD]" />
                    </div>
                    <div>
                      <h4 className="text-xs font-bold text-[#FFE8C2]">Pranayama 4-7-8 Release</h4>
                      <p className="text-[10px] text-[#94D2BD]">Calming Breathwork • 4 min</p>
                    </div>
                  </div>
                  <span className="text-[11px] text-[#FFE8C2] font-semibold px-2 py-1 rounded-md bg-[#81B29A]/20 border border-[#81B29A]/30">
                    Integrated
                  </span>
                </motion.div>
              </div>

              {/* Right Column: Copy & Action */}
              <div className="lg:col-span-6 space-y-4 lg:pl-4">
                <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-[#81B29A]/15 border border-[#81B29A]/30 text-[#94D2BD] text-[11px] font-semibold uppercase tracking-wider">
                  <span>Always-There Companion</span>
                </div>
                <h3 className="font-serif-title text-3xl sm:text-4xl italic font-normal tracking-tight text-[#FFE8C2] leading-tight">
                  Meet Saathi, Your Wellbeing Companion
                </h3>
                <p className="text-[#E8B4B8]/90 text-sm leading-relaxed">
                  Reflect on daily stressors, academic pressure, and unspoken thoughts with compassionate conversational guidance and instant grounding exercises.
                </p>
                <div className="pt-1">
                  <Button 
                    onClick={() => navigate('/saathi')}
                    className="bg-[#81B29A] hover:bg-[#94D2BD] text-slate-950 font-bold text-xs uppercase tracking-wider px-6 py-3 rounded-full shadow-[0_0_20px_rgba(129,178,154,0.35)] transition-all inline-flex items-center gap-2"
                  >
                    🌿 Talk with Saathi <ArrowRight className="w-3.5 h-3.5" />
                  </Button>
                </div>
              </div>

            </div>
          </div>
        </section>
      </main>

      {/* ── CLEAN, RESPECTFUL FOOTER ── */}
      <footer className="border-t border-[#81B29A]/20 bg-[#16111B] relative z-20 py-8">
        <div className="max-w-6xl mx-auto px-6 flex flex-col sm:flex-row items-center justify-between gap-4 text-xs text-[#E8B4B8]/70">
          <div className="flex items-center gap-2.5">
            <Brain className="text-[#94D2BD] w-4 h-4" />
            <span className="font-serif-title text-base font-bold text-[#FFE8C2]">MindScreen</span>
            <span className="text-white/20">|</span>
            <span>Multimodal Clinical Screening</span>
          </div>

          <div className="flex items-center gap-2 text-[#94D2BD]">
            <ShieldCheck className="w-3.5 h-3.5" />
            <span>Confidential & Research Guided</span>
          </div>

          <p className="text-[#E8B4B8]/50 text-[11px]">
            © {new Date().getFullYear()} MindScreen (RVITM BCS685)
          </p>
        </div>
      </footer>
    </div>
  );
}
