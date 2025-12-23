import axios from 'axios';
import type { Location } from '@/types/location';
import type { Photo } from '@/types/album';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '';

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
});

export const locationService = {
  async getLocations(level: 'city' | 'province' = 'city', skip: number = 0, limit: number = 100) {
    const { data } = await api.get<Location[]>('/api/locations', {
      params: { level, skip, limit }
    });
    return data;
  },
  
  async getLocationPhotos(name: string, level: 'city' | 'province' = 'city', skip: number = 0, limit: number = 50) {
    const { data } = await api.get<Photo[]>(`/api/locations/${name}/photos`, {
      params: { level, skip, limit }
    });
    return data;
  }
};
