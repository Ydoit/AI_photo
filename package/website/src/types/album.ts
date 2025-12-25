// src/types/album.ts
// 定义相册相关的类型

export enum FileType {
  Image = 'image',
  Video = 'video',
  LivePhoto = 'live_photo'
}

export interface Tag {
  id: string;
  tag_name: string;
  confidence: number;
}

export interface PhotoMetadata {
  photo_id: string;
  exif_info?: string;
  location?: any;
  address?: string;
  albums?: Album[];
  faces_identities?: FaceIdentity[];
  country?: string;
  province?: string;
  city?: string;
  district?: string;
  latitude?: number;
  longitude?: number;
  tags?: Tag[];
}

export interface Photo {
  id: string;
  album_ids?: string[];
  filename?: string;
  photo_time?: string;
  // file_path: string; // Deprecated/Excluded
  url: string;
  thumbnail_url: string;
  file_type: FileType;
  upload_time: string;
  size: number;
  width?: number;
  height?: number;
  duration?: number;
}

export interface PhotoGroup {
  date: string;
  items: Photo[];
}

export interface TimelineItem {
  year: number;
  month: number;
  day: number;
  count: number;
}

export interface TimelineStats {
  total_photos: number;
  time_range: {
    start: string | null;
    end: string | null;
  };
  timeline: TimelineItem[];
}

export interface AlbumImage {
  id: string
  url: string
  thumbnail: string
  preview: string
  srcset: string
  timestamp: number
  albumIds: string[]
  width?: number
  height?: number
  size?: number
  filename?: string
  file_type: 'image' | 'video' | 'live_photo'
  duration?: string
}

export interface ApiAlbum {
  id: string;
  name: string;
  create_time: string;
  description?: string;
  cover?: Photo;
  type: string;
  num_photos: number;
  photos?: Photo[];
}

export interface Album {
  id: string
  title: string
  name: string
  type: string
  cover: AlbumImage
  count: number
  description?: string
  createdAt: number
}

export interface CreateAlbumDto {
  name: string;
  description?: string;
}

export interface CoverPhotoInfo {
  photo_id: string
  width: number | null
  height: number | null
  face_rect: number[] | null
}

export interface FaceIdentity {
  id: string
  identity_name: string
  default_face_id: number | null
  face_count: number
  cover_photo: CoverPhotoInfo | null
  cover: Photo | null
}