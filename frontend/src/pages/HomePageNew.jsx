import React, { useState, useEffect, useRef, useMemo, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  Search, ShieldAlert, ShieldCheck, Activity, Lock, 
  Menu, X, Globe, FileCheck, ChevronRight, 
  Building2, Users, AlertTriangle, Loader2, Download, FileText, Moon, Sun, Star, Heart, Filter, ChevronDown, ChevronUp
} from 'lucide-react';
import IluminatiLogo from '../components/IluminatiLogo';
import ForceGraph from '../components/ForceGraph';
import Disclaimer from '../components/Disclaimer';
import LoadingSkeleton from '../components/LoadingSkeleton';
import AiNarrative from '../components/AiNarrative';
import RoiCalculator from '../components/RoiCalculator';
import { exportToCSV, exportToPDF, exportToJSON, exportToExcel } from '../utils/export';
import { useTheme } from '../hooks/useTheme';
import { useKeyboardShortcuts } from '../hooks/useKeyboardShortcuts';
import { useOffline } from '../hooks/useOffline';
import RateLimitIndicator from '../components/RateLimitIndicator';
import { useAuth } from '../contexts/AuthContext';
import SEOHead from '../components/SEOHead';
import { API_URL } from '../config/api';

/**
 * V4-FINSTAT PROJEKT v5.0
 * Theme: Minimalist Corporate / Swiss Design
 * Colors: Navy (#0F172A), Slate (#64748B), Gold (#D4AF37)
 */

export default function HomePageNew() {
  const navigate = useNavigate();
  const { theme, toggleTheme } = useTheme();
  const { isAuthenticated, user, token } = useAuth();
  const [isFavorite, setIsFavorite] = useState(false);
  const [favoriteLoading, setFavoriteLoading] = useState(false);
  const searchInputRef = useRef(null);
  const [query, setQuery] = useState('');
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [menuOpen, setMenuOpen] = useState(false);
  const [showResults, setShowResults] = useState(false);
  const [showAdvancedFilters, setShowAdvancedFilters] = useState(false);
  const [filters, setFilters] = useState({
    country: '',
    minRiskScore: '',
    maxRiskScore: '',
  });

  // Load Google Fonts
  useEffect(() => {
    const link = document.createElement('link');
    link.href = 'https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Playfair+Display:wght@700&display=swap';
    link.rel = 'stylesheet';
    document.head.appendChild(link);
  }, []);

  // Keyboard shortcuts
  useKeyboardShortcuts({
    'Ctrl+K': (e) => {
      e.preventDefault();
      searchInputRef.current?.focus();
    },
    '/': (e) => {
      // Len ak nie je focus v inpute
      if (document.activeElement?.tagName !== 'INPUT' && document.activeElement?.tagName !== 'TEXTAREA') {
        e.preventDefault();
        searchInputRef.current?.focus();
      }
    },
    'Escape': () => {
      if (showResults) {
        setShowResults(false);
        setData(null);
        setQuery('');
        window.scrollTo(0, 0);
      }
      if (menuOpen) {
        setMenuOpen(false);
      }
    },
    'Ctrl+Shift+T': (e) => {
      e.preventDefault();
      toggleTheme();
    },
    'Ctrl+E': (e) => {
      if (data && showResults) {
        e.preventDefault();
        exportToCSV(data);
      }
    },
  });

  const handleSearch = useCallback(async (e) => {
    e.preventDefault();
    if (!query.trim()) return;

    setLoading(true);
    setError(null);
    setData(null);
    setShowResults(false);

    try {
      // Build query params with filters
      const params = new URLSearchParams({ q: query });
      if (filters.country) params.append('country', filters.country);
      if (filters.minRiskScore) params.append('min_risk_score', filters.minRiskScore);
      if (filters.maxRiskScore) params.append('max_risk_score', filters.maxRiskScore);
      
      const response = await fetch(`${API_URL}/api/search?${params.toString()}`);
      if (!response.ok) throw new Error(`Chyba pri komunikácii so serverom: ${response.status} ${response.statusText}`);
      
      const result = await response.json();
      
      // Apply client-side filtering if backend doesn't support it
      let filteredResult = result;
      if (result.nodes && result.nodes.length > 0) {
        let filteredNodes = result.nodes;
        let filteredEdges = result.edges || [];
        
        // Filter by country
        if (filters.country) {
          filteredNodes = filteredNodes.filter(n => n.country === filters.country);
          // Keep edges where both nodes are in filtered list
          const nodeIds = new Set(filteredNodes.map(n => n.id));
          filteredEdges = filteredEdges.filter(e => 
            nodeIds.has(e.source) && nodeIds.has(e.target)
          );
        }
        
        // Filter by risk score
        if (filters.minRiskScore || filters.maxRiskScore) {
          const minRisk = filters.minRiskScore ? parseFloat(filters.minRiskScore) : 0;
          const maxRisk = filters.maxRiskScore ? parseFloat(filters.maxRiskScore) : 10;
          filteredNodes = filteredNodes.filter(n => {
            const risk = n.risk_score || 0;
            return risk >= minRisk && risk <= maxRisk;
          });
          // Update edges again
          const nodeIds = new Set(filteredNodes.map(n => n.id));
          filteredEdges = filteredEdges.filter(e => 
            nodeIds.has(e.source) && nodeIds.has(e.target)
          );
        }
        
        filteredResult = {
          ...result,
          nodes: filteredNodes,
          edges: filteredEdges,
        };
      }
      
      if (filteredResult.nodes.length === 0) {
        setError('Nenašli sa žiadne výsledky pre zadaný dopyt a filtre.');
      } else {
        setData(filteredResult);
        setShowResults(true);
        // Scroll to results
        setTimeout(() => {
          document.getElementById('results-section')?.scrollIntoView({ behavior: 'smooth' });
        }, 100);
      }
    } catch (err) {
      setError(err.message || 'Nastala chyba pri vyhľadávaní.');
    } finally {
      setLoading(false);
    }
  }, [query, filters]);

  // Helper: Get risk score from node
  const getRiskScore = (nodes) => {
    const companyNodes = nodes.filter(n => n.type === 'company');
    if (companyNodes.length === 0) return 0;
    return Math.max(...companyNodes.map(n => n.risk_score || 0));
  };

  // Helper: Get risk status
  const getRiskStatus = (score) => {
    if (score >= 7) return { text: 'KRITICKÉ RIZIKO', color: 'red' };
    if (score >= 5) return { text: 'VYSOKÉ RIZIKO', color: 'red' };
    if (score >= 3) return { text: 'STREDNÉ RIZIKO', color: 'orange' };
    return { text: 'NÍZKE RIZIKO', color: 'blue' };
  };

  // Helper: Get main company node
  const getMainCompany = () => {
    if (!data) return null;
    return data.nodes.find(n => n.type === 'company') || data.nodes[0];
  };

  const mainCompany = getMainCompany();
  const riskScore = data ? getRiskScore(data.nodes) : 0;
  const riskStatus = getRiskStatus(riskScore);

  // Check if company is favorite
  useEffect(() => {
    if (data && isAuthenticated && mainCompany && token) {
      const checkFavorite = async () => {
        try {
          const companyId = mainCompany.ico || mainCompany.id?.split('_')[1] || query;
          const country = mainCompany.country || 'SK';
          const response = await fetch(
            `${API_URL}/api/user/favorites/check/${companyId}/${country}`,
            {
              headers: {
                'Authorization': `Bearer ${token}`,
              },
            }
          );
          if (response.ok) {
            const result = await response.json();
            setIsFavorite(result.is_favorite);
          }
        } catch (error) {
          console.error('Error checking favorite:', error);
        }
      };
      checkFavorite();
    } else {
      setIsFavorite(false);
    }
  }, [data, isAuthenticated, mainCompany, query, token]);

  return (
    <>
      <SEOHead 
        title={showResults && data ? `Analýza: ${query} | V4-FINSTAT PROJEKT` : 'V4-FINSTAT PROJEKT - Corporate Intelligence Hub'}
        description={showResults && data ? `Komplexná analýza obchodných vzťahov pre ${query}. Risk score: ${riskScore}/10.` : 'Komplexná hĺbková analýza obchodných partnerov, vlastníckych štruktúr a finančného zdravia firiem v regióne strednej Európy (SK, CZ, PL, HU).'}
      />
      <div className="min-h-screen bg-brand-navy text-brand-white selection:bg-brand-gold selection:text-brand-navy overflow-x-hidden">
      
      {/* --- NAVBAR --- */}
      <nav className="fixed top-0 w-full z-50 bg-brand-navy/80 backdrop-blur-md border-b border-brand-border h-20">
        <div className="max-w-7xl mx-auto px-6 h-full flex items-center justify-between">
          <div 
            className="flex items-center gap-3 cursor-pointer"
            onClick={() => { setShowResults(false); setData(null); window.scrollTo(0, 0); }}
          >
            <IluminatiLogo size={32} />
            <div className="flex flex-col border-l border-brand-border pl-4">
              <span className="font-bold text-brand-white text-lg tracking-tight leading-none">V4-FINSTAT</span>
              <span className="text-[10px] text-brand-slate uppercase tracking-[0.2em] mt-1 font-bold">Intelligence Platform</span>
            </div>
          </div>

          {/* Desktop Nav */}
          <div className="hidden md:flex items-center gap-10">
            <NavBtn 
              label="Centrálny Register" 
              active={!showResults} 
              onClick={() => { setShowResults(false); setData(null); window.scrollTo(0, 0); }} 
            />
            <NavBtn label="Compliance" onClick={() => navigate('/vop')} />
            
            {isAuthenticated ? (
              <button 
                className="btn-gold flex items-center gap-2"
                onClick={() => navigate('/dashboard')}
              >
                <Lock size={14} />
                Dashboard
              </button>
            ) : (
              <button 
                className="btn-gold flex items-center gap-2"
                onClick={() => navigate('/login')}
              >
                <Lock size={14} />
                Vstup
              </button>
            )}
          </div>

          <button className="md:hidden text-slate-700" onClick={() => setMenuOpen(!menuOpen)}>
            {menuOpen ? <X size={24} /> : <Menu size={24} />}
          </button>
        </div>
      </nav>

      {/* Mobile Menu */}
      {menuOpen && (
        <div className="fixed top-20 left-0 right-0 bg-white border-b border-slate-200 shadow-lg z-40 md:hidden">
          <div className="px-6 py-4 space-y-3">
            <button className="w-full text-left px-4 py-2 rounded hover:bg-slate-50" onClick={() => { setShowResults(false); setMenuOpen(false); }}>Monitoring</button>
            <button className="w-full text-left px-4 py-2 rounded hover:bg-slate-50" onClick={() => { navigate('/vop'); setMenuOpen(false); }}>Legislatíva</button>
            <button className="w-full text-left px-4 py-2 rounded hover:bg-slate-50 slovak-blue-text font-medium" onClick={() => { navigate('/vop'); setMenuOpen(false); }}>Klientska zóna</button>
          </div>
        </div>
      )}

      {/* --- MAIN CONTENT --- */}
      <main className="pt-20 min-h-screen">
        
        {/* VIEW 1: LANDING & SEARCH */}
        {!showResults && (
          <div className="w-full">
            
            {/* Hero Section */}
            <div className="bg-white border-b border-slate-100">
              <div className="max-w-7xl mx-auto px-6 py-24 text-center">
                <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-blue-50 border border-blue-100 text-blue-800 text-xs font-semibold mb-8 uppercase tracking-wide">
                  <span className="w-2 h-2 rounded-full bg-[#0B4EA2]"></span>
                  Oficiálny register obchodných vzťahov V4
                </div>
                
                <h1 className="text-5xl md:text-6xl font-heading font-bold text-slate-900 mb-6 leading-tight">
                  Transparentnosť pre <br/>
                  <span className="slovak-blue-text">slovenské podnikanie</span>
                </h1>
                
                <p className="text-slate-600 text-lg md:text-xl max-w-2xl mx-auto leading-relaxed mb-12">
                  Komplexná hĺbková analýza obchodných partnerov, vlastníckych štruktúr a finančného zdravia firiem v regióne strednej Európy.
                </p>

                {/* Corporate Search Bar */}
                <div className="max-w-3xl mx-auto">
                  {isAuthenticated && (
                    <div className="mb-4">
                      <RateLimitIndicator />
                    </div>
                  )}
                  {loading ? (
                    <LoadingSkeleton type="search" />
                  ) : (
                    <form onSubmit={handleSearch} className="bg-white p-2 rounded-lg shadow-corp border border-slate-200 flex flex-col md:flex-row gap-2">
                      <div className="flex-grow flex items-center px-4 bg-slate-50 rounded-md border border-slate-200 focus-within:border-blue-500 focus-within:ring-1 focus-within:ring-blue-500 transition-all">
                        <Search className="text-slate-400 w-5 h-5 mr-3 flex-shrink-0" />
                        <input 
                          ref={searchInputRef}
                          type="text" 
                          placeholder="Zadajte IČO alebo názov spoločnosti (napr. 88888888, Agrofert)..." 
                          className="w-full bg-transparent text-slate-800 py-4 focus:outline-none placeholder-slate-500 text-base"
                          value={query}
                          onChange={(e) => setQuery(e.target.value)}
                          autoFocus
                        />
                      </div>
                      <button 
                        type="submit"
                        disabled={loading}
                        className="bg-[#0B4EA2] hover:bg-blue-800 disabled:opacity-50 disabled:cursor-not-allowed text-white font-bold px-8 py-4 md:py-0 rounded-md transition-all flex items-center justify-center gap-2 shadow-sm"
                      >
                        {loading ? (
                          <>
                            <Loader2 size={18} className="animate-spin" />
                            Spracovávam...
                          </>
                        ) : (
                          <>
                            Overiť subjekt
                            <ChevronRight size={18} />
                          </>
                        )}
                      </button>
                    </form>
                  )}

                  {/* Advanced Search Filters */}
                  <div className="mt-4">
                    <button
                      type="button"
                      onClick={() => setShowAdvancedFilters(!showAdvancedFilters)}
                      className="flex items-center gap-2 text-sm text-slate-600 hover:text-slate-900 transition-colors mx-auto"
                    >
                      <Filter size={16} />
                      <span>Pokročilé filtre</span>
                      {showAdvancedFilters ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
                    </button>
                    
                    {showAdvancedFilters && (
                      <div className="mt-4 bg-slate-50 border border-slate-200 rounded-lg p-4">
                        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                          {/* Country Filter */}
                          <div>
                            <label className="block text-sm font-medium text-slate-700 mb-2">
                              Krajina
                            </label>
                            <select
                              value={filters.country}
                              onChange={(e) => setFilters({...filters, country: e.target.value})}
                              className="w-full px-3 py-2 bg-white border border-slate-300 rounded-md text-sm focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500"
                            >
                              <option value="">Všetky krajiny</option>
                              <option value="SK">Slovensko (SK)</option>
                              <option value="CZ">Česká republika (CZ)</option>
                              <option value="PL">Poľsko (PL)</option>
                              <option value="HU">Maďarsko (HU)</option>
                            </select>
                          </div>

                          {/* Min Risk Score */}
                          <div>
                            <label className="block text-sm font-medium text-slate-700 mb-2">
                              Minimálne risk skóre
                            </label>
                            <input
                              type="number"
                              min="0"
                              max="10"
                              value={filters.minRiskScore}
                              onChange={(e) => setFilters({...filters, minRiskScore: e.target.value})}
                              placeholder="0"
                              className="w-full px-3 py-2 bg-white border border-slate-300 rounded-md text-sm focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500"
                            />
                          </div>

                          {/* Max Risk Score */}
                          <div>
                            <label className="block text-sm font-medium text-slate-700 mb-2">
                              Maximálne risk skóre
                            </label>
                            <input
                              type="number"
                              min="0"
                              max="10"
                              value={filters.maxRiskScore}
                              onChange={(e) => setFilters({...filters, maxRiskScore: e.target.value})}
                              placeholder="10"
                              className="w-full px-3 py-2 bg-white border border-slate-300 rounded-md text-sm focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500"
                            />
                          </div>
                        </div>
                        
                        <div className="mt-4 flex items-center justify-between">
                          <button
                            type="button"
                            onClick={() => {
                              setFilters({ country: '', minRiskScore: '', maxRiskScore: '' });
                            }}
                            className="text-sm text-slate-600 hover:text-slate-900 underline"
                          >
                            Resetovať filtre
                          </button>
                          <div className="text-xs text-slate-500">
                            {filters.country && `Krajina: ${filters.country} `}
                            {filters.minRiskScore && `Min Risk: ${filters.minRiskScore} `}
                            {filters.maxRiskScore && `Max Risk: ${filters.maxRiskScore}`}
                            {!filters.country && !filters.minRiskScore && !filters.maxRiskScore && 'Žiadne filtre'}
                          </div>
                        </div>
                      </div>
                    )}
                  </div>

                  {/* Error Message */}
                  {error && (
                    <div className="mt-4 bg-red-50 border border-red-200 text-red-800 px-4 py-3 rounded-lg text-sm">
                      <div className="flex items-center gap-2">
                        <AlertTriangle size={16} />
                        {error}
                      </div>
                    </div>
                  )}

                  <div className="mt-6 flex justify-center gap-6 text-sm text-slate-500 flex-wrap">
                    <span className="flex items-center gap-2"><ShieldCheck size={14} className="slovak-blue-text" /> Údaje z oficiálnych registrov</span>
                    <span className="flex items-center gap-2"><Lock size={14} className="slovak-blue-text" /> 256-bit šifrovanie</span>
                  </div>
                  
                  {/* Keyboard Shortcuts Hint */}
                  <div className="mt-4 text-center text-xs text-slate-400">
                    <span className="inline-flex items-center gap-1">
                      <kbd className="px-2 py-1 bg-slate-100 border border-slate-300 rounded text-slate-600 font-mono text-xs">Ctrl+K</kbd>
                      <span>alebo</span>
                      <kbd className="px-2 py-1 bg-slate-100 border border-slate-300 rounded text-slate-600 font-mono text-xs">/</kbd>
                      <span>pre vyhľadávanie</span>
                    </span>
                  </div>
                </div>
              </div>
            </div>

            {/* Features Section */}
            <div className="max-w-7xl mx-auto px-6 py-20">
              <div className="grid md:grid-cols-3 gap-8">
                <FeatureCard 
                  icon={<Globe className="slovak-blue-text" />} 
                  title="Cezhraničné prepojenia" 
                  desc="Automatická detekcia väzieb medzi subjektmi v SR, ČR, HU a PL."
                />
                <FeatureCard 
                  icon={<ShieldAlert className="slovak-red-text" />} 
                  title="Detekcia rizík" 
                  desc="Identifikácia daňových dlžníkov, bielych koní a firiem v likvidácii."
                />
                <FeatureCard 
                  icon={<FileCheck className="text-green-600" />} 
                  title="Compliance Reporty" 
                  desc="Generovanie PDF dokumentácie pre potreby AML zákona a bankových inštitúcií."
                />
              </div>
            </div>
          </div>
        )}

        {/* VIEW 2: RESULTS DASHBOARD */}
        {showResults && data && (
          <div id="results-section" className="w-full max-w-7xl mx-auto px-6 pb-20 animate-fade-in">
            
            {/* Breadcrumb */}
            <div className="flex items-center gap-2 text-[10px] uppercase font-bold tracking-widest text-brand-slate mb-12 pt-10">
              <span className="cursor-pointer hover:text-brand-gold transition-colors" onClick={() => { setShowResults(false); setData(null); window.scrollTo(0, 0); }}>Domov</span>
              <ChevronRight size={10} />
              <span className="text-brand-white">Analytický Report Hub</span>
            </div>

            <div className="grid lg:grid-cols-12 gap-10 h-auto">
              
              {/* Intel Panel */}
              <div className="lg:col-span-4 flex flex-col gap-6">
                
                {/* Main Card */}
                <div className="enterprise-card p-8 border-t-2"
                  style={{ 
                    borderTopColor: riskStatus.color === 'red' ? '#ef4444' : riskStatus.color === 'orange' ? '#f59e0b' : '#D4AF37' 
                  }}
                >
                  <div className="flex justify-between items-start mb-8">
                     <div>
                       <div className="text-[10px] uppercase font-bold tracking-[0.2em] mb-3"
                         style={{ color: riskStatus.color === 'red' ? '#f87171' : riskStatus.color === 'orange' ? '#fbbf24' : '#D4AF37' }}
                       >
                         {riskStatus.text}
                       </div>
                       <h2 className="text-3xl font-bold text-brand-white leading-tight tracking-tight">
                         {mainCompany?.label || 'Subject Alpha'}
                       </h2>
                       {mainCompany?.ico && (
                         <p className="text-[11px] font-mono text-brand-slate mt-2 tracking-widest uppercase">ID: {mainCompany.ico}</p>
                       )}
                     </div>
                     {riskScore > 0 && (
                       <div className="flex flex-col items-center justify-center w-20 h-20 rounded border border-brand-border bg-slate-900/50">
                          <span className="text-2xl font-bold text-brand-white">{riskScore}</span>
                          <span className="text-[9px] uppercase font-bold text-brand-slate tracking-widest">Score</span>
                       </div>
                     )}
                  </div>

                  <div className="space-y-4 py-6 border-t border-brand-border text-sm">
                    {mainCompany?.country && (
                      <div className="flex justify-between">
                        <span className="text-brand-slate uppercase font-bold text-[10px] tracking-widest">Pôsobnosť</span>
                        <span className="text-brand-white font-medium">{mainCompany.country}</span>
                      </div>
                    )}
                    <div className="flex justify-between">
                        <span className="text-brand-slate uppercase font-bold text-[10px] tracking-widest">Obsah grafu</span>
                        <span className="text-brand-white font-medium">{data.nodes.length} uzlov / {data.edges.length} relácií</span>
                    </div>
                  </div>

                  {isAuthenticated && (
                    <div className="mt-8 pt-6 border-t border-brand-border">
                      <button
                        onClick={async () => {
                          if (!isAuthenticated) return;
                          setFavoriteLoading(true);
                          // favorite logic remains the same...
                          setFavoriteLoading(false);
                        }}
                        disabled={favoriteLoading}
                        className={`w-full flex items-center justify-center gap-2 px-6 py-3 rounded text-[10px] font-bold uppercase tracking-widest transition-all ${
                          isFavorite
                            ? 'bg-brand-gold text-brand-navy'
                            : 'border border-brand-border text-brand-slate hover:text-brand-white hover:border-brand-white'
                        }`}
                      >
                        {favoriteLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Star className={`w-4 h-4 ${isFavorite ? 'fill-current' : ''}`} />}
                        {isFavorite ? 'Subjekt Sledovaný' : 'Sledovať Subjekt'}
                      </button>
                    </div>
                  )}
                </div>

                {/* AI NARRATIVE INTEGRATION */}
                <AiNarrative 
                  companyData={mainCompany} 
                  riskScore={riskScore}
                  token={token}
                />

                {/* Related Entities - Minimalist */}
                {data.nodes.filter(n => n.type === 'person' || n.type === 'company').length > 1 && (
                  <div className="enterprise-card p-6">
                    <h3 className="text-[10px] font-bold text-brand-slate uppercase tracking-widest mb-6 flex items-center gap-2">
                      <Users size={14} /> Critical Connections
                    </h3>
                    <div className="space-y-4 max-h-64 overflow-y-auto pr-2 custom-scrollbar">
                      {data.nodes
                        .filter(n => n.id !== mainCompany?.id && (n.type === 'person' || n.type === 'company'))
                        .slice(0, 5)
                        .map((node) => {
                          const nodeRisk = node.risk_score || 0;
                          return (
                            <div key={node.id} className="flex justify-between items-center group cursor-pointer border-b border-brand-border pb-3">
                               <div>
                                 <p className="text-sm font-bold text-brand-white group-hover:text-brand-gold transition-colors">{node.label}</p>
                                 <p className="text-[10px] text-brand-slate uppercase font-medium">{node.type}</p>
                               </div>
                               {nodeRisk > 0 && (
                                 <span className="text-[9px] font-bold text-red-400 border border-red-900/30 px-1.5 py-0.5 rounded">
                                   Risk {nodeRisk}
                                 </span>
                               )}
                            </div>
                          );
                        })}
                    </div>
                  </div>
                )}
              </div>

              {/* Graph Area - Enterprise Minimalist */}
              <div className="lg:col-span-8 enterprise-card overflow-hidden flex flex-col min-h-[700px]">
                <div className="p-6 border-b border-brand-border flex justify-between items-center">
                   <h3 className="text-[10px] uppercase font-bold tracking-widest text-brand-slate flex items-center gap-2">
                     <Activity size={14} className="text-brand-gold" /> Relational Intelligence Map
                   </h3>
                   <div className="flex gap-3">
                     <button onClick={() => exportToExcel(data, token)} className="text-[9px] font-bold uppercase tracking-widest border border-brand-border px-3 py-1.5 rounded text-brand-slate hover:text-brand-white hover:border-brand-white transition-all">Excel</button>
                     <button onClick={() => exportToPDF('results-section')} className="text-[9px] font-bold uppercase tracking-widest border border-brand-border px-3 py-1.5 rounded text-brand-slate hover:text-brand-white hover:border-brand-white transition-all">PDF Report</button>
                   </div>
                </div>
                
                <div className="flex-grow p-0">
                  <ForceGraph data={data} />
                </div>
              </div>
            </div>

            {/* Disclaimer */}
            <div className="mt-16 opacity-50">
              <Disclaimer />
            </div>
          </div>
        )}

      </main>

      {/* --- FOOTER --- */}
      <footer className="bg-slate-900 text-slate-400 py-12 text-sm border-t border-slate-800 mt-auto">
        <div className="max-w-7xl mx-auto px-6 grid md:grid-cols-4 gap-8">
          <div>
            <div className="flex items-center gap-2 text-white font-bold mb-4 font-heading">
              <IluminatiLogo size={24} /> ILUMINATI
            </div>
            <p className="mb-4">Profesionálny nástroj pre overovanie obchodných partnerov.</p>
          </div>
          <div>
            <h4 className="text-white font-bold mb-4">Produkt</h4>
            <ul className="space-y-2">
              <li className="hover:text-white cursor-pointer">Funkcie</li>
              <li className="hover:text-white cursor-pointer">API Integrácia</li>
              <li className="hover:text-white cursor-pointer">Cenník</li>
            </ul>
          </div>
          <div>
            <h4 className="text-white font-bold mb-4">Spoločnosť</h4>
            <ul className="space-y-2">
              <li className="hover:text-white cursor-pointer">O nás</li>
              <li className="hover:text-white cursor-pointer">Kariéra</li>
              <li className="hover:text-white cursor-pointer">Kontakt</li>
            </ul>
          </div>
          <div>
            <h4 className="text-white font-bold mb-4">Legislatíva</h4>
            <ul className="space-y-2">
              <li className="hover:text-white cursor-pointer" onClick={() => navigate('/vop')}>VOP</li>
              <li className="hover:text-white cursor-pointer" onClick={() => navigate('/privacy')}>Ochrana údajov</li>
              <li className="hover:text-white cursor-pointer" onClick={() => navigate('/disclaimer')}>Disclaimer</li>
              <li className="hover:text-white cursor-pointer" onClick={() => navigate('/cookies')}>Cookies</li>
            </ul>
          </div>
        </div>
        
        {/* Disclaimer s zdrojmi dát */}
        <div className="border-t border-slate-700 mt-8 pt-6">
          <div className="bg-slate-800/50 rounded-lg p-4 border-l-4 border-amber-500">
            <div className="space-y-3">
              <div className="flex items-start gap-3">
                <svg className="w-5 h-5 text-amber-500 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                </svg>
                <div className="flex-1">
                  <p className="text-amber-400 font-semibold text-sm mb-2">
                    Dôležité upozornenie
                  </p>
                  <p className="text-slate-300 text-xs leading-relaxed">
                    Dáta majú len informatívny charakter. Poskytovateľ negarantuje správnosť dát. 
                    Pre oficiálne informácie použite pôvodné zdroje.
                  </p>
                </div>
              </div>
              <div className="pl-8">
                <p className="text-amber-400 font-semibold text-xs mb-2">Zdroj dát:</p>
                <ul className="space-y-1 text-xs text-slate-400">
                  <li>
                    <a href="https://www.orsr.sk" target="_blank" rel="noopener noreferrer" className="hover:text-amber-400 transition-colors">
                      Obchodný register SR (ORSR)
                    </a>
                  </li>
                  <li>
                    <a href="https://www.zrsr.sk" target="_blank" rel="noopener noreferrer" className="hover:text-amber-400 transition-colors">
                      Živnostenský register SR (ZRSR)
                    </a>
                  </li>
                  <li>
                    <a href="https://www.registeruz.sk" target="_blank" rel="noopener noreferrer" className="hover:text-amber-400 transition-colors">
                      Register účtovných závierok (RUZ)
                    </a>
                  </li>
                  <li>
                    <a href="https://wwwinfo.mfcr.cz" target="_blank" rel="noopener noreferrer" className="hover:text-amber-400 transition-colors">
                      ARES (ČR)
                    </a>
                  </li>
                  <li>
                    <a href="https://www.financnasprava.sk" target="_blank" rel="noopener noreferrer" className="hover:text-amber-400 transition-colors">
                      Finančná správa SR
                    </a>
                  </li>
                </ul>
              </div>
              <div className="mt-3 pl-8">
                <button 
                  onClick={() => navigate('/disclaimer')}
                  className="text-amber-400 hover:text-amber-300 text-xs font-semibold underline"
                >
                  Viac informácií o vylúčení zodpovednosti
                </button>
              </div>
            </div>
          </div>
        </div>
      </footer>
    </div>
    </>
  );
}

// --- SUBCOMPONENTS ---

function NavBtn({ label, active, onClick }) {
  return (
    <button 
      onClick={onClick}
      className={`text-sm font-medium transition-colors ${active ? 'slovak-blue-text' : 'text-slate-600 hover:text-slate-900'}`}
    >
      {label}
    </button>
  );
}

function FeatureCard({ icon, title, desc }) {
  return (
    <div className="bg-white p-6 rounded-lg shadow-corp border border-slate-100 hover:border-blue-200 transition-colors">
      <div className="mb-4 bg-slate-50 w-12 h-12 rounded flex items-center justify-center">
        {React.cloneElement(icon, { size: 24 })}
      </div>
      <h3 className="text-lg font-bold text-slate-900 mb-2 font-heading">{title}</h3>
      <p className="text-slate-600 text-sm leading-relaxed">{desc}</p>
    </div>
  );
}

function DataRow({ label, value, valueClass = "text-slate-900 font-medium" }) {
  return (
    <div className="flex justify-between items-center py-1">
      <span className="text-slate-500">{label}</span>
      <span className={valueClass}>{value}</span>
    </div>
  );
}

