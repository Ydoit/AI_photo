import request from '@/utils/request';

export interface ChatRequest {
  message: string;
  session_id?: string;
}

export interface ChatResponse {
  response: string;
  session_id: string;
}

export interface AgentSession {
  id: string;
  user_id: string;
  title: string | null;
  status: string;
  context_summary: string | null;
  summary_update_time: string | null;
  is_pinned: boolean;
  created_at: string;
}

export interface AgentMessage {
  id: number;
  session_id: string;
  role: string;
  content: string;
  content_type: string;
  content_ext: any | null;
  token_count: number;
  created_at: string;
}

export interface CreateSessionRequest {
  id?: string;
  title?: string;
  status?: string;
  context_summary?: string;
  is_pinned?: boolean;
}

export const agentApi = {
  chat(data: ChatRequest) {
    return request.post<ChatResponse>('/api/agent/chat', data);
  },
  getSessions(params?: { skip?: number; limit?: number }) {
    return request.get<AgentSession[]>('/api/agent/sessions', { params });
  },
  createSession(data: CreateSessionRequest) {
    return request.post<AgentSession>('/api/agent/sessions', data);
  },
  deleteSession(sessionId: string) {
    return request.delete<{ message: string }>(`/api/agent/sessions/${sessionId}`);
  },
  pinSession(sessionId: string, isPinned: boolean) {
    return request.put<AgentSession>(`/api/agent/sessions/${sessionId}/pin`, null, {
      params: { is_pinned: isPinned }
    });
  },
  getSessionMessages(sessionId: string, params?: { skip?: number; limit?: number }) {
    return request.get<AgentMessage[]>(`/api/agent/sessions/${sessionId}/messages`, { params });
  },
  deleteMessages(sessionId: string, messageIds?: number[]) {
    return request.delete<{ message: string }>('/api/agent/messages', {
      params: { 
        session_id: sessionId,
        message_ids: messageIds?.join(',')
      }
    });
  }
};
