// src/api/types/index.ts
/** 基础响应模型 */
export interface BaseResponse<T = any> {
  code: number;
  msg: string;
  data: T | null;
}

/** 分页响应基础模型 */
export interface PageResponse<T = any> {
  total: number;
  page: number;
  page_size: number;
  total_page: number;
  list: T[];
}

// ------------------------------ 车站相关类型 ------------------------------
/** 车站创建/更新参数 */
export interface StationCreate {
  telecode?: string;
  station_name: string;
  station_pinyin: string;
  station_py: string;
  province: string;
  city: string;
  district?: string;
  is_high_speed?: 0 | 1;
  status?: 0 | 1;
}

/** 车站信息 */
export interface StationRead {
  station_name: string;
  station_pinyin: string;
  province: string;
  city: string;
  district?: string;
  telecode?: string;
  is_high_speed: number;
  status: number;
}

/** 单条车站查询参数 */
export interface StationSingleQuery {
  station_id?: number;
  telecode?: string;
  station_name?: string;
}

/** 车站列表查询参数 */
export interface StationListQuery {
  province?: string;
  city?: string;
  district?: string;
  is_high_speed?: 0 | 1;
  status?: 0 | 1;
  keyword?: string;
  page?: number;
  page_size?: number;
}

/** 车站列表响应 */
export type StationListResponse = PageResponse<StationRead>;

// ------------------------------ 运行计划相关类型 ------------------------------
/** 运行计划创建/更新参数 */
export interface TrainOperationPlanCreate {
  train_no: string;
  start_date: string; // YYYY-MM-DD
  end_date?: string; // YYYY-MM-DD
  run_rule?: 0 | 1 | 2 | 3 | 4 | 5;
  custom_run_days?: string[]; // YYYY-MM-DD 数组
  station_num?: number;
  total_mileage?: number;
  total_running_time?: number;
  status?: 0 | 1;
}

/** 运行计划信息 */
export interface TrainOperationPlanRead {
  operation_id: number;
  train_no: string;
  start_date: string; // YYYY-MM-DD
  end_date?: string; // YYYY-MM-DD
  run_rule: number;
  custom_run_days?: string[];
  station_num: number;
  total_mileage: number;
  total_running_time: number;
  status: number;
}

/** 单条运行计划查询参数 */
export interface TrainOperationPlanSingleQuery {
  operation_id?: number;
  train_no?: string;
}

/** 运行计划列表查询参数 */
export interface TrainOperationPlanListQuery {
  train_no?: string;
  start_date?: string; // YYYY-MM-DD
  end_date?: string; // YYYY-MM-DD
  run_rule?: 0 | 1 | 2 | 3 | 4 | 5;
  status?: 0 | 1;
  page?: number;
  page_size?: number;
}

// ------------------------------ 车次相关类型 ------------------------------
/** 车次创建/更新参数 */
export interface TrainCreate {
  train_no: string;
  train_code: string;
  train_type: string;
  from_station: string;
  to_station: string;
}

/** 车次信息 */
export interface TrainRead {
  train_id: number;
  train_no: string;
  train_code: string;
  train_type: string;
  from_station: string;
  to_station: string;
  departure_station_name?: string;
  arrival_station_name?: string;
}

/** 单条车次查询参数 */
export interface TrainSingleQuery {
  train_id?: number;
  train_no?: string;
  train_code?: string;
  from_station?: string;
  to_station?: string;
}

/** 车次列表查询参数 */
export interface TrainListQuery {
  train_code?: string;
  train_type?: string;
  from_station?: string;
  to_station?: string;
  page?: number;
  page_size?: number;
}

/** 车次列表响应 */
export type TrainListResponse = PageResponse<TrainRead>;

// ------------------------------ 时刻表相关类型 ------------------------------
/** 单条时刻表创建参数 */
export interface TrainScheduleCreate {
  train_no: string;
  train_code: string;
  station_telecode: string;
  station_name: string;
  sequence: number;
  arrive_day_diff?: number;
  arrival_time?: string; // HH:mm:ss
  departure_time?: string; // HH:mm:ss
  stop_duration?: number;
  accumulated_mileage: number;
  running_time: number;
  is_departure?: 0 | 1;
  is_arrival?: 0 | 1;
}

/** 批量创建时刻表参数 */
export interface TrainScheduleBatchCreate {
  schedules: TrainScheduleCreate[];
}

/** 时刻表信息 */
export interface TrainScheduleRead {
  schedule_id: number;
  train_no: string;
  train_code: string;
  station_telecode: string;
  station_name: string;
  sequence: number;
  arrive_day_diff: number;
  arrival_time?: string; // HH:mm:ss
  departure_time?: string; // HH:mm:ss
  stop_duration: number;
  accumulated_mileage: number;
  running_time: number;
  is_departure: number;
  is_arrival: number;
}

/** 单条时刻表查询参数 */
export interface TrainScheduleSingleQuery {
  schedule_id?: number;
  train_no?: string;
  station_telecode?: string;
  sequence?: number;
}

/** 时刻表列表查询参数 */
export interface TrainScheduleListQuery {
  train_no?: string;
  train_code?: string;
  station_telecode?: string;
  station_name?: string;
  is_departure?: 0 | 1;
  is_arrival?: 0 | 1;
  page?: number;
  page_size?: number;
}

/** 时刻表列表响应 */
export type TrainScheduleResponse = PageResponse<TrainScheduleRead>;