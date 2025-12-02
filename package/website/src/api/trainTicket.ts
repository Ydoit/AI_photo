// src/api/trainTicket.ts
// 该文件用于定义火车票相关的 API 接口
// 使用公共的 Axios 实例来发送请求，确保所有 API 调用都遵循统一的配置和错误处理
import request from '@/utils/request'; // 导入公共 Axios 实例
import {
  TrainTicketCreate,
  TrainTicketUpdate,
  TrainTicketResponse,
  TrainTicketListResponse,
  TrainTicketQueryParams
} from '@/types/trainTicket';

// 所有火车票 API 都复用 request 实例
export const createTrainTicket = (data: TrainTicketCreate): Promise<TrainTicketResponse> => {
  return request.post('/train-ticket', data); // 直接用实例发请求
};

export const getTrainTicketById = (ticketId: number): Promise<TrainTicketResponse> => {
  return request.get(`/train-ticket/${ticketId}`);
};

export const getTrainTicketList = (params?: TrainTicketQueryParams): Promise<TrainTicketListResponse> => {
  return request.get('/train-ticket', { params });
};

export const updateTrainTicket = (
  ticketId: number,
  data: TrainTicketUpdate
): Promise<TrainTicketResponse> => {
  return request.put(`/train-ticket/${ticketId}`, data);
};

export const deleteTrainTicket = (ticketId: number): Promise<{ message: string }> => {
  return request.delete(`/train-ticket/${ticketId}`);
};

export default {
  createTrainTicket,
  getTrainTicketById,
  getTrainTicketList,
  updateTrainTicket,
  deleteTrainTicket
};