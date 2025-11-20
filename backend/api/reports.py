"""
API routes for report management.
"""
from fastapi import APIRouter, HTTPException, Depends, Response
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List

from backend.models.database import get_db, ReportModel, MeetingModel
from backend.models.schemas import ReportResponse
from backend.utils.logger import log
from backend.services.report_generator import get_report_generator_service
from pathlib import Path

router = APIRouter(prefix="/api/reports", tags=["reports"])


@router.get("/{report_id}", response_model=ReportResponse)
async def get_report(report_id: str, db: Session = Depends(get_db)):
    """
    Get a generated report.
    """
    try:
        report = db.query(ReportModel).filter(ReportModel.id == report_id).first()

        if not report:
            raise HTTPException(status_code=404, detail="Report not found")

        # Get meeting info
        meeting = db.query(MeetingModel).filter(MeetingModel.id == report.meeting_id).first()

        # Get transcription
        from backend.models.database import TranscriptionModel
        transcriptions = db.query(TranscriptionModel).filter(
            TranscriptionModel.meeting_id == report.meeting_id
        ).order_by(TranscriptionModel.start_time).all()

        # Build response
        from backend.models.schemas import TranscriptionSegment
        segments = [TranscriptionSegment.from_orm(t) for t in transcriptions]

        report_resp = ReportResponse(
            id=report.id,
            meeting_id=report.meeting_id,
            generated_at=report.generated_at,
            executive_summary=report.executive_summary,
            full_transcription=segments,
            fact_checks=report.fact_checks,
            blind_spots=report.blind_spots,
            recommendations=report.recommendations,
            language=report.language,
            metadata=report.metadata
        )

        return report_resp

    except HTTPException:
        raise
    except Exception as e:
        log.error(f"Error getting report: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{report_id}/markdown")
async def get_report_markdown(report_id: str, db: Session = Depends(get_db)):
    """
    Get report in markdown format.
    """
    try:
        report = db.query(ReportModel).filter(ReportModel.id == report_id).first()

        if not report:
            raise HTTPException(status_code=404, detail="Report not found")

        # Get transcription
        from backend.models.database import TranscriptionModel
        transcriptions = db.query(TranscriptionModel).filter(
            TranscriptionModel.meeting_id == report.meeting_id
        ).order_by(TranscriptionModel.start_time).all()

        # Build report data
        report_data = {
            "id": report.id,
            "meeting_id": report.meeting_id,
            "generated_at": report.generated_at,
            "executive_summary": report.executive_summary,
            "full_transcription": [
                {
                    "start_time": t.start_time,
                    "end_time": t.end_time,
                    "text": t.text
                }
                for t in transcriptions
            ],
            "fact_checks": report.fact_checks,
            "blind_spots": report.blind_spots,
            "recommendations": report.recommendations,
            "language": report.language,
            "metadata": report.metadata
        }

        # Generate markdown
        report_generator = get_report_generator_service()
        markdown_content = await report_generator.export_report_to_markdown(report_data)

        return Response(
            content=markdown_content,
            media_type="text/markdown",
            headers={
                "Content-Disposition": f"attachment; filename=report_{report_id}.md"
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        log.error(f"Error exporting report to markdown: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/meeting/{meeting_id}", response_model=List[ReportResponse])
async def get_meeting_reports(meeting_id: str, db: Session = Depends(get_db)):
    """
    Get all reports for a specific meeting.
    """
    try:
        reports = db.query(ReportModel).filter(
            ReportModel.meeting_id == meeting_id
        ).order_by(ReportModel.generated_at.desc()).all()

        if not reports:
            return []

        # Get transcription once
        from backend.models.database import TranscriptionModel
        transcriptions = db.query(TranscriptionModel).filter(
            TranscriptionModel.meeting_id == meeting_id
        ).order_by(TranscriptionModel.start_time).all()

        from backend.models.schemas import TranscriptionSegment
        segments = [TranscriptionSegment.from_orm(t) for t in transcriptions]

        # Build responses
        results = []
        for report in reports:
            report_resp = ReportResponse(
                id=report.id,
                meeting_id=report.meeting_id,
                generated_at=report.generated_at,
                executive_summary=report.executive_summary,
                full_transcription=segments,
                fact_checks=report.fact_checks,
                blind_spots=report.blind_spots,
                recommendations=report.recommendations,
                language=report.language,
                metadata=report.metadata
            )
            results.append(report_resp)

        return results

    except Exception as e:
        log.error(f"Error getting meeting reports: {e}")
        raise HTTPException(status_code=500, detail=str(e))
