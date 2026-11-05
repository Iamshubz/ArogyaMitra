import axios from 'axios'

export const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '',
  timeout: 8000,
})

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('arogyamitra_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

export type HealthStatus = {
  status: string
  database: string
}

export type AuthUser = {
  id: number
  full_name: string
  email: string
  phone_number: string | null
  role: 'patient' | 'healthcare_worker' | 'admin'
  is_active: boolean
  preferred_language: { code: string; name: string }
  age: number | null
  facility_name: string | null
  specialization: string | null
}

type AuthResponse = {
  access_token: string
  token_type: string
  user: AuthUser
}

export async function getHealthStatus(): Promise<HealthStatus> {
  const response = await api.get<HealthStatus>('/api/v1/health')
  return response.data
}

export async function registerAccount(payload: {
  full_name: string
  email: string
  password: string
  phone_number?: string
  age?: number
  preferred_language: string
  role: 'patient' | 'healthcare_worker'
}): Promise<AuthResponse> {
  const response = await api.post<AuthResponse>('/api/v1/auth/register', payload)
  return response.data
}

export async function loginAccount(email: string, password: string): Promise<AuthResponse> {
  const response = await api.post<AuthResponse>('/api/v1/auth/login', { email, password })
  return response.data
}

export async function getProfile(): Promise<AuthUser> {
  const response = await api.get<AuthUser>('/api/v1/auth/me')
  return response.data
}

export async function updateProfile(payload: {
  full_name: string
  phone_number: string
  preferred_language: string
  age?: number
  facility_name?: string
  specialization?: string
}): Promise<AuthUser> {
  const response = await api.put<AuthUser>('/api/v1/users/profile', payload)
  return response.data
}
