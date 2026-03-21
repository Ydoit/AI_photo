import request from '@/utils/request';

export interface ChatRequest {
  message: string;
  session_id?: string;
}

export interface ChatResponse {
  response: string;
  session_id: string;
}

export const agentApi = {
  chat(data: ChatRequest) {
    return request.post<ChatResponse>('/api/agent/chat', data);
  }
};
