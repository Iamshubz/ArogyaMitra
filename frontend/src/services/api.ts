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
  date_of_birth: string | null
  gender: string | null
  address: string | null
  designation: string | null
  worker_approved: boolean | null
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
  date_of_birth?: string
  gender?: string
  address?: string
  preferred_language: string
  role: 'patient' | 'healthcare_worker'
  designation?: string
  facility_name?: string
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
  date_of_birth?: string
  gender?: string
  address?: string
  facility_name?: string
  specialization?: string
  designation?: string
}): Promise<AuthUser> {
  const response = await api.put<AuthUser>('/api/v1/users/profile', payload)
  return response.data
}

export type Reminder = {
  id: number
  patient_id: number
  medication_name: string
  dosage: string
  instructions: string
  scheduled_at: string
  status: 'scheduled' | 'taken' | 'missed' | 'cancelled'
  delivery_status: string
  taken_at: string | null
}

export type HealthContent = {
  id: number
  title: string
  description: string
  category: string
  language_code: string
  body: string
  publication_date: string
  author_id: number
}

export async function listReminders(): Promise<Reminder[]> {
  const response = await api.get<Reminder[]>('/api/v1/reminders')
  return response.data
}

export async function createReminder(payload: {
  medication_name: string
  dosage: string
  instructions: string
  scheduled_at: string
}): Promise<Reminder> {
  const response = await api.post<Reminder>('/api/v1/reminders', payload)
  return response.data
}

export async function updateReminderStatus(id: number, status: 'taken' | 'missed' | 'cancelled'): Promise<Reminder> {
  const response = await api.patch<Reminder>(`/api/v1/reminders/${id}/${status}`)
  return response.data
}

export async function listHealthContent(languageCode?: string): Promise<HealthContent[]> {
  const response = await api.get<HealthContent[]>('/api/v1/content', { params: { language_code: languageCode } })
  return response.data
}

export async function listEmergencyContacts(): Promise<Array<{ id: number; name: string; phone_number: string; is_verified: boolean }>> {
  const response = await api.get('/api/v1/emergency/contacts')
  return response.data
}

export type PatientSummary = { id: number; full_name: string; email: string; phone_number: string | null; preferred_language: string }
export type FollowUp = { id: number; patient_id: number; worker_id: number; due_at: string; notes: string; status: 'scheduled' | 'completed' | 'missed'; completed_at: string | null }

export async function listAssignedPatients(): Promise<PatientSummary[]> {
  const response = await api.get<PatientSummary[]>('/api/v1/worker/patients')
  return response.data
}

export async function listWorkerFollowUps(): Promise<FollowUp[]> {
  const response = await api.get<FollowUp[]>('/api/v1/worker/follow-ups')
  return response.data
}

export async function listAdminAnalytics(): Promise<Record<string, number>> {
  const response = await api.get<Record<string, number>>('/api/v1/admin/analytics')
  return response.data
}

export async function getSystemMonitoring(): Promise<{ api_status: string; database_status: string; ai_provider: string; storage_provider: string }> {
  const response = await api.get('/api/v1/admin/system')
  return response.data
}

export type AiResult = {
  original_text?: string
  translated_text?: string
  simplified_text?: string
  disclaimer: string
}

export async function simplifyMedicalText(text: string, targetLanguage: string): Promise<AiResult> {
  const response = await api.post<AiResult>('/api/v1/ai/simplification', {
    text,
    source_language: 'en',
    target_language: targetLanguage,
  })
  return response.data
}

export async function translateMedicalText(text: string, targetLanguage: string): Promise<AiResult> {
  const response = await api.post<AiResult>('/api/v1/ai/translation', {
    text,
    source_language: 'en',
    target_language: targetLanguage,
  })
  return response.data
}

export async function chatWithPatient(message: string, language: string): Promise<{ answer: string; disclaimer: string }> {
  const response = await api.post('/api/v1/ai/chat', { message, language })
  return response.data
}

export async function analyzeMedicalImage(file: File): Promise<{ filename: string; answer: string; disclaimer: string }> {
  const formData = new FormData()
  formData.append('file', file)
  const response = await api.post('/api/v1/ai/vision', formData)
  return response.data
}

export async function listTranslationHistory(patientId: number): Promise<Array<{
  id: number
  document_id: number
  original_text: string
  translated_text: string
  review_required: boolean
}>> {
  const response = await api.get(`/api/v1/worker/patients/${patientId}/translation-history`)
  return response.data
}

export async function listAdminContent(): Promise<HealthContent[]> {
  const response = await api.get<HealthContent[]>('/api/v1/admin/content')
  return response.data
}
