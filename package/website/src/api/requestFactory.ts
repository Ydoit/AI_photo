// src/api/requestFactory.ts
import axios, { AxiosRequestConfig, AxiosError, AxiosInstance, AxiosResponse } from 'axios';
import { ApiConfig, getApiConfig, DEFAULT_API_KEY } from './config';
import { BaseResponse } from '@/types/railway';

/**
 * 创建单个API请求实例
 * @param config API配置
 */
const createRequestInstance = (config: ApiConfig): AxiosInstance => {
  const instance = axios.create({
    baseURL: config.baseURL,
    timeout: config.timeout || 10000,
    headers: {
      'Content-Type': 'application/json;charset=utf-8',
      ...config.headers,
    },
  });

  // 请求拦截器（统一添加token等）
  instance.interceptors.request.use(
    (reqConfig) => {
      const token = localStorage.getItem('token');
      if (token) {
        reqConfig.headers.Authorization = `Bearer ${token}`;
      }
      return reqConfig;
    },
    (error: AxiosError) => Promise.reject(error)
  );

  // 响应拦截器（统一处理响应格式）- 修复类型问题
  instance.interceptors.response.use(
    (response: AxiosResponse<BaseResponse>) => {  // 明确响应数据类型是 BaseResponse
      const res = response.data;
      
      // 错误处理：非200状态码直接reject
      if (res.code !== 200) {
        console.error(`[${config.key} API Error]`, res.msg);
        // 返回 Promise.reject，携带完整的错误信息（包含 AxiosResponse 上下文）
        return Promise.reject({
          ...response,  // 保留原始响应信息
          data: res     // 确保 data 是 BaseResponse 类型
        });
      }
      
      // 成功：返回原始 AxiosResponse（保持类型一致），仅确保 data 是 BaseResponse
      return response;
    },
    (error: AxiosError) => {
      const errorMsg = error.message || `[${config.key} Network Error]`;
      console.error(errorMsg);
      
      // 网络错误：构造统一的 BaseResponse 格式，包裹到 AxiosError 中
      return Promise.reject({
        ...error,
        response: {
          ...error.response,
          data: {
            code: 500,
            msg: errorMsg,
            data: null
          } as BaseResponse
        }
      } as AxiosError<BaseResponse>);
    }
  );

  return instance;
};

/**
 * API请求工厂
 * 缓存已创建的实例，避免重复创建
 */
class ApiRequestFactory {
  /** 缓存的请求实例 */
  private instances: Record<string, AxiosInstance> = {};

  /**
   * 获取API请求实例
   * @param key API配置key（默认使用DEFAULT_API_KEY）
   */
  getInstance(key: string = DEFAULT_API_KEY): AxiosInstance {
    if (!this.instances[key]) {
      const config = getApiConfig(key);
      this.instances[key] = createRequestInstance(config);
    }
    return this.instances[key];
  }

  /**
   * 通用请求方法（支持指定API实例）
   * @param config 请求配置
   * @param apiKey API配置key
   */
  async request<T = any>(
    config: AxiosRequestConfig,
    apiKey: string = DEFAULT_API_KEY
  ): Promise<BaseResponse<T>> {
    const instance = this.getInstance(apiKey);
    try {
      // 发起请求，获取 AxiosResponse<BaseResponse<T>> 类型
      const response = await instance.request<BaseResponse<T>>(config);
      // 返回 response.data（BaseResponse<T> 类型），符合业务层使用习惯
      return response.data;
    } catch (error) {
      // 错误处理：提取 BaseResponse 格式的错误信息
      const axiosError = error as AxiosError<BaseResponse<T>>;
      return axiosError.response?.data || {
        code: 500,
        msg: '未知错误',
        data: null
      } as BaseResponse<T>;
    }
  }
}

/** 全局API请求工厂实例 */
export const apiFactory = new ApiRequestFactory();

/** 通用请求函数（默认使用默认API实例） */
export const request = <T = any>(
  config: AxiosRequestConfig,
  apiKey: string = DEFAULT_API_KEY
) => {
  return apiFactory.request<T>(config, apiKey);
};

/** 按API模块导出专用请求函数（可选，更直观） */
export const railwayRequest = <T = any>(config: AxiosRequestConfig) => {
  return apiFactory.request<T>(config, 'railway');
};

export const userRequest = <T = any>(config: AxiosRequestConfig) => {
  return apiFactory.request<T>(config, 'user');
};

export const paymentRequest = <T = any>(config: AxiosRequestConfig) => {
  return apiFactory.request<T>(config, 'payment');
};