// API Types
export interface Document {
  id: string
  filename: string
  file_type: 'pdf' | 'docx' | 'csv' | 'xlsx'
  upload_date: string
  size_bytes: number
  category: string
  status: 'uploading' | 'processing' | 'indexed' | 'error'
  metadata?: any
  error_message?: string
  problematiques?: string[]
}

export interface DocumentStats {
  total_documents: number
  total_size_mb: number
  documents_by_category: Record<string, number>
  documents_by_type: Record<string, number>
  total_chunks: number
  last_updated?: string
}

export interface Meeting {
  id: string
  title: string
  date: string
  participants: string[]
  agenda?: string
  language: string
  status: 'scheduled' | 'in_progress' | 'completed' | 'cancelled'
  duration: number
  transcription_count: number
  alert_count: number
}

export interface TranscriptionSegment {
  id: string
  meeting_id: string
  start_time: number
  end_time: number
  text: string
  speaker?: string
  language: string
  confidence: number
}

export interface Alert {
  id: string
  meeting_id: string
  timestamp: number
  severity: 'info' | 'warning' | 'critical'
  statement: string
  issue: string
  source_docs: string[]
  created_at: string
}

export interface FactCheck {
  statement: string
  is_accurate: boolean
  confidence_score: number
  explanation: string
  supporting_sources: string[]
  contradictions: string[]
  timestamp?: number
}

export interface BlindSpotsAnalysis {
  unmentioned_risks: any[]
  missed_opportunities: any[]
  alternative_solutions: any[]
  forgotten_constraints: Record<string, string[]>
  unconsidered_stakeholders: string[]
  improvement_points: any[]
}

export interface Recommendation {
  priority: 'high' | 'medium' | 'low'
  category: string
  title: string
  description: string
  rationale: string
  expected_impact: string
}

export interface Report {
  id: string
  meeting_id: string
  generated_at: string
  executive_summary: string
  full_transcription: TranscriptionSegment[]
  fact_checks: FactCheck[]
  blind_spots: BlindSpotsAnalysis
  recommendations: Recommendation[]
  language: string
  metadata: any
}

export interface WSMessage {
  type: 'transcription' | 'alert' | 'status' | 'error' | 'pong'
  data: any
  timestamp: number
}
