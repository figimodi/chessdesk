import axios, { type AxiosInstance } from 'axios'
import { clearStoredAccessToken, getStoredAccessToken } from '@/auth/storage'

const baseURL = import.meta.env.VITE_API_URL ?? 'http://localhost:8010'

export const customAxios: AxiosInstance = axios.create({ baseURL })

customAxios.interceptors.request.use((config) => {
  const token = getStoredAccessToken()
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

customAxios.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      clearStoredAccessToken()
    }
    return Promise.reject(error)
  },
)
