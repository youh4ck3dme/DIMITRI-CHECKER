import React, { useState, useEffect } from 'react';
import { Brain, Sparkles, Loader2, AlertCircle } from 'lucide-react';
import { API_URL } from '../config/api';

export default function AiNarrative({ companyData, riskScore, token }) {
  const [narrative, setNarrative] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (companyData && token) {
      fetchNarrative();
    }
  }, [companyData, token]);

  const fetchNarrative = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(`${API_URL}/api/ai/narrative`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          company_data: companyData,
          risk_score: riskScore
        })
      });

      if (!response.ok) throw new Error('AI analysis offline');
      const result = await response.json();
      setNarrative(result.narrative);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  if (!token) return (
    <div className="bg-slate-800/50 border border-brand-border rounded p-4 text-xs text-brand-slate text-center">
      Prihláste sa pre AI Audit a strategické zhrnutie rizika firiem.
    </div>
  );

  return (
    <div className="enterprise-card p-6 border-brand-gold/20">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <Brain className="text-brand-gold w-5 h-5" />
          <h3 className="font-bold text-brand-white uppercase tracking-wider text-xs">Strategický AI Audit</h3>
        </div>
        {loading && <Loader2 className="w-4 h-4 animate-spin text-brand-gold" />}
      </div>

      {loading ? (
        <div className="space-y-2 animate-pulse">
          <div className="h-3 bg-slate-800 rounded w-full"></div>
          <div className="h-3 bg-slate-800 rounded w-5/6"></div>
          <div className="h-3 bg-slate-800 rounded w-4/6"></div>
        </div>
      ) : error ? (
        <div className="text-xs text-red-400 flex items-center gap-2">
          <AlertCircle size={14} />
          {error}
        </div>
      ) : (
        <div className="text-sm text-brand-white/90 leading-relaxed font-light italic">
          "{narrative || 'Analýza subjektu sa pripravuje...'}"
        </div>
      )}

      <div className="mt-4 pt-4 border-t border-brand-border flex items-center justify-between">
        <span className="text-[10px] text-brand-slate uppercase font-bold tracking-widest">Powered by V4-Intelligence Model</span>
        <Sparkles size={12} className="text-brand-gold" />
      </div>
    </div>
  );
}
