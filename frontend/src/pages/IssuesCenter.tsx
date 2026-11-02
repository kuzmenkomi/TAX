import { useI18n } from '../i18n/I18nContext';
import { useAppContext } from '../context/AppContext';
import { DataQualityCenter } from '../components/DataQualityCenter';
import { Plus, ShieldAlert } from 'lucide-react';

export function IssuesCenter() {
  const { t } = useI18n();

  return (
    <div className="space-y-6">
      <DataQualityCenter />
    </div>
  );
}
