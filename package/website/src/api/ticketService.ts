// src/services/ticketService.ts
import axios from 'axios';
import type { TicketBackend, TicketQueryParams, FlightTicketBackend } from '@/types/ticket';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: { 'Content-Type': 'application/json' },
});

export const ticketService = {
  // 获取列表
  async getTickets(params: TicketQueryParams) {
    const { data } = await api.get<{ items: TicketBackend[], total: number }>('/api/train-ticket', { params });
    return data;
  },

  // 创建
  async createTicket(data: Partial<TicketBackend>) {
    const { data: res } = await api.post<TicketBackend>('/api/train-ticket', data);
    return res;
  },

  // 获取飞机票列表
  async getFlightTickets(params: TicketQueryParams) {
    const { data } = await api.get<{ items: FlightTicketBackend[], total: number }>('/api/flight-ticket', { params });
    // 标记类型
    data.items.forEach(item => item.type = 'flight');
    return data;
  },

  // 创建飞机票
  async createFlightTicket(data: Partial<FlightTicketBackend>) {
    const { data: res } = await api.post<FlightTicketBackend>('/api/flight-ticket', data);
    res.type = 'flight';
    return res;
  },

  // 更新飞机票
  async updateFlightTicket(id: string, data: Partial<FlightTicketBackend>) {
    const { data: res } = await api.put<FlightTicketBackend>(`/api/flight-ticket/${id}`, data);
    res.type = 'flight';
    return res;
  },

  // 删除飞机票
  async deleteFlightTicket(id: string) {
    await api.delete(`/api/flight-ticket/${id}`);
    return true;
  },

  // 更新
  async updateTicket(id: number | string, data: Partial<TicketBackend>) {
    const { data: res } = await api.put<TicketBackend>(`/api/train-ticket/${id}`, data);
    return res;
  },

  // 删除
  async deleteTicket(id: number | string) {
    await api.delete(`/api/train-ticket/${id}`);
    return true;
  },

  // 批量删除 (前端循环调用或后端支持批量接口)
  async batchDeleteTickets(ids: (number | string)[]) {
    // 假设后端没有批量接口，使用 Promise.all
    const promises = ids.map(id => api.delete(`/api/train-ticket/${id}`));
    await Promise.all(promises);
    return true;
  },

  // 识别车票
  async recognizeTicket(file: File) {
    const formData = new FormData();
    formData.append('file', file);
    const { data } = await api.post('/api/train-ticket/recognize', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    });
    return data;
  },

  // 导出数据
  async exportTickets(format: 'json' | 'csv' = 'json') {
    const response = await api.get(`/api/train-ticket/export`, {
      params: { format },
      responseType: 'blob'
    });
    
    // 创建下载链接
    const url = window.URL.createObjectURL(new Blob([response.data]));
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', `tickets_export_${new Date().getTime()}.${format}`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  },

  // 导入数据
  async importTickets(file: File) {
    const formData = new FormData();
    formData.append('file', file);
    const { data } = await api.post('/api/train-ticket/import', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    });
    return data;
  }
};