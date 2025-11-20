"""
Transcription service using OpenAI Whisper API.
Handles audio chunk processing and speech-to-text conversion.
"""
from openai import OpenAI
from typing import Dict, Any, Optional
from pathlib import Path
import tempfile
from backend.config import settings
from backend.utils.logger import log
from backend.utils.helpers import detect_language
import io


class TranscriptionService:
    """Service for audio transcription using OpenAI Whisper."""

    def __init__(self):
        """Initialize the transcription service."""
        self.client = OpenAI(api_key=settings.openai_api_key)
        self.model = settings.whisper_model
        self.default_language = settings.whisper_language

    async def transcribe_audio(
        self,
        audio_data: bytes,
        filename: str = "audio.webm",
        language: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Transcribe audio data using Whisper API.

        Args:
            audio_data: Raw audio bytes
            filename: Filename for the audio (determines format)
            language: Optional language code (ISO-639-1)

        Returns:
            Transcription result with text and metadata
        """
        try:
            log.info(f"Transcribing audio chunk: {filename}")

            # Create a file-like object from bytes
            audio_file = io.BytesIO(audio_data)
            audio_file.name = filename

            # Prepare API parameters
            transcription_params = {
                "model": self.model,
                "file": audio_file,
                "response_format": "verbose_json"
            }

            # Add language if specified and not auto
            if language and language != "auto":
                transcription_params["language"] = language

            # Call Whisper API
            response = self.client.audio.transcriptions.create(**transcription_params)

            # Extract information
            result = {
                "text": response.text,
                "language": response.language if hasattr(response, 'language') else (language or "unknown"),
                "duration": response.duration if hasattr(response, 'duration') else 0,
                "segments": []
            }

            # Extract segments if available
            if hasattr(response, 'segments') and response.segments:
                result["segments"] = [
                    {
                        "start": segment.get("start", 0),
                        "end": segment.get("end", 0),
                        "text": segment.get("text", "")
                    }
                    for segment in response.segments
                ]

            log.info(f"Transcription completed: {len(result['text'])} characters, language: {result['language']}")

            return result

        except Exception as e:
            log.error(f"Error transcribing audio: {e}")
            raise

    async def transcribe_file(
        self,
        file_path: Path,
        language: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Transcribe an audio file from disk.

        Args:
            file_path: Path to the audio file
            language: Optional language code

        Returns:
            Transcription result
        """
        try:
            with open(file_path, "rb") as audio_file:
                audio_data = audio_file.read()

            return await self.transcribe_audio(
                audio_data=audio_data,
                filename=file_path.name,
                language=language
            )

        except Exception as e:
            log.error(f"Error transcribing file {file_path}: {e}")
            raise

    def detect_language_from_text(self, text: str) -> str:
        """
        Detect language from transcribed text.

        Args:
            text: Transcribed text

        Returns:
            Language code
        """
        try:
            return detect_language(text)
        except Exception as e:
            log.warning(f"Error detecting language: {e}")
            return settings.default_language

    async def transcribe_with_timestamps(
        self,
        audio_data: bytes,
        start_time: float,
        filename: str = "audio.webm",
        language: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Transcribe audio with adjusted timestamps for a meeting segment.

        Args:
            audio_data: Raw audio bytes
            start_time: Start time of this segment in the meeting (seconds)
            filename: Filename for the audio
            language: Optional language code

        Returns:
            Transcription with adjusted timestamps
        """
        try:
            # Transcribe the audio
            result = await self.transcribe_audio(audio_data, filename, language)

            # Adjust timestamps
            if result["segments"]:
                for segment in result["segments"]:
                    segment["start"] += start_time
                    segment["end"] += start_time

            # Add overall start and end times
            if result["segments"]:
                result["start_time"] = result["segments"][0]["start"]
                result["end_time"] = result["segments"][-1]["end"]
            else:
                result["start_time"] = start_time
                result["end_time"] = start_time + result.get("duration", 0)

            return result

        except Exception as e:
            log.error(f"Error transcribing with timestamps: {e}")
            raise

    def validate_audio_format(self, filename: str) -> bool:
        """
        Validate if the audio format is supported by Whisper.

        Args:
            filename: Audio filename

        Returns:
            True if supported, False otherwise
        """
        supported_formats = [
            '.mp3', '.mp4', '.mpeg', '.mpga',
            '.m4a', '.wav', '.webm', '.ogg', '.flac'
        ]

        file_ext = Path(filename).suffix.lower()
        return file_ext in supported_formats


# Global instance
_transcription_service = None


def get_transcription_service() -> TranscriptionService:
    """Get or create the global transcription service instance."""
    global _transcription_service
    if _transcription_service is None:
        _transcription_service = TranscriptionService()
    return _transcription_service
