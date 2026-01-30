import axios from 'axios';
import type { BaseResponse } from '@/types/railway';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '';

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

export interface Station {
  station_name: string;
  city: string;
  province: string;
  telecode?: string;
}

export interface StationListResponse {
  total: number;
  list: Station[];
}

export const railwayService = {
  /**
   * 批量计算车票里程和时长
   */
  async getBatchStats(items: TicketItem[]) {
    const { data } = await api.post<BaseResponse<TicketStats[]>>('/api/railway/stats/batch', { items });
    return data;
  },

  /**
   * 获取所有站点信息
   */
  async getStations(params?: { page?: number; page_size?: number; keyword?: string }) {
    const { data } = await api.get<BaseResponse<StationListResponse>>('/api/railway/stations', { params });
    return data;
  }
};
