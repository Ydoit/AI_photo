import axios from 'axios'
import type { FaceIdentity } from '@/types/album'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || ''
const api = axios.create({ baseURL: API_BASE_URL })

export const faceApi = {
  async listIdentities(page = 1, limit = 20) {
    const { data } = await api.get<FaceIdentity[]>('/api/faces/identities', {
      params: { page, limit }
    })
    return data
  },

  async getIdentityPhotos(id: string, page = 1, limit = 50) {
    // Return photos structure
    // We might need to define Photo interface if not available, or reuse existing
    const { data } = await api.get<any[]>(`/api/faces/identities/${id}/photos`, {
      params: { page, limit }
    })
    return data
  },

  async deleteIdentity(id: string) {
    const { data } = await api.delete(`/api/faces/identities/${id}`)
    return data
  },

  async renameIdentity(id: string, name: string) {
    const { data } = await api.put(`/api/faces/identities/${id}/name`, { name })
    return data
  },

  async mergeIdentities(targetId: string, sourceIds: string[]) {
    const { data } = await api.post('/api/faces/identities/merge', {
      target_id: targetId,
      source_ids: sourceIds
    })
    return data
  },

  async removePhotos(identityId: string, photoIds: string[]) {
    const { data } = await api.post(`/api/faces/identities/${identityId}/remove-photos`, {
      photo_ids: photoIds
    })
    return data
  },

  async setCover(identityId: string, photoId: string) {
    const { data } = await api.put(`/api/faces/identities/${identityId}/cover`, {
      photo_id: photoId
    })
    return data
  }
}
