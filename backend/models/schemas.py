"""
Pydantic models for request/response validation and data structures.
"""
from pydantic import BaseModel, Field, UUID4
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


# Enums
class DocumentStatus(str, Enum):
    """Status of document processing."""
    UPLOADING = "uploading"
    PROCESSING = "processing"
    INDEXED = "indexed"
    ERROR = "error"


class DocumentType(str, Enum):
    """Supported document types."""
    PDF = "pdf"
    DOCX = "docx"
    CSV = "csv"
    XLSX = "xlsx"


class DocumentCategory(str, Enum):
    """Document categories."""
    FINANCE = "finance"
    STRATEGY = "strategy"
    HR = "hr"
    PROJECTS = "projects"
    LEGAL = "legal"
    OPERATIONS = "operations"
    OTHER = "other"


class MeetingStatus(str, Enum):
    """Status of a meeting."""
    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class AlertSeverity(str, Enum):
    """Severity levels for real-time alerts."""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


# Document Models
class DocumentMetadata(BaseModel):
    """Extracted metadata from documents."""
    page_count: Optional[int] = None
    word_count: Optional[int] = None
    creation_date: Optional[datetime] = None
    author: Optional[str] = None
    extracted_kpis: List[str] = Field(default_factory=list)
    extracted_dates: List[str] = Field(default_factory=list)
    extracted_amounts: List[str] = Field(default_factory=list)
    key_entities: List[str] = Field(default_factory=list)


class DocumentCreate(BaseModel):
    """Schema for creating a document record."""
    filename: str
    file_type: DocumentType
    size_bytes: int


class DocumentResponse(BaseModel):
    """Schema for document response."""
    id: str
    filename: str
    file_type: DocumentType
    upload_date: datetime
    size_bytes: int
    category: DocumentCategory
    status: DocumentStatus
    metadata: Optional[DocumentMetadata] = None
    error_message: Optional[str] = None
    problematiques: List[str] = Field(default_factory=list)

    class Config:
        from_attributes = True


class DocumentStats(BaseModel):
    """Statistics about the document knowledge base."""
    total_documents: int
    total_size_mb: float
    documents_by_category: Dict[str, int]
    documents_by_type: Dict[str, int]
    total_chunks: int
    last_updated: Optional[datetime] = None


# Meeting Models
class MeetingCreate(BaseModel):
    """Schema for creating a meeting."""
    title: str
    participants: List[str] = Field(default_factory=list)
    agenda: Optional[str] = None
    language: str = "fr"


class MeetingUpdate(BaseModel):
    """Schema for updating a meeting."""
    title: Optional[str] = None
    participants: Optional[List[str]] = None
    agenda: Optional[str] = None
    language: Optional[str] = None


class MeetingResponse(BaseModel):
    """Schema for meeting response."""
    id: str
    title: str
    date: datetime
    participants: List[str]
    agenda: Optional[str] = None
    language: str
    status: MeetingStatus
    duration: int = 0  # in seconds
    transcription_count: int = 0
    alert_count: int = 0

    class Config:
        from_attributes = True


# Transcription Models
class TranscriptionSegment(BaseModel):
    """A segment of transcribed audio."""
    id: str
    meeting_id: str
    start_time: float
    end_time: float
    text: str
    speaker: Optional[str] = None
    language: str
    confidence: float

    class Config:
        from_attributes = True


class TranscriptionResponse(BaseModel):
    """Response containing transcription segments."""
    meeting_id: str
    segments: List[TranscriptionSegment]
    total_duration: float
    language: str


# Alert Models
class AlertCreate(BaseModel):
    """Schema for creating a real-time alert."""
    meeting_id: str
    timestamp: float
    severity: AlertSeverity
    statement: str
    issue: str
    source_docs: List[str] = Field(default_factory=list)


class AlertResponse(BaseModel):
    """Schema for alert response."""
    id: str
    meeting_id: str
    timestamp: float
    severity: AlertSeverity
    statement: str
    issue: str
    source_docs: List[str]
    created_at: datetime

    class Config:
        from_attributes = True


# Fact-Checking Models
class FactCheck(BaseModel):
    """Result of fact-checking an assertion."""
    statement: str
    is_accurate: bool
    confidence_score: int  # 0-100
    explanation: str
    supporting_sources: List[str] = Field(default_factory=list)
    contradictions: List[str] = Field(default_factory=list)
    timestamp: Optional[float] = None


# Blind Spots Analysis Models
class BlindSpotsAnalysis(BaseModel):
    """Analysis of blind spots in the meeting."""
    unmentioned_risks: List[Dict[str, str]] = Field(default_factory=list)
    missed_opportunities: List[Dict[str, str]] = Field(default_factory=list)
    alternative_solutions: List[Dict[str, str]] = Field(default_factory=list)
    forgotten_constraints: Dict[str, List[str]] = Field(default_factory=dict)
    unconsidered_stakeholders: List[str] = Field(default_factory=list)
    improvement_points: List[Dict[str, str]] = Field(default_factory=list)


class Recommendation(BaseModel):
    """An actionable recommendation."""
    priority: str  # high, medium, low
    category: str
    title: str
    description: str
    rationale: str
    expected_impact: str


# Report Models
class ReportResponse(BaseModel):
    """Complete meeting report."""
    id: str
    meeting_id: str
    generated_at: datetime
    executive_summary: str
    full_transcription: List[TranscriptionSegment]
    fact_checks: List[FactCheck]
    blind_spots: BlindSpotsAnalysis
    recommendations: List[Recommendation]
    language: str
    metadata: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        from_attributes = True


# WebSocket Messages
class WSMessage(BaseModel):
    """WebSocket message structure."""
    type: str  # transcription, alert, status, error
    data: Dict[str, Any]
    timestamp: float = Field(default_factory=lambda: datetime.now().timestamp())


# Health Check
class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    version: str = "1.0.0"
    services: Dict[str, str]
    timestamp: datetime = Field(default_factory=datetime.now)


# Configuration Response
class ConfigResponse(BaseModel):
    """Application configuration exposed to frontend."""
    supported_languages: List[str]
    max_upload_size_mb: int
    max_meeting_duration_hours: int
    audio_chunk_duration_seconds: int
    supported_file_types: List[str]
