import axios from 'axios'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL ?? '',
  withCredentials: true, // send httpOnly refresh cookie automatically
})

// Token refresh interceptor
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const original = error.config
    if (error.response?.status === 401 && !original._retry) {
      original._retry = true
      try {
        const { data } = await api.post<{ access_token: string }>('/api/v1/auth/refresh')
        api.defaults.headers.common['Authorization'] = `Bearer ${data.access_token}`
        original.headers['Authorization'] = `Bearer ${data.access_token}`
        return api(original)
      } catch {
        // Refresh failed — let the caller handle the 401
      }
    }
    return Promise.reject(error)
  },
)

export default api
