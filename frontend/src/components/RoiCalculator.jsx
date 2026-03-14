import React, { useState } from 'react';
import { Calculator, TrendingUp, Clock, AlertCircle } from 'lucide-react';

export default function RoiCalculator() {
  const [employees, setEmployees] = useState(5);
  const [checksPerMonth, setChecksPerMonth] = useState(20);
  const [hourlyRate, setHourlyRate] = useState(25);

  const manualTimePerCheck = 2.5; // hours
  const automatedTimePerCheck = 0.15; // hours (9 mins)
  
  const monthlyManualCost = employees * checksPerMonth * manualTimePerCheck * hourlyRate;
  const monthlyAutomatedCost = employees * checksPerMonth * automatedTimePerCheck * hourlyRate;
  const savings = monthlyManualCost - monthlyAutomatedCost;

  return (
    <div className="enterprise-card p-8 max-w-4xl mx-auto my-12">
      <div className="flex items-center gap-3 mb-8">
        <Calculator className="text-brand-gold w-6 h-6" />
        <h2 className="text-2xl font-bold tracking-tight">Enterprise ROI Kalkulačka</h2>
      </div>

      <div className="grid md:grid-cols-2 gap-12">
        <div className="space-y-6">
          <div>
            <label className="block text-sm font-medium text-brand-slate mb-2">
              Počet analytikov / nákupcov
            </label>
            <input 
              type="range" min="1" max="50" value={employees}
              onChange={(e) => setEmployees(parseInt(e.target.value))}
              className="w-full accent-brand-gold"
            />
            <div className="flex justify-between text-xs mt-1">
              <span>{employees} zamestnancov</span>
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-brand-slate mb-2">
              Počet previerok mesačne (na osobu)
            </label>
            <input 
              type="range" min="1" max="100" value={checksPerMonth}
              onChange={(e) => setChecksPerMonth(parseInt(e.target.value))}
              className="w-full accent-brand-gold"
            />
            <div className="flex justify-between text-xs mt-1">
              <span>{checksPerMonth} previerok</span>
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-brand-slate mb-2">
              Priemerná hodinová mzda (€)
            </label>
            <input 
              type="number" value={hourlyRate}
              onChange={(e) => setHourlyRate(parseInt(e.target.value))}
              className="w-full bg-slate-800 border border-brand-border rounded px-3 py-2 text-white focus:outline-none focus:border-brand-gold"
            />
          </div>
        </div>

        <div className="bg-brand-navy/50 p-6 border border-brand-gold/20 rounded flex flex-col justify-center">
          <div className="text-sm uppercase tracking-widest text-brand-slate mb-2">Mesačná úspora nákladov</div>
          <div className="text-5xl font-bold text-brand-gold mb-4 leading-none">
            {new Intl.NumberFormat('sk-SK', { style: 'currency', currency: 'EUR' }).format(savings)}
          </div>
          
          <div className="space-y-3 mt-4 text-sm text-brand-white/80">
            <div className="flex items-center gap-2">
              <Clock className="w-4 h-4 text-brand-slate" />
              <span>Ušetrený čas: <strong>{Math.round((manualTimePerCheck - automatedTimePerCheck) * checksPerMonth * employees)} hodín</strong> / mesiac</span>
            </div>
            <div className="flex items-center gap-2">
              <TrendingUp className="w-4 h-4 text-brand-slate" />
              <span>Zvýšenie efektivity o <strong>94%</strong></span>
            </div>
            <div className="flex items-center gap-2">
              <AlertCircle className="w-4 h-4 text-brand-slate" />
              <span>Zníženie rizika ľudskej chyby pri compliance</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
