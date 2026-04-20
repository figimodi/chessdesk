import axios, { type AxiosInstance } from 'axios'

const baseURL = import.meta.env.VITE_API_URL ?? 'http://localhost:8010'

export const customAxios: AxiosInstance = axios.create({ baseURL })
