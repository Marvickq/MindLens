'use client';
import React, { useState, useEffect, useRef } from 'react';
import { motion, useScroll, useTransform } from 'framer-motion';

export default function MindLensScrollExperience() {
  const containerRef = useRef<HTMLDivElement>(null);
  const { scrollYProgress } = useScroll({ 
    target: containerRef,
    offset: ["start start", "end end"] 
  });
  
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
  
  // Opacity transitions for text
  const textOpacity = useTransform(scrollYProgress, [0, 0.1, 0.9, 1], [0, 1, 1, 0]);
  const textY = useTransform(scrollYProgress, [0, 0.1], [50, 0]);

  return (
    <section 
      ref={containerRef} 
      className="relative w-full bg-[#050607]"
      style={{ height: '400vh' }}
    >
      <div className="sticky top-0 h-screen w-full flex items-center justify-center overflow-hidden px-6 md:px-12">
        <div className="absolute inset-0 bg-gradient-to-b from-white via-transparent to-[#050607] opacity-10 pointer-events-none"></div>
        
        <div className="w-full max-w-7xl mx-auto grid grid-cols-1 lg:grid-cols-2 gap-12 lg:gap-24 items-center z-10">
          
          {/* LEFT: Image Sequence */}
          <div className="relative aspect-video rounded-3xl overflow-hidden shadow-2xl bg-[#0A0C0E] border border-white/5 order-2 lg:order-1">
            <img 
              src={`/mindlens-frames/ezgif-frame-${currentFrame.toString().padStart(3, '0')}.jpg`} 
              alt="MindLens Evolution"
              className="w-full h-full object-cover"
            />
            <div className="absolute inset-0 shadow-[inset_0_0_80px_rgba(0,0,0,0.8)] pointer-events-none"></div>
            
            <motion.div 
              style={{ opacity: useTransform(scrollYProgress, [0, 0.1], [1, 0]) }}
              className="absolute bottom-6 left-0 right-0 flex justify-center pointer-events-none"
            >
              <div className="px-5 py-2 rounded-full bg-black/60 backdrop-blur-md border border-white/10 flex items-center gap-3">
                <span className="w-1.5 h-1.5 rounded-full bg-cyan-400 animate-pulse"></span>
                <span className="text-[10px] uppercase tracking-[0.2em] text-white/70 font-medium">Keep scrolling</span>
              </div>
            </motion.div>
          </div>

          {/* RIGHT: Typography & Story */}
          <motion.div 
            style={{ opacity: textOpacity, y: textY }}
            className="flex flex-col justify-center max-w-lg order-1 lg:order-2 py-12 lg:py-0"
          >
            <h2 
              className="text-4xl md:text-5xl font-light text-white mb-6 leading-[1.1]" 
              style={{ fontFamily: 'Newsreader, serif' }}
            >
              See the student <br/>
              <span className="italic text-[#4C9A94]">from more than one point of view.</span>
            </h2>
            
            <p className="text-lg md:text-xl text-white/60 mb-10 leading-relaxed font-light">
              Counselors often work with fragmented information, while different informants may legitimately see the same student differently.
            </p>
            
            <div className="p-8 rounded-2xl bg-white/[0.03] border border-white/[0.05] backdrop-blur-xl mb-10">
              <p className="text-sm md:text-base text-white/70 leading-relaxed font-light mb-6">
                "Research shows parent–teacher agreement can be low-to-moderate across behavioral and emotional dimensions."
              </p>
              <button className="text-xs font-bold uppercase tracking-[0.15em] text-[#4C9A94] hover:text-[#78c7c1] transition-colors flex items-center gap-2 group">
                Explore the evidence 
                <span className="group-hover:translate-x-1 transition-transform">→</span>
              </button>
            </div>
            
            <p className="text-[10px] text-white/30 uppercase tracking-[0.2em] leading-relaxed font-bold">
              MindLens doesn’t replace counselor judgment.<br/>
              It makes the information easier to understand.
            </p>
          </motion.div>

        </div>
      </div>
    </section>
  );
}
