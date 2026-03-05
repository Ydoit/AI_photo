import request from '@/utils/request';
import type { BaseResponse } from '@/types/railway';

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
    // request interceptor handles unwrapping of BaseResponse
    const data = await request.post<{data:TicketStats[],code:number,message:string}>('/api/railway/stats/batch', { items });
    return data.data
  },

  /**
   * 获取所有站点信息
   */
  async getStations(params?: { page?: number; page_size?: number; keyword?: string }) {
    const data = await request.get<{data:StationListResponse,code:number,message:string}>('/api/railway/stations', { params });
    return data.data
  }
};
