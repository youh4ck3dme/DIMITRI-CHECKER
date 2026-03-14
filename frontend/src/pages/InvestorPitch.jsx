import React, { useEffect, useState, useRef } from 'react';
import { useNavigate } from 'react-router-dom';

const InvestorPitch = () => {
  const navigate = useNavigate();
  const [currentSlide, setCurrentSlide] = useState(0);
  const sliderRef = useRef(null);
  
  const slidesCount = 8; // Number of slides in the provided HTML

  const nextSlide = () => {
    if (currentSlide < slidesCount - 1) {
      setCurrentSlide(prev => prev + 1);
    }
  };

  const prevSlide = () => {
    if (currentSlide > 0) {
      setCurrentSlide(prev => prev - 1);
    }
  };

  const goToSlide = (index) => {
    setCurrentSlide(index);
  };

  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === 'ArrowRight' || e.key === ' ') {
        nextSlide();
      } else if (e.key === 'ArrowLeft') {
        prevSlide();
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [currentSlide]);

  return (
    <div className="h-screen w-full relative flex flex-col antialiased selection:bg-cyan-500 selection:text-white bg-[#0f172a] text-[#f8fafc] overflow-hidden font-sans">
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;800;900&family=Inter:wght@300;400;500;600&display=swap');
        
        .outfit { font-family: 'Outfit', sans-serif; }
        .slide-transition {
          transition: opacity 0.5s ease, transform 0.5s ease;
        }
        .glass-panel {
          background: rgba(30, 41, 59, 0.85);
          backdrop-filter: blur(16px);
          -webkit-backdrop-filter: blur(16px);
          border: 1px solid rgba(148, 163, 184, 0.15);
          box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5);
        }
        .text-gradient {
          background-clip: text;
          -webkit-background-clip: text;
          -webkit-text-fill-color: transparent;
          background-image: linear-gradient(to right, #22d3ee, #3b82f6);
        }
        .bg-gradient-glow {
          position: absolute;
          width: 600px;
          height: 600px;
          background: radial-gradient(circle, rgba(56,189,248,0.12) 0%, rgba(15,23,42,0) 70%);
          border-radius: 50%;
          pointer-events: none;
          z-index: 0;
        }
        .custom-scrollbar::-webkit-scrollbar { width: 6px; }
        .custom-scrollbar::-webkit-scrollbar-track { background: transparent; }
        .custom-scrollbar::-webkit-scrollbar-thumb { background: rgba(51, 65, 85, 0.8); border-radius: 10px; }
      `}</style>

      {/* Global Header */}
      <header className="absolute top-0 left-0 w-full p-4 md:p-6 z-50 flex justify-between items-center pointer-events-none">
        <div className="flex items-center gap-3 glass-panel px-4 py-2 rounded-2xl pointer-events-auto shadow-lg cursor-pointer" onClick={() => navigate('/')}>
          <div className="w-8 h-8 md:w-10 md:h-10 rounded-lg bg-gradient-to-br from-cyan-400 to-blue-600 flex items-center justify-center shadow-lg shadow-blue-500/30">
            <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M3 3v18h18"/><path d="M18 17V9"/><path d="M13 17V5"/><path d="M8 17v-3"/></svg>
          </div>
          <span className="outfit font-bold text-[22px] md:text-2xl tracking-wide hidden sm:block">📊 V4-Finstat v5.0</span>
          <span className="outfit font-bold text-[22px] tracking-wide sm:hidden">V4-Finstat</span>
        </div>
        <div className="hidden md:block px-4 py-1.5 rounded-full glass-panel text-base font-semibold text-cyan-400 uppercase tracking-widest">
          Inwestor Presentation
        </div>
      </header>

      {/* Background Effects */}
      <div className="bg-gradient-glow top-[-100px] left-[-100px]"></div>
      <div className="bg-gradient-glow bottom-[-200px] right-[-100px] opacity-70" style={{ background: 'radial-gradient(circle, rgba(59,130,246,0.15) 0%, rgba(15,23,42,0) 70%)' }}></div>

      <main className="relative w-full h-full overflow-hidden z-10">
        
        {/* Slide 1 */}
        <section className={`slide-transition absolute inset-0 overflow-y-auto custom-scrollbar px-4 py-24 md:px-8 ${currentSlide === 0 ? 'opacity-100 z-20 scale-100' : 'opacity-0 z-0 scale-95 pointer-events-none'}`}>
          <div className="m-auto w-full max-w-5xl text-center space-y-6 md:space-y-8">
            <div className="inline-flex items-center gap-2 px-4 py-2 md:px-6 md:py-3 rounded-full bg-blue-500/10 border border-blue-500/20 text-blue-400 font-bold text-base md:text-lg uppercase tracking-widest">
              B2B SaaS Softvér | Live na produkcii
            </div>
            <h1 className="text-[40px] sm:text-[52px] md:text-[5.75rem] font-black leading-tight tracking-tight uppercase outfit">
              Vyhľadávač firiem<br />
              <span className="text-gradient">pre celý región V4</span>
            </h1>
            <div className="glass-panel p-5 md:p-8 rounded-3xl border-2 border-cyan-500/30 mt-8">
              <p className="text-[22px] sm:text-2xl md:text-[34px] text-slate-200 font-medium leading-relaxed">
                <strong className="text-white font-black block mb-2">Aké riešenie prinášame?</strong>
                B2B platforma, kde po zadaní IČO obchodného partnera <span className="text-cyan-400 font-bold">do 1 sekundy</span> zistíte: reálnu štruktúru, <span className="text-red-400 font-bold">dlhy</span> a risk.
              </p>
            </div>
            <div className="pt-6">
              <button onClick={nextSlide} className="group px-10 py-5 bg-white text-slate-900 font-black rounded-2xl transition-all hover:scale-105 shadow-xl text-xl uppercase tracking-wider">
                Zistiť viac
              </button>
            </div>
          </div>
        </section>

        {/* Slide 2: Features */}
        <section className={`slide-transition absolute inset-0 overflow-y-auto custom-scrollbar px-4 py-24 md:px-8 ${currentSlide === 1 ? 'opacity-100 z-20 scale-100' : 'opacity-0 z-0 scale-95 pointer-events-none'}`}>
          <div className="m-auto w-full max-w-7xl">
            <h2 className="text-[34px] md:text-[64px] font-black mb-12 text-center uppercase tracking-wider outfit">Kľúčové funkcie <span className="text-gradient">systému</span></h2>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div className="glass-panel p-8 rounded-3xl border-t-4 border-blue-500">
                <h3 className="text-2xl font-bold text-white mb-3">1. Agregácia V4 dát</h3>
                <p className="text-slate-300 text-lg leading-relaxed">Konsolidácia SK, CZ, PL a HU registrov do jedného inteligentného engine.</p>
              </div>
              <div className="glass-panel p-8 rounded-3xl border-t-4 border-cyan-400">
                <h3 className="text-2xl font-bold text-white mb-3">2. Vizualizácia</h3>
                <p className="text-slate-300 text-lg leading-relaxed">Grafické mapovanie vzťahov pre odhalenie bielych koní a schránkových firiem.</p>
              </div>
              <div className="glass-panel p-8 rounded-3xl border-t-4 border-red-500">
                <h3 className="text-2xl font-bold text-white mb-3">3. ERP Integrácia</h3>
                <p className="text-slate-300 text-lg leading-relaxed">Priame napojenie na SAP, Pohodu a Money S3 pre audit platieb v reálnom čase.</p>
              </div>
            </div>
          </div>
        </section>

        {/* Slide 3: Tech */}
        <section className={`slide-transition absolute inset-0 overflow-y-auto custom-scrollbar px-4 py-24 md:px-8 ${currentSlide === 2 ? 'opacity-100 z-20 scale-100' : 'opacity-0 z-0 scale-95 pointer-events-none'}`}>
          <div className="m-auto w-full max-w-5xl text-center">
            <h2 className="text-[34px] md:text-[52px] font-bold mb-8 outfit">Technologická <span className="text-gradient">stabilita</span></h2>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div className="glass-panel p-8 rounded-2xl">
                <h4 className="text-[40px] font-black text-white mb-2">93 / 93</h4>
                <p className="text-slate-400 uppercase tracking-widest font-bold">QA Testy</p>
              </div>
              <div className="glass-panel p-8 rounded-2xl">
                <h4 className="text-2xl font-bold text-white mb-2">Nexus Resolver</h4>
                <p className="text-slate-400 uppercase tracking-widest font-bold">Vlastný Algoritmus</p>
              </div>
              <div className="glass-panel p-8 rounded-2xl">
                <h4 className="text-2xl font-bold text-white mb-2">Production</h4>
                <p className="text-slate-400 uppercase tracking-widest font-bold">Docker & Cloud</p>
              </div>
            </div>
          </div>
        </section>

        {/* Slide 4: ERP */}
        <section className={`slide-transition absolute inset-0 overflow-y-auto custom-scrollbar px-4 py-24 md:px-8 ${currentSlide === 3 ? 'opacity-100 z-20 scale-100' : 'opacity-0 z-0 scale-95 pointer-events-none'}`}>
          <div className="m-auto w-full max-w-6xl">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
              <div>
                <h2 className="text-[34px] md:text-[52px] font-bold mb-6 outfit">ERP Integrácie:<br /><span className="text-gradient">Enterprise Standard</span></h2>
                <p className="text-xl text-slate-300 mb-6">Navrhnuté pre automatizáciu compliance procesov vo veľkých firmách.</p>
                <div className="flex items-center gap-4 p-4 glass-panel rounded-xl mb-4">
                  <span className="font-bold text-white">SAP / Pohoda / Money S3</span>
                </div>
              </div>
              <div className="glass-panel p-8 rounded-2xl border-l-4 border-cyan-500">
                <h3 className="text-2xl font-bold text-white mb-4">Plug & Play Konektory</h3>
                <p className="text-slate-400 leading-relaxed italic">Vytvárame vysoké switching costs, čo zabezpečuje lojalitu klientov v enterprise segmente.</p>
              </div>
            </div>
          </div>
        </section>

        {/* Slide 5: Monetization */}
        <section className={`slide-transition absolute inset-0 overflow-y-auto custom-scrollbar px-4 py-24 md:px-8 ${currentSlide === 4 ? 'opacity-100 z-20 scale-100' : 'opacity-0 z-0 scale-95 pointer-events-none'}`}>
          <div className="m-auto w-full max-w-6xl text-center">
            <h2 className="text-[34px] md:text-[52px] font-bold mb-12 outfit">Monetizácia a <span className="text-gradient">Zisk</span></h2>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
              <div className="glass-panel p-6 rounded-2xl border-t-4 border-slate-500">
                <h3 className="text-xl font-bold text-white">PRO</h3>
                <div className="text-3xl font-black my-4 text-white">500 €</div>
                <p className="text-slate-400 text-sm">SME Segment</p>
              </div>
              <div className="glass-panel p-6 rounded-2xl border-2 border-cyan-500 scale-110 shadow-cyan-500/20">
                <h3 className="text-xl font-bold text-cyan-400">ENTERPRISE</h3>
                <div className="text-3xl font-black my-4 text-white">700 €+</div>
                <p className="text-slate-400 text-sm">Logistika & Korporácie</p>
              </div>
              <div className="glass-panel p-6 rounded-2xl border-t-4 border-blue-500">
                <h3 className="text-xl font-bold text-white">API DATA</h3>
                <div className="text-3xl font-black my-4 text-white">Usage-Based</div>
                <p className="text-slate-400 text-sm">Banky & Poisťovne</p>
              </div>
            </div>
            <div className="mt-16 flex justify-center gap-12">
              <div>
                <div className="text-4xl font-black text-green-400">85%+</div>
                <div className="text-xs uppercase font-bold text-slate-500 tracking-widest mt-2">Marža</div>
              </div>
              <div>
                <div className="text-4xl font-black text-white">3M €</div>
                <div className="text-xs uppercase font-bold text-slate-500 tracking-widest mt-2">Cieľ ARR</div>
              </div>
            </div>
          </div>
        </section>

        {/* Slide 6: Legal */}
        <section className={`slide-transition absolute inset-0 overflow-y-auto custom-scrollbar px-4 py-24 md:px-8 ${currentSlide === 5 ? 'opacity-100 z-20 scale-100' : 'opacity-0 z-0 scale-95 pointer-events-none'}`}>
          <div className="m-auto w-full max-w-5xl">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
              <div className="glass-panel p-8 rounded-2xl border border-green-500/30">
                <h3 className="text-2xl font-bold text-white mb-6">Compliance Proof</h3>
                <ul className="space-y-4 text-slate-300">
                  <li><strong>GDPR Ready:</strong> Oprávnený záujem podľa čl. 6.</li>
                  <li><strong>Legálne zdroje:</strong> 100% verejné registre.</li>
                  <li><strong>Scale Risk:</strong> Proxy infraštruktúra chráni prevádzku.</li>
                </ul>
              </div>
              <h2 className="text-[34px] md:text-[52px] font-bold outfit">Bezpečná <span className="text-gradient">Investícia</span></h2>
            </div>
          </div>
        </section>

        {/* Slide 7: Roadmap */}
        <section className={`slide-transition absolute inset-0 overflow-y-auto custom-scrollbar px-4 py-24 md:px-8 ${currentSlide === 6 ? 'opacity-100 z-20 scale-100' : 'opacity-0 z-0 scale-95 pointer-events-none'}`}>
          <div className="m-auto w-full max-w-6xl text-center">
            <h2 className="text-[34px] md:text-[52px] font-bold mb-12 outfit">Roadmapa <span className="text-gradient">2024/25</span></h2>
            <div className="flex flex-col md:flex-row gap-4">
              <div className="glass-panel p-6 flex-1 rounded-xl">
                <div className="text-cyan-400 font-bold mb-2">Q1: Launch</div>
                <p className="text-slate-400 text-sm">Prvých 10 B2B zmlúv a penetrácia trhu.</p>
              </div>
              <div className="glass-panel p-6 flex-1 rounded-xl opacity-50">
                <div className="text-slate-300 font-bold mb-2">Q2: V4 Expanzia</div>
                <p className="text-slate-500 text-sm">PL a HU integrácia naplno.</p>
              </div>
              <div className="glass-panel p-6 flex-1 rounded-xl opacity-30">
                <div className="text-slate-300 font-bold mb-2">Q3: AI Scoring</div>
                <p className="text-slate-600 text-sm">Nasadenie prediktívnych modelov.</p>
              </div>
              <div className="glass-panel p-6 flex-1 rounded-xl bg-yellow-400/5">
                <div className="text-yellow-400 font-bold mb-2">Q4: Exit Preparations</div>
                <p className="text-slate-400 text-sm">Series A pri 15M EUR valuácii.</p>
              </div>
            </div>
          </div>
        </section>

        {/* Slide 8: The Ask */}
        <section className={`slide-transition absolute inset-0 overflow-y-auto custom-scrollbar px-4 py-24 md:px-8 ${currentSlide === 7 ? 'opacity-100 z-20 scale-100' : 'opacity-0 z-0 scale-95 pointer-events-none'}`}>
          <div className="m-auto w-full max-w-5xl text-center space-y-8">
            <h2 className="text-[34px] md:text-[52px] font-black text-slate-300 uppercase outfit">Investičná požiadavka</h2>
            <div className="text-[80px] md:text-[160px] font-black text-gradient leading-none">100 000 €</div>
            <div className="text-3xl md:text-5xl font-black text-green-400 drop-shadow-lg">Target Exit: 10x ROI</div>
            <h3 className="text-xl md:text-2xl text-slate-400 font-light">
              Participujte na technológii s cieľovou valuáciou <span className="text-white font-bold">15 000 000 €</span>
            </h3>
            <div className="pt-10">
              <button 
                onClick={() => navigate('/')}
                className="px-12 py-6 bg-gradient-to-r from-cyan-500 to-blue-600 text-white font-black rounded-xl text-2xl uppercase tracking-widest shadow-2xl hover:scale-105 transition-transform"
              >
                Otvoriť Systém
              </button>
            </div>
          </div>
        </section>

        {/* Navigation */}
        <button onClick={prevSlide} className="absolute left-4 top-1/2 -translate-y-1/2 z-50 p-3 rounded-full glass-panel hover:bg-white/10 transition-colors">
          <svg width="24" height="24" fill="none" stroke="white" strokeWidth="3" viewBox="0 0 24 24"><path d="M15 18l-6-6 6-6"/></svg>
        </button>
        <button onClick={nextSlide} className="absolute right-4 top-1/2 -translate-y-1/2 z-50 p-3 rounded-full glass-panel hover:bg-white/10 transition-colors">
          <svg width="24" height="24" fill="none" stroke="white" strokeWidth="3" viewBox="0 0 24 24"><path d="M9 18l6-6-6-6"/></svg>
        </button>

        {/* Dots */}
        <div className="absolute bottom-8 w-full flex justify-center gap-3 z-50">
          {[...Array(slidesCount)].map((_, i) => (
            <button
              key={i}
              onClick={() => goToSlide(i)}
              className={`h-2 rounded-full transition-all duration-300 ${currentSlide === i ? 'w-8 bg-cyan-400' : 'w-2 bg-slate-600'}`}
            />
          ))}
        </div>
      </main>
    </div>
  );
};

export default InvestorPitch;
