import axios from 'axios';
import type { Location, Scene, SceneCreate, SceneUpdate, LocationStatistics } from '@/types/location';
import type { Photo } from '@/types/album';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '';

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
});

export const locationService = {
  async getLocations(level: 'city' | 'province' | 'district' | 'scene' = 'city', skip: number = 0, limit: number = 100) {
    const { data } = await api.get<Location[]>('/api/locations', {
      params: { level, skip, limit }
    });
    return data;
  },

  async getStatistics() {
    const { data } = await api.get<LocationStatistics>('/api/locations/statistics');
    return data;
  },

  async getDistribution(level: 'city' | 'province' | 'district' | 'scene' = 'city') {
    const { data } = await api.get<{name: string, count: number, level: string}[]>('/api/locations/distribution', {
      params: { level }
    });
    return data;
  },
  
  async getLocationPhotos(name: string, level: 'city' | 'province' | 'district' | 'scene' = 'city', skip: number = 0, limit: number = 50) {
    const { data } = await api.get<Photo[]>(`/api/locations/${name}/photos`, {
      params: { level, skip, limit }
    });
    return data;
  },

  async getMapMarkers() {
    const { data } = await api.get<{id: string, lat: number, lng: number}[]>('/api/locations/markers');
    return data;
  },

  async getScene(id: string) {
    const { data } = await api.get<Scene>(`/api/locations/scenes/${id}`);
    return data;
  },

  async createScene(scene: SceneCreate) {
    const { data } = await api.post<Scene>('/api/locations/scenes', scene);
    return data;
  },

  async updateScene(id: string, scene: SceneUpdate) {
    const { data } = await api.put<Scene>(`/api/locations/scenes/${id}`, scene);
    return data;
  },

  async getScenesList(skip: number = 0, limit: number = 100) {
    const { data } = await api.get<Scene[]>('/api/locations/scenes/list', {
      params: { skip, limit }
    });
    return data;
  },

  async deleteScene(id: string) {
    const { data } = await api.delete(`/api/locations/scenes/${id}`);
    return data;
  }
};
