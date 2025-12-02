import axios, { 
  AxiosInstance, 
  InternalAxiosRequestConfig, // 关键：导入内部请求配置类型
  AxiosResponse, 
  AxiosError,
  AxiosRequestHeaders // 导入请求头类型
} from 'axios';
import { ElMessage } from 'element-plus';
import { useRouter } from 'vue-router';

// 创建 Axios 实例（类型不变）
const service: AxiosInstance = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '',
  timeout: 5000,
  headers: {
    'Content-Type': 'application/json'
  },
});

const router = useRouter();

// ------------------- 修正请求拦截器（核心修改）-------------------
service.interceptors.request.use(
  // 1. 参数类型改为 InternalAxiosRequestConfig
  (config: InternalAxiosRequestConfig) => {
    // 2. 处理 headers 可选性：确保 headers 存在（避免 undefined 报错）
    const headers = config.headers as AxiosRequestHeaders; // 类型断言（或用可选链）
    
    // 或用可选链 + 空值合并（更安全）：
    // config.headers = config.headers ?? {}; // 若 headers 为 undefined，初始化为空对象

    // 添加 Token（安全赋值）
    const token = localStorage.getItem('user_token');
    if (token) {
      headers.Authorization = `Bearer ${token}`;
    }

    // 添加自定义请求头（同样处理可选性）
    headers['X-Api-Version'] = 'v1';

    return config; // 返回类型自动匹配 InternalAxiosRequestConfig
  },
  (error: AxiosError) => {
    ElMessage.error('请求配置错误：' + error.message);
    return Promise.reject(error);
  }
);

// ------------------- 响应拦截器（无需修改，保持原样）-------------------
service.interceptors.response.use(
  (response: AxiosResponse) => {
    const res = response.data;
    if (res.code !== 200) {
      ElMessage.error(res.message || '接口请求失败');
      return Promise.reject(res);
    }
    return res.data;
  },
  (error: AxiosError) => {
    let errorMsg = '网络异常，请重试';
    if (error.response) {
      switch (error.response.status) {
        case 401:
          errorMsg = '登录已过期，请重新登录';
          localStorage.removeItem('user_token');
          router.push('/login');
          break;
        case 403:
          errorMsg = '暂无权限访问';
          break;
        case 404:
          errorMsg = '接口地址不存在';
          break;
        case 500:
          errorMsg = '服务器内部错误';
          break;
        default:
          errorMsg = `请求错误（${error.response.status}）`;
      }
    } else if (error.request) {
      errorMsg = '请求超时，请检查网络';
    }
    ElMessage.error(errorMsg);
    return Promise.reject(error);
  }
);

export default service;