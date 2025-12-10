import axios from 'axios';
import type { Album, CreateAlbumDto, Photo, PhotoMetadata, TimelineStats, PhotoGroup } from '@/types/album';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '';

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
  async setAlbumCover(id: string, photoId: string) {
    const { data } = await api.put<Album>(`/api/albums/${id}/cover`, { photo_id: photoId })
    return data
  },
  async deleteAlbum(id: string) {
    await api.delete(`/api/albums/${id}`);
  },

  // Stats
  async getTimelineStats(albumId?: string) {
    const { data } = await api.get<TimelineStats>('/api/stats/timeline', {
      params: { album_id: albumId }
    });
    return data;
  },

  // Photos
  async getAllPhotos(skip: number = 0, limit: number = 100, filters?: { year?: string, month?: string, day?: string, city?: string, tag?: string}) {
    const { data } = await api.get<Photo[]>('/api/photos', {
      params: { skip, limit, ...filters }
    });
    return data;
  },

  async getPhotos(albumId: string, skip: number = 0, limit: number = 100, filters?: { year?: string, month?: string, day?: string }) {
    const { data } = await api.get<Photo[]>(`/api/albums/${albumId}/photos`, {
      params: { skip, limit, ...filters }
    });
    return data;
  },
  
  // Remove photo from specific album (Association)
  async removePhotoFromAlbum(albumId: string, photoId: string) {
    await api.delete(`/api/albums/${albumId}/photos/${photoId}`);
  },

  // Delete photo globally
  async deletePhoto(photoId: string) {
    await api.delete(`/api/photos/${photoId}`);
  },

  // Batch Update
  async batchUpdatePhotos(data: { photo_ids: string[], action: 'add_tags' | 'remove_tags' | 'add_to_album' | 'remove_from_album' | 'delete', album_id?: string }) {
      const { data: res } = await api.post<{count: number}>('/api/photos/batch', data);
      return res;
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
  // Note: Using the generic endpoint if available or falling back to album-specific
  // Ideally backend should provide /api/photos/{id}/metadata
  async getMetadata(albumId: string | undefined, photoId: string) {
      const url = albumId 
        ? `/api/albums/${albumId}/photos/${photoId}/metadata`
        : `/api/photos/${photoId}/metadata`; // Assuming this exists or will exist
      const { data } = await api.get<PhotoMetadata>(url);
      return data;
  },

  async updateMetadata(albumId: string | undefined, photoId: string, metadata: Partial<PhotoMetadata>) {
      const url = albumId
        ? `/api/albums/${albumId}/photos/${photoId}/metadata`
        : `/api/photos/${photoId}/metadata`;
      const { data } = await api.put<PhotoMetadata>(url, metadata);
      return data;
  },

  async getThumbnail(photoId: string) {
    const { data } = await api.get<{ thumbnail: string }>(`/api/medias/${photoId}/thumbnail`);
  }
};
