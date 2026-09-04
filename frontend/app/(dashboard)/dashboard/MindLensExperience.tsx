'use client';
import React, { useState, useEffect, useRef } from 'react';
import { motion, useScroll, useTransform, AnimatePresence } from 'framer-motion';

export default function MindLensExperience() {
  const [isOpen, setIsOpen] = useState(false);
  
  return (
    <>
      <div 
        onClick={() => setIsOpen(true)}
        className="rounded-2xl p-6 border cursor-pointer relative overflow-hidden group transition-all duration-500 hover:shadow-xl col-span-2 md:col-span-4"
        style={{ background: '#121417', borderColor: '#2A2E35' }}
      >
        <div className="absolute inset-0 bg-gradient-to-br from-[#1A1F26] to-[#0A0C0E] opacity-50"></div>
        <div className="relative z-10 flex flex-col md:flex-row justify-between items-center h-full gap-4">
          <div>
            <span className="text-[10px] font-bold uppercase tracking-[0.2em] mb-1 block" style={{ color: '#4C9A94' }}>Introducing</span>
            <h3 className="text-xl font-light text-white" style={{ fontFamily: 'Newsreader, serif' }}>Experience MindLens</h3>
            <p className="text-sm text-white/50 mt-1 font-light">See how fragmented perspectives become clear.</p>
          </div>
          <div className="flex items-center gap-3">
            <span className="text-xs text-white/40 uppercase tracking-widest font-medium">Expand Experience</span>
            <span className="text-white/70 group-hover:translate-x-1 transition-transform group-hover:text-white">→</span>
          </div>
        </div>
      </div>

      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-[100] flex items-center justify-center bg-[#050607]/95 backdrop-blur-xl"
          >
            <motion.button 
              onClick={() => setIsOpen(false)}
              className="absolute top-8 right-8 text-white/50 hover:text-white z-50 text-xs tracking-[0.2em] uppercase font-bold transition-colors"
            >
              Close
            </motion.button>
            <CinematicView />
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
}

function CinematicView() {
  const containerRef = useRef<HTMLDivElement>(null);
  const { scrollYProgress } = useScroll({ container: containerRef });
  
  // 30 frames in the sequence
  const frameIndex = useTransform(scrollYProgress, [0, 1], [1, 30]);
  const [currentFrame, setCurrentFrame] = useState(1);

  useEffect(() => {
    return frameIndex.onChange((latest) => {
      setCurrentFrame(Math.max(1, Math.min(30, Math.round(latest))));
    });
  }, [frameIndex]);

  // Preload images for smooth playback
  useEffect(() => {
    for (let i = 1; i <= 30; i++) {
      const img = new Image();
      img.src = `/mindlens-frames/ezgif-frame-${i.toString().padStart(3, '0')}.jpg`;
    }
  }, []);

  const textOpacity = useTransform(scrollYProgress, [0, 0.1, 0.9, 1], [0.5, 1, 1, 0.5]);
  
  return (
    <div className="w-full h-full overflow-y-auto custom-scrollbar" ref={containerRef}>
      <div className="h-[400vh] w-full relative">
        <div className="sticky top-0 h-screen w-full flex items-center justify-center p-8 md:p-16">
          
          <div className="w-full max-w-7xl mx-auto grid grid-cols-1 lg:grid-cols-2 gap-16 lg:gap-24 items-center">
            
            {/* LEFT: Image Sequence */}
            <div className="relative aspect-video rounded-3xl overflow-hidden shadow-2xl bg-[#0A0C0E] border border-white/5">
              <img 
                src={`/mindlens-frames/ezgif-frame-${currentFrame.toString().padStart(3, '0')}.jpg`} 
                alt="MindLens Evolution"
                className="w-full h-full object-cover"
              />
              <div className="absolute inset-0 shadow-[inset_0_0_120px_rgba(0,0,0,0.9)] pointer-events-none"></div>
              
              <motion.div 
                style={{ opacity: useTransform(scrollYProgress, [0, 0.1], [1, 0]) }}
                className="absolute bottom-8 left-0 right-0 flex justify-center pointer-events-none"
              >
                <div className="px-5 py-2.5 rounded-full bg-black/60 backdrop-blur-md border border-white/10 flex items-center gap-3">
                  <span className="w-1.5 h-1.5 rounded-full bg-cyan-400 animate-pulse"></span>
                  <span className="text-[10px] uppercase tracking-[0.2em] text-white/70 font-medium">Scroll to explore</span>
                </div>
              </motion.div>
            </div>

            {/* RIGHT: Typography & Story */}
            <motion.div 
              style={{ opacity: textOpacity }}
              className="flex flex-col justify-center max-w-lg"
            >
              <motion.h2 
                initial={{ opacity: 0, y: 30 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ margin: "-10%" }}
                transition={{ duration: 1, ease: [0.16, 1, 0.3, 1] }}
                className="text-4xl md:text-5xl font-light text-white mb-8 leading-[1.1]" 
                style={{ fontFamily: 'Newsreader, serif' }}
              >
                One student.<br/>
                <span className="italic text-[#4C9A94]">Three perspectives.</span>
              </motion.h2>
              
              <motion.p 
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                transition={{ duration: 1, delay: 0.1, ease: [0.16, 1, 0.3, 1] }}
                className="text-lg md:text-xl text-white/60 mb-12 leading-relaxed font-light"
              >
                Counselors often work with fragmented information, while different informants may legitimately see the same student differently.
              </motion.p>
              
              <motion.div 
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                transition={{ duration: 1, delay: 0.2, ease: [0.16, 1, 0.3, 1] }}
                className="p-8 rounded-2xl bg-white/[0.02] border border-white/[0.05] backdrop-blur-xl mb-12"
              >
                <p className="text-sm md:text-base text-white/70 leading-relaxed font-light mb-6">
                  "Research shows parent–teacher agreement can be low-to-moderate across behavioral and emotional dimensions."
                </p>
                <button className="text-xs font-bold uppercase tracking-[0.15em] text-[#4C9A94] hover:text-[#78c7c1] transition-colors flex items-center gap-2 group">
                  Explore the evidence 
                  <span className="group-hover:translate-x-1 transition-transform">→</span>
                </button>
              </motion.div>
              
              <motion.p 
                initial={{ opacity: 0 }}
                whileInView={{ opacity: 1 }}
                transition={{ duration: 1, delay: 0.4 }}
                className="text-[10px] text-white/30 uppercase tracking-[0.2em] leading-relaxed font-bold"
              >
                MindLens doesn’t replace counselor judgment.<br/>
                It makes the information easier to understand.
              </motion.p>
            </motion.div>

          </div>
        </div>
      </div>
    </div>
  );
}
