'use client';

import Link from 'next/link';
import { motion, AnimatePresence } from 'framer-motion';
import { useState } from 'react';
import Image from 'next/image';
import MindLensScrollExperience from './components/MindLensScrollExperience';
import PricingSection from './components/PricingSection';

export default function LandingPage() {
  const [openAccordion, setOpenAccordion] = useState<number | null>(null);

  const toggleAccordion = (index: number) => {
    setOpenAccordion(openAccordion === index ? null : index);
  };

  return (
    <div className="flex flex-col min-h-screen bg-base text-textPrimary selection:bg-surface">
      {/* 4. NAVIGATION */}
      <nav className="fixed top-0 left-0 right-0 z-50 flex items-center justify-between px-6 md:px-12 h-[68px] bg-base/90 backdrop-blur-md border-b border-neutral transition-all">
        <div className="flex items-center">
          <span className="text-xl font-bold tracking-tight text-primary font-serif uppercase">MindLens</span>
        </div>
        <div className="hidden md:flex items-center gap-8">
          <Link href="#how-it-works" className="text-sm font-medium text-textSecondary hover:text-primary transition-colors">How It Works</Link>
          <Link href="#evidence" className="text-sm font-medium text-textSecondary hover:text-primary transition-colors">Evidence</Link>
          <Link href="#for-counselors" className="text-sm font-medium text-textSecondary hover:text-primary transition-colors">For Counselors</Link>
          <Link href="#research" className="text-sm font-medium text-textSecondary hover:text-primary transition-colors">Research</Link>
        </div>
        <div className="flex items-center gap-6">
          <Link href="/login" className="hidden sm:block text-sm font-medium text-textSecondary hover:text-primary transition-colors">
            Counselor Login
          </Link>
          <Link href="#request-access" className="px-5 py-2 text-sm font-medium bg-primary text-white hover:bg-primary/90 transition-colors shadow-sm uppercase tracking-wide">
            Request Access
          </Link>
        </div>
      </nav>

      <main className="flex-grow pt-[68px]">
        {/* 5. HERO & 6. HERO IMAGE */}
        <section className="relative min-h-[90vh] flex flex-col md:flex-row items-center px-6 md:px-12 py-12 md:py-24 overflow-hidden">
          <div className="w-full md:w-1/2 flex flex-col justify-center gap-8 z-10 md:pr-12">
            <span className="text-xs uppercase tracking-widest text-textSecondary font-semibold">
              Counselor Decision Support
            </span>
            <motion.h1 
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.8, ease: "easeOut" }}
              className="text-5xl md:text-7xl text-primary leading-[1.1] font-serif uppercase"
            >
              One Student.<br/>
              Three Perspectives.<br/>
              A Clearer Picture.
            </motion.h1>
            <motion.p 
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.8, delay: 0.2, ease: "easeOut" }}
              className="text-lg md:text-xl text-textSecondary leading-relaxed max-w-xl font-sans"
            >
              MindLens brings structured perspectives from the adolescent, parent and teacher together so counselors can see meaningful differences before the conversation begins.
            </motion.p>
            <motion.div 
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.8, delay: 0.4, ease: "easeOut" }}
              className="flex flex-col sm:flex-row gap-4 pt-4"
            >
              <Link href="#request-access" className="inline-flex justify-center items-center px-8 py-4 text-sm font-medium bg-primary text-white hover:bg-primary/90 transition-transform hover:-translate-y-0.5 shadow-sm uppercase tracking-wide">
                Request Access
              </Link>
              <Link href="#how-it-works" className="inline-flex justify-center items-center px-8 py-4 text-sm font-medium bg-transparent border border-primary text-primary hover:bg-primary/5 transition-colors uppercase tracking-wide">
                See How It Works
              </Link>
            </motion.div>
          </div>
          
          <motion.div 
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 1.2, delay: 0.3, ease: "easeOut" }}
            className="w-full md:w-1/2 h-[60vh] md:h-[80vh] relative mt-12 md:mt-0"
          >
            {/* Photographic Metaphor: 1 large + 2 smaller overlapping frames */}
            <div className="absolute inset-0 right-0 md:-right-12 bottom-0 bg-neutral/20 z-0 hidden md:block"></div>
            
            {/* Main large frame - Adolescent */}
            <div className="absolute right-0 top-1/2 -translate-y-1/2 w-[80%] h-[90%] md:w-[75%] md:h-[85%] z-10 shadow-xl overflow-hidden">
              <Image src="/images/adolescent.png" alt="Adolescent Perspective" fill className="object-cover" />
              <div className="absolute bottom-4 left-4 bg-white/90 backdrop-blur-sm px-3 py-1 text-xs uppercase tracking-widest text-primary font-medium">
                Adolescent
              </div>
            </div>
            
            {/* Overlapping frame 1 - Parent */}
            <div className="absolute left-0 md:left-[-10%] top-[10%] w-[45%] h-[40%] z-20 shadow-2xl overflow-hidden border-4 border-base">
              <Image src="/images/parent.png" alt="Parent Perspective" fill className="object-cover" />
              <div className="absolute bottom-3 left-3 bg-white/90 backdrop-blur-sm px-3 py-1 text-xs uppercase tracking-widest text-primary font-medium">
                Parent
              </div>
            </div>
            
            {/* Overlapping frame 2 - Teacher */}
            <div className="absolute left-[5%] md:left-[-5%] bottom-[15%] w-[40%] h-[35%] z-20 shadow-2xl overflow-hidden border-4 border-base">
              <Image src="/images/teacher.png" alt="Teacher Perspective" fill className="object-cover" />
              <div className="absolute bottom-3 left-3 bg-white/90 backdrop-blur-sm px-3 py-1 text-xs uppercase tracking-widest text-primary font-medium">
                Teacher
              </div>
            </div>
          </motion.div>
        </section>

        {/* 7. ABOUT SECTION / INTERACTIVE EXPERIENCE */}
        <div id="how-it-works">
          <MindLensScrollExperience />
        </div>

        {/* 8. THREE-PERSPECTIVE COLLAGE */}
        <section className="py-24 px-6 md:px-12 bg-base overflow-hidden">
          <div className="max-w-7xl mx-auto">
            <div className="relative h-[600px] md:h-[800px] w-full flex items-center justify-center">
              <motion.div 
                initial={{ opacity: 0, y: 50, rotate: -2 }}
                whileInView={{ opacity: 1, y: 0, rotate: -2 }}
                viewport={{ once: true, margin: "-100px" }}
                transition={{ duration: 0.8 }}
                className="absolute left-[5%] md:left-[10%] top-[10%] w-[40%] md:w-[30%] h-[50%] md:h-[60%] rounded-xl shadow-2xl overflow-hidden z-10"
              >
                <Image src="/images/parent.png" alt="Parent" fill className="object-cover" />
              </motion.div>
              
              <motion.div 
                initial={{ opacity: 0, y: 30, rotate: 1 }}
                whileInView={{ opacity: 1, y: 0, rotate: 1 }}
                viewport={{ once: true, margin: "-100px" }}
                transition={{ duration: 0.8, delay: 0.2 }}
                className="absolute right-[5%] md:right-[15%] top-[5%] md:top-[15%] w-[45%] md:w-[35%] h-[45%] md:h-[55%] rounded-xl shadow-2xl overflow-hidden z-20"
              >
                <Image src="/images/teacher.png" alt="Teacher" fill className="object-cover" />
              </motion.div>
              
              <motion.div 
                initial={{ opacity: 0, y: 40, rotate: -1 }}
                whileInView={{ opacity: 1, y: 0, rotate: -1 }}
                viewport={{ once: true, margin: "-100px" }}
                transition={{ duration: 0.8, delay: 0.4 }}
                className="absolute left-[20%] md:left-[35%] bottom-[10%] w-[50%] md:w-[40%] h-[55%] md:h-[65%] rounded-xl shadow-2xl overflow-hidden z-30"
              >
                <Image src="/images/adolescent.png" alt="Adolescent" fill className="object-cover" />
              </motion.div>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-3 gap-12 max-w-4xl mx-auto mt-24 text-center border-t border-neutral pt-16">
              <div className="flex flex-col gap-2">
                <span className="text-5xl font-serif text-primary">3</span>
                <span className="text-xs font-semibold text-textSecondary uppercase tracking-widest">Perspectives</span>
              </div>
              <div className="flex flex-col gap-2">
                <span className="text-5xl font-serif text-primary">6</span>
                <span className="text-xs font-semibold text-textSecondary uppercase tracking-widest">Dimensions</span>
              </div>
              <div className="flex flex-col gap-2">
                <span className="text-5xl font-serif text-primary">1</span>
                <span className="text-xs font-semibold text-textSecondary uppercase tracking-widest">Counselor View</span>
              </div>
            </div>
          </div>
        </section>

        {/* 9. PRICING SECTION */}
        <PricingSection />

        {/* 10. QUESTIONS SECTION (ACCORDION) */}
        <section className="py-24 px-6 md:px-12 bg-base border-t border-neutral">
          <div className="max-w-4xl mx-auto">
            <h2 className="text-3xl md:text-5xl font-serif text-primary uppercase leading-tight mb-16">
              Questions worth <br /> looking closer at.
            </h2>
            
            <div className="flex flex-col border-t border-primary/20">
              {[
                "Where do perspectives differ?",
                "What changed across environments?",
                "Which observations are shared?",
                "What evidence supports the signal?"
              ].map((question, i) => (
                <div key={i} className="border-b border-primary/20">
                  <button 
                    onClick={() => toggleAccordion(i)}
                    className="w-full flex items-center justify-between py-8 text-left group"
                  >
                    <div className="flex items-center gap-8">
                      <span className="text-sm font-medium text-textSecondary font-sans">0{i + 1}</span>
                      <span className="text-2xl md:text-3xl font-serif text-primary group-hover:text-accent transition-colors">{question}</span>
                    </div>
                    <span className="text-2xl font-light text-primary">{openAccordion === i ? '−' : '+'}</span>
                  </button>
                  <AnimatePresence>
                    {openAccordion === i && (
                      <motion.div
                        initial={{ height: 0, opacity: 0 }}
                        animate={{ height: "auto", opacity: 1 }}
                        exit={{ height: 0, opacity: 0 }}
                        transition={{ duration: 0.3, ease: "easeInOut" }}
                        className="overflow-hidden"
                      >
                        <p className="pb-8 pl-14 text-textSecondary text-lg max-w-2xl">
                          MindLens highlights the subtle deviations in structured feedback, giving the counselor a map of areas that require professional human interpretation.
                        </p>
                      </motion.div>
                    )}
                  </AnimatePresence>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* 11. PRODUCT SECTION */}
        <section id="for-counselors" className="py-32 px-6 md:px-12 bg-neutral/30">
          <div className="max-w-7xl mx-auto">
            <div className="text-center mb-16">
              <span className="text-xs uppercase tracking-widest text-textSecondary font-semibold mb-6 block">
                The Counselor View
              </span>
              <h2 className="text-3xl md:text-5xl font-serif text-primary uppercase leading-tight mb-6">
                Make the differences visible.
              </h2>
              <p className="text-lg text-textSecondary max-w-2xl mx-auto">
                A counselor should not have to reconstruct three perspectives manually.
              </p>
            </div>
            
            <motion.div 
              initial={{ opacity: 0, y: 40 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 1 }}
              className="bg-white rounded-none border border-neutral shadow-2xl p-8 md:p-12 overflow-hidden"
            >
              {/* Abstracted Interface Representation */}
              <div className="flex flex-col gap-6 w-full min-w-[800px]">
                {/* Headers */}
                <div className="flex gap-4 border-b border-neutral pb-4">
                  <div className="w-1/4"></div>
                  <div className="w-1/4 text-xs font-semibold uppercase tracking-widest text-textSecondary">Parent</div>
                  <div className="w-1/4 text-xs font-semibold uppercase tracking-widest text-textSecondary">Teacher</div>
                  <div className="w-1/4 text-xs font-semibold uppercase tracking-widest text-textSecondary">Adolescent</div>
                </div>
                
                {/* Rows */}
                {[
                  "Attention & Persistence",
                  "Activity",
                  "Adaptability",
                  "Sensitivity",
                  "Sociability",
                  "Self-Regulation"
                ].map((dim, i) => (
                  <div key={i} className="flex gap-4 items-center border-b border-neutral/30 pb-4">
                    <div className="w-1/4 text-sm font-medium text-primary uppercase">{dim}</div>
                    <div className="w-1/4">
                      <div className={`h-8 bg-surface/50 w-full relative`}>
                         <div className={`absolute left-0 top-0 bottom-0 bg-surface w-[${Math.floor(Math.random() * 40 + 40)}%]`}></div>
                      </div>
                    </div>
                    <div className="w-1/4">
                      <div className={`h-8 bg-surface/50 w-full relative`}>
                         <div className={`absolute left-0 top-0 bottom-0 bg-surface w-[${Math.floor(Math.random() * 40 + 40)}%]`}></div>
                      </div>
                    </div>
                    <div className="w-1/4">
                      <div className={`h-8 bg-surface/50 w-full relative ${i === 1 || i === 4 ? 'border-2 border-accent/40' : ''}`}>
                         <div className={`absolute left-0 top-0 bottom-0 bg-accent/80 w-[${Math.floor(Math.random() * 40 + 20)}%]`}></div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </motion.div>
          </div>
        </section>

        {/* 12. EVIDENCE SECTION */}
        <section id="evidence" className="py-32 px-6 md:px-12 bg-white">
          <div className="max-w-4xl mx-auto flex flex-col items-center">
            <h2 className="text-3xl md:text-5xl font-serif text-primary uppercase leading-tight mb-20 text-center">
              Every signal has a trail.
            </h2>
            
            <div className="flex flex-col items-center w-full relative">
              <div className="absolute top-0 bottom-0 left-1/2 w-[1px] bg-neutral -translate-x-1/2 z-0"></div>
              
              {[
                "Rater",
                "Question",
                "Response",
                "Dimension",
                "Score",
                "Rater Pair",
                "Discrepancy",
                "Signal",
                "Evidence",
                "Counselor"
              ].map((step, i) => (
                <motion.div 
                  key={i}
                  initial={{ opacity: 0, y: 20 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  viewport={{ once: true, margin: "-10%" }}
                  transition={{ delay: i * 0.1, duration: 0.5 }}
                  className="bg-white px-8 py-3 my-4 border border-neutral z-10 text-center uppercase tracking-widest text-sm font-medium text-primary min-w-[200px]"
                >
                  {step}
                </motion.div>
              ))}
            </div>
          </div>
        </section>

        {/* 13. HUMAN DECISION SECTION */}
        <section className="py-32 px-6 md:px-12 bg-primary text-base flex flex-col items-center text-center">
          <div className="max-w-5xl w-full">
            <h2 className="text-4xl md:text-6xl font-serif text-base uppercase leading-tight mb-24">
              The system organizes.<br />
              The counselor decides.
            </h2>
            
            <div className="grid grid-cols-1 md:grid-cols-3 gap-12 md:gap-8 border-t border-base/20 pt-16">
              <div className="flex justify-center">
                <span className="text-xl md:text-2xl font-serif text-base uppercase tracking-widest">Monitor</span>
              </div>
              <div className="flex justify-center md:border-l md:border-r border-base/20">
                <span className="text-xl md:text-2xl font-serif text-base uppercase tracking-widest">Reach Out</span>
              </div>
              <div className="flex justify-center">
                <span className="text-xl md:text-2xl font-serif text-base uppercase tracking-widest">Refer</span>
              </div>
            </div>
          </div>
        </section>

        {/* 14. RESEARCH SECTION */}
        <section id="research" className="py-32 px-6 md:px-12 bg-white">
          <div className="max-w-5xl mx-auto">
            <span className="text-xs uppercase tracking-widest text-textSecondary font-semibold mb-6 block">
              Research-Informed
            </span>
            <h2 className="text-3xl md:text-5xl font-serif text-primary uppercase leading-tight mb-24">
              Designed around evidence,<br />not assumptions.
            </h2>
            
            <div className="flex flex-col">
              <div className="border-t border-neutral py-12 flex flex-col md:flex-row gap-6 md:gap-16">
                <h3 className="w-full md:w-1/3 text-2xl font-serif text-primary uppercase">Multi-Rater</h3>
                <p className="w-full md:w-2/3 text-lg text-textSecondary">
                  Different observers can describe the same student differently. MindLens structures this reality rather than hiding it.
                </p>
              </div>
              <div className="border-t border-neutral py-12 flex flex-col md:flex-row gap-6 md:gap-16">
                <h3 className="w-full md:w-1/3 text-2xl font-serif text-primary uppercase">Deterministic</h3>
                <p className="w-full md:w-2/3 text-lg text-textSecondary">
                  Core calculations are reproducible and versioned. There is no hidden inference layer changing the data.
                </p>
              </div>
              <div className="border-t border-b border-neutral py-12 flex flex-col md:flex-row gap-6 md:gap-16">
                <h3 className="w-full md:w-1/3 text-2xl font-serif text-primary uppercase">Auditable</h3>
                <p className="w-full md:w-2/3 text-lg text-textSecondary">
                  A counselor can trace why information was surfaced, down to the exact questions and discrepancies.
                </p>
              </div>
            </div>
          </div>
        </section>

        {/* 15. AI BOUNDARY */}
        <section className="py-32 px-6 md:px-12 bg-base border-t border-neutral">
          <div className="max-w-6xl mx-auto text-center">
            <h2 className="text-3xl md:text-5xl font-serif text-primary uppercase leading-tight mb-24 max-w-4xl mx-auto">
              AI can organize the signal.<br />People decide what it means.
            </h2>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-0 border border-neutral bg-white">
              <div className="p-12 md:p-16 border-b md:border-b-0 md:border-r border-neutral text-left">
                <h3 className="text-xl font-serif text-primary uppercase mb-8 pb-4 border-b border-neutral/50">System</h3>
                <ul className="flex flex-col gap-4 text-textSecondary font-medium">
                  <li>Validation</li>
                  <li>Scoring</li>
                  <li>Normalization</li>
                  <li>Discrepancy calculation</li>
                  <li>Evidence retrieval</li>
                  <li>Workflow</li>
                  <li>Audit</li>
                </ul>
              </div>
              <div className="p-12 md:p-16 text-left">
                <h3 className="text-xl font-serif text-accent uppercase mb-8 pb-4 border-b border-neutral/50">Counselor</h3>
                <ul className="flex flex-col gap-4 text-primary font-medium">
                  <li>Interpretation</li>
                  <li>Context</li>
                  <li>Conversation</li>
                  <li>Professional judgment</li>
                  <li>Action</li>
                </ul>
              </div>
            </div>
          </div>
        </section>

        {/* 16. SECURITY */}
        <section className="relative py-48 px-6 md:px-12 overflow-hidden flex items-center justify-center bg-primary">
          <div className="absolute inset-0 z-0 opacity-40 mix-blend-overlay">
            <Image src="/images/security.png" alt="Security environment" fill className="object-cover" />
          </div>
          <div className="absolute inset-0 bg-primary/80 z-0"></div>
          
          <div className="relative z-10 max-w-4xl text-center text-base">
            <h2 className="text-4xl md:text-6xl font-serif uppercase leading-tight mb-16">
              Sensitive information <br /> deserves a quieter kind <br /> of design.
            </h2>
            
            <div className="flex flex-col md:flex-row justify-center gap-8 md:gap-16">
              <span className="text-sm uppercase tracking-widest font-semibold text-rare border-b border-rare/30 pb-2">Private Intake</span>
              <span className="text-sm uppercase tracking-widest font-semibold text-rare border-b border-rare/30 pb-2">Controlled Access</span>
              <span className="text-sm uppercase tracking-widest font-semibold text-rare border-b border-rare/30 pb-2">Traceable Activity</span>
            </div>
          </div>
        </section>

        {/* 17. FINAL CTA */}
        <section id="request-access" className="relative py-32 px-6 md:px-12 overflow-hidden">
          <div className="absolute inset-0 z-0">
            <Image src="/images/cta.png" alt="Architectural space" fill className="object-cover" />
          </div>
          <div className="absolute inset-0 bg-primary/60 z-0 backdrop-blur-sm"></div>
          
          <div className="relative z-10 max-w-3xl mx-auto text-base">
            <div className="text-center mb-16">
              <h2 className="text-4xl md:text-6xl font-serif uppercase leading-tight mb-6">
                Start with <br /> a clearer picture.
              </h2>
              <p className="text-lg text-rare/80 max-w-xl mx-auto">
                Bring structured perspectives together before the conversation begins.
              </p>
            </div>
            
            <div className="bg-base/5 p-8 md:p-12 border border-base/20 backdrop-blur-md">
              <form className="flex flex-col gap-6" onSubmit={(e) => e.preventDefault()}>
                <div className="flex flex-col gap-2">
                  <label className="text-xs uppercase tracking-widest font-semibold text-rare">School / Organization</label>
                  <input type="text" className="w-full bg-transparent border-b border-rare/30 py-3 text-base placeholder-rare/40 focus:outline-none focus:border-rare transition-colors" placeholder="e.g. Lincoln High School" />
                </div>
                <div className="flex flex-col gap-2">
                  <label className="text-xs uppercase tracking-widest font-semibold text-rare">Role</label>
                  <input type="text" className="w-full bg-transparent border-b border-rare/30 py-3 text-base placeholder-rare/40 focus:outline-none focus:border-rare transition-colors" placeholder="e.g. Head Counselor" />
                </div>
                <div className="flex flex-col gap-2">
                  <label className="text-xs uppercase tracking-widest font-semibold text-rare">Work Email</label>
                  <input type="email" className="w-full bg-transparent border-b border-rare/30 py-3 text-base placeholder-rare/40 focus:outline-none focus:border-rare transition-colors" placeholder="name@school.edu" />
                </div>
                <div className="flex flex-col gap-2">
                  <label className="text-xs uppercase tracking-widest font-semibold text-rare">Message</label>
                  <textarea rows={3} className="w-full bg-transparent border-b border-rare/30 py-3 text-base placeholder-rare/40 focus:outline-none focus:border-rare transition-colors resize-none" placeholder="How can we help?"></textarea>
                </div>
                
                <button type="submit" className="mt-8 group relative inline-flex items-center justify-center px-8 py-5 bg-base text-primary font-medium text-sm uppercase tracking-widest hover:bg-white transition-colors overflow-hidden">
                  <span className="relative z-10 transition-transform group-hover:-translate-y-0.5">Request Access</span>
                </button>
              </form>
            </div>
          </div>
        </section>
      </main>

      {/* 18. FOOTER */}
      <footer className="bg-base border-t border-neutral py-16 px-6 md:px-12">
        <div className="max-w-7xl mx-auto flex flex-col gap-16">
          <div className="flex flex-col md:flex-row justify-between items-start gap-12">
            <div>
              <span className="text-2xl font-serif text-primary uppercase block mb-4">MindLens</span>
              <p className="text-lg text-textSecondary font-serif italic max-w-sm">
                Three perspectives.<br />A clearer picture.
              </p>
            </div>
            
            <div className="grid grid-cols-2 md:grid-cols-2 gap-x-12 gap-y-4">
              <div className="flex flex-col gap-4">
                <Link href="#how-it-works" className="text-sm font-medium text-textSecondary hover:text-primary transition-colors uppercase tracking-wide">How It Works</Link>
                <Link href="#evidence" className="text-sm font-medium text-textSecondary hover:text-primary transition-colors uppercase tracking-wide">Evidence</Link>
                <Link href="#for-counselors" className="text-sm font-medium text-textSecondary hover:text-primary transition-colors uppercase tracking-wide">For Counselors</Link>
                <Link href="#research" className="text-sm font-medium text-textSecondary hover:text-primary transition-colors uppercase tracking-wide">Research</Link>
              </div>
              <div className="flex flex-col gap-4">
                <Link href="#security" className="text-sm font-medium text-textSecondary hover:text-primary transition-colors uppercase tracking-wide">Security</Link>
                <Link href="/login" className="text-sm font-medium text-textSecondary hover:text-primary transition-colors uppercase tracking-wide">Counselor Login</Link>
                <Link href="#request-access" className="text-sm font-medium text-textSecondary hover:text-primary transition-colors uppercase tracking-wide">Request Access</Link>
              </div>
            </div>
          </div>
          
          <div className="flex flex-col md:flex-row justify-between items-center pt-8 border-t border-neutral/50 gap-4 text-xs font-medium text-textSecondary uppercase tracking-widest">
            <div className="flex gap-8">
              <Link href="/privacy" className="hover:text-primary transition-colors">Privacy</Link>
              <Link href="/terms" className="hover:text-primary transition-colors">Terms</Link>
            </div>
            <span>© 2026 MindLens</span>
          </div>
        </div>
      </footer>
    </div>
  );
}
