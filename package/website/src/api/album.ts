import axios from 'axios';
import type { Album, CreateAlbumDto, Photo, PhotoMetadata } from '@/types/album';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
});

export const albumService = {
  // Albums
  async getAlbums() {
    const { data } = await api.get<Album[]>('/api/albums');
    return data;
  },
  async getAlbum(id: string) {
    const { data } = await api.get<Album>(`/api/albums/${id}`);
    return data;
  },
  async createAlbum(album: CreateAlbumDto) {
    const { data } = await api.post<Album>('/api/albums', album);
    return data;
  },
  async updateAlbum(id: string, album: CreateAlbumDto) {
    const { data } = await api.put<Album>(`/api/albums/${id}`, album);
    return data;
  },
  async deleteAlbum(id: string) {
    await api.delete(`/api/albums/${id}`);
  },

  // Photos
  async getAllPhotos(skip: number = 0, limit: number = 100, filters?: { year?: string, city?: string, tag?: string }) {
    const { data } = await api.get<Photo[]>('/api/photos', {
      params: { skip, limit, ...filters }
    });
    return data;
  },

  async getPhotos(albumId: string, skip: number = 0, limit: number = 100) {
    const { data } = await api.get<Photo[]>(`/api/albums/${albumId}/photos`, {
      params: { skip, limit }
    });
    return data;
  },
  
  async deletePhoto(albumId: string, photoId: string) {
    await api.delete(`/api/albums/${albumId}/photos/${photoId}`);
  },

  // Upload (Simple)
  async uploadPhoto(file: File, albumId?: string) {
    const formData = new FormData();
    formData.append('file', file);
    if (albumId) {
        formData.append('album_id', albumId);
    }
    const { data } = await api.post<Photo>('/api/photos', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
    });
    return data;
  },
  
  // Chunk Upload
  async initUpload() {
      const { data } = await api.post<{upload_id: string}>('/api/upload/init');
      return data.upload_id;
  },
  
  async uploadChunk(uploadId: string, chunkIndex: number, chunk: Blob) {
      const formData = new FormData();
      formData.append('upload_id', uploadId);
      formData.append('chunk_index', chunkIndex.toString());
      formData.append('file', chunk);
      await api.post('/api/upload/chunk', formData);
  },
  
  async finishUpload(uploadId: string, fileName: string, albumId?: string) {
      const formData = new FormData();
      formData.append('upload_id', uploadId);
      formData.append('file_name', fileName);
      if (albumId) {
          formData.append('album_id', albumId);
      }
      const { data } = await api.post<Photo>('/api/upload/finish', formData);
      return data;
  },

  // Metadata
  async getMetadata(albumId: string, photoId: string) {
      const { data } = await api.get<PhotoMetadata>(`/api/albums/${albumId}/photos/${photoId}/metadata`);
      return data;
  },
  
  async updateMetadata(albumId: string, photoId: string, metadata: Partial<PhotoMetadata>) {
      const { data } = await api.put<PhotoMetadata>(`/api/albums/${albumId}/photos/${photoId}/metadata`, metadata);
      return data;
  },

  async batchUpdatePhotos(photoIds: string[], action: 'move_to_album' | 'delete', targetAlbumId?: string) {
    await api.post('/api/photos/batch', {
      photo_ids: photoIds,
      action,
      target_album_id: targetAlbumId
    });
  }
};
