import React from 'react';
import { Link } from 'react-router-dom';
import { FileText, Shield, Cookie, AlertCircle } from 'lucide-react';
import Logo from './Logo';
import IluminatiLogo from './IluminatiLogo';
import Disclaimer from './Disclaimer';

const Footer = () => {
  return (
    <footer className="bg-brand-navy border-t border-brand-border text-brand-slate py-20 relative overflow-hidden">
      <div className="max-w-7xl mx-auto px-6 relative z-10">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-16 mb-20">
          {/* Brand */}
          <div className="col-span-1 md:col-span-1">
            <div className="flex items-center gap-3 mb-8">
              <IluminatiLogo size={24} />
              <span className="font-black text-brand-white text-sm tracking-widest uppercase">V4-FINSTAT</span>
            </div>
            <p className="text-xs leading-relaxed font-light mb-6">
              Poskytujeme strategické business intelligence riešenia pre enterprise sektor v regióne V4. Transparentnosť ako standard.
            </p>
            <div className="text-[10px] font-bold uppercase tracking-widest text-brand-gold">
              Established 2024
            </div>
          </div>

          {/* Links */}
          <div>
            <h4 className="text-[10px] font-black uppercase tracking-[0.3em] text-brand-white mb-8">Právne aspekty</h4>
            <ul className="space-y-4 text-[11px] uppercase tracking-widest font-bold">
              <li><Link to="/investor" className="hover:text-brand-gold transition-colors opacity-40 hover:opacity-100">Enterprise Investor</Link></li>
              <li><Link to="/vop" className="hover:text-brand-gold transition-colors">Všeobecné obchodné podmienky</Link></li>
              <li><Link to="/privacy" className="hover:text-brand-gold transition-colors">Zásady ochrany osobných údajov</Link></li>
              <li><Link to="/disclaimer" className="hover:text-brand-gold transition-colors">Vyhlásenie o odmietnutí zodpovednosti</Link></li>
              <li><Link to="/cookie" className="hover:text-brand-gold transition-colors">Cookie Policy</Link></li>
              <li><Link to="/dpa" className="hover:text-brand-gold transition-colors">Data Processing Agreement (B2B)</Link></li>
            </ul>
          </div>

          {/* Connection */}
          <div>
            <h4 className="text-[10px] font-black uppercase tracking-[0.3em] text-brand-white mb-8">Support Hub</h4>
            <ul className="space-y-2 text-[11px] text-brand-white">
              <li className="font-mono">intelligence@v4-finstat.com</li>
              <li className="font-mono">compliance@v4-finstat.com</li>
              <li className="mt-4 text-brand-slate text-[10px] uppercase font-bold tracking-widest">
                Cross-Border Nexus s.r.o.<br/>
                Eurovea Tower, Bratislava
              </li>
            </ul>
          </div>

          {/* Disclaimer Info */}
          <div className="col-span-1">
            <h4 className="text-[10px] font-black uppercase tracking-[0.3em] text-brand-white mb-8">Oznámenie</h4>
            <p className="text-[10px] leading-relaxed italic border-l-2 border-brand-gold/30 pl-4">
              Agregované dáta z verejných zdrojov. Informácie majú informatívny charakter pre účely B2B compliance a risk manažmentu.
            </p>
          </div>
        </div>

        {/* Data Sources Disclaimer */}
        <div className="pt-10 border-t border-brand-border flex flex-col md:flex-row justify-between items-center gap-6">
          <div className="flex flex-wrap gap-4 text-[9px] uppercase font-bold tracking-widest text-brand-slate">
            <span>ORSR</span>
            <span className="text-brand-gold">•</span>
            <span>RUZ SK</span>
            <span className="text-brand-gold">•</span>
            <span>ARES CZ</span>
            <span className="text-brand-gold">•</span>
            <span>FINANČNÁ SPRÁVA</span>
          </div>
          <p className="text-[10px] font-bold uppercase tracking-widest text-brand-white/40">
            &copy; {new Date().getFullYear()} V4-FINSTAT PROJEKT s.r.o. Všetky práva vyhradené.
          </p>
        </div>
      </div>
    </footer>
  );
};

export default Footer;

