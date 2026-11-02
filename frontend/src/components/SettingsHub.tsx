import React, { useEffect, useState } from 'react';
import { ChevronRight, LogOut } from 'lucide-react';
import { useAuth } from '../auth/AuthContext';
import { useToast } from '../context/ToastContext';
import { useTheme } from '../context/ThemeContext';
import { useAppContext } from '../context/AppContext';
import { useNavigate } from 'react-router-dom';
import { cn } from '../utils/cn';
import { TwoFactorPanel } from './TwoFactorPanel';
import { useI18n, Locale } from '../i18n/I18nContext';
import { tax } from '../api/v1';
import { currencyLabelForJurisdiction } from '../utils/currencyLabels';

type Tab = 'account' | 'tax' | 'subscription';

function SettingRow({ label, description, value, onClick, danger = false }: {
  label: string; description?: string; value?: React.ReactNode;
  onClick?: () => void; danger?: boolean;
}) {
  return (
    <div
      onClick={onClick}
      className={cn('flex items-center justify-between px-5 py-4 border-b last:border-b-0 transition-colors', onClick && 'cursor-pointer hover:bg-[var(--bg2)]')}
      style={{ borderColor: 'var(--border)' }}
    >
      <div className="flex-1 min-w-0 mr-6">
        <p className="text-sm font-semibold" style={{ color: danger ? 'var(--red)' : 'var(--text)' }}>{label}</p>
        {description && <p className="text-xs mt-1 leading-relaxed" style={{ color: 'var(--text3)' }}>{description}</p>}
      </div>
      {value !== undefined && (
        <div className="flex items-center gap-1.5 shrink-0">
          <span className="text-sm font-medium" style={{ color: 'var(--text2)' }}>{value}</span>
          {onClick && <ChevronRight size={15} style={{ color: 'var(--text3)' }} />}
        </div>
      )}
    </div>
  );
}

function SettingToggle({ label, description, enabled, onToggle, comingSoon = false }: {
  label: string; description?: string; enabled: boolean; onToggle: () => void; comingSoon?: boolean;
}) {
  return (
    <div className="flex items-center justify-between px-5 py-4 border-b last:border-b-0" style={{ borderColor: 'var(--border)' }}>
      <div className="flex-1 min-w-0 mr-6">
        <p className="text-sm font-semibold" style={{ color: 'var(--text)' }}>{label}</p>
        {description && <p className="text-xs mt-1 leading-relaxed" style={{ color: 'var(--text3)' }}>{description}</p>}
      </div>
      <div className="flex items-center gap-3 shrink-0">
        {comingSoon && (
          <span className="text-[9px] font-black uppercase tracking-widest px-2 py-0.5 rounded-full" style={{ background: 'var(--accent-dim)', color: 'var(--accent)' }}>
            Soon
          </span>
        )}
        <button
          onClick={comingSoon ? undefined : onToggle}
          className={cn('relative w-11 h-6 rounded-full transition-all duration-200', comingSoon && 'opacity-40 cursor-not-allowed')}
          style={{ background: enabled ? 'var(--accent)' : 'var(--border2)' }}
        >
          <span className={cn('absolute top-0.5 left-0.5 w-5 h-5 rounded-full bg-white shadow-sm transition-transform duration-200', enabled ? 'translate-x-5' : 'translate-x-0')} />
        </button>
      </div>
    </div>
  );
}

function Card({ children }: { children: React.ReactNode }) {
  return (
    <div className="rounded-2xl border overflow-hidden" style={{ background: 'var(--surface)', borderColor: 'var(--border)' }}>
      {children}
    </div>
  );
}

function AccountTab() {
  const { user, logout, refreshUser } = useAuth();
  const { addToast } = useToast();
  const { theme, toggleTheme } = useTheme();
  const { locale, setLocale, t } = useI18n();
  const { setCurrentJurisdiction } = useAppContext();
  const navigate = useNavigate();
  const [showDelete, setShowDelete] = useState(false);
  const [deleteInput, setDeleteInput] = useState('');
  const [showLangSelector, setShowLangSelector] = useState(false);
  const [showJurisdictionSelector, setShowJurisdictionSelector] = useState(false);
  const [jurisdictions, setJurisdictions] = useState<{ code: string; name: string }[]>([]);
  const [jurisdictionCode, setJurisdictionCode] = useState(user?.jurisdiction_code || 'BR');
  const [jurisdictionName, setJurisdictionName] = useState(user?.jurisdiction_name || 'Brazil');

  useEffect(() => {
    setJurisdictionCode(user?.jurisdiction_code || 'BR');
    setJurisdictionName(user?.jurisdiction_name || 'Brazil');
  }, [user?.jurisdiction_code, user?.jurisdiction_name]);

  useEffect(() => {
    tax.getJurisdictions().then((list) => {
      setJurisdictions(list as { code: string; name: string }[]);
    }).catch(() => undefined);
  }, []);

  const languages: { code: Locale; name: string }[] = [
    { code: 'en', name: 'English' },
    { code: 'pt', name: 'Português' },
    { code: 'es', name: 'Español' },
  ];

  const currentLang = languages.find(l => l.code === locale) || languages[0];

  const handleLangSelect = (code: Locale) => {
    setLocale(code);
    setShowLangSelector(false);
  };

  const handleJurisdictionSelect = async (code: string) => {
    try {
      const saved = await tax.setJurisdiction(code);
      setJurisdictionCode(saved.jurisdiction_code);
      setJurisdictionName(saved.jurisdiction_name);
      setCurrentJurisdiction(saved.jurisdiction_code);
      setShowJurisdictionSelector(false);
      await refreshUser();
      addToast(`Tax jurisdiction saved: ${saved.jurisdiction_name}`, 'success');
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to save tax jurisdiction';
      addToast(message, 'error');
      console.error('Failed to update jurisdiction', err);
    }
  };

  const baseCurrencyLabel = currencyLabelForJurisdiction(jurisdictionCode);

  return (
    <div className="space-y-4">
      <Card>
        <SettingRow label={t('settings.account.email')} description={t('settings.account.emailSocialDesc')} value={user?.email} />
        <SettingRow label={t('settings.account.theme')} value={theme === 'dark' ? t('settings.account.themeDark') : t('settings.account.themeLight')} onClick={toggleTheme} />
      </Card>
      <Card>
        <SettingRow 
          label={t('settings.account.language')} 
          value={currentLang.name} 
          onClick={() => setShowLangSelector(!showLangSelector)} 
        />
        {showLangSelector && (
          <div className="px-5 py-2 space-y-1 bg-[var(--bg2)] border-t" style={{ borderColor: 'var(--border)' }}>
            {languages.map((lang) => (
              <button
                key={lang.code}
                onClick={() => handleLangSelect(lang.code)}
                className={cn(
                  "w-full flex items-center justify-between px-3 py-2.5 rounded-xl text-sm font-medium transition-all",
                  locale === lang.code ? "bg-[var(--accent-dim)] text-[var(--accent)]" : "hover:bg-[var(--border)] text-[var(--text2)]"
                )}
              >
                {lang.name}
                {locale === lang.code && <div className="w-1.5 h-1.5 rounded-full bg-[var(--accent)] shadow-[0_0_8px_var(--accent)]" />}
              </button>
            ))}
          </div>
        )}
        <SettingRow
          label={t('settings.account.jurisdiction')}
          value={jurisdictionName}
          onClick={() => {
            setShowJurisdictionSelector(!showJurisdictionSelector);
            setShowLangSelector(false);
          }}
        />
        {showJurisdictionSelector && (
          <div className="px-5 py-2 space-y-1 bg-[var(--bg2)] border-t max-h-64 overflow-y-auto custom-scrollbar" style={{ borderColor: 'var(--border)' }}>
            {jurisdictions.map((j) => (
              <button
                key={j.code}
                onClick={() => handleJurisdictionSelect(j.code)}
                className={cn(
                  'w-full flex items-center justify-between px-3 py-2.5 rounded-xl text-sm font-medium transition-all',
                  jurisdictionCode === j.code
                    ? 'bg-[var(--accent-dim)] text-[var(--accent)]'
                    : 'hover:bg-[var(--border)] text-[var(--text2)]'
                )}
              >
                {j.name}
                {jurisdictionCode === j.code && (
                  <div className="w-1.5 h-1.5 rounded-full bg-[var(--accent)] shadow-[0_0_8px_var(--accent)]" />
                )}
              </button>
            ))}
          </div>
        )}
        <SettingRow label={t('settings.account.currency')} value={baseCurrencyLabel} onClick={() => {}} />
      </Card>
      <Card>
        <TwoFactorPanel />
        <SettingToggle label={t('settings.account.support')} description={t('settings.account.supportDesc')} enabled={false} onToggle={() => {}} comingSoon />
        <SettingToggle label={t('settings.account.pro')} description={t('settings.account.proDesc')} enabled={false} onToggle={() => {}} comingSoon />
      </Card>
      <Card>
        {!showDelete ? (
          <div className="flex items-center justify-between px-5 py-4">
            <div>
              <p className="text-sm font-semibold" style={{ color: 'var(--red)' }}>{t('settings.account.delete')}</p>
              <p className="text-xs mt-1 leading-relaxed" style={{ color: 'var(--text3)' }}>{t('settings.account.deleteDesc')}</p>
            </div>
            <button onClick={() => setShowDelete(true)} className="ml-4 shrink-0 px-4 py-2 rounded-xl text-sm font-bold text-white transition-colors" style={{ background: 'var(--red)' }}>
              {t('settings.account.delete')}
            </button>
          </div>
        ) : (
          <div className="px-5 py-5 space-y-3">
            <p className="text-sm font-bold" style={{ color: 'var(--red)' }}>⚠️ Type DELETE to confirm permanent deletion</p>
            <input type="text" value={deleteInput} onChange={(e) => setDeleteInput(e.target.value)} placeholder='Type "DELETE"'
              className="w-full px-4 py-2.5 rounded-xl border text-sm font-medium outline-none transition-colors"
              style={{ background: 'var(--bg2)', borderColor: 'var(--border)', color: 'var(--text)' }} />
            <div className="flex gap-3">
              <button disabled={deleteInput !== 'DELETE'} className="px-5 py-2 text-white text-sm font-bold rounded-xl transition-colors disabled:opacity-40 disabled:cursor-not-allowed" style={{ background: 'var(--red)' }}>
                {t('common.delete')}
              </button>
              <button onClick={() => { setShowDelete(false); setDeleteInput(''); }} className="px-5 py-2 text-sm font-bold rounded-xl border transition-colors" style={{ borderColor: 'var(--border)', color: 'var(--text)' }}>
                {t('common.cancel')}
              </button>
            </div>
          </div>
        )}
      </Card>
      <button onClick={() => logout().then(() => navigate('/'))} className="flex items-center gap-2 text-sm font-bold transition-colors px-1" style={{ color: 'var(--red)' }}>
        <LogOut size={15} /> {t('settings.account.signOut')}
      </button>
    </div>
  );
}

function TaxTab() {
  const [tData, setTData] = useState({ liquidStaking: false, wrapping: false, liquidLending: false, liquidityPool: false, stakingRewards: false, receivesAsIncome: false });
  const { t } = useI18n();
  const tog = (k: keyof typeof tData) => setTData(p => ({ ...p, [k]: !p[k] }));
  return (
    <div className="space-y-4">
      <Card>
        <SettingRow label={t('settings.tax.basis')} description={t('settings.tax.basisDesc')} value={<span style={{ color: 'var(--accent)' }}>FIFO</span>} />
        <SettingRow label={t('settings.tax.tracking')} value="Universal" onClick={() => {}} />
        <SettingRow label={t('settings.tax.year')} value="January 1st to December 31st" onClick={() => {}} />
      </Card>
      <Card>
        <SettingToggle label={t('settings.tax.staking')} enabled={tData.liquidStaking} onToggle={() => tog('liquidStaking')} comingSoon />
        <SettingToggle label={t('settings.tax.wrapping')} enabled={tData.wrapping} onToggle={() => tog('wrapping')} comingSoon />
        <SettingToggle label={t('settings.tax.lending')} enabled={tData.liquidLending} onToggle={() => tog('liquidLending')} comingSoon />
        <SettingToggle label={t('settings.tax.liquidity')} enabled={tData.liquidityPool} onToggle={() => tog('liquidityPool')} comingSoon />
        <SettingToggle label={t('settings.tax.rewards')} enabled={tData.stakingRewards} onToggle={() => tog('stakingRewards')} comingSoon />
        <SettingToggle label={t('settings.tax.income')} enabled={tData.receivesAsIncome} onToggle={() => tog('receivesAsIncome')} comingSoon />
      </Card>
    </div>
  );
}

function SubscriptionTab() {
  const { t } = useI18n();
  return (
    <div className="space-y-4">
      <Card>
        <SettingRow label={t('settings.sub.plan')} value="Free" />
        <SettingRow label={t('settings.sub.txs')} value="25 / 25 used" />
        <SettingRow label={t('settings.sub.reports')} description={t('settings.sub.reportsDesc')} value={t('settings.sub.notAvailable')} />
      </Card>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {[
          { name: 'Starter', price: '$19.99', txs: '250 transactions', popular: true },
          { name: 'Trader',  price: '$49.99', txs: '1,500 transactions', popular: false },
          { name: 'Whale',   price: '$99.99', txs: 'Unlimited', popular: false },
        ].map(plan => (
          <div key={plan.name}
            className={cn('relative p-6 rounded-2xl border transition-all hover:-translate-y-0.5', plan.popular && 'ring-1')}
            style={{ background: 'var(--surface)', borderColor: plan.popular ? 'var(--accent)' : 'var(--border)', boxShadow: plan.popular ? '0 0 0 1px var(--accent)' : undefined }}>
            {plan.popular && (
              <div className="absolute -top-3 left-1/2 -translate-x-1/2 text-[9px] font-black uppercase px-3 py-1 rounded-full text-brand-dark" style={{ background: 'var(--accent)' }}>
                Popular
              </div>
            )}
            <p className="text-[10px] font-black uppercase tracking-widest mb-1" style={{ color: 'var(--text3)' }}>{plan.name}</p>
            <p className="text-2xl font-black tracking-tight mb-1" style={{ color: 'var(--text)' }}>
              {plan.price}<span className="text-xs font-medium ml-1" style={{ color: 'var(--text3)' }}>/year</span>
            </p>
            <p className="text-xs mb-5" style={{ color: 'var(--text2)' }}>{plan.txs}</p>
            <button
              className="w-full py-2.5 rounded-xl text-sm font-bold transition-all"
              style={plan.popular ? { background: 'var(--accent)', color: 'var(--brand-dark, #07090d)' } : { background: 'var(--bg2)', border: '1px solid var(--border)', color: 'var(--text)' }}>
              {t('settings.sub.choose')} {plan.name}
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}

export function SettingsHub({ setActiveTab }: { setActiveTab?: (tab: string) => void }) {
  const [tab, setTab] = useState<Tab>('account');
  const { t } = useI18n();
  const tabs: { id: Tab; label: string }[] = [
    { id: 'account', label: t('settings.tabs.account') },
    { id: 'tax', label: t('settings.tabs.tax') },
    { id: 'subscription', label: t('settings.tabs.subscription') },
  ];

  const handleTabClick = (id: Tab) => {
    if (id === 'subscription' && setActiveTab) {
      setActiveTab('billing');
    } else {
      setTab(id);
    }
  };

  return (
    <div className="max-w-2xl mx-auto py-4 space-y-6 animate-in fade-in duration-300">
      <h1 className="text-3xl font-syne font-bold tracking-tight" style={{ color: 'var(--text)' }}>{t('settings.title')}</h1>

      <div className="flex border-b" style={{ borderColor: 'var(--border)' }}>
        {tabs.map(t => (
          <button key={t.id} onClick={() => handleTabClick(t.id)}
            className={cn('px-4 py-3 text-sm font-semibold transition-all border-b-2 -mb-px', tab === t.id ? 'border-[var(--accent)]' : 'border-transparent hover:text-[var(--text)]')}
            style={{ color: tab === t.id ? 'var(--accent)' : 'var(--text3)' }}>
            {t.label}
          </button>
        ))}
      </div>

      {tab === 'account'      && <AccountTab />}
      {tab === 'tax'          && <TaxTab />}
      {tab === 'subscription' && <SubscriptionTab />}
    </div>
  );
}
