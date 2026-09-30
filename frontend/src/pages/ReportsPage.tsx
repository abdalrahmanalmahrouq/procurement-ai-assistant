import { useEffect, useState, type FormEvent } from 'react';
import { Download, FileBarChart2, Loader2, Plus, RefreshCw } from 'lucide-react';
import { streamChat } from '../services/chatService';
import { getReport, listReports, reportCsvUrl, reportPdfUrl, reportPdfDownloadUrl } from '../services/reportService';
import type { ChatEvent } from '../types/chat';
import type { Report, ReportSection, ReportSpec, ReportSummary } from '../types/reports';

const choices: { key: ReportSection; label: string }[] = [
  { key: 'spending_overview', label: 'Spending overview' },
  { key: 'order_statistics', label: 'Order statistics' },
  { key: 'top_suppliers', label: 'Top suppliers' },
  { key: 'department_spending', label: 'Department spending' },
  { key: 'department_quarterly', label: 'Departments by quarter' },
  { key: 'monthly_trends', label: 'Monthly trends' },
  { key: 'quarterly_trends', label: 'Quarterly trends' },
  { key: 'category_spending', label: 'Category spending' },
  { key: 'category_comparison', label: 'Category comparison' },
];

const initialSpec: ReportSpec = {
  report_focus: 'comprehensive', report_type: 'annual', year: 2014, quarter: null, department: null, acquisition_type: null, supplier: null,
  category: null, sections: choices.filter((choice) => choice.key !== 'category_comparison' && choice.key !== 'department_quarterly').map((choice) => choice.key), ranking_limit: 10,
  charts: ['supplier', 'department', 'monthly', 'quarterly', 'category'],
  tables: ['supplier', 'department', 'monthly', 'quarterly', 'category'],
  export_format: 'pdf_csv', custom_requirements: [],
};

const tableSections = ['spending_overview', 'order_statistics', 'top_suppliers', 'department_spending', 'department_quarterly', 'monthly_trends', 'quarterly_trends', 'category_spending', 'category_comparison', 'custom_analysis'];

export function ReportsPage() {
  const [spec, setSpec] = useState<ReportSpec>(initialSpec);
  const [custom, setCustom] = useState('');
  const [reports, setReports] = useState<ReportSummary[]>([]);
  const [selected, setSelected] = useState<Report | null>(null);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [progress, setProgress] = useState('');
  const [error, setError] = useState('');

  async function refresh() {
    try {
      setReports(await listReports());
      setError('');
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'Could not load reports.');
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    let mounted = true;
    listReports().then((items) => {
      if (mounted) setReports(items);
    }).catch((cause: unknown) => {
      if (mounted) setError(cause instanceof Error ? cause.message : 'Could not load reports.');
    }).finally(() => {
      if (mounted) setLoading(false);
    });
    const id = new URLSearchParams(window.location.search).get('open');
    if (id) {
      getReport(id).then((report) => {
        if (mounted) setSelected(report);
      }).catch((cause: unknown) => {
        if (mounted) setError(cause instanceof Error ? cause.message : 'Could not open report.');
      });
    }
    return () => { mounted = false; };
  }, []);

  async function openReport(id: string) {
    try {
      setSelected(await getReport(id));
      setError('');
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'Could not open report.');
    }
  }

  function toggleSection(section: ReportSection) {
    setSpec((current) => ({ ...current, sections: current.sections.includes(section) ? current.sections.filter((item) => item !== section) : [...current.sections, section] }));
  }

  async function createReport(event: FormEvent) {
    event.preventDefault();
    if (generating || !spec.sections.length) return;
    const reportSpec: ReportSpec = { ...spec, department: spec.department?.trim() || null, supplier: spec.supplier?.trim() || null, category: spec.category?.trim() || null, sections: custom.trim() ? [...spec.sections.filter((item) => item !== 'custom_analysis'), 'custom_analysis'] : spec.sections.filter((item) => item !== 'custom_analysis'), custom_requirements: custom.trim() ? [custom.trim()] : [] };
    setGenerating(true);
    setProgress('Starting report');
    setError('');
    const controller = new AbortController();
    try {
      const period = reportSpec.report_type === 'all' ? 'all available years' : `${reportSpec.year}${reportSpec.quarter ? ` Q${reportSpec.quarter}` : ''}`;
      await streamChat(`Generate a ${reportSpec.report_type} procurement report for ${period}.`, undefined, (streamEvent: ChatEvent) => {
        if (streamEvent.type === 'progress' && streamEvent.status === 'running') setProgress(streamEvent.label);
        if (streamEvent.type === 'done' && streamEvent.report) void openReport(streamEvent.report.id);
      }, controller.signal, crypto.randomUUID(), reportSpec);
      await refresh();
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'Report generation failed.');
    } finally {
      setGenerating(false);
      setProgress('');
    }
  }

  return (
    <div className="mx-auto max-w-[1500px] space-y-5">
      <div className="flex items-center justify-between gap-4">
        <div><h2 className="text-lg font-bold text-slate-950">Procurement Reports</h2><p className="mt-1 text-xs text-slate-500">Create, preview, and reopen verified reports.</p></div>
        <button type="button" onClick={() => void refresh()} className="soft-button"><RefreshCw className="h-4 w-4" /> Refresh</button>
      </div>
      {error && <p role="alert" className="rounded-xl border border-rose-200 bg-rose-50 p-3 text-sm text-rose-700">{error}</p>}
      <div className="grid gap-5 xl:grid-cols-[360px_minmax(0,1fr)]">
        <form onSubmit={(event) => void createReport(event)} className="space-y-4 rounded-xl border border-slate-200 bg-white p-5 shadow-card">
          <h3 className="flex items-center gap-2 text-sm font-bold text-slate-900"><Plus className="h-4 w-4 text-emerald" /> Create report</h3>
          <label className="block text-xs font-medium text-slate-700">Report focus<select value={spec.report_focus} onChange={(event) => {
            const focus = event.target.value as ReportSpec['report_focus'];
            const presets: Record<ReportSpec['report_focus'], ReportSection[]> = {
              comprehensive: choices.filter((choice) => choice.key !== 'category_comparison' && choice.key !== 'department_quarterly').map((choice) => choice.key),
              supplier: ['spending_overview', 'order_statistics', 'top_suppliers', 'monthly_trends'],
              department: ['spending_overview', 'order_statistics', 'department_spending', 'department_quarterly', 'monthly_trends'],
              category: ['spending_overview', 'order_statistics', 'category_spending', 'monthly_trends'],
            };
            setSpec({ ...spec, report_focus: focus, sections: presets[focus] });
          }} className="mt-1 w-full rounded-lg border border-slate-200 p-2.5 text-sm"><option value="comprehensive">Comprehensive</option><option value="supplier">Supplier</option><option value="department">Department</option><option value="category">Category</option></select></label>
          <div className="grid grid-cols-2 gap-3">
            <label className="text-xs font-medium text-slate-700">Period<select value={spec.report_type} onChange={(event) => {
              const type = event.target.value as ReportSpec['report_type'];
              setSpec({ ...spec, report_type: type, year: type === 'all' ? null : spec.year ?? 2014, quarter: type === 'quarterly' ? 1 : null, sections: type === 'all' ? spec.sections.filter((section) => section !== 'category_comparison') : spec.sections });
            }} className="mt-1 w-full rounded-lg border border-slate-200 p-2.5 text-sm"><option value="all">All available years</option><option value="annual">Annual</option><option value="quarterly">Quarterly</option></select></label>
            {spec.report_type !== 'all' && <label className="text-xs font-medium text-slate-700">Year<input type="number" min="2000" max="2100" required value={spec.year ?? ''} onChange={(event) => setSpec({ ...spec, year: Number(event.target.value) })} className="mt-1 w-full rounded-lg border border-slate-200 p-2.5 text-sm" /></label>}
          </div>
          {spec.report_type === 'quarterly' && <label className="block text-xs font-medium text-slate-700">Quarter<select value={spec.quarter ?? 1} onChange={(event) => setSpec({ ...spec, quarter: Number(event.target.value) })} className="mt-1 w-full rounded-lg border border-slate-200 p-2.5 text-sm">{[1, 2, 3, 4].map((quarter) => <option key={quarter} value={quarter}>Q{quarter}</option>)}</select></label>}
          <label className="block text-xs font-medium text-slate-700">Acquisition type<select value={spec.acquisition_type ?? ''} onChange={(event) => setSpec({ ...spec, acquisition_type: event.target.value || null })} className="mt-1 w-full rounded-lg border border-slate-200 p-2.5 text-sm"><option value="">All</option><option value="IT Goods">IT Goods</option><option value="NON-IT Goods">NON-IT Goods</option></select></label>
          {(['department', 'supplier', 'category'] as const).map((field) => <label key={field} className="block text-xs font-medium capitalize text-slate-700">{field} filter<input value={spec[field] ?? ''} onChange={(event) => setSpec({ ...spec, [field]: event.target.value || null })} placeholder="All" className="mt-1 w-full rounded-lg border border-slate-200 p-2.5 text-sm" /></label>)}
          <label className="block text-xs font-medium text-slate-700">Top ranking limit<input type="number" min="1" max="50" required value={spec.ranking_limit} onChange={(event) => setSpec({ ...spec, ranking_limit: Number(event.target.value) })} className="mt-1 w-full rounded-lg border border-slate-200 p-2.5 text-sm" /></label>
          <fieldset><legend className="mb-2 text-xs font-semibold text-slate-700">Sections</legend><div className="grid grid-cols-2 gap-2">{choices.map(({ key, label }) => <label key={key} className="flex items-start gap-2 text-xs text-slate-600"><input type="checkbox" checked={spec.sections.includes(key)} onChange={() => toggleSection(key)} className="mt-0.5 accent-emerald" />{label}</label>)}</div></fieldset>
          <details className="text-xs text-slate-700"><summary className="cursor-pointer font-semibold">Charts and tables</summary><div className="mt-2 grid grid-cols-2 gap-3">{(['charts', 'tables'] as const).map((kind) => <fieldset key={kind}><legend className="mb-1 font-medium capitalize">{kind}</legend>{(['supplier', 'department', 'monthly', 'quarterly', 'category'] as const).map((value) => <label key={value} className="mb-1 flex items-center gap-2 capitalize"><input type="checkbox" checked={spec[kind].includes(value)} onChange={() => setSpec((current) => ({ ...current, [kind]: current[kind].includes(value) ? current[kind].filter((item) => item !== value) : [...current[kind], value] }))} className="accent-emerald" />{value}</label>)}</fieldset>)}</div></details>
          <label className="block text-xs font-medium text-slate-700">Custom analysis question <span className="font-normal text-slate-400">(optional)</span><textarea value={custom} onChange={(event) => setCustom(event.target.value)} maxLength={500} rows={2} className="mt-1 w-full rounded-lg border border-slate-200 p-2.5 text-sm" /></label>
          <label className="flex items-center gap-2 text-xs text-slate-700"><input type="checkbox" checked={spec.export_format === 'pdf_csv'} onChange={(event) => setSpec({ ...spec, export_format: event.target.checked ? 'pdf_csv' : 'pdf' })} className="accent-emerald" /> Include CSV exports</label>
          <button type="submit" disabled={generating || !spec.sections.length} className="flex w-full items-center justify-center gap-2 rounded-lg bg-emerald px-4 py-3 text-sm font-semibold text-white disabled:opacity-50">{generating ? <Loader2 className="h-4 w-4 animate-spin" /> : <FileBarChart2 className="h-4 w-4" />}{generating ? progress : 'Generate report'}</button>
        </form>
        <div className="space-y-5">
          <section className="rounded-xl border border-slate-200 bg-white p-5 shadow-card"><h3 className="text-sm font-bold text-slate-900">Saved reports</h3>{loading ? <p className="mt-4 text-sm text-slate-500">Loading reports…</p> : reports.length ? <div className="mt-3 divide-y divide-slate-100">{reports.map((report) => <button type="button" key={report.id} onClick={() => void openReport(report.id)} className="flex w-full items-center justify-between gap-3 py-3 text-left hover:text-emerald"><span><span className="block text-sm font-semibold">{report.title}</span><span className="text-xs text-slate-500">{report.period} · Completed {new Date(report.created_at).toLocaleDateString()}</span></span><span className="rounded-full bg-emerald-50 px-2 py-1 text-xs text-emerald-700">Ready</span></button>)}</div> : <p className="mt-4 text-sm text-slate-500">No reports have been generated yet.</p>}</section>
          {selected && <section className="space-y-4 rounded-xl border border-slate-200 bg-white p-5 shadow-card"><div className="flex flex-wrap items-center justify-between gap-3"><div><h3 className="text-base font-bold text-slate-900">{selected.title}</h3><p className="text-xs text-slate-500">{selected.period} · Completed</p></div><a className="inline-flex items-center gap-2 rounded-lg bg-emerald px-3 py-2 text-xs font-semibold text-white" href={reportPdfDownloadUrl(selected.id)}><Download className="h-4 w-4" /> Download PDF</a></div><p className="text-sm leading-6 text-slate-700">{selected.narrative.executive_summary}</p><iframe title={`${selected.title} PDF preview`} src={reportPdfUrl(selected.id)} className="h-[600px] w-full rounded-lg border border-slate-200" />{selected.spec.export_format === 'pdf_csv' && <div><h4 className="text-xs font-bold text-slate-700">CSV exports</h4><div className="mt-2 flex flex-wrap gap-2">{tableSections.filter((section) => selected.spec.sections.includes(section as ReportSection)).map((section) => <a key={section} href={reportCsvUrl(selected.id, section)} download className="rounded-lg border border-slate-200 px-3 py-2 text-xs font-medium text-slate-700 hover:border-emerald hover:text-emerald">{section.replaceAll('_', ' ')}</a>)}</div></div>}</section>}
        </div>
      </div>
    </div>
  );
}
