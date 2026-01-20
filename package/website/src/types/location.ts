import type { Photo } from './album'

export interface Location {
  id?: string
  is_custom?: boolean
  name: string
  level: 'city' | 'province' | 'district' | 'scene'
  count: number
  cover: Photo | null
}

export interface LocationStatistics {
  province_count: number
  city_count: number
  district_count: number
  country_count: number
}

export interface Scene {
  id: string
  name: string
  description?: string
  level?: number
  address?: string
  latitude?: number
  longitude?: number
  radius?: number
  polygon?: number[][]
  is_custom?: boolean
}

export interface SceneCreate {
  name: string
  description?: string
  level?: number
  address?: string
  latitude?: number
  longitude?: number
  radius?: number
  polygon?: number[][]
}

export interface SceneUpdate extends SceneCreate {}
