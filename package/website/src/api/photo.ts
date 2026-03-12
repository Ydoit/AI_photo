import request from '@/utils/request'
import type { AlbumImage,Photo } from '@/types/album'

export const photoApi = {
  async getCleanupPhotos(params: { skip: number; limit: number; sort_by: 'asc' | 'desc' }) {
    const data = await request.get<Photo[]>('/api/photos/cleanup', {
      params
    });
    return data.data;
  },

  async getOnThisDayPhotos(params?: { year?: number; month?: number; day?: number; limit?: number }) {
    const data = await request.get<Photo[]>('/api/photos/on-this-day', {
      params
    });
    return data.data;
  }
}
