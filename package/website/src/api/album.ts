import axios from 'axios';
import type { ApiAlbum, Album, CreateAlbumDto, Photo, PhotoMetadata, TimelineStats, PhotoGroup } from '@/types/album';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '';

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000, // Default timeout 30s
});

export const albumService = {
  // Albums
  async getAlbums() {
    const { data } = await api.get<ApiAlbum[]>('/api/albums');
    return data;
  },
  async getAlbum(id: string) {
    const { data } = await api.get<ApiAlbum>(`/api/albums/${id}`);
    return data;
  },
  async createAlbum(album: CreateAlbumDto) {
    const { data } = await api.post<ApiAlbum>('/api/albums', album);
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
  async getAllPhotos(skip: number = 0, limit: number = 100, filters?: { start_time?: string, end_time?: string, city?: string, tag?: string}) {
    const { data } = await api.get<Photo[]>('/api/photos', {
      params: { skip, limit, ...filters }
    });
    return data;
  },

  async getPhotosByIds(ids: string[]) {
    // Chunk requests to avoid URL length limits
    const chunks = [];
    const chunkSize = 40; // Conservative chunk size
    for (let i = 0; i < ids.length; i += chunkSize) {
        chunks.push(ids.slice(i, i + chunkSize));
    }
    
    const results = await Promise.all(chunks.map(async chunk => {
        const { data } = await api.get<Photo[]>('/api/photos', {
          params: { ids: chunk },
          paramsSerializer: params => {
            const p = new URLSearchParams();
            if (params.ids && Array.isArray(params.ids)) {
                params.ids.forEach((id: string) => p.append('ids', id));
            }
            return p.toString();
          }
        });
        return data;
    }));
    return results.flat();
  },

  async getPhotos(albumId: string, skip: number = 0, limit: number = 100, filters?: { start_time?: string, end_time?: string }) {
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
    const { data } = await api.post<Photo>('/api/medias', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
    });
    return data;
  },

  // Chunk Upload
  async initUpload() {
      const { data } = await api.post<{upload_id: string}>('/api/medias/upload/init');
      return data.upload_id;
  },

  async uploadChunk(uploadId: string, chunkIndex: number, chunk: Blob) {
      const formData = new FormData();
      formData.append('upload_id', uploadId);
      formData.append('chunk_index', chunkIndex.toString());
      formData.append('file', chunk);
      await api.post('/api/medias/upload/chunk', formData);
  },

  async finishUpload(uploadId: string, fileName: string, albumId?: string) {
      const formData = new FormData();
      formData.append('upload_id', uploadId);
      formData.append('file_name', fileName);
      if (albumId) {
          formData.append('album_id', albumId);
      }
      const { data } = await api.post<Photo>('/api/medias/upload/finish', formData);
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
  },

  // Tags
  async getPhotoTags(photoId: string) {
    const { data } = await api.get<{id: string, tag_name: string, confidence: number}[]>(`/api/photos/${photoId}/tags`);
    return data;
  },

  async addPhotoTag(photoId: string, tagName: string, confidence: number = 1.0) {
    const { data } = await api.post<{id: string, tag_name: string, confidence: number}>(`/api/photos/${photoId}/tags`, {
      tag_name: tagName,
      confidence
    });
    return data;
  },

  async deletePhotoTag(photoId: string, tagId: string) {
    await api.delete(`/api/photos/${photoId}/tags/${tagId}`);
  }
};
