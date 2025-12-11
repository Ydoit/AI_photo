import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || ''
const api = axios.create({ baseURL: API_BASE_URL })

export interface Task {
  id: string
  type: string
  status: string
  priority: number
  created_at: string
  updated_at?: string
  error?: string
  payload?: any
  total_items?: number
  processed_items?: number
  result?: any
}

export const tasksApi = {
  async listTasks(status?: string, limit = 50) {
    const params: any = { limit }
    if (status) params.status = status
    const { data } = await api.get<Task[]>('/api/tasks/', { params })
    return data
  },

  async getTask(taskId: string) {
    const { data } = await api.get<Task>(`/api/tasks/${taskId}`)
    return data
  },

  async createTask(type: string, payload: any = {}) {
    const { data } = await api.post<Task>('/api/tasks/', { type, payload })
    return data
  },

  async cancelTask(taskId: string) {
    const { data } = await api.post<Task>(`/api/tasks/${taskId}/cancel`)
    return data
  }
}
