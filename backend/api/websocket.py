"""
WebSocket handler for real-time meeting communication.
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from sqlalchemy.orm import Session
from typing import Dict, Set
import json
from datetime import datetime

from backend.models.database import get_db, MeetingModel, AlertModel
from backend.models.schemas import AlertSeverity, WSMessage
from backend.utils.logger import log
from backend.services.real_time_analysis import get_real_time_analysis_service

router = APIRouter(tags=["websocket"])


class ConnectionManager:
    """Manages WebSocket connections for meetings."""

    def __init__(self):
        # meeting_id -> set of websockets
        self.active_connections: Dict[str, Set[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, meeting_id: str):
        """Connect a websocket to a meeting."""
        await websocket.accept()
        if meeting_id not in self.active_connections:
            self.active_connections[meeting_id] = set()
        self.active_connections[meeting_id].add(websocket)
        log.info(f"WebSocket connected to meeting {meeting_id}")

    def disconnect(self, websocket: WebSocket, meeting_id: str):
        """Disconnect a websocket from a meeting."""
        if meeting_id in self.active_connections:
            self.active_connections[meeting_id].discard(websocket)
            if not self.active_connections[meeting_id]:
                del self.active_connections[meeting_id]
        log.info(f"WebSocket disconnected from meeting {meeting_id}")

    async def send_personal_message(self, message: dict, websocket: WebSocket):
        """Send a message to a specific websocket."""
        await websocket.send_json(message)

    async def broadcast_to_meeting(self, message: dict, meeting_id: str):
        """Broadcast a message to all connections in a meeting."""
        if meeting_id in self.active_connections:
            dead_connections = set()
            for connection in self.active_connections[meeting_id]:
                try:
                    await connection.send_json(message)
                except Exception as e:
                    log.error(f"Error broadcasting to connection: {e}")
                    dead_connections.add(connection)

            # Remove dead connections
            for conn in dead_connections:
                self.active_connections[meeting_id].discard(conn)


manager = ConnectionManager()


@router.websocket("/ws/meeting/{meeting_id}")
async def websocket_endpoint(websocket: WebSocket, meeting_id: str):
    """
    WebSocket endpoint for real-time meeting communication.

    Messages from client:
    - {"type": "transcription", "data": {"text": "...", "timestamp": 123.45}}
    - {"type": "ping"}

    Messages to client:
    - {"type": "transcription", "data": {...}}
    - {"type": "alert", "data": {...}}
    - {"type": "status", "data": {"status": "..."}}
    - {"type": "error", "data": {"message": "..."}}
    """
    # Get a database session
    from backend.models.database import SessionLocal
    db = SessionLocal()

    try:
        # Verify meeting exists
        meeting = db.query(MeetingModel).filter(MeetingModel.id == meeting_id).first()
        if not meeting:
            await websocket.close(code=1008, reason="Meeting not found")
            return

        # Connect
        await manager.connect(websocket, meeting_id)

        # Send connection confirmation
        await manager.send_personal_message(
            {
                "type": "status",
                "data": {"status": "connected", "meeting_id": meeting_id},
                "timestamp": datetime.now().timestamp()
            },
            websocket
        )

        # Get real-time analysis service
        analysis_service = get_real_time_analysis_service()
        analysis_service.reset_buffer()

        # Listen for messages
        while True:
            try:
                # Receive message
                data = await websocket.receive_text()
                message = json.loads(data)

                message_type = message.get("type")
                message_data = message.get("data", {})

                if message_type == "ping":
                    # Respond to ping
                    await manager.send_personal_message(
                        {"type": "pong", "data": {}, "timestamp": datetime.now().timestamp()},
                        websocket
                    )

                elif message_type == "transcription":
                    # Handle transcription segment
                    text = message_data.get("text", "")
                    timestamp = message_data.get("timestamp", 0)

                    if text.strip():
                        # Broadcast transcription to all clients
                        await manager.broadcast_to_meeting(
                            {
                                "type": "transcription",
                                "data": {
                                    "text": text,
                                    "timestamp": timestamp
                                },
                                "timestamp": datetime.now().timestamp()
                            },
                            meeting_id
                        )

                        # Analyze in real-time
                        try:
                            alerts = await analysis_service.analyze_statement(
                                statement=text,
                                timestamp=timestamp,
                                meeting_context={
                                    "title": meeting.title,
                                    "language": meeting.language
                                }
                            )

                            # If alerts detected, save and broadcast
                            for alert_data in alerts:
                                # Save alert to database
                                alert = AlertModel(
                                    meeting_id=meeting_id,
                                    timestamp=alert_data["timestamp"],
                                    severity=alert_data["severity"],
                                    statement=alert_data["statement"],
                                    issue=alert_data["issue"],
                                    source_docs=alert_data["source_docs"]
                                )
                                db.add(alert)
                                db.commit()
                                db.refresh(alert)

                                # Broadcast alert
                                await manager.broadcast_to_meeting(
                                    {
                                        "type": "alert",
                                        "data": {
                                            "id": alert.id,
                                            "timestamp": alert.timestamp,
                                            "severity": alert.severity.value,
                                            "statement": alert.statement,
                                            "issue": alert.issue,
                                            "source_docs": alert.source_docs
                                        },
                                        "timestamp": datetime.now().timestamp()
                                    },
                                    meeting_id
                                )

                                log.info(f"Alert generated for meeting {meeting_id}: {alert.severity.value}")

                        except Exception as e:
                            log.error(f"Error in real-time analysis: {e}")
                            # Don't break the connection for analysis errors

                elif message_type == "status_update":
                    # Broadcast status update to all clients
                    await manager.broadcast_to_meeting(
                        {
                            "type": "status",
                            "data": message_data,
                            "timestamp": datetime.now().timestamp()
                        },
                        meeting_id
                    )

                else:
                    log.warning(f"Unknown message type: {message_type}")

            except json.JSONDecodeError as e:
                log.error(f"Invalid JSON received: {e}")
                await manager.send_personal_message(
                    {
                        "type": "error",
                        "data": {"message": "Invalid JSON"},
                        "timestamp": datetime.now().timestamp()
                    },
                    websocket
                )

    except WebSocketDisconnect:
        manager.disconnect(websocket, meeting_id)
        log.info(f"Client disconnected from meeting {meeting_id}")

    except Exception as e:
        log.error(f"WebSocket error: {e}")
        manager.disconnect(websocket, meeting_id)
        try:
            await websocket.close(code=1011, reason="Internal server error")
        except:
            pass

    finally:
        db.close()
