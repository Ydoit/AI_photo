export enum FileType {
  Image = 'image',
  Video = 'video',
  LivePhoto = 'live_photo'
}

export interface PhotoMetadata {
  photo_id: string;
  camera_info?: string;
  location?: any;
  tags?: any[];
  faces?: any[];
}

export interface Photo {
  id: string;
  album_id?: string;
  file_path: string;
  file_type: FileType;
  upload_time: string;
  size: number;
  width?: number;
  height?: number;
  metadata_info?: PhotoMetadata;
}

export interface Album {
  id: string;
  name: string;
  create_time: string;
  description?: string;
  photos?: Photo[];
}

export interface CreateAlbumDto {
  name: string;
  description?: string;
}
