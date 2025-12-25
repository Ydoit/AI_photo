import axios from 'axios';
import type { Photo } from '@/types/album';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '';

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
});

export interface SearchResult {
  photo: Photo;
  score: number;
}

export interface TextSearchRequest {
  text: string;
  limit?: number;
  skip?: number;
  threshold?: number;
}

const searchService = {
  /**
   * Search photos by text
   */
  async searchByText(data: TextSearchRequest) {
    const { data: res } = await api.post<SearchResult[]>('/api/search/text', data);
    return res;
  },
  
  /**
   * Search photos by image
   */
  async searchByImage(file: File, limit: number = 20, threshold: number = 0.0) {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('limit', limit.toString());
    formData.append('threshold', threshold.toString());

    const { data: res } = await api.post<SearchResult[]>('/api/search/image', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    });
    return res;
  }
};

export default searchService;
