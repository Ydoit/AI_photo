import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { format } from 'date-fns'
import { albumService } from '@/api/album'
import type { Photo, Album as ApiAlbum } from '@/types/album'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

export interface AlbumImage {
  id: string
  url: string
  thumbnail: string
  srcset: string
  timestamp: number
  category: string
  tags: string[]
  city?: string
  location?: string
  albumId: string
  width?: number
  height?: number
}

export interface Album {
  id: string
  title: string
  type: 'conditional' | 'custom'
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

  // --- Helpers ---
  const mapPhotoToImage = (photo: Photo): AlbumImage => {
    // Normalize path separator for URL
    const normalizedPath = photo.file_path.replace(/\\/g, '/');
    const url = `${API_BASE_URL}/${normalizedPath}`;
    // Thumbnail: check if exists, else use original
    // Backend thumbnail logic: uploads/thumbnails/{uuid}.jpg
    const thumbnail = `${API_BASE_URL}/uploads/thumbnails/${photo.id}.jpg`;
    
    // Metadata extraction
    const metadata = photo.metadata_info;
    const timestamp = photo.upload_time ? new Date(photo.upload_time).getTime() : Date.now();
    
    // Try to get city from location or tags
    let city = 'Unknown';
    if (metadata && metadata.location) {
        // If location is string, try to parse city
        if (typeof metadata.location === 'string') {
             // Simple heuristic or just use full string
             city = metadata.location.split('·')[0] || metadata.location;
        }
    }
    
    const tags = metadata?.tags || [];
    const category = tags.length > 0 ? tags[0] : 'Uncategorized';

    return {
      id: photo.id,
      url,
      thumbnail, // Ideally check if thumbnail exists, but for now assume yes or fallback
      srcset: `${thumbnail} 400w, ${url} 1200w`, // Simple srcset
      timestamp,
      category,
      tags,
      city: city !== 'Unknown' ? city : undefined,
      location: metadata && typeof metadata.location === 'string' ? metadata.location : undefined,
      albumId: photo.album_id || '',
      width: photo.width,
      height: photo.height
    }
  }

  // --- Actions ---
  const fetchAlbums = async () => {
      try {
          const albumsData = await albumService.getAlbums();
          apiAlbums.value = albumsData;
      } catch (error) {
          console.error("Failed to fetch albums", error);
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
        
        if (albumId.startsWith('city-')) {
            const city = albumId.replace('city-', '');
            photosData = await albumService.getAllPhotos(skip.value, limit, { city });
        } else if (albumId.startsWith('year-')) {
            const year = albumId.replace('year-', '');
            photosData = await albumService.getAllPhotos(skip.value, limit, { year });
        } else if (albumId.startsWith('cat-')) {
            const cat = albumId.replace('cat-', '');
            photosData = await albumService.getAllPhotos(skip.value, limit, { tag: cat });
        } else {
            photosData = await albumService.getPhotos(albumId, skip.value, limit);
        }
        
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

  // Keep fetchAllData for backward compatibility or initial load if needed
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

  const deleteCustomAlbum = async (albumId: string) => {
      await albumService.deleteAlbum(albumId);
      apiAlbums.value = apiAlbums.value.filter(a => a.id !== albumId);
  }

  const addPhotoToAlbum = async (albumId: string, file: File) => {
      const photo = await albumService.uploadPhoto(file, albumId);
      // Only add to local state if we are viewing all photos or this specific album
      if (currentContext.value.type === 'all' || (currentContext.value.type === 'album' && currentContext.value.id === albumId)) {
          images.value.unshift(mapPhotoToImage(photo));
      }
  }

  const deletePhoto = async (photoId: string) => {
      const photo = images.value.find(p => p.id === photoId);
      if (photo) {
          await albumService.deletePhoto(photo.albumId, photoId);
          images.value = images.value.filter(p => p.id !== photoId);
      }
  }

  // --- Computed Albums ---
  
  // 1. Conditional Albums (Auto-generated)
  const conditionalAlbums = computed<Album[]>(() => {
    const albums: Album[] = []
    
    // By City
    const cityGroups: Record<string, AlbumImage[]> = {}
    images.value.forEach(img => {
      if (img.city) {
        if (!cityGroups[img.city]) cityGroups[img.city] = []
        cityGroups[img.city].push(img)
      }
    })
    
    Object.entries(cityGroups).forEach(([city, photos]) => {
      if (photos.length > 0) {
        albums.push({
          id: `city-${city}`,
          title: city,
          type: 'conditional',
          cover: photos[0].thumbnail,
          count: photos.length,
          description: `${city}的足迹`,
          createdAt: photos[0].timestamp
        })
      }
    })

    // By Year
    const yearGroups: Record<string, AlbumImage[]> = {}
    images.value.forEach(img => {
      const year = format(new Date(img.timestamp), 'yyyy')
      if (!yearGroups[year]) yearGroups[year] = []
      yearGroups[year].push(img)
    })

    Object.entries(yearGroups).forEach(([year, photos]) => {
      if (photos.length > 0) {
        albums.push({
          id: `year-${year}`,
          title: `${year}年`,
          type: 'conditional',
          cover: photos[0].thumbnail,
          count: photos.length,
          description: `${year}年的回忆`,
          createdAt: photos[0].timestamp
        })
      }
    })

    // By Category
    const categoryGroups: Record<string, AlbumImage[]> = {}
    images.value.forEach(img => {
      if (!categoryGroups[img.category]) categoryGroups[img.category] = []
      categoryGroups[img.category].push(img)
    })

    Object.entries(categoryGroups).forEach(([cat, photos]) => {
       if (photos.length > 0) {
        albums.push({
          id: `cat-${cat}`,
          title: cat,
          type: 'conditional',
          cover: photos[0].thumbnail,
          count: photos.length,
          description: `${cat}精选`,
          createdAt: photos[0].timestamp
        })
      }
    })

    return albums
  })

  // 2. Custom Albums (Synced with Backend)
  const userAlbums = computed<Album[]>(() => {
    return apiAlbums.value.map(album => {
      // Count photos in this album
      // Note: If paginated, this count is only loaded photos. 
      // Ideal: backend returns count. For now, we use loaded.
      const photos = images.value.filter(img => img.albumId === album.id);
      const cover = photos.length > 0 ? photos[0].thumbnail : 'https://placehold.co/400x300?text=Empty';
      
      return {
        id: album.id,
        title: album.name,
        type: 'custom',
        cover,
        count: photos.length,
        description: album.description || `${photos.length}张照片(已加载)`,
        createdAt: new Date(album.create_time).getTime()
      }
    })
  })

  const allAlbums = computed(() => [...conditionalAlbums.value, ...userAlbums.value])

  // --- Getters ---
  const getPhotosByAlbumId = (albumId: string): AlbumImage[] => {
    if (albumId.startsWith('city-')) {
      const city = albumId.replace('city-', '')
      return images.value.filter(img => img.city === city)
    }
    if (albumId.startsWith('year-')) {
      const year = albumId.replace('year-', '')
      return images.value.filter(img => format(new Date(img.timestamp), 'yyyy') === year)
    }
    if (albumId.startsWith('cat-')) {
      const cat = albumId.replace('cat-', '')
      return images.value.filter(img => img.category === cat)
    }
    
    // Custom Album (UUID)
    if (currentContext.value.type === 'album' && currentContext.value.id === albumId) {
        return images.value;
    }
    
    return images.value.filter(img => img.albumId === albumId)
  }
  
  const getAlbumDetails = (albumId: string): Album | undefined => {
    return allAlbums.value.find(a => a.id === albumId)
  }

  const deleteAlbum = async (albumId: string) => {
    await albumService.deleteAlbum(albumId);
    apiAlbums.value = apiAlbums.value.filter(a => a.id !== albumId);
  }

  return {
    images,
    loading,
    hasMore,
    allAlbums,
    conditionalAlbums,
    userAlbums,
    fetchAllData,
    fetchAlbums,
    loadPhotos,
    loadAlbumPhotos,
    createCustomAlbum,
    deleteCustomAlbum,
    addPhotoToAlbum,
    getPhotosByAlbumId,
    getAlbumDetails,
    deletePhoto,
    deleteAlbum
  }
})
