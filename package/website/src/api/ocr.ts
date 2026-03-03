import request from '@/utils/request';

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
    const data = await request.get<OCRResponse>('/api/ocr', { 
        params: { photo_id: photoId } 
    })
    return data
  },

  async deleteOCR(photoId: string) {
    const data = await request.delete(`/api/ocr/${photoId}`)
    return data
  }
}
