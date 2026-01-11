import type { Photo } from './album'

export interface Location {
  name: string
  level: 'city' | 'province' | 'district' | 'scene'
  count: number
  cover: Photo | null
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
