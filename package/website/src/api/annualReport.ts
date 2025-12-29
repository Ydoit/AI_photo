import type { 
  AnnualReportData, 
  UserInfo, 
  TimeMetrics, 
  MemoryMetrics, 
  LocationMetrics, 
  SeasonMetrics, 
  EmotionMetrics, 
  EasterEgg 
} from '@/types/annualReport';
import type { Photo } from '@/types/album';
import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || ''
const api = axios.create({ baseURL: API_BASE_URL })

export async function getReportSummary(startTime: string, endTime: string): Promise<{user: UserInfo, time: TimeMetrics}> {
  const { data } = await api.get<{user: UserInfo, time: TimeMetrics}>('/api/annual-report/summary', {
    params: {
        start_time: startTime,
        end_time: endTime
    }
  });
  return data
}

export async function getReportMemory(startTime: string, endTime: string): Promise<MemoryMetrics> {
  const { data } = await api.get<MemoryMetrics>('/api/annual-report/memory', {
    params: {
        start_time: startTime,
        end_time: endTime
    }
  });
  return data
}

export async function getReportLocation(startTime: string, endTime: string): Promise<LocationMetrics> {
  const { data } = await api.get<LocationMetrics>('/api/annual-report/location', {
    params: {
        start_time: startTime,
        end_time: endTime
    }
  });
  return data
}

export async function getReportSeason(startTime: string, endTime: string): Promise<SeasonMetrics> {
  const { data } = await api.get<SeasonMetrics>('/api/annual-report/season', {
    params: {
        start_time: startTime,
        end_time: endTime
    }
  });
  return data
}

export async function getReportEmotion(startTime: string, endTime: string): Promise<EmotionMetrics> {
  const { data } = await api.get<EmotionMetrics>('/api/annual-report/emotion', {
    params: {
        start_time: startTime,
        end_time: endTime
    }
  });
  return data
}

export async function getReportEasterEgg(startTime: string, endTime: string): Promise<EasterEgg> {
  const { data } = await api.get<EasterEgg>('/api/annual-report/easter-egg', {
    params: {
        start_time: startTime,
        end_time: endTime
    }
  });
  return data
}

export async function getAnnualReportPhotos(startTime: string, endTime: string): Promise<Record<number, Photo[]>> {
  const { data } = await api.get<Record<number, Photo[]>>('/api/annual-report/photos', {
    params: {
        start_time: startTime,
        end_time: endTime
    }
  });
  return data
}
