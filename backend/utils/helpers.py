"""
Helper utility functions.
"""
import re
from typing import List, Dict, Any
from pathlib import Path
import hashlib
import unicodedata


def sanitize_filename(filename: str) -> str:
    """
    Sanitize a filename to prevent directory traversal and other issues.

    Args:
        filename: Original filename

    Returns:
        Sanitized filename
    """
    # Normalize unicode characters
    filename = unicodedata.normalize('NFKD', filename)

    # Remove path components
    filename = Path(filename).name

    # Remove dangerous characters
    filename = re.sub(r'[^\w\s.-]', '', filename)

    # Replace spaces with underscores
    filename = filename.replace(' ', '_')

    # Limit length
    name, ext = Path(filename).stem, Path(filename).suffix
    if len(name) > 200:
        name = name[:200]

    return name + ext


def calculate_file_hash(file_path: Path) -> str:
    """
    Calculate SHA256 hash of a file.

    Args:
        file_path: Path to the file

    Returns:
        Hex digest of the file hash
    """
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def extract_numbers(text: str) -> List[str]:
    """
    Extract numbers (including decimals, percentages, currency) from text.

    Args:
        text: Input text

    Returns:
        List of extracted numbers
    """
    patterns = [
        r'\d+[.,]\d+%',  # Percentages with decimals
        r'\d+%',  # Percentages
        r'\$\d+[.,]\d+[KMB]?',  # Currency with K/M/B
        r'€\d+[.,]?\d*[KMB]?',  # Euro
        r'\d+[.,]\d+[KMB]?',  # Numbers with K/M/B
        r'\d+[.,]\d+',  # Decimals
        r'\d+',  # Integers
    ]

    numbers = []
    for pattern in patterns:
        numbers.extend(re.findall(pattern, text))

    return list(set(numbers))  # Remove duplicates


def extract_dates(text: str) -> List[str]:
    """
    Extract dates from text in various formats.

    Args:
        text: Input text

    Returns:
        List of extracted dates
    """
    patterns = [
        r'\d{1,2}/\d{1,2}/\d{4}',  # DD/MM/YYYY or MM/DD/YYYY
        r'\d{4}-\d{2}-\d{2}',  # YYYY-MM-DD
        r'\d{1,2}\s+(?:janvier|février|mars|avril|mai|juin|juillet|août|septembre|octobre|novembre|décembre)\s+\d{4}',  # French
        r'\d{1,2}\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4}',  # English
        r'Q[1-4]\s+\d{4}',  # Quarters
    ]

    dates = []
    for pattern in patterns:
        dates.extend(re.findall(pattern, text, re.IGNORECASE))

    return dates


def chunk_text(text: str, chunk_size: int = 512, overlap: int = 50) -> List[Dict[str, Any]]:
    """
    Split text into overlapping chunks.

    Args:
        text: Input text
        chunk_size: Target size of each chunk in characters
        overlap: Number of characters to overlap between chunks

    Returns:
        List of chunks with metadata
    """
    if not text:
        return []

    chunks = []
    start = 0
    text_length = len(text)
    chunk_id = 0

    while start < text_length:
        end = start + chunk_size

        # Try to break at sentence boundary
        if end < text_length:
            # Look for sentence endings
            sentence_end = max(
                text.rfind('. ', start, end),
                text.rfind('! ', start, end),
                text.rfind('? ', start, end),
                text.rfind('\n', start, end)
            )
            if sentence_end > start:
                end = sentence_end + 1

        chunk_text = text[start:end].strip()

        if chunk_text:
            chunks.append({
                'id': chunk_id,
                'text': chunk_text,
                'start_char': start,
                'end_char': end,
                'length': len(chunk_text)
            })
            chunk_id += 1

        start = end - overlap

    return chunks


def detect_language(text: str) -> str:
    """
    Detect the language of text.

    Args:
        text: Input text

    Returns:
        Language code (fr, en, etc.)
    """
    try:
        from langdetect import detect
        return detect(text)
    except Exception:
        return "fr"  # Default to French


def format_duration(seconds: int) -> str:
    """
    Format duration in seconds to human-readable string.

    Args:
        seconds: Duration in seconds

    Returns:
        Formatted string (e.g., "1h 23m 45s")
    """
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60

    parts = []
    if hours > 0:
        parts.append(f"{hours}h")
    if minutes > 0:
        parts.append(f"{minutes}m")
    if secs > 0 or not parts:
        parts.append(f"{secs}s")

    return " ".join(parts)


def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """
    Truncate text to a maximum length.

    Args:
        text: Input text
        max_length: Maximum length
        suffix: Suffix to add when truncated

    Returns:
        Truncated text
    """
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)].strip() + suffix
