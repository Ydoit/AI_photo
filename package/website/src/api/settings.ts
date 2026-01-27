import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || ''
const api = axios.create({ baseURL: API_BASE_URL })

export const settingsApi = {
  async getStorageRoot() {
    const { data } = await api.get('/api/settings/storage-root')
    return data
  },
  async updateStorageRoot(storageRoot: string) {
    const { data } = await api.put('/api/settings/storage-root', { storage_root: storageRoot })
    return data
  },
  async rebuildIndex() {
    const { data } = await api.post('/api/index/rebuild')
    return data
  },
  async getIndexStatus() {
    const { data } = await api.get('/api/index/status')
    return data
  },
  async getIndexLogs(limit = 100) {
    const { data } = await api.get('/api/index/logs', { params: { limit } })
    return data
  },
  async getDirectories() {
    const { data } = await api.get('/api/settings/directories')
    return data
  },
  async addDirectory(path: string) {
    const { data } = await api.post('/api/settings/directories', { path })
    return data
  },
  async removeDirectory(path: string) {
    const { data } = await api.delete('/api/settings/directories', { data: { path } })
    return data
  },
  async getSettings() {
    const { data } = await api.get('/api/settings/')
    return data
  },
  async updateSettings(config: any) {
    const { data } = await api.put('/api/settings/', config)
    return data
  },
  async exportSettings() {
    const { data } = await api.get('/api/settings/export')
    return data
  },
  async importSettings(config: any) {
    const { data } = await api.post('/api/settings/import', config)
    return data
  },
  async getMapCountries() {
    const { data } = await api.get('/api/settings/map/countries')
    return data
  },
  async getDownloadedMapData() {
    const { data } = await api.get('/api/settings/map/downloaded')
    return data
  },
  async downloadMapData(code: string) {
    const { data } = await api.post('/api/settings/map/download', { code })
    return data
  },
  async uploadMapData(file: File) {
    const formData = new FormData()
    formData.append('file', file)
    const { data } = await api.post('/api/settings/map/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
    return data
  },
  async downloadMapFile(filename: string) {
    const response = await api.get(`/api/settings/map/files/${filename}`, {
      responseType: 'blob'
    })
    return response.data
  },
  async deleteMapData(filename: string) {
    const { data } = await api.delete(`/api/settings/map/files/${filename}`)
    return data
  }
}

