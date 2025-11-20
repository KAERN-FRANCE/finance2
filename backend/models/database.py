"""
SQLAlchemy database models for persistent storage.
"""
from sqlalchemy import create_engine, Column, String, Integer, Float, DateTime, Text, Enum, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import uuid
from backend.config import settings
from backend.models.schemas import DocumentStatus, DocumentType, DocumentCategory, MeetingStatus, AlertSeverity

Base = declarative_base()


def generate_uuid():
    """Generate a UUID string."""
    return str(uuid.uuid4())


class DocumentModel(Base):
    """Database model for documents."""
    __tablename__ = "documents"

    id = Column(String, primary_key=True, default=generate_uuid)
    filename = Column(String, nullable=False)
    file_type = Column(Enum(DocumentType), nullable=False)
    upload_date = Column(DateTime, default=datetime.now, nullable=False)
    size_bytes = Column(Integer, nullable=False)
    category = Column(Enum(DocumentCategory), default=DocumentCategory.OTHER)
    status = Column(Enum(DocumentStatus), default=DocumentStatus.UPLOADING)
    metadata = Column(JSON, default=dict)
    error_message = Column(Text, nullable=True)

    # Vector store reference
    vector_store_id = Column(String, nullable=True)


class MeetingModel(Base):
    """Database model for meetings."""
    __tablename__ = "meetings"

    id = Column(String, primary_key=True, default=generate_uuid)
    title = Column(String, nullable=False)
    date = Column(DateTime, default=datetime.now, nullable=False)
    participants = Column(JSON, default=list)
    agenda = Column(Text, nullable=True)
    language = Column(String, default="fr")
    status = Column(Enum(MeetingStatus), default=MeetingStatus.SCHEDULED)
    duration = Column(Integer, default=0)  # in seconds

    # Relationships
    transcriptions = relationship("TranscriptionModel", back_populates="meeting", cascade="all, delete-orphan")
    alerts = relationship("AlertModel", back_populates="meeting", cascade="all, delete-orphan")
    reports = relationship("ReportModel", back_populates="meeting", cascade="all, delete-orphan")


class TranscriptionModel(Base):
    """Database model for transcription segments."""
    __tablename__ = "transcriptions"

    id = Column(String, primary_key=True, default=generate_uuid)
    meeting_id = Column(String, ForeignKey("meetings.id"), nullable=False)
    start_time = Column(Float, nullable=False)
    end_time = Column(Float, nullable=False)
    text = Column(Text, nullable=False)
    speaker = Column(String, nullable=True)
    language = Column(String, nullable=False)
    confidence = Column(Float, default=0.0)

    # Relationship
    meeting = relationship("MeetingModel", back_populates="transcriptions")


class AlertModel(Base):
    """Database model for real-time alerts."""
    __tablename__ = "alerts"

    id = Column(String, primary_key=True, default=generate_uuid)
    meeting_id = Column(String, ForeignKey("meetings.id"), nullable=False)
    timestamp = Column(Float, nullable=False)
    severity = Column(Enum(AlertSeverity), nullable=False)
    statement = Column(Text, nullable=False)
    issue = Column(Text, nullable=False)
    source_docs = Column(JSON, default=list)
    created_at = Column(DateTime, default=datetime.now)

    # Relationship
    meeting = relationship("MeetingModel", back_populates="alerts")


class ReportModel(Base):
    """Database model for meeting reports."""
    __tablename__ = "reports"

    id = Column(String, primary_key=True, default=generate_uuid)
    meeting_id = Column(String, ForeignKey("meetings.id"), nullable=False)
    generated_at = Column(DateTime, default=datetime.now)
    executive_summary = Column(Text, nullable=False)
    fact_checks = Column(JSON, default=list)
    blind_spots = Column(JSON, default=dict)
    recommendations = Column(JSON, default=list)
    language = Column(String, default="fr")
    metadata = Column(JSON, default=dict)

    # Relationship
    meeting = relationship("MeetingModel", back_populates="reports")


# Database setup
engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False} if "sqlite" in settings.database_url else {}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    """Initialize the database by creating all tables."""
    Base.metadata.create_all(bind=engine)


def get_db():
    """Dependency for getting database sessions."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
