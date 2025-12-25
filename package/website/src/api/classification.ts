import axios from 'axios';
import type { Photo } from '@/types/album';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '';

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
});

export interface TagStats {
  id: string
  tag_name: string
  count: number
  cover: Photo | null
}

export const classificationService = {
  async getTags(skip: number = 0, limit: number = 100) {
    const { data } = await api.get<TagStats[]>('/api/tags', {
      params: { skip, limit }
    });
    return data;
  },
  
  async getTagPhotos(name: string, skip: number = 0, limit: number = 50) {
    const { data } = await api.get<Photo[]>(`/api/tags/${encodeURIComponent(name)}/photos`, {
      params: { skip, limit }
    });
    return data;
  }
};
