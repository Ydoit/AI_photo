import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || ''
const api = axios.create({ baseURL: API_BASE_URL })

export interface UpdateCheckResult {
  current_version: string
  latest_version: string | null
  has_update: boolean
  update_info: string | null
  download_url: string | null
  error?: string
}

export const systemApi = {
  async getVersion(): Promise<{version: string}> {
    const { data } = await api.get('/api/system/version')
    return data
  },
  async checkUpdate(): Promise<UpdateCheckResult> {
    const { data } = await api.get('/api/system/update-check')
    return data
  }
}
