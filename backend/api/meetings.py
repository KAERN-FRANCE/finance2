"""
API routes for meeting management.
"""
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, BackgroundTasks
from typing import List
from sqlalchemy.orm import Session
from datetime import datetime

from backend.models.database import (
    get_db, MeetingModel, TranscriptionModel, AlertModel, ReportModel
)
from backend.models.schemas import (
    MeetingCreate, MeetingUpdate, MeetingResponse,
    MeetingStatus, TranscriptionResponse, TranscriptionSegment,
    AlertResponse, ReportResponse
)
from backend.config import settings
from backend.utils.logger import log
from backend.services.transcription import get_transcription_service
from backend.services.report_generator import get_report_generator_service

router = APIRouter(prefix="/api/meetings", tags=["meetings"])


@router.post("", response_model=MeetingResponse)
async def create_meeting(meeting: MeetingCreate, db: Session = Depends(get_db)):
    """
    Create a new meeting.
    """
    try:
        new_meeting = MeetingModel(
            title=meeting.title,
            participants=meeting.participants,
            agenda=meeting.agenda,
            language=meeting.language,
            status=MeetingStatus.SCHEDULED
        )

        db.add(new_meeting)
        db.commit()
        db.refresh(new_meeting)

        log.info(f"Meeting created: {new_meeting.title} ({new_meeting.id})")

        return MeetingResponse.from_orm(new_meeting)

    except Exception as e:
        log.error(f"Error creating meeting: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("", response_model=List[MeetingResponse])
async def list_meetings(
    skip: int = 0,
    limit: int = 100,
    status: str = None,
    db: Session = Depends(get_db)
):
    """
    List all meetings with optional filtering.
    """
    try:
        query = db.query(MeetingModel)

        if status:
            try:
                status_enum = MeetingStatus(status)
                query = query.filter(MeetingModel.status == status_enum)
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid status: {status}")

        meetings = query.order_by(MeetingModel.date.desc()).offset(skip).limit(limit).all()

        # Add counts
        result = []
        for meeting in meetings:
            meeting_resp = MeetingResponse.from_orm(meeting)
            meeting_resp.transcription_count = len(meeting.transcriptions)
            meeting_resp.alert_count = len(meeting.alerts)
            result.append(meeting_resp)

        return result

    except HTTPException:
        raise
    except Exception as e:
        log.error(f"Error listing meetings: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{meeting_id}", response_model=MeetingResponse)
async def get_meeting(meeting_id: str, db: Session = Depends(get_db)):
    """
    Get details of a specific meeting.
    """
    try:
        meeting = db.query(MeetingModel).filter(MeetingModel.id == meeting_id).first()

        if not meeting:
            raise HTTPException(status_code=404, detail="Meeting not found")

        meeting_resp = MeetingResponse.from_orm(meeting)
        meeting_resp.transcription_count = len(meeting.transcriptions)
        meeting_resp.alert_count = len(meeting.alerts)

        return meeting_resp

    except HTTPException:
        raise
    except Exception as e:
        log.error(f"Error getting meeting: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{meeting_id}", response_model=MeetingResponse)
async def update_meeting(
    meeting_id: str,
    meeting_update: MeetingUpdate,
    db: Session = Depends(get_db)
):
    """
    Update meeting details.
    """
    try:
        meeting = db.query(MeetingModel).filter(MeetingModel.id == meeting_id).first()

        if not meeting:
            raise HTTPException(status_code=404, detail="Meeting not found")

        # Update fields
        if meeting_update.title is not None:
            meeting.title = meeting_update.title
        if meeting_update.participants is not None:
            meeting.participants = meeting_update.participants
        if meeting_update.agenda is not None:
            meeting.agenda = meeting_update.agenda
        if meeting_update.language is not None:
            meeting.language = meeting_update.language

        db.commit()
        db.refresh(meeting)

        log.info(f"Meeting updated: {meeting_id}")

        return MeetingResponse.from_orm(meeting)

    except HTTPException:
        raise
    except Exception as e:
        log.error(f"Error updating meeting: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{meeting_id}")
async def delete_meeting(meeting_id: str, db: Session = Depends(get_db)):
    """
    Delete a meeting and all associated data.
    """
    try:
        meeting = db.query(MeetingModel).filter(MeetingModel.id == meeting_id).first()

        if not meeting:
            raise HTTPException(status_code=404, detail="Meeting not found")

        db.delete(meeting)
        db.commit()

        log.info(f"Meeting deleted: {meeting_id}")

        return {"message": "Meeting deleted successfully", "id": meeting_id}

    except HTTPException:
        raise
    except Exception as e:
        log.error(f"Error deleting meeting: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{meeting_id}/start")
async def start_meeting(meeting_id: str, db: Session = Depends(get_db)):
    """
    Start a meeting recording.
    """
    try:
        meeting = db.query(MeetingModel).filter(MeetingModel.id == meeting_id).first()

        if not meeting:
            raise HTTPException(status_code=404, detail="Meeting not found")

        if meeting.status == MeetingStatus.IN_PROGRESS:
            raise HTTPException(status_code=400, detail="Meeting already in progress")

        meeting.status = MeetingStatus.IN_PROGRESS
        meeting.date = datetime.now()
        db.commit()

        log.info(f"Meeting started: {meeting_id}")

        return {"message": "Meeting started", "id": meeting_id, "start_time": meeting.date}

    except HTTPException:
        raise
    except Exception as e:
        log.error(f"Error starting meeting: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{meeting_id}/stop")
async def stop_meeting(meeting_id: str, db: Session = Depends(get_db)):
    """
    Stop a meeting recording.
    """
    try:
        meeting = db.query(MeetingModel).filter(MeetingModel.id == meeting_id).first()

        if not meeting:
            raise HTTPException(status_code=404, detail="Meeting not found")

        if meeting.status != MeetingStatus.IN_PROGRESS:
            raise HTTPException(status_code=400, detail="Meeting not in progress")

        # Calculate duration
        if meeting.date:
            duration = int((datetime.now() - meeting.date).total_seconds())
            meeting.duration = duration

        meeting.status = MeetingStatus.COMPLETED
        db.commit()

        log.info(f"Meeting stopped: {meeting_id}, duration: {meeting.duration}s")

        return {
            "message": "Meeting stopped",
            "id": meeting_id,
            "duration": meeting.duration
        }

    except HTTPException:
        raise
    except Exception as e:
        log.error(f"Error stopping meeting: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{meeting_id}/audio")
async def upload_audio_chunk(
    meeting_id: str,
    start_time: float,
    audio: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Upload an audio chunk for transcription.
    """
    try:
        meeting = db.query(MeetingModel).filter(MeetingModel.id == meeting_id).first()

        if not meeting:
            raise HTTPException(status_code=404, detail="Meeting not found")

        if meeting.status != MeetingStatus.IN_PROGRESS:
            raise HTTPException(status_code=400, detail="Meeting not in progress")

        # Read audio data
        audio_data = await audio.read()

        # Transcribe
        transcription_service = get_transcription_service()
        result = await transcription_service.transcribe_with_timestamps(
            audio_data=audio_data,
            start_time=start_time,
            filename=audio.filename,
            language=meeting.language if meeting.language != "auto" else None
        )

        # Save transcription segments
        for segment in result.get("segments", []):
            trans = TranscriptionModel(
                meeting_id=meeting_id,
                start_time=segment["start"],
                end_time=segment["end"],
                text=segment["text"],
                language=result["language"],
                confidence=1.0
            )
            db.add(trans)

        db.commit()

        log.info(f"Audio chunk transcribed for meeting {meeting_id}: {len(result.get('segments', []))} segments")

        return {
            "message": "Audio transcribed",
            "segments": result.get("segments", []),
            "language": result["language"]
        }

    except HTTPException:
        raise
    except Exception as e:
        log.error(f"Error transcribing audio: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{meeting_id}/transcription", response_model=TranscriptionResponse)
async def get_transcription(meeting_id: str, db: Session = Depends(get_db)):
    """
    Get the complete transcription of a meeting.
    """
    try:
        meeting = db.query(MeetingModel).filter(MeetingModel.id == meeting_id).first()

        if not meeting:
            raise HTTPException(status_code=404, detail="Meeting not found")

        transcriptions = db.query(TranscriptionModel).filter(
            TranscriptionModel.meeting_id == meeting_id
        ).order_by(TranscriptionModel.start_time).all()

        segments = [TranscriptionSegment.from_orm(t) for t in transcriptions]

        total_duration = max([s.end_time for s in segments]) if segments else 0

        return TranscriptionResponse(
            meeting_id=meeting_id,
            segments=segments,
            total_duration=total_duration,
            language=meeting.language
        )

    except HTTPException:
        raise
    except Exception as e:
        log.error(f"Error getting transcription: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{meeting_id}/alerts", response_model=List[AlertResponse])
async def get_alerts(meeting_id: str, db: Session = Depends(get_db)):
    """
    Get all alerts for a meeting.
    """
    try:
        meeting = db.query(MeetingModel).filter(MeetingModel.id == meeting_id).first()

        if not meeting:
            raise HTTPException(status_code=404, detail="Meeting not found")

        alerts = db.query(AlertModel).filter(
            AlertModel.meeting_id == meeting_id
        ).order_by(AlertModel.timestamp).all()

        return [AlertResponse.from_orm(alert) for alert in alerts]

    except HTTPException:
        raise
    except Exception as e:
        log.error(f"Error getting alerts: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{meeting_id}/generate-report")
async def generate_report(
    meeting_id: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Generate a comprehensive report for the meeting.
    """
    try:
        meeting = db.query(MeetingModel).filter(MeetingModel.id == meeting_id).first()

        if not meeting:
            raise HTTPException(status_code=404, detail="Meeting not found")

        if meeting.status != MeetingStatus.COMPLETED:
            raise HTTPException(status_code=400, detail="Meeting not completed yet")

        # Get transcription and alerts
        transcriptions = db.query(TranscriptionModel).filter(
            TranscriptionModel.meeting_id == meeting_id
        ).order_by(TranscriptionModel.start_time).all()

        alerts = db.query(AlertModel).filter(
            AlertModel.meeting_id == meeting_id
        ).all()

        if not transcriptions:
            raise HTTPException(status_code=400, detail="No transcription available")

        # Prepare data
        transcription_segments = [
            {
                "id": t.id,
                "start_time": t.start_time,
                "end_time": t.end_time,
                "text": t.text,
                "speaker": t.speaker,
                "language": t.language,
                "confidence": t.confidence
            }
            for t in transcriptions
        ]

        alert_data = [
            {
                "id": a.id,
                "timestamp": a.timestamp,
                "severity": a.severity.value,
                "statement": a.statement,
                "issue": a.issue,
                "source_docs": a.source_docs
            }
            for a in alerts
        ]

        meeting_data = {
            "title": meeting.title,
            "date": meeting.date,
            "participants": meeting.participants,
            "agenda": meeting.agenda,
            "language": meeting.language,
            "duration": meeting.duration
        }

        # Generate report
        report_generator = get_report_generator_service()
        report_data = await report_generator.generate_report(
            meeting_id=meeting_id,
            meeting_data=meeting_data,
            transcription_segments=transcription_segments,
            alerts=alert_data
        )

        # Save report to database
        report = ReportModel(
            meeting_id=meeting_id,
            executive_summary=report_data["executive_summary"],
            fact_checks=report_data["fact_checks"],
            blind_spots=report_data["blind_spots"],
            recommendations=report_data["recommendations"],
            language=report_data["language"],
            metadata=report_data["metadata"]
        )

        db.add(report)
        db.commit()
        db.refresh(report)

        log.info(f"Report generated for meeting {meeting_id}")

        return {
            "message": "Report generated successfully",
            "report_id": report.id,
            "meeting_id": meeting_id
        }

    except HTTPException:
        raise
    except Exception as e:
        log.error(f"Error generating report: {e}")
        raise HTTPException(status_code=500, detail=str(e))
