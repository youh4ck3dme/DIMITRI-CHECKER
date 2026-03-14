import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import IluminatiLogo from '../components/IluminatiLogo';
import { exportBatchToExcel } from '../utils/export';
import { Download } from 'lucide-react';

const Dashboard = () => {
  const { user, logout, refreshUser } = useAuth();
  const navigate = useNavigate();
  const [searchHistory, setSearchHistory] = useState([]);
  const [favorites, setFavorites] = useState([]);
  const [tierLimits, setTierLimits] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = async () => {
    try {
      const token = localStorage.getItem('access_token');
      
      // Načítať tier limits
      const limitsResponse = await fetch('http://localhost:8000/api/auth/tier/limits', {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });
      if (limitsResponse.ok) {
        const limits = await limitsResponse.json();
        setTierLimits(limits);
      }

      // Načítať search history
      const historyResponse = await fetch('http://localhost:8000/api/search/history', {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });
      if (historyResponse.ok) {
        const history = await historyResponse.json();
        setSearchHistory(history.slice(0, 10)); // Posledných 10
      }

      // Načítať favorites
      const favoritesResponse = await fetch('http://localhost:8000/api/user/favorites', {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });
      if (favoritesResponse.ok) {
        const favoritesData = await favoritesResponse.json();
        setFavorites(favoritesData.favorites || []);
      }
    } catch (error) {
      console.error('Error loading dashboard data:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleUpgrade = async (tier) => {
    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch(`http://localhost:8000/api/payment/checkout?tier=${tier}`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (response.ok) {
        const data = await response.json();
        if (data.url) {
          window.location.href = data.url; // Redirect to Stripe Checkout
        }
      }
    } catch (error) {
      console.error('Error creating checkout:', error);
    }
  };

  const getTierColor = (tier) => {
    switch (tier) {
      case 'free':
        return 'bg-gray-500';
      case 'pro':
        return 'bg-blue-500';
      case 'enterprise':
        return 'bg-purple-500';
      default:
        return 'bg-gray-500';
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-brand-navy flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-brand-gold"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-brand-navy text-brand-white">
      <nav className="fixed top-0 w-full z-50 bg-brand-navy/80 backdrop-blur-md border-b border-brand-border h-20">
        <div className="max-w-7xl mx-auto px-6 h-full flex items-center justify-between">
          <div 
            className="flex items-center gap-3 cursor-pointer"
            onClick={() => navigate('/')}
          >
            <IluminatiLogo size={32} />
            <div className="flex flex-col border-l border-brand-border pl-4">
              <span className="font-bold text-brand-white text-lg tracking-tight leading-none uppercase">V4-FINSTAT</span>
              <span className="text-[10px] text-brand-slate uppercase tracking-[0.2em] mt-1 font-bold">Terminal Access</span>
            </div>
          </div>
          <div className="flex items-center gap-6">
            <span className="text-[10px] uppercase font-bold text-brand-slate tracking-widest">{user?.email}</span>
            <button
              onClick={logout}
              className="text-[10px] uppercase font-bold text-red-400 hover:text-red-300 transition-colors tracking-widest"
            >
              Odhlásiť
            </button>
          </div>
        </div>
      </nav>

      <div className="max-w-7xl mx-auto px-6 pt-32 pb-20">
        {/* Profile Card */}
        <div className="enterprise-card p-10 mb-10 border-t-2 border-brand-gold">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
            <div>
              <div className="text-[10px] uppercase font-bold text-brand-gold tracking-[0.3em] mb-4">Enterprise User Profile</div>
              <h2 className="text-4xl font-bold tracking-tighter mb-2">
                {user?.full_name || 'Strategic Analyst'}
              </h2>
              <p className="text-brand-slate font-mono text-sm">{user?.email}</p>
            </div>
            <div className="flex flex-col items-end gap-3">
              <div className="px-5 py-2 border border-brand-gold/30 bg-brand-gold/5 text-brand-gold text-xs font-black uppercase tracking-widest">
                Tier: {user?.tier || 'FREE'}
              </div>
              {user?.tier === 'free' && (
                <button
                  onClick={() => handleUpgrade('pro')}
                  className="btn-gold px-8 py-3 text-[10px]"
                >
                  Upgrade to Unlimited
                </button>
              )}
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
          {/* Stats */}
          <div className="enterprise-card p-8">
            <h3 className="text-[10px] font-bold text-brand-slate uppercase tracking-widest mb-8">Intelligence Limits</h3>
            {tierLimits ? (
              <div className="space-y-6">
                <div className="flex justify-between items-end border-b border-brand-border pb-4">
                  <span className="text-sm text-brand-white">Denné dopyty</span>
                  <span className="text-xl font-bold text-brand-gold">
                    {tierLimits.searches_per_day === -1 ? '∞' : tierLimits.searches_per_day}
                  </span>
                </div>
                <div className="flex justify-between items-end border-b border-brand-border pb-4">
                  <span className="text-sm text-brand-white">Hĺbka grafu</span>
                  <span className="text-xl font-bold text-brand-gold">
                    {tierLimits.max_graph_nodes === -1 ? 'Full' : tierLimits.max_graph_nodes}
                  </span>
                </div>
                <div className="flex justify-between items-end">
                  <span className="text-sm text-brand-white">Export Intelligence</span>
                  <span className={`text-[10px] font-black uppercase tracking-widest ${tierLimits.can_export_pdf ? 'text-green-500' : 'text-red-900'}`}>
                    {tierLimits.can_export_pdf ? 'Povolený' : 'Zablokovaný'}
                  </span>
                </div>
              </div>
            ) : (
              <div className="animate-pulse flex space-y-4 flex-col">
                <div className="h-4 bg-slate-800 rounded w-full"></div>
                <div className="h-4 bg-slate-800 rounded w-3/4"></div>
              </div>
            )}
          </div>

          {/* History */}
          <div className="enterprise-card p-8">
            <h3 className="text-[10px] font-bold text-brand-slate uppercase tracking-widest mb-8">Monitorovací log</h3>
            {searchHistory.length > 0 ? (
              <div className="space-y-4 max-h-64 overflow-y-auto pr-2 custom-scrollbar">
                {searchHistory.map((search, index) => (
                  <div
                    key={index}
                    className="flex justify-between items-center border-b border-brand-border pb-3 group cursor-pointer"
                    onClick={() => navigate(`/?q=${search.query}`)}
                  >
                    <div>
                      <div className="text-sm font-bold text-brand-white group-hover:text-brand-gold transition-colors">{search.query}</div>
                      <div className="text-[10px] text-brand-slate uppercase mt-1">
                        {new Date(search.timestamp).toLocaleDateString('sk-SK')}
                      </div>
                    </div>
                    <Download size={12} className="text-brand-slate opacity-0 group-hover:opacity-100 transition-opacity" />
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-xs text-brand-slate italic uppercase tracking-widest">Žiadne záznamy</p>
            )}
          </div>

          {/* Quick Actions */}
          <div className="enterprise-card p-8 flex flex-col justify-between">
            <h3 className="text-[10px] font-bold text-brand-slate uppercase tracking-widest mb-8">Systémové akcie</h3>
            <div className="grid grid-cols-2 gap-3">
              <button onClick={() => navigate('/')} className="px-4 py-3 border border-brand-border text-[9px] font-black uppercase tracking-widest hover:border-brand-white transition-all">Nová analýza</button>
              <button className="px-4 py-3 border border-brand-border text-[9px] font-black uppercase tracking-widest opacity-50 cursor-not-allowed">API Dokumentácia</button>
              {user?.tier === 'enterprise' && (
                <>
                  <button onClick={() => navigate('/api-keys')} className="px-4 py-3 border border-brand-gold text-brand-gold text-[9px] font-black uppercase tracking-widest hover:bg-brand-gold/10 transition-all">API Kľúče</button>
                  <button className="px-4 py-3 border border-brand-border text-[9px] font-black uppercase tracking-widest">Webhooks</button>
                </>
              )}
            </div>
            <div className="mt-8 text-[9px] text-brand-slate uppercase tracking-widest leading-relaxed">
              V prípade potreby zvýšenia limitov kontaktujte enterprise support.
            </div>
          </div>
        </div>

        {/* Favorites */}
        <div className="mt-10 enterprise-card p-10">
          <div className="flex justify-between items-center mb-10">
            <h3 className="text-[10px] font-bold text-brand-slate uppercase tracking-widest">Sledované subjekty (Core Watchlist)</h3>
            <button className="text-[9px] font-black uppercase tracking-widest text-brand-gold hover:underline">Exportovať zoznam</button>
          </div>
          
          {favorites.length > 0 ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {favorites.map((favorite) => (
                <div
                  key={favorite.id}
                  className="border border-brand-border p-6 rounded hover:border-brand-gold transition-all group"
                >
                  <div className="flex items-start justify-between mb-4">
                    <div className="flex-1">
                      <div className="font-bold text-lg tracking-tight group-hover:text-brand-gold transition-colors">{favorite.company_name}</div>
                      <div className="text-[10px] text-brand-slate uppercase font-medium mt-1">
                        {favorite.company_identifier} • {favorite.country}
                      </div>
                    </div>
                    <button
                      onClick={async (e) => {
                        e.stopPropagation();
                        try {
                          const token = localStorage.getItem('access_token');
                          const response = await fetch(`${API_URL}/api/user/favorites/${favorite.id}`, {
                            method: 'DELETE',
                            headers: { 'Authorization': `Bearer ${token}` }
                          });
                          if (response.ok) setFavorites(favorites.filter(f => f.id !== favorite.id));
                        } catch (error) { console.error(error); }
                      }}
                      className="text-brand-slate hover:text-red-500 transition-colors"
                    >
                      <span className="text-xl">×</span>
                    </button>
                  </div>
                  
                  {favorite.risk_score !== null && (
                    <div className="flex items-center gap-2 mb-6">
                      <div className="flex-1 h-1 bg-slate-800 rounded-full overflow-hidden">
                        <div 
                          className="h-full" 
                          style={{ 
                            width: `${favorite.risk_score * 10}%`,
                            backgroundColor: favorite.risk_score >= 7 ? '#ef4444' : favorite.risk_score >= 4 ? '#f59e0b' : '#10b981'
                          }}
                        ></div>
                      </div>
                      <span className="text-[10px] font-bold text-brand-white">Risk: {favorite.risk_score.toFixed(1)}</span>
                    </div>
                  )}

                  <button
                    onClick={() => navigate(`/?q=${favorite.company_identifier}`)}
                    className="w-full border border-brand-border py-2 text-[9px] font-black uppercase tracking-widest hover:bg-brand-white hover:text-brand-navy transition-all"
                  >
                    Otvoriť Report
                  </button>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-20 border border-brand-border border-dashed rounded">
               <p className="text-xs text-brand-slate uppercase tracking-widest">Váš Watchlist je prázdny. Začnite novú analýzu.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default Dashboard;

