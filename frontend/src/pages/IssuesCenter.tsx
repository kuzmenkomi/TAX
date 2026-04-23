import { useI18n } from '../i18n/I18nContext';
import { useAppContext } from '../context/AppContext';
import { DataQualityCenter } from '../components/DataQualityCenter';

export function IssuesCenter() {
  const { t } = useI18n();

  return (
    <div className="space-y-6">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-syne font-bold tracking-tight" style={{ color: 'var(--text)' }}>
            {t('issues.title') || 'Data Quality & Compliance'}
          </h1>
          <p className="text-[13px] mt-1" style={{ color: 'var(--text3)' }}>
            Audit your transaction history for accuracy and missing tax data.
          </p>
        </div>
      </div>

      <DataQualityCenter />
    </div>
  );
}
