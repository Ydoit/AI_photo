import axios from 'axios';
import type { BaseResponse } from '@/types/railway';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: { 'Content-Type': 'application/json' },
});

export interface TicketItem {
  id?: string;
  train_code: string;
  departure_station: string;
  arrival_station: string;
  date_time?: string;
}

export interface TicketStats {
  id?: string;
  distance_km: number;
  duration_minutes: number;
  train_no?: string;
}

export const railwayService = {
  /**
   * 批量计算车票里程和时长
   */
  async getBatchStats(items: TicketItem[]) {
    const { data } = await api.post<BaseResponse<TicketStats[]>>('/railway/stats/batch', { items });
    return data;
  }
};
