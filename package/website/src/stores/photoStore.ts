// src/stores/photoStore.ts
// 定义照片相关的状态管理

import { defineStore } from 'pinia'
import { ref, reactive } from 'vue'
import { albumService } from '@/api/album'
import type { Photo, TimelineStats } from '@/types/album'

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

// --- 缓存工具 ---
const CACHE_PREFIX = 'trailsnap:';
const CACHE_TTL = 24 * 60 * 60 * 1000; // 24小时

interface CacheRecord<T> {
  timestamp: number;
  data: T;
}

const getLocalCache = <T>(key: string): T | null => {
  try {
    const json = localStorage.getItem(CACHE_PREFIX + key);
    if (!json) return null;
    const record = JSON.parse(json) as CacheRecord<T>;
    if (Date.now() - record.timestamp > CACHE_TTL) {
      localStorage.removeItem(CACHE_PREFIX + key);
      return null;
    }
    return record.data;
  } catch (e) {
    return null;
  }
}

const setLocalCache = <T>(key: string, data: T) => {
  try {
    const record: CacheRecord<T> = {
      timestamp: Date.now(),
      data
    };
    localStorage.setItem(CACHE_PREFIX + key, JSON.stringify(record));
  } catch (e) {
    // QuotaExceededError
    if (e instanceof DOMException && e.name === 'QuotaExceededError') {
       try {
           // 清理所有相关缓存
           Object.keys(localStorage).forEach(k => {
               if (k.startsWith(CACHE_PREFIX)) localStorage.removeItem(k);
           });
           // 重试一次
           const recordToStore: CacheRecord<T> = {
               timestamp: Date.now(),
               data
           };
           localStorage.setItem(CACHE_PREFIX + key, JSON.stringify(recordToStore));
       } catch (retryErr) {
           console.warn('缓存写入失败', retryErr);
       }
    }
  }
}

export const usePhotoStore = defineStore('photo', () => {
  // --- 状态 ---
  const images = ref<AlbumImage[]>([])
  const loading = ref(false)
  const hasMore = ref(true)
  const currentContext = ref<{ type: 'all' | 'album', id?: string }>({ type: 'all' })
  const timelineStats = ref<TimelineStats>()

  // --- 辅助函数 ---
  const mapPhotoToImage = (photo: Photo): AlbumImage => {
    // 新 API 在 url 和 thumbnail_url 字段中返回相对地址
    const url = `${API_BASE_URL}${photo.url}`;
    const thumbnail = `${API_BASE_URL}${photo.thumbnail_url}`;
    
    // 提取元数据
    const metadata = photo.metadata_info;
    // 优先使用 photo_time，其次 upload_time，最后取当前时间
    let timestamp = Date.now();
    if (photo.photo_time) {
        timestamp = new Date(photo.photo_time).getTime();
    } else if (photo.upload_time) {
        timestamp = new Date(photo.upload_time).getTime();
    }
    
    // 尝试从 location 或 tags 中解析城市
    let city = 'Unknown';
    if (metadata && metadata.location) {
        // 如果 location 是字符串，尝试解析城市（兼容旧格式）
        if (typeof metadata.location === 'string') {
             city = metadata.location.split('·')[0] || metadata.location;
        } else if (typeof metadata.location === 'object' && metadata.location.formatted_address) {
             // 新 JSON 格式
             city = metadata.location.formatted_address.split('·')[0] || 'Unknown';
        }
    }
    
    const tags = metadata?.tags || [];
    const category = tags.length > 0 ? tags[0] : 'Uncategorized';

    return {
      id: photo.id,
      url,
      thumbnail,
      srcset: '', // 暂不分发多尺寸，后端按需动态处理
      timestamp,
      category,
      tags,
      city: city !== 'Unknown' ? city : undefined,
      location: metadata?.location,
      albumIds: photo.album_ids || [],
      width: photo.width || 300,
      height: photo.height || 300,
      filename: photo.filename || '',
      file_type: photo.file_type
    }
  }

  // --- 动作 ---
  const fetchTimelineStats = async (albumId?: string) => {
    try {
      const stats = await albumService.getTimelineStats(albumId)
      timelineStats.value = stats
    } catch (e) {
      console.error("获取时间轴统计失败", e)
    }
  }

  const activeOffsets = new Set<number>();
  const loadedDates = reactive(new Set<string>());
  const photoOffsetMap = reactive(new Map<number, AlbumImage>());

  // 追踪活跃请求以支持取消
  let currentRequestId = 0;
  const activeRequests = new Map<number, AbortController>();

  const getOffsetRangeForMonth = (year: number, month: number): { start: number, count: number } | null => {
      if (!timelineStats.value?.timeline) return null;

      // Sort timeline to match gallery order
      const sortedTimeline = [...timelineStats.value.timeline].sort((a, b) => {
          if (a.year !== b.year) return b.year - a.year;
          if (a.month !== b.month) return b.month - a.month;
          return b.day - a.day;
      });

      let currentOffset = 0;
      let startOffset = -1;
      let totalCount = 0;

      for (const item of sortedTimeline) {
          if (item.year === year && item.month === month) {
              if (startOffset === -1) startOffset = currentOffset;
              totalCount += item.count;
          }
          currentOffset += item.count;
      }

      if (startOffset !== -1) {
          return { start: startOffset, count: totalCount };
      }
      return null;
  }

  const pruneCache = (centerOffset: number) => {
      const KEEP_RADIUS = 300; // 保留中心前后 300 张
      const min = centerOffset - KEEP_RADIUS;
      const max = centerOffset + KEEP_RADIUS;
      // 清理 Map
      for (const key of photoOffsetMap.keys()) {
          if (key < min || key > max) {
              photoOffsetMap.delete(key);
          }
      }
  }

  const loadPhotosByMonth = async (year: number, month: number, albumId?: string, refresh = false) => {
    const dateKey = `${year}-${String(month).padStart(2, '0')}`;
    // Check if already loaded or loading
    if (loadedDates.has(dateKey) && !refresh) return;

    // Get offset info for the whole month
    const offsetInfo = getOffsetRangeForMonth(year, month);
    if (!offsetInfo || offsetInfo.count === 0) return;

    const processPhotos = (photos: Photo[]) => {
        const newImages = photos.map(mapPhotoToImage);

        // Populate PhotoOffsetMap
        newImages.forEach((img, index) => {
            photoOffsetMap.set(offsetInfo.start + index, img);
        });

        // Sync main list
        const existingIds = new Set(images.value.map(i => i.id));
        const toAdd = newImages.filter(i => !existingIds.has(i.id));

        if (toAdd.length > 0) {
            images.value.push(...toAdd);
            images.value.sort((a, b) => b.timestamp - a.timestamp);
        }
        // Prune cache around the loaded area
        pruneCache(offsetInfo.start + offsetInfo.count / 2);
    };

    loading.value = true;
    loadedDates.add(dateKey);

    const requestId = ++currentRequestId;
    const controller = new AbortController();
    activeRequests.set(requestId, controller);

    try {
        let photosData: Photo[] = [];
        const filters = { year: String(year), month: String(month) };
        const count = offsetInfo.count;

        if (albumId) {
             photosData = await albumService.getPhotos(albumId, 0, count, filters);
        } else {
             photosData = await albumService.getAllPhotos(0, count, filters);
        }

        if (!activeRequests.has(requestId)) {
            loadedDates.delete(dateKey); 
            return;
        }
        processPhotos(photosData);

    } catch (error) {
        loadedDates.delete(dateKey);
        if (error instanceof Error && error.name === 'AbortError') {
           console.log('请求已取消');
        } else {
           console.error("按月获取照片失败", error);
        }
    } finally {
        activeRequests.delete(requestId);
        if (activeRequests.size === 0) {
            loading.value = false;
        }
    }
  }

  const cancelAllPendingLoads = () => {
      activeRequests.forEach(controller => controller.abort());
      activeRequests.clear();
      activeOffsets.clear();
      loading.value = false;
  }

  const loadPhotos = async (reset: boolean = false) => {
      // Placeholder if needed, but loadPhotosByMonth is the main driver now
      if (reset) {
          images.value = [];
          photoOffsetMap.clear();
          loadedDates.clear();
          currentContext.value = { type: 'all' };
      }
      await fetchTimelineStats();
      // Logic to load initial view could go here
  }

  const loadAlbumPhotos = async (albumId: string, reset: boolean = false) => {
      if (reset) {
          images.value = [];
          photoOffsetMap.clear();
          loadedDates.clear();
      }
      currentContext.value = { type: 'album', id: albumId };
      await fetchTimelineStats(albumId);
  }

  const removeLocalPhoto = (photoId: string) => {
      images.value = images.value.filter(img => img.id !== photoId);
      // Clean map
      for (const [key, val] of photoOffsetMap.entries()) {
          if (val.id === photoId) {
              photoOffsetMap.delete(key);
          }
      }
  }

  const deletePhoto = async (photoId: string) => {
      await deletePhotos([photoId])
  }

  const deletePhotos = async (photoIds: string[]) => {
      await albumService.batchUpdatePhotos({
          photo_ids: photoIds,
          action: 'delete'
      });
      // Remove locally
      images.value = images.value.filter(img => !photoIds.includes(img.id));
      // Also update map
      for (const [key, val] of photoOffsetMap.entries()) {
          if (photoIds.includes(val.id)) {
              photoOffsetMap.delete(key);
          }
      }
  }
  const resetAll = () => {
      timelineStats.value = { total_photos: 0, time_range: {start: null, end: null}, timeline: [] };
      images.value = [];
      photoOffsetMap.clear();
      loadedDates.clear();
      currentContext.value = { type: 'all' };
  }

  return {
    images,
    loading,
    hasMore,
    currentContext,
    timelineStats,
    photoOffsetMap,
    fetchTimelineStats,
    loadPhotos,
    loadAlbumPhotos,
    loadPhotosByMonth,
    removeLocalPhoto,
    deletePhoto,
    deletePhotos,
    cancelAllPendingLoads,
    resetAll
  }
})
