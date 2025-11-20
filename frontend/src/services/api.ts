import axios from 'axios'
import type {
  Document,
  DocumentStats,
  Meeting,
  Report,
  Alert,
  TranscriptionSegment,
} from '../types'

const api = axios.create({
  baseURL: '/api',
  headers: {
    'Content-Type': 'application/json',
  },
})

// Documents
export const documentsApi = {
  upload: async (file: File): Promise<Document> => {
    const formData = new FormData()
    formData.append('file', file)
    const { data } = await api.post('/documents/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    return data
  },

  list: async (): Promise<Document[]> => {
    const { data } = await api.get('/documents')
    return data
  },

  getStats: async (): Promise<DocumentStats> => {
    const { data } = await api.get('/documents/stats')
    return data
  },

  delete: async (id: string): Promise<void> => {
    await api.delete(`/documents/${id}`)
  },
}

// Meetings
export const meetingsApi = {
  create: async (meeting: {
    title: string
    participants: string[]
    agenda?: string
    language: string
  }): Promise<Meeting> => {
    const { data } = await api.post('/meetings', meeting)
    return data
  },

  list: async (): Promise<Meeting[]> => {
    const { data } = await api.get('/meetings')
    return data
  },

  get: async (id: string): Promise<Meeting> => {
    const { data } = await api.get(`/meetings/${id}`)
    return data
  },

  start: async (id: string): Promise<void> => {
    await api.post(`/meetings/${id}/start`)
  },

  stop: async (id: string): Promise<void> => {
    await api.post(`/meetings/${id}/stop`)
  },

  uploadAudio: async (
    id: string,
    audioBlob: Blob,
    startTime: number
  ): Promise<{ segments: any[] }> => {
    const formData = new FormData()
    formData.append('audio', audioBlob, 'audio.webm')
    formData.append('start_time', startTime.toString())
    const { data } = await api.post(`/meetings/${id}/audio`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    return data
  },

  getTranscription: async (
    id: string
  ): Promise<{ segments: TranscriptionSegment[] }> => {
    const { data } = await api.get(`/meetings/${id}/transcription`)
    return data
  },

  getAlerts: async (id: string): Promise<Alert[]> => {
    const { data } = await api.get(`/meetings/${id}/alerts`)
    return data
  },

  generateReport: async (id: string): Promise<{ report_id: string }> => {
    const { data} = await api.post(`/meetings/${id}/generate-report`)
    return data
  },
}

// Reports
export const reportsApi = {
  get: async (id: string): Promise<Report> => {
    const { data } = await api.get(`/reports/${id}`)
    return data
  },

  getByMeeting: async (meetingId: string): Promise<Report[]> => {
    const { data } = await api.get(`/reports/meeting/${meetingId}`)
    return data
  },

  downloadMarkdown: async (id: string): Promise<Blob> => {
    const { data } = await api.get(`/reports/${id}/markdown`, {
      responseType: 'blob',
    })
    return data
  },
}

export default api
