import { useState } from 'react';
import { 
  FileText, 
  Download, 
  FileSpreadsheet, 
  FileJson, 
  ShieldCheck, 
  ArrowRight,
  Loader2,
  CheckCircle2,
  AlertCircle
} from 'lucide-react';
import { useAppContext } from '../context/AppContext';
import { getApiUrl } from '../api/v1';

export function ReportDownloader() {
  const { analyzeResult, backendOnline } = useAppContext();
  const [downloading, setDownloading] = useState<string | null>(null);

  const reports = [
    {
      id: 'pdf_official',
      title: 'Official Tax Report',
      description: 'Comprehensive PDF for tax authorities with full audit trail and cost-basis matching.',
      icon: <FileText size={20} />,
      format: 'PDF',
      endpoint: '/v1/accounting/reports/pdf',
      color: 'from-brand-green-500/10 to-brand-green-500/5',
      accent: 'text-brand-green-500',
      badge: 'Certified'
    },
    {
      id: 'csv_turbotax',
      title: 'TurboTax / TaxAct',
      description: 'Standard CSV format compatible with major tax software for automated filing.',
      icon: <FileSpreadsheet size={20} />,
      format: 'CSV',
      endpoint: '/v1/accounting/reports/turbotax',
      color: 'from-blue-500/10 to-blue-500/5',
      accent: 'text-blue-500',
      badge: 'Popular'
    },
    {
      id: 'csv_detailed',
      title: 'Detailed Transaction Ledger',
      description: 'Full list of taxable events with lot matching details for deep audits.',
      icon: <FileJson size={20} />,
      format: 'CSV',
      endpoint: '/v1/accounting/reports/detailed',
      color: 'from-orange-500/10 to-orange-500/5',
      accent: 'text-orange-500',
      badge: 'Audit Ready'
    }
  ];

  const handleDownload = async (report: typeof reports[0]) => {
    if (!backendOnline) return;
    setDownloading(report.id);
    
    try {
      // In a real app, we'd use a token for auth
      const url = getApiUrl(report.endpoint);
      const response = await fetch(url, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          // Authorization: `Bearer ${token}` 
        },
        body: JSON.stringify({
          jurisdiction: 'BR', // Default or from context
          year: 2024
        })
      });

      if (!response.ok) throw new Error('Download failed');

      const blob = await response.blob();
      const downloadUrl = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = downloadUrl;
      a.download = `${report.id}_${new Date().getFullYear()}.` + (report.format.toLowerCase());
      document.body.appendChild(a);
      a.click();
      a.remove();
    } catch (error) {
      console.error('Download error:', error);
      alert('Failed to generate report. Please try again.');
    } finally {
      setDownloading(null);
    }
  };

  if (!analyzeResult) {
    return (
      <div className="p-12 text-center border-2 border-dashed rounded-[3rem] opacity-40" style={{ borderColor: 'var(--border)' }}>
        <AlertCircle size={40} className="mx-auto mb-4" />
        <h3 className="text-lg font-syne font-bold" style={{ color: 'var(--text)' }}>No Analysis Data</h3>
        <p className="text-[13px] max-w-xs mx-auto mt-2" style={{ color: 'var(--text3)' }}>
          Please complete your portfolio analysis first to generate tax reports.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {reports.map((report) => (
          <div 
            key={report.id}
            className={`p-8 rounded-[2.5rem] border bg-gradient-to-br flex flex-col justify-between transition-all group hover:-translate-y-1 hover:shadow-xl ${report.color}`}
            style={{ borderColor: 'var(--border)' }}
          >
            <div>
              <div className="flex items-center justify-between mb-6">
                <div className={`p-3 rounded-2xl bg-white/10 ${report.accent}`}>
                  {report.icon}
                </div>
                <span className={`text-[10px] font-black uppercase tracking-widest px-2.5 py-1 rounded-full bg-white/20 ${report.accent}`}>
                  {report.badge}
                </span>
              </div>
              <h3 className="text-lg font-syne font-bold mb-2" style={{ color: 'var(--text)' }}>{report.title}</h3>
              <p className="text-[12px] leading-relaxed opacity-70 mb-8" style={{ color: 'var(--text3)' }}>{report.description}</p>
            </div>
            
            <button
              onClick={() => handleDownload(report)}
              disabled={!!downloading}
              className={`w-full py-4 rounded-2xl text-[12px] font-black uppercase tracking-widest flex items-center justify-center gap-3 transition-all ${
                downloading === report.id ? 'bg-white/10 opacity-50' : 'bg-brand-dark text-white hover:scale-105 active:scale-95'
              }`}
            >
              {downloading === report.id ? (
                <Loader2 size={16} className="animate-spin" />
              ) : (
                <Download size={16} />
              )}
              {downloading === report.id ? 'Generating...' : `Download ${report.format}`}
            </button>
          </div>
        ))}
      </div>

      <div className="p-8 rounded-[2.5rem] bg-brand-green-500/5 border border-brand-green-500/20 flex items-center gap-6">
        <div className="w-12 h-12 bg-brand-green-500/20 rounded-full flex items-center justify-center text-brand-green-500 flex-shrink-0">
          <ShieldCheck size={24} />
        </div>
        <div className="flex-1">
          <h4 className="text-[14px] font-bold" style={{ color: 'var(--text)' }}>Professional Compliance & Audits</h4>
          <p className="text-[12px] opacity-60" style={{ color: 'var(--text3)' }}>
            All reports are generated using the TaxFlow Institutional Engine, ensuring 100% mathematical precision and 
            compliance with jurisdictional requirements.
          </p>
        </div>
        <button className="text-[12px] font-black flex items-center gap-2 group" style={{ color: 'var(--text)' }}>
          Compliance Notes <ArrowRight size={14} className="group-hover:translate-x-1 transition-transform" />
        </button>
      </div>
    </div>
  );
}
