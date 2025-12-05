import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { format } from 'date-fns'

export interface AlbumImage {
  id: number
  url: string
  thumbnail: string
  srcset: string
  timestamp: number
  category: string
  tags: string[]
  city?: string
  location?: string
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
  // --- Mock Data Generation ---
  const categories = ['人物', '风景', '证件', '美食', '建筑', '宠物']
  const tagsPool = ['AI识别', '高清', '夜景', '人像', '自然', '街拍', '旅行', '快乐']
  const cities = ['北京', '上海', '广州', '深圳', '成都', '杭州', '西安', '重庆', '南京', '武汉', '厦门', '青岛', '大理', '丽江', '三亚', '拉萨', '苏州', '长沙', '天津', '郑州', '昆明', '福州']
  const locations = ['市中心', '老街', '公园', '海边', '山顶', '博物馆', '艺术区', '古镇', '夜市', '大剧院', '体育馆', '植物园', '动物园', '游乐园', '大学城']

  const generateImages = (count: number): AlbumImage[] => {
    return Array.from({ length: count }).map((_, i) => {
      const id = i + 1
      const category = categories[Math.floor(Math.random() * categories.length)]
      const randomTags = [category, tagsPool[Math.floor(Math.random() * tagsPool.length)]]
      const baseUrl = `https://picsum.photos/id/${(id % 100) + 10}` // Use mod to avoid invalid IDs
      const city = cities[Math.floor(Math.random() * cities.length)]
      const location = locations[Math.floor(Math.random() * locations.length)]
      
      // Generate timestamp: 40% from current year, 30% last year, 30% 2-3 years ago
      const now = Date.now()
      const year = new Date().getFullYear()
      const r = Math.random()
      let timestamp
      
      if (r < 0.4) {
        // Current year
        timestamp = new Date(year, Math.floor(Math.random() * 12), Math.floor(Math.random() * 28)).getTime()
      } else if (r < 0.7) {
        // Last year
        timestamp = new Date(year - 1, Math.floor(Math.random() * 12), Math.floor(Math.random() * 28)).getTime()
      } else {
        // 2-3 years ago
        timestamp = new Date(year - 2 - Math.floor(Math.random() * 2), Math.floor(Math.random() * 12), Math.floor(Math.random() * 28)).getTime()
      }

      return {
        id,
        url: `${baseUrl}/1200/800.webp`,
        thumbnail: `${baseUrl}/400/300.webp`,
        srcset: `${baseUrl}/400/300.webp 1x, ${baseUrl}/800/600.webp 2x`,
        timestamp,
        category,
        tags: [...new Set(randomTags)],
        city,
        location: `${city}·${location}`
      }
    })
  }

  // --- State ---
  const images = ref<AlbumImage[]>(generateImages(300))
  const customAlbums = ref<Map<string, { title: string, photoIds: number[], createdAt: number }>>(new Map())

  // Initialize some custom albums
  if (customAlbums.value.size === 0) {
    customAlbums.value.set('fav-1', {
      title: '我的收藏',
      photoIds: [1, 2, 3, 4, 5],
      createdAt: Date.now()
    })
    customAlbums.value.set('trip-2023', {
      title: '2023毕业旅行',
      photoIds: [10, 11, 12, 20, 21],
      createdAt: Date.now() - 1000000000
    })
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

  // 2. Custom Albums (User managed)
  const userAlbums = computed<Album[]>(() => {
    return Array.from(customAlbums.value.entries()).map(([id, data]) => {
      const photos = images.value.filter(img => data.photoIds.includes(img.id))
      const cover = photos.length > 0 ? photos[0].thumbnail : 'https://placehold.co/400x300?text=Empty'
      return {
        id,
        title: data.title,
        type: 'custom',
        cover,
        count: photos.length,
        description: `${photos.length}张照片`,
        createdAt: data.createdAt
      }
    })
  })

  const allAlbums = computed(() => [...conditionalAlbums.value, ...userAlbums.value])

  // --- Actions ---
  const addPhoto = (photo: AlbumImage) => {
    images.value.unshift(photo)
  }

  const addPhotoToAlbum = (albumId: string, photoId: number) => {
    if (customAlbums.value.has(albumId)) {
      const album = customAlbums.value.get(albumId)!
      if (!album.photoIds.includes(photoId)) {
        album.photoIds.unshift(photoId)
      }
    }
  }

  const removePhotoFromAlbum = (albumId: string, photoId: number) => {
    if (customAlbums.value.has(albumId)) {
      const album = customAlbums.value.get(albumId)!
      album.photoIds = album.photoIds.filter(id => id !== photoId)
    }
  }

  const createCustomAlbum = (title: string) => {
    const id = `custom-${Date.now()}`
    customAlbums.value.set(id, {
      title,
      photoIds: [],
      createdAt: Date.now()
    })
    return id
  }

  const deleteCustomAlbum = (albumId: string) => {
    if (customAlbums.value.has(albumId)) {
      customAlbums.value.delete(albumId)
    }
  }

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
    if (customAlbums.value.has(albumId)) {
      const albumData = customAlbums.value.get(albumId)!
      return images.value.filter(img => albumData.photoIds.includes(img.id))
    }
    return [] // Default or unknown
  }
  
  const getAlbumDetails = (albumId: string): Album | undefined => {
    return allAlbums.value.find(a => a.id === albumId)
  }

  return {
    images,
    allAlbums,
    conditionalAlbums,
    userAlbums,
    addPhoto,
    addPhotoToAlbum,
    removePhotoFromAlbum,
    createCustomAlbum,
    deleteCustomAlbum,
    getPhotosByAlbumId,
    getAlbumDetails
  }
})
