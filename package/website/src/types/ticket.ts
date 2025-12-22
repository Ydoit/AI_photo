// src/types/ticket.ts

// 后端原始数据接口 (Snake Case)
export interface TicketBackend {
  id: number;
  train_code: string;
  departure_station: string;
  arrival_station: string;
  date_time: string; // "YYYY-MM-DD HH:mm:ss"
  carriage: string;
  seat_num: string;
  berth_type?: string;
  price: number;
  seat_type: string;
  name: string;
  discount_type?: string;
  total_running_time: number; // minutes
  total_mileage: number; // km
  stop_stations?: string;
  comments?: string;
}

// 前端展示用的数据接口 (Camel Case)
export interface TicketFrontend {
  id: number;
  from: string;
  to: string;
  trainCode: string;
  name: string;
  date: string;       // "YYYY-MM-DD"
  time: string;       // "HH:mm"
  dateTime: string;   // 原始完整时间字符串
  carriage: string;
  seatNumber: string;
  berthType: string;
  price: number;
  seatType: string;
  discountType: string;
  totalRunningTime: number;
  distance: number;
  comments: string;
  duration: string; // "xh yymin"
}

// 表单提交用的数据接口
export interface TicketFormData {
  id?: number | null;
  from: string;
  to: string;
  train_code: string;
  name: string;
  dateTime: string;
  carriage: string;
  seatNumber: string;
  berthType: string;
  price: number;
  seatType: string;
  discountType: string;
  totalRunningTime: number;
  distance: number;
  comments: string;
}

// 筛选查询参数
export interface TicketQueryParams {
  skip?: number;
  limit?: number;
  train_code?: string;
  departure_station?: string;
  arrival_station?: string;
  name?: string;
}

export type SortType = 'date' | 'distance' | 'duration' | 'price';
export type FilterType = 'all' | 'highspeed' | 'normal';