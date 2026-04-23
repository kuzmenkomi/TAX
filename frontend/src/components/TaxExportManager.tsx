import React, { useState, useEffect } from 'react';
import { apiFetch } from '../api/client';
import { FileText, Download, Loader2, AlertCircle, CheckCircle2 } from 'lucide-react';

interface ExportFormat {
  format: string;
  label: string;
  description: string;
  icon: string;
}

interface ExportPreview {
  format: string;
  filename: string;
  preview: string;
  size_bytes: number;
}

interface TaxExportManagerProps {
  jurisdictionCode: string;
  taxYear: number;
  taxProfileId?: string;
}

const TaxExportManager: React.FC<TaxExportManagerProps> = ({ jurisdictionCode, taxYear, taxProfileId }) => {
  const [supportedFormats, setSupportedFormats] = useState<ExportFormat[]>([]);
  const [selectedFormat, setSelectedFormat] = useState<string>('csv');
  const [preview, setPreview] = useState<ExportPreview | null>(null);
  const [loading, setLoading] = useState(false);
  const [downloading, setDownloading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [includeDetails, setIncludeDetails] = useState(true);
  const [includeSummary, setIncludeSummary] = useState(true);

  const formatDefinitions: { [key: string]: ExportFormat } = {
    csv: { format: 'csv', label: 'CSV Summary', description: 'Universal spreadsheet format for Excel/Google.', icon: '📊' },
    ods: { format: 'ods', label: 'ODS Document', description: 'Open format for LibreOffice and Calc.', icon: '📑' },
    pdf: { format: 'pdf', label: 'PDF Audit', description: 'Official report for tax authorities.', icon: '📄' },
    xml: { format: 'xml', label: 'XML Stream', description: 'Structured data for automated filing.', icon: '🔗' },
  };

  useEffect(() => {
    const fetchFormats = async () => {
      try {
        const response = await apiFetch('/tax/export/formats');
        if (!response.ok) throw new Error('Failed to load formats');
        const data = await response.json();
        const formats = data.formats.map((fmt: string) => formatDefinitions[fmt] || { format: fmt, label: fmt.toUpperCase(), description: '', icon: '📄' });
        setSupportedFormats(formats);
      } catch { setError('Failed to load export formats'); }
    };
    fetchFormats();
  }, []);

  useEffect(() => {
    const loadPreview = async () => {
      setLoading(true); setError(null);
      try {
        const response = await apiFetch(`/tax/export/${jurisdictionCode}/${taxYear}/preview?format=${selectedFormat}`, {
          method: 'POST', headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ jurisdiction_code: jurisdictionCode, tax_year: taxYear, format: selectedFormat, include_summary: includeSummary, include_details: includeDetails, transactions: [] }),
        });
        if (!response.ok) { const data = await response.json().catch(() => ({ detail: 'Failed' })); throw new Error(data.detail); }
        setPreview(await response.json());
      } catch (err: any) { setError(err.message || 'Failed to load preview'); setPreview(null); }
      finally { setLoading(false); }
    };
    if (jurisdictionCode && taxYear) loadPreview();
  }, [selectedFormat, jurisdictionCode, taxYear, includeSummary, includeDetails]);

  const handleDownload = async () => {
    setDownloading(true); setError(null);
    try {
      const response = await apiFetch(`/tax/export/${jurisdictionCode}/${taxYear}?format=${selectedFormat}`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ jurisdiction_code: jurisdictionCode, tax_year: taxYear, format: selectedFormat, include_summary: includeSummary, include_details: includeDetails, transactions: [] }),
      });
      if (!response.ok) { const data = await response.json().catch(() => ({ detail: 'Failed' })); throw new Error(data.detail); }
      const blob = await response.blob();
      const cd = response.headers.get('content-disposition');
      const filename = cd?.split('filename=')[1]?.replace(/"/g, '') || `tax_export_${jurisdictionCode}_${taxYear}.${selectedFormat}`;
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a'); link.href = url; link.setAttribute('download', filename);
      document.body.appendChild(link); link.click(); link.parentNode?.removeChild(link); window.URL.revokeObjectURL(url);
    } catch (err: any) { setError(err.message || 'Download failed'); }
    finally { setDownloading(false); }
  };

  const currentFormat = formatDefinitions[selectedFormat];

  return (
    <div className="space-y-6 animate-in fade-in duration-500">

      {/* Header */}
      <div>
        <h1 className="text-2xl font-syne font-bold tracking-tight" style={{ color: 'var(--text)' }}>Export Engine</h1>
        <p className="text-[14px] mt-1" style={{ color: 'var(--text3)' }}>
          Finalize your {taxYear} report for {jurisdictionCode} by generating high-fidelity files.
        </p>
      </div>

      {/* Error Banner */}
      {error && (
        <div className="px-5 py-3 bg-danger/10 border border-danger/20 rounded-2xl flex items-center gap-3 animate-shake">
          <AlertCircle className="w-5 h-5 text-danger flex-shrink-0" />
          <p className="text-[13px] font-bold text-danger">{error}</p>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-6">
          
          {/* Format selection */}
          <div className="border rounded-[2.5rem] p-8 shadow-sm" style={{ background: 'var(--surface)', borderColor: 'var(--border)' }}>
            <h3 className="text-xs font-black uppercase tracking-widest mb-6" style={{ color: 'var(--text2)' }}>Archive Formats</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {supportedFormats.map((fmt) => (
                <button key={fmt.format} onClick={() => setSelectedFormat(fmt.format)}
                  className={`p-5 rounded-3xl border text-left transition-all hover:scale-[1.02] ${
                    selectedFormat === fmt.format
                      ? 'border-brand-green-500 bg-brand-green-500/10'
                      : 'hover:bg-brand-green-500/5'
                  }`}
                  style={selectedFormat !== fmt.format ? { background: 'var(--bg2)', borderColor: 'var(--border)' } : undefined}>
                  <div className="flex items-start gap-4">
                    <span className="text-3xl bg-surface p-2 rounded-2xl shadow-sm" style={{ background: 'var(--surface)' }}>{fmt.icon}</span>
                    <div className="flex-1">
                      <h4 className={`text-[13px] font-black tracking-tight ${selectedFormat === fmt.format ? 'text-brand-green-500' : ''}`} style={selectedFormat !== fmt.format ? { color: 'var(--text)' } : undefined}>{fmt.label}</h4>
                      <p className="text-[11px] mt-1 italic leading-relaxed" style={{ color: 'var(--text3)' }}>{fmt.description}</p>
                    </div>
                  </div>
                </button>
              ))}
            </div>
          </div>

          {/* Preview Section */}
          {preview && !loading && (
            <div className="border rounded-[2.5rem] p-8 shadow-sm" style={{ background: 'var(--surface)', borderColor: 'var(--border)' }}>
              <div className="flex items-center justify-between mb-6">
                <h3 className="text-xs font-black uppercase tracking-widest" style={{ color: 'var(--text2)' }}>Data Preview</h3>
                <div className="px-3 py-1 bg-[#6af0c8]/10 text-[#6af0c8] rounded-full text-[9px] font-black uppercase tracking-widest border border-[#6af0c8]/20">
                  Ready for generation
                </div>
              </div>
              
              <div className="border rounded-3xl p-6 space-y-6" style={{ background: 'var(--bg2)', borderColor: 'var(--border)' }}>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
                  <div>
                    <p className="text-[10px] font-black uppercase tracking-widest opacity-40 mb-1" style={{ color: 'var(--text)' }}>Registry Name</p>
                    <p className="text-[12px] font-mono font-bold break-all" style={{ color: 'var(--text)' }}>{preview.filename}</p>
                  </div>
                  <div>
                    <p className="text-[10px] font-black uppercase tracking-widest opacity-40 mb-1" style={{ color: 'var(--text)' }}>Runway Size</p>
                    <p className="text-[12px] font-bold" style={{ color: 'var(--accent)' }}>
                      {typeof preview.size_bytes === 'number' ? `${(preview.size_bytes / 1024).toFixed(2)} KB` : preview.size_bytes}
                    </p>
                  </div>
                </div>
                
                <div>
                  <p className="text-[10px] font-black uppercase tracking-widest opacity-40 mb-3" style={{ color: 'var(--text)' }}>Stream Metadata</p>
                  <pre className="p-5 rounded-2xl font-mono text-[11px] h-48 overflow-auto border shadow-inner" style={{ background: 'var(--surface)', borderColor: 'var(--border)', color: 'var(--text2)' }}>
                    {preview.preview}
                  </pre>
                </div>
              </div>
            </div>
          )}

          {loading && (
            <div className="border rounded-[2.5rem] p-20 flex flex-col items-center justify-center gap-4" style={{ background: 'var(--surface)', borderColor: 'var(--border)' }}>
              <Loader2 className="w-10 h-10 text-brand-green-500 animate-spin" />
              <p className="text-xs font-black uppercase tracking-widest opacity-40" style={{ color: 'var(--text)' }}>Constructing Preview</p>
            </div>
          )}
        </div>

        {/* Configuration Column */}
        <div className="space-y-6">
          <div className="border rounded-[2.5rem] p-8 shadow-sm" style={{ background: 'var(--surface)', borderColor: 'var(--border)' }}>
            <h3 className="text-sm font-black uppercase tracking-widest mb-8 underline decoration-brand-green-500/30 decoration-4 underline-offset-8" style={{ color: 'var(--text)' }}>Preferences</h3>
            
            <div className="space-y-5">
              {[
                { label: 'Include Tax Summary', checked: includeSummary, setter: setIncludeSummary },
                { label: 'Include Transaction Details', checked: includeDetails, setter: setIncludeDetails },
              ].map((opt) => (
                <label key={opt.label} className="flex items-center gap-4 cursor-pointer group">
                  <div className="relative inline-flex items-center">
                    <input type="checkbox" checked={opt.checked} onChange={(e) => opt.setter(e.target.checked)} className="sr-only peer" />
                    <div className="w-11 h-6 bg-border peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-brand-green-500"></div>
                  </div>
                  <span className="text-[13px] font-bold opacity-60 group-hover:opacity-100 transition-opacity" style={{ color: 'var(--text)' }}>{opt.label}</span>
                </label>
              ))}
            </div>

            <button onClick={handleDownload} disabled={downloading || !preview}
              className="w-full mt-10 py-5 bg-brand-green-500 text-brand-dark rounded-2xl text-[14px] font-black shadow-xl shadow-brand-green-500/20 hover:bg-brand-green-400 disabled:opacity-30 transform active:scale-95 transition-all flex items-center justify-center gap-3">
              {downloading ? <Loader2 className="w-5 h-5 animate-spin" /> : <Download className="w-5 h-5" />}
              {downloading ? 'STREAMING...' : `GENERATE ${selectedFormat.toUpperCase()}`}
            </button>
          </div>

          {/* Verification / Security Card */}
          <div className="border rounded-[2.5rem] p-8 space-y-6" style={{ background: 'var(--bg2)', borderColor: 'var(--border)' }}>
            <div className="w-12 h-12 bg-brand-green-500/10 rounded-2xl flex items-center justify-center text-brand-green-500">
              <CheckCircle2 size={24} />
            </div>
            <div>
              <h4 className="text-sm font-black mb-2" style={{ color: 'var(--text)' }}>Official Compliance</h4>
              <p className="text-[11px] leading-relaxed" style={{ color: 'var(--text3)' }}>
                Our exports are formatted according to current tax laws for {jurisdictionCode}. PDF reports include a detailed audit trail of every matched pair for total transparency.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default TaxExportManager;
