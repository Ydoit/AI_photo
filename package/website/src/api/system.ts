import request from '@/utils/request';

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
    const data = await request.get<{version: string}>('/api/system/version')
    return data.data
  },
  async checkUpdate(): Promise<UpdateCheckResult> {
    const data = await request.get<UpdateCheckResult>('/api/system/update-check')
    return data.data
  }
}
