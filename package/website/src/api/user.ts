import request from '@/utils/request';

export interface User {
  id: string
  username: string
  email: string
  is_active: boolean
  is_superuser: boolean
}

export const userService = {
  async getUsers()  {
    const data = await request.get<User[]>('/api/users/')
    return data
  },

  async getCurrentUser() {
    const data = await request.get<User>('/api/users/me')
    return data
  },

  async deleteUser(userId: string) {
    const data = await request.delete<User>(`/api/users/${userId}`)
    return data
  }
}


