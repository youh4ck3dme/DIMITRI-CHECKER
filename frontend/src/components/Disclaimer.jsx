import React from 'react';
import { AlertTriangle } from 'lucide-react';

const Disclaimer = () => {
  return (
    <div className="bg-amber-50 border-l-4 border-amber-400 p-4 rounded-r-lg mt-6">
      <div className="flex items-start gap-3">
        <AlertTriangle className="text-amber-600 flex-shrink-0 mt-0.5" size={20} />
        <div className="text-sm text-amber-800">
            <p className="font-semibold mb-1">Dôležité upozornenie:</p>
            <p>
              Dáta zobrazené na portáli ILUMINATE SYSTEM sú agregované z verejných zdrojov
            (Obchodné registre, Finančné správy V4) automatizovaným spôsobom. ILUMINATE SYSTEM nevytvára tieto 
            dáta a nenesie zodpovednosť za ich aktuálnosť, správnosť či úplnosť. Informácie slúžia 
            výhradne na podporu rozhodovania (business intelligence) a nenahrádzajú oficiálne právne 
            úkony alebo úradné výpisy. Rizikové skóre je výsledkom štatistického modelu, nie obvinením 
            z trestnej činnosti.
          </p>
        </div>
      </div>
    </div>
  );
};

export default Disclaimer;

