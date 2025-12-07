import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { format } from 'date-fns'
import { albumService } from '@/api/album'
import type { Photo, Album as ApiAlbum } from '@/types/album'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '';

export interface AlbumImage {
  id: string
  url: string
  thumbnail: string
  srcset: string
  timestamp: number
  category: string
  tags: string[]
  city?: string
  location?: any
  albumIds: string[]
  width?: number
  height?: number
  filename?: string
  file_type: 'image' | 'video' | 'live_photo'
}

export interface Album {
  id: string
  title: string
  type: string
  cover: string
  count: number
  description?: string
  createdAt: number
}

export const useAlbumStore = defineStore('album', () => {
  // --- State ---
  const images = ref<AlbumImage[]>([])
  const apiAlbums = ref<ApiAlbum[]>([])
  const loading = ref(false)
  // Pagination State
  const limit = 50
  const skip = ref(0)
  const hasMore = ref(true)
  const currentContext = ref<{ type: 'all' | 'album', id?: string }>({ type: 'all' })
  const timelineStats = ref<any>(null)

  // --- Helpers ---
  const mapPhotoToImage = (photo: Photo): AlbumImage => {
    // New API returns relative URLs in url and thumbnail_url fields
    const url = `${API_BASE_URL}${photo.url}`;
    const thumbnail = `${API_BASE_URL}${photo.thumbnail_url}`;
    
    // Metadata extraction
    const metadata = photo.metadata_info;
    // Use photo_time if available, else upload_time, else now
    let timestamp = Date.now();
    if (photo.photo_time) {
        timestamp = new Date(photo.photo_time).getTime();
    } else if (photo.upload_time) {
        timestamp = new Date(photo.upload_time).getTime();
    }
    
    // Try to get city from location or tags
    let city = 'Unknown';
    if (metadata && metadata.location) {
        // If location is string, try to parse city (legacy)
        if (typeof metadata.location === 'string') {
             city = metadata.location.split('·')[0] || metadata.location;
        } else if (typeof metadata.location === 'object' && metadata.location.formatted_address) {
             // New JSON format
             city = metadata.location.formatted_address.split('·')[0] || 'Unknown';
        }
    }
    
    const tags = metadata?.tags || [];
    const category = tags.length > 0 ? tags[0] : 'Uncategorized';

    return {
      id: photo.id,
      url,
      thumbnail,
      srcset: '', // No separate sizes for now, handled by backend dynamic sizing if needed
      timestamp,
      category,
      tags,
      city: city !== 'Unknown' ? city : undefined,
      location: metadata?.location,
      albumIds: photo.album_ids || [],
      width: photo.width,
      height: photo.height,
      filename: photo.filename,
      file_type: photo.file_type
    }
  }

  // --- Actions ---
  const fetchAlbums = async () => {
      try {
          const albumsData = await albumService.getAlbums();
          apiAlbums.value = albumsData;
      } catch (e) {
          console.error("Failed to fetch albums", e)
      }
  }

  const fetchTimelineStats = async () => {
    try {
      const stats = await albumService.getTimelineStats()
      timelineStats.value = stats
    } catch (e) {
      console.error("Failed to fetch timeline stats", e)
    }
  }

  const loadPhotos = async (reset: boolean = false) => {
    if (loading.value && !reset) return;
    
    if (reset) {
        skip.value = 0;
        hasMore.value = true;
        images.value = [];
        currentContext.value = { type: 'all' };
    }

    if (!hasMore.value) return;

    loading.value = true;
    try {
        const photosData = await albumService.getAllPhotos(skip.value, limit);
        
        if (photosData.length < limit) {
            hasMore.value = false;
        }
        
        const newImages = photosData.map(mapPhotoToImage);
        if (reset) {
             images.value = newImages;
        } else {
             images.value.push(...newImages);
        }
        skip.value += limit;
        
    } catch (error) {
        console.error("Failed to fetch photos", error);
    } finally {
        loading.value = false;
    }
  }

  const loadAlbumPhotos = async (albumId: string, reset: boolean = false) => {
    if (loading.value && !reset) return;
    
    if (reset) {
        skip.value = 0;
        hasMore.value = true;
        images.value = [];
        currentContext.value = { type: 'album', id: albumId };
    }

    if (!hasMore.value) return;

    loading.value = true;
    try {
        let photosData: Photo[] = [];
        
        photosData = await albumService.getPhotos(albumId, skip.value, limit);
        
        if (photosData.length < limit) {
            hasMore.value = false;
        }
        
        const newImages = photosData.map(mapPhotoToImage);
        if (reset) {
             images.value = newImages;
        } else {
             images.value.push(...newImages);
        }
        skip.value += limit;
        
    } catch (error) {
        console.error("Failed to fetch album photos", error);
    } finally {
        loading.value = false;
    }
  }

  // Keep fetchAllData for backward compatibility
  const fetchAllData = async () => {
      await Promise.all([
          fetchAlbums(),
          loadPhotos(true)
      ]);
  }

  const createCustomAlbum = async (title: string, description?: string) => {
      const newAlbum = await albumService.createAlbum({ name: title, description: description || '' });
      apiAlbums.value.push(newAlbum);
      return newAlbum.id;
  }

  const deleteAlbum = async (albumId: string) => {
      await albumService.deleteAlbum(albumId);
      apiAlbums.value = apiAlbums.value.filter(a => a.id !== albumId);
  }

  const addPhotoToAlbum = async (albumId: string, file: File) => {
      const photo = await albumService.uploadPhoto(file, albumId);
      // If viewing this album or all photos, add to list
      if (currentContext.value.type === 'all' || (currentContext.value.type === 'album' && currentContext.value.id === albumId)) {
          images.value.unshift(mapPhotoToImage(photo));
      }
  }

  const deletePhoto = async (photoId: string) => {
      const photo = images.value.find(p => p.id === photoId);
      if (photo) {
          await albumService.deletePhoto(photoId); // Global delete
          images.value = images.value.filter(p => p.id !== photoId);
      }
  }
  
  const removePhotoFromAlbum = async (albumId: string, photoId: string) => {
      await albumService.removePhotoFromAlbum(albumId, photoId);
      if (currentContext.value.type === 'album' && currentContext.value.id === albumId) {
          images.value = images.value.filter(p => p.id !== photoId);
      }
      const photo = images.value.find(p => p.id === photoId);
      if (photo) {
          photo.albumIds = photo.albumIds.filter(id => id !== albumId);
      }
  }

  const removePhotosFromAlbum = async (albumId: string, photoIds: string[]) => {
      await albumService.batchUpdatePhotos({
          photo_ids: photoIds,
          action: 'remove_from_album',
          album_id: albumId
      });
      
      if (currentContext.value.type === 'album' && currentContext.value.id === albumId) {
          images.value = images.value.filter(p => !photoIds.includes(p.id));
      }
      
      // Update local state for all affected photos
      photoIds.forEach(id => {
          const photo = images.value.find(p => p.id === id);
          if (photo) {
              photo.albumIds = photo.albumIds.filter(aid => aid !== albumId);
          }
      });
  }

  const deletePhotos = async (photoIds: string[]) => {
      await albumService.batchUpdatePhotos({
          photo_ids: photoIds,
          action: 'delete'
      });
      images.value = images.value.filter(p => !photoIds.includes(p.id));
  }

  // --- Computed Albums ---
  const allAlbums = computed<Album[]>(() => {
    return apiAlbums.value.map(album => {
      const cover = album.cover ? `${API_BASE_URL}${album.cover.thumbnail_url}` : 'https://placehold.co/400x300?text=Empty';
      return {
        id: album.id,
        title: album.name,
        type: album.type,
        cover,
        count: album.num_photos,
        description: album.description || `${album.num_photos}张照片`,
        createdAt: new Date(album.create_time).getTime()
      }
    })
  })

  // --- Getters ---
  const getPhotosByAlbumId = (albumId: string): AlbumImage[] => {
    // Custom Album (UUID)
    if (currentContext.value.type === 'album' && currentContext.value.id === albumId) {
        return images.value;
    }
    
    return images.value.filter(img => img.albumIds.includes(albumId))
  }
  
  const getAlbumDetails = (albumId: string): Album | undefined => {
    return allAlbums.value.find(a => a.id === albumId)
  }

  const addPhotosToAlbum = async (photoIds: string[], action: 'add_to_album', targetAlbumId: string) => {
    await albumService.batchUpdatePhotos({
      photo_ids: photoIds,
      action,
      album_id: targetAlbumId
    })
  }

  return {
    images,
    loading,
    hasMore,
    allAlbums,
    fetchAllData,
    fetchAlbums,
    loadPhotos,
    loadAlbumPhotos,
    createCustomAlbum,
    deleteAlbum,
    addPhotoToAlbum,
    getPhotosByAlbumId,
    getAlbumDetails,
    deletePhoto,
    deletePhotos,
    removePhotoFromAlbum,
    removePhotosFromAlbum,
    addPhotosToAlbum,
    timelineStats,
    fetchTimelineStats
  }
})
