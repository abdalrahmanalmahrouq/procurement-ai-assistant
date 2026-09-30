import type { Report, ReportSummary } from '../types/reports';

const AI_API_URL = import.meta.env.VITE_AI_API_URL ?? '';

export const reportPdfUrl = (id: string) => `${AI_API_URL}/api/reports/${encodeURIComponent(id)}/pdf`;
export const reportPdfDownloadUrl = (id: string) => `${reportPdfUrl(id)}?download=1`;
export const reportCsvUrl = (id: string, section: string) => `${AI_API_URL}/api/reports/${encodeURIComponent(id)}/csv/${encodeURIComponent(section)}`;

async function getJson<T>(path: string): Promise<T> {
  const response = await fetch(`${AI_API_URL}${path}`);
  if (!response.ok) throw new Error(`Could not load reports (${response.status}).`);
  return response.json() as Promise<T>;
}

export const listReports = () => getJson<ReportSummary[]>('/api/reports');
export const getReport = (id: string) => getJson<Report>(`/api/reports/${encodeURIComponent(id)}`);
