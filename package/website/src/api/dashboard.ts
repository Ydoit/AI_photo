import request from '@/utils/request';

export interface DashboardCard {
  total_media: number;
  today_new: number;
  storage_used: string;
}

export interface DashboardFaceItem {
  id: string;
  name: string;
  count: number;
  avatar_url?: string;
}

export interface DashboardFace {
  total_identified: number;
  top_faces: DashboardFaceItem[];
  pending_faces_count: number;
  unidentified_photos_count: number;
}

export interface ContentDetail {
  total: number;
  sub_1_label: string;
  sub_1_count: number;
  sub_2_label: string;
  sub_2_count: number;
}

export interface DashboardContentStats {
  photos: ContentDetail;
  videos: ContentDetail;
  scenery_count: number;
  food_count: number;
}

export interface DashboardTimeChartItem {
  year: number;
  count: number;
  percentage: number;
  color: string;
}

export interface DashboardTime {
  current_year_percentage: number;
  chart_data: DashboardTimeChartItem[];
  monthly_peak: string;
}

export interface DashboardResponse {
  card: DashboardCard;
  face: DashboardFace;
  content: DashboardContentStats;
  time: DashboardTime;
}

export const dashboardApi = {
  async getOverview() {
    const data = await request.get<DashboardResponse>('/api/stats/dashboard');
    return data;
  }
};
