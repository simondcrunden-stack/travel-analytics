import api from './api'

export default {
  async login(username, password) {
    const response = await api.post('/auth/login/', {
      username,
      password,
    })
    return response.data
  },

  async getCurrentUser() {
    const response = await api.get('/users/me/')
    return response.data
  },

  logout() {
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    localStorage.removeItem('user')
  },
}
