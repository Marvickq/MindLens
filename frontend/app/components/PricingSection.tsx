'use client';
import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import Link from 'next/link';

interface PricingPlan {
  id: string;
  name: string;
  price: string;
  period: string;
  description: string;
  features: string[];
  ctaText: string;
  ctaSubtext?: string;
  isPremium?: boolean;
}

const pricingPlans: PricingPlan[] = [
  {
    id: 'school-start',
    name: 'SCHOOL START',
    price: '$0',
    period: 'Up to 20 students · Pilot',
    description: 'Try MindLens with a small student cohort before committing.',
    features: [
      'Up to 20 student cases',
      'Student perspective',
      'Counselor dashboard',
      'Perspective comparison',
      'Evidence Chain',
      '1 semester pilot'
    ],
    ctaText: 'Start Free Pilot',
    ctaSubtext: 'No credit card required',
    isPremium: false,
  },
  {
    id: 'school',
    name: 'SCHOOL',
    price: '$2,500',
    period: 'per school / year',
    description: 'For schools ready to use MindLens as part of their counseling workflow.',
    features: [
      '20+ student cases',
      'Student + Parent + Teacher perspectives',
      'Secure QR intake',
      'Perspective comparison',
      'Evidence Chain',
      'PDF reports',
      'Multiple counselor access',
      'Standard support'
    ],
    ctaText: 'Get School Access',
    ctaSubtext: 'Built for school-level adoption',
    isPremium: false,
  },
  {
    id: 'premium',
    name: 'PREMIUM',
    price: 'COMING SOON',
    period: 'Version 2',
    description: 'For schools ready to connect the entire support network around a student.',
    features: [
      'Everything in School',
      'Expanded student capacity',
      'Teacher onboarding',
      'Parent onboarding',
      'Guided stakeholder invitations',
      'Advanced school administration',
      'Enhanced reporting',
      'Priority support',
      'Future integrations'
    ],
    ctaText: 'Join the Premium Waitlist',
    isPremium: true,
  }
];

export default function PricingSection() {
  const [premiumModalOpen, setPremiumModalOpen] = useState(false);
  const [email, setEmail] = useState('');
  const [submitted, setSubmitted] = useState(false);

  const handleWaitlistSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (email) {
      setSubmitted(true);
      setTimeout(() => {
        setPremiumModalOpen(false);
        setSubmitted(false);
        setEmail('');
      }, 2000);
    }
  };

  return (
    <section className="py-32 md:py-48 px-6 md:px-12 bg-white flex flex-col items-center overflow-hidden">
      <div className="max-w-7xl w-full flex flex-col items-center">
        
        {/* HEADER */}
        <motion.div 
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: "-10%" }}
          transition={{ duration: 1, ease: "easeOut" }}
          className="text-center max-w-3xl mb-24"
        >
          <span className="text-xs uppercase tracking-widest text-[#5B6470] font-semibold mb-6 block">
            PLANS FOR SCHOOLS
          </span>
          <h2 className="text-4xl md:text-6xl font-serif text-[#1C3A56] uppercase leading-tight mb-8">
            Start with a school.<br/>Scale to a community.
          </h2>
          <p className="text-lg text-[#5B6470] font-light leading-relaxed">
            MindLens is built around the school — with students, counselors, teachers and parents connected through one workflow.
          </p>
        </motion.div>

        {/* PRICING CARDS */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 w-full mb-32 items-start relative z-10">
          {pricingPlans.map((plan, i) => (
            <motion.div
              key={plan.id}
              initial={{ opacity: 0, y: 30 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, margin: "-10%" }}
              transition={{ duration: 0.8, delay: i * 0.2, ease: "easeOut" }}
              whileHover={{ y: -8, transition: { duration: 0.3 } }}
              className={`flex flex-col h-full bg-white rounded-2xl p-8 md:p-10 transition-shadow duration-300 ${
                plan.isPremium 
                  ? 'border-2 border-[#4C9A94]/30 shadow-[0_20px_40px_-15px_rgba(28,58,86,0.15)] relative lg:-mt-4 bg-[#FAF7F0]/30' 
                  : 'border border-[#E7E3DA] shadow-sm hover:shadow-[0_15px_30px_-15px_rgba(28,58,86,0.1)]'
              }`}
            >
              {plan.isPremium && (
                <div className="absolute top-0 left-0 right-0 h-1 bg-[#4C9A94] rounded-t-2xl opacity-80" />
              )}
              
              <div className="mb-8">
                <h3 className="text-sm font-bold uppercase tracking-widest text-[#1C3A56] mb-6">
                  {plan.name}
                </h3>
                <div className="flex items-baseline mb-2">
                  <span className={`font-serif text-[#1C3A56] ${plan.price === 'COMING SOON' ? 'text-2xl md:text-3xl tracking-tight' : 'text-5xl md:text-6xl'}`}>
                    {plan.price}
                  </span>
                </div>
                <p className="text-xs font-semibold text-[#5B6470] uppercase tracking-widest min-h-[20px]">
                  {plan.period}
                </p>
              </div>

              <p className="text-sm text-[#5B6470] leading-relaxed mb-10 pb-10 border-b border-[#E7E3DA] min-h-[100px]">
                {plan.description}
              </p>

              <ul className="flex flex-col gap-4 mb-12 flex-grow">
                {plan.features.map((feature, idx) => (
                  <motion.li 
                    key={idx}
                    initial={{ opacity: 0, x: -10 }}
                    whileInView={{ opacity: 1, x: 0 }}
                    viewport={{ once: true }}
                    transition={{ delay: (i * 0.2) + (idx * 0.1) + 0.4, duration: 0.5 }}
                    className="flex items-start gap-3"
                  >
                    <span className="text-[#4C9A94] text-sm mt-0.5">✓</span>
                    <span className="text-sm text-[#1A1F26] leading-snug">{feature}</span>
                  </motion.li>
                ))}
              </ul>

              <div className="mt-auto pt-4 flex flex-col gap-3">
                <button
                  onClick={() => plan.isPremium ? setPremiumModalOpen(true) : null}
                  className={`w-full py-4 px-6 text-sm font-bold uppercase tracking-widest transition-colors rounded-xl text-center flex items-center justify-center ${
                    plan.isPremium 
                      ? 'bg-[#FAF7F0] border border-[#1C3A56]/20 text-[#1C3A56] hover:bg-[#1C3A56] hover:text-white' 
                      : 'bg-[#1C3A56] text-white hover:bg-[#2A4B6B]'
                  }`}
                >
                  {plan.ctaText}
                </button>
                {plan.ctaSubtext && (
                  <p className="text-[10px] text-center text-[#5B6470] uppercase tracking-widest font-medium">
                    {plan.ctaSubtext}
                  </p>
                )}
              </div>
            </motion.div>
          ))}
        </div>

        {/* POSITIONING VISUAL */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 1, delay: 0.4 }}
          className="flex flex-col items-center text-center max-w-2xl mx-auto mb-32"
        >
          <p className="text-sm md:text-base font-serif text-[#1C3A56] italic mb-12 border-b border-[#E7E3DA] pb-8">
            “Teachers and parents participate through the school — not separate subscriptions.”
          </p>
          
          <div className="flex flex-col items-center gap-2 text-xs font-bold uppercase tracking-widest text-[#5B6470]">
            <div className="text-[#1C3A56]">Counselor</div>
            <div className="text-[#E7E3DA]">↓</div>
            <div className="text-[#1C3A56] border border-[#E7E3DA] px-6 py-2 rounded-lg shadow-sm bg-white z-10">School</div>
            <div className="flex w-32 justify-between mt-1 text-[#E7E3DA]">
              <span className="transform -translate-x-2">↙</span>
              <span className="transform translate-x-2">↘</span>
            </div>
            <div className="flex w-48 justify-between">
              <div className="text-[#4C9A94]">Parent</div>
              <div className="text-[#4C9A94]">Teacher</div>
            </div>
            <div className="text-[#E7E3DA] mt-2">↓</div>
            <div className="text-[#1C3A56] border border-[#E7E3DA] px-6 py-2 rounded-lg bg-white mt-1">Student</div>
          </div>
        </motion.div>

        {/* BOTTOM BUSINESS MESSAGE */}
        <motion.div
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          viewport={{ once: true }}
          transition={{ duration: 1.2, delay: 0.6 }}
          className="text-center"
        >
          <h3 className="text-3xl md:text-5xl font-serif text-[#1C3A56] uppercase leading-tight mb-8">
            One School.<br/>
            Many Perspectives.<br/>
            One Workflow.
          </h3>
          <p className="text-lg text-[#5B6470] font-light">
            MindLens grows with the people already supporting the student.
          </p>
        </motion.div>

      </div>

      {/* PREMIUM COMING SOON MODAL */}
      <AnimatePresence>
        {premiumModalOpen && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-50 flex items-center justify-center bg-[#1C3A56]/40 backdrop-blur-sm p-6"
          >
            <motion.div 
              initial={{ scale: 0.95, y: 20, opacity: 0 }}
              animate={{ scale: 1, y: 0, opacity: 1 }}
              exit={{ scale: 0.95, y: 20, opacity: 0 }}
              transition={{ duration: 0.4, ease: [0.16, 1, 0.3, 1] }}
              className="bg-white rounded-3xl p-10 md:p-14 max-w-xl w-full shadow-2xl relative border border-[#E7E3DA]"
            >
              <button 
                onClick={() => setPremiumModalOpen(false)}
                className="absolute top-6 right-6 text-[#5B6470] hover:text-[#1C3A56] text-xl"
              >
                ✕
              </button>
              
              <div className="mb-10 text-center">
                <span className="text-xs uppercase tracking-widest text-[#4C9A94] font-bold mb-4 block">Version 2</span>
                <h3 className="text-3xl md:text-4xl font-serif text-[#1C3A56] mb-6 leading-tight">
                  Premium is coming.
                </h3>
                <p className="text-[#5B6470] leading-relaxed font-light">
                  We’re currently working on Version 2 of MindLens — including deeper teacher and parent onboarding, expanded school administration and additional institutional capabilities.
                </p>
              </div>
              
              {submitted ? (
                <motion.div 
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  className="bg-[#FAF7F0] rounded-xl p-8 text-center border border-[#E7E3DA]"
                >
                  <p className="text-[#1C3A56] font-serif text-lg">Thank you for joining the waitlist.</p>
                </motion.div>
              ) : (
                <div className="bg-[#FAF7F0]/50 rounded-2xl p-8 border border-[#E7E3DA]">
                  <p className="text-sm font-semibold text-[#1C3A56] mb-4 text-center uppercase tracking-widest">
                    Want to be first to know?
                  </p>
                  <form onSubmit={handleWaitlistSubmit} className="flex flex-col gap-4">
                    <input 
                      type="email" 
                      placeholder="Your email address" 
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                      required
                      className="w-full px-5 py-4 rounded-xl border border-[#c1c7cc] bg-white text-[#1a1c1d] focus:outline-none focus:border-[#4C9A94] transition-colors shadow-sm"
                    />
                    <button 
                      type="submit"
                      className="w-full py-4 bg-[#1C3A56] text-white rounded-xl text-sm font-bold uppercase tracking-widest hover:bg-[#2A4B6B] transition-colors"
                    >
                      Join the Waitlist
                    </button>
                  </form>
                </div>
              )}
              
              <div className="mt-8 text-center">
                <button 
                  onClick={() => setPremiumModalOpen(false)}
                  className="text-xs font-bold uppercase tracking-widest text-[#5B6470] hover:text-[#1C3A56] transition-colors"
                >
                  Continue with School
                </button>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </section>
  );
}
