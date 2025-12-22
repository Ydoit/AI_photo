// src/services/ticketService.ts
import axios from 'axios';
import type { TicketBackend, TicketQueryParams } from '@/types/ticket';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

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

  // 更新
  async updateTicket(id: number, data: Partial<TicketBackend>) {
    const { data: res } = await api.put<TicketBackend>(`/api/train-ticket/${id}`, data);
    return res;
  },

  // 删除
  async deleteTicket(id: number) {
    await api.delete(`/api/train-ticket/${id}`);
    return true;
  },

  // 批量删除 (前端循环调用或后端支持批量接口)
  async batchDeleteTickets(ids: number[]) {
    // 假设后端没有批量接口，使用 Promise.all
    const promises = ids.map(id => api.delete(`/api/train-ticket/${id}`));
    await Promise.all(promises);
    return true;
  }
};