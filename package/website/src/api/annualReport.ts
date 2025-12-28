import type { AnnualReportData } from '@/types/annualReport';
import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || ''
const api = axios.create({ baseURL: API_BASE_URL })

export async function getAnnualReport(): Promise<AnnualReportData> {
  const { data } = await api.get<AnnualReportData>('/api/annual-report', {
    params: {
        year: new Date().getFullYear()
    }
  });
  return data
}
