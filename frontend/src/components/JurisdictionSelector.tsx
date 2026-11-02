import React, { useEffect, useState } from 'react';
import { Globe, ChevronDown, Check } from 'lucide-react';
import { useAppContext } from '../context/AppContext';
import { useAuth } from '../auth/AuthContext';
import { useToast } from '../context/ToastContext';
import { apiFetch, tax } from '../api/v1';

const JurisdictionSelector: React.FC = () => {
  const { currentJurisdiction, setCurrentJurisdiction, jurisdictions, backendOnline } = useAppContext();
  const { refreshUser } = useAuth();
  const { addToast } = useToast();
  const [isOpen, setIsOpen] = useState(false);
  const [availableJurisdictions, setAvailableJurisdictions] = useState<any[]>(jurisdictions);

  useEffect(() => {
    const fetchJurisdictions = async () => {
      try {
        const response = await apiFetch('/tax/jurisdictions');
        if (response.ok) {
          const data = await response.json();
          setAvailableJurisdictions(data);
        }
      } catch (err) {
        console.error('Failed to fetch jurisdictions', err);
      }
    };

    if (backendOnline && availableJurisdictions.length === 0) {
      fetchJurisdictions();
    }
  }, [backendOnline, availableJurisdictions.length]);

  const selected = availableJurisdictions.find(j => j.code === currentJurisdiction) || {
    code: currentJurisdiction,
    name: 'Select Country',
    currency_symbol: '$'
  };

  return (
    <div className="relative">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-3 px-5 py-2.5 border rounded-2xl transition-all shadow-sm hover:scale-[1.02] active:scale-95"
        style={{ background: 'var(--surface)', borderColor: 'var(--border)' }}
      >
        <Globe className="w-4 h-4 text-brand-green-500" />
        <span className="text-sm font-bold truncate max-w-[120px]" style={{ color: 'var(--text)' }}>
          {selected.name}
        </span>
        <div className="w-px h-4 mx-1" style={{ background: 'var(--border)' }} />
        <span className="text-[10px] font-black uppercase tracking-widest opacity-40" style={{ color: 'var(--text)' }}>
          {selected.code}
        </span>
        <ChevronDown className={`w-4 h-4 opacity-40 transition-transform ${isOpen ? 'rotate-180' : ''}`} style={{ color: 'var(--text)' }} />
      </button>

      {isOpen && (
        <>
          <div
            className="fixed inset-0 z-10"
            onClick={() => setIsOpen(false)}
          />
          <div className="absolute right-0 mt-3 w-72 border rounded-[2rem] shadow-2xl z-20 overflow-hidden animate-in fade-in zoom-in-95 duration-200"
            style={{ background: 'var(--surface)', borderColor: 'var(--border)' }}>

            <div className="px-6 py-4 border-b" style={{ background: 'var(--bg2)', borderColor: 'var(--border)' }}>
              <p className="text-[10px] font-black uppercase tracking-[2px] opacity-40" style={{ color: 'var(--text)' }}>Select Jurisdiction</p>
            </div>

            <div className="p-3 max-h-96 overflow-y-auto custom-scrollbar">
              {availableJurisdictions.map((j) => (
                <button
                  key={j.code}
                  onClick={async () => {
                    try {
                      const saved = await tax.setJurisdiction(j.code);
                      setCurrentJurisdiction(saved.jurisdiction_code);
                      await refreshUser();
                      setIsOpen(false);
                    } catch (err) {
                      addToast(
                        err instanceof Error ? err.message : 'Failed to save jurisdiction',
                        'error',
                      );
                    }
                  }}
                  className={`w-full flex items-center justify-between px-5 py-4 rounded-2xl text-left transition-all group ${currentJurisdiction === j.code
                      ? 'bg-brand-green-500/10'
                      : 'hover:bg-brand-green-500/5'
                    }`}
                >
                  <div className="flex flex-col gap-0.5">
                    <span className={`text-[13px] font-bold ${currentJurisdiction === j.code ? 'text-brand-green-500' : ''}`} style={currentJurisdiction !== j.code ? { color: 'var(--text)' } : undefined}>
                      {j.name}
                    </span>
                    <span className="text-[10px] font-bold opacity-40 uppercase tracking-widest" style={{ color: 'var(--text)' }}>
                      {j.tax_authority} · {j.currency}
                    </span>
                  </div>
                  {currentJurisdiction === j.code && (
                    <div className="w-6 h-6 bg-brand-green-500 rounded-full flex items-center justify-center text-brand-dark">
                      <Check className="w-4 h-4 stroke-[3px]" />
                    </div>
                  )}
                </button>
              ))}
            </div>
            <div className="p-4 border-t flex items-center justify-center gap-2" style={{ background: 'var(--bg2)', borderColor: 'var(--border)' }}>
              <Globe className="w-3 h-3 text-brand-green-500" />
              <p className="text-[9px] font-black uppercase tracking-widest opacity-40" style={{ color: 'var(--text)' }}>
                {availableJurisdictions.length} Global Regions Active
              </p>
            </div>
          </div>
        </>
      )}
    </div>
  );
};

export default JurisdictionSelector;
