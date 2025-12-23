import type { Photo } from './album'

export interface Location {
  name: string
  level: 'city' | 'province'
  count: number
  cover: Photo | null
}
