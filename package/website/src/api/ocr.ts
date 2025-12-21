import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || ''
const api = axios.create({ baseURL: API_BASE_URL })

export interface OCRRecord {
  id: number
  photo_id: string
  text: string
  text_score: number
  polygon: number[][] // [[x,y], [x,y], ...]
}

export interface OCRResponse {
  count: number
  records: OCRRecord[]
}

export const ocrApi = {
  async getOCR(photoId: string) {
    const { data } = await api.get<OCRResponse>('/api/ocr', { 
        params: { photo_id: photoId } 
    })
    return data
  },

  async deleteOCR(photoId: string) {
    const { data } = await api.delete(`/api/ocr/${photoId}`)
    return data
  }
}
