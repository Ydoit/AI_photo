// src/api/config.ts
/** API配置类型 */
export interface ApiConfig {
  /** API标识（唯一） */
  key: string;
  /** 基础路径 */
  baseURL: string;
  /** 超时时间（默认10秒） */
  timeout?: number;
  /** 自定义请求头 */
  headers?: Record<string, string>;
}

/**
 * 多API配置列表
 * 可根据业务需求扩展（如按模块、环境区分）
 */
export const API_CONFIGS: ApiConfig[] = [
  {
    key: 'railway', // 铁路时刻表主API
    baseURL: import.meta.env.VITE_API_RAILWAY_URL || 'http://localhost:8005',
  },
  {
    key: 'user', // 用户系统API（示例）
    baseURL: import.meta.env.VITE_API_USER_URL || 'http://localhost:8006',
  },
  {
    key: 'payment', // 支付系统API（示例）
    baseURL: import.meta.env.VITE_API_PAYMENT_URL || 'http://localhost:8007',
    timeout: 15000, // 支付接口超时时间更长
  },
];

/** 获取指定key的API配置 */
export const getApiConfig = (key: string): ApiConfig => {
  const config = API_CONFIGS.find(item => item.key === key);
  if (!config) {
    throw new Error(`未找到key为${key}的API配置`);
  }
  return config;
};

/** 默认API配置key */
export const DEFAULT_API_KEY = 'railway';