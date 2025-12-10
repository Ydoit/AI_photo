// src/types/album.ts
// 定义相册相关的类型

export enum FileType {
  Image = 'image',
  Video = 'video',
  LivePhoto = 'live_photo'
}

export interface PhotoMetadata {
  photo_id: string;
  exif_info?: string;
  location?: any;
  location_api?: string;
  tags?: string[];
  faces?: any[];
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
  metadata_info?: PhotoMetadata;
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

export interface Album {
  id: string;
  name: string;
  create_time: string;
  description?: string;
  cover?: Photo;
  type: string;
  num_photos: number;
  photos?: Photo[];
}

export interface CreateAlbumDto {
  name: string;
  description?: string;
}