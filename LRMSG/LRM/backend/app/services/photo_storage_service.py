"""Photo storage service for field intelligence report photographs.

Provides:
- Configurable local development storage adapter.
- Server-side filename generation (UUID4) preventing client filename spoofing.
- Strict MIME type and content-type verification (JPEG, PNG, WebP).
- Chunked streaming write with hard upper bounds to avoid loading files into memory.
- Path traversal mitigation.
- Relative URL path resolution (never leaking local filesystem paths).
"""

import os
from pathlib import Path
from typing import BinaryIO, Optional, Protocol, Tuple
from uuid import uuid4


ALLOWED_MIME_TYPES = {
    "image/jpeg": ".jpg",
    "image/pjpeg": ".jpg",
    "image/png": ".png",
    "image/x-png": ".png",
    "image/webp": ".webp",
}

DEFAULT_MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB
CHUNK_SIZE = 64 * 1024  # 64 KB


class PhotoStorageAdapter(Protocol):
    """Abstract interface for storing report photos."""

    def save_photo(
        self,
        stream: BinaryIO,
        content_type: str,
        size_hint: Optional[int] = None,
    ) -> Tuple[str, str, int]:
        """Save a photo stream.

        Returns:
            Tuple of (photo_url, generated_filename, total_bytes_written)
        """
        ...

    def delete_photo(self, filename: str) -> bool:
        """Delete a photo by filename."""
        ...

    def read_photo(self, photo_url_or_filename: str) -> Optional[Tuple[bytes, str]]:
        """Safely read photo bytes and MIME type by relative URL or filename."""
        ...


class LocalStorageAdapter:
    """Local development storage adapter storing files on disk and serving via FastAPI."""

    def __init__(
        self,
        upload_dir: Optional[Path] = None,
        url_prefix: str = "/uploads/field_reports",
        max_size_bytes: int = DEFAULT_MAX_FILE_SIZE,
    ):
        if upload_dir is None:
            # Default to backend/uploads/field_reports
            backend_dir = Path(__file__).resolve().parents[2]
            upload_dir = backend_dir / "uploads" / "field_reports"

        self.upload_dir = upload_dir.resolve()
        self.url_prefix = url_prefix.rstrip("/")
        self.max_size_bytes = max_size_bytes

        # Ensure upload directory exists
        self.upload_dir.mkdir(parents=True, exist_ok=True)

    def validate_content_type(self, content_type: Optional[str]) -> str:
        """Verify content type is an allowed image format."""
        if not content_type:
            raise ValueError("Photo content-type header is missing or empty.")
        clean_type = content_type.split(";")[0].strip().lower()
        if clean_type not in ALLOWED_MIME_TYPES:
            allowed = ", ".join(sorted(ALLOWED_MIME_TYPES.keys()))
            raise ValueError(
                f"Unsupported image type '{clean_type}'. Allowed formats: {allowed}"
            )
        return clean_type

    @staticmethod
    def verify_magic_bytes(header: bytes, expected_type: str) -> None:
        """Verify image header signature (magic bytes) matches declared MIME type."""
        if not header or len(header) < 4:
            raise ValueError("Uploaded file is too small or empty (0 bytes).")
        if expected_type in ("image/jpeg", "image/pjpeg"):
            if not header.startswith(b"\xff\xd8\xff"):
                raise ValueError("File content does not match JPEG image signature.")
        elif expected_type in ("image/png", "image/x-png"):
            if not header.startswith(b"\x89PNG\r\n\x1a\n"):
                raise ValueError("File content does not match PNG image signature.")
        elif expected_type == "image/webp":
            if not (header.startswith(b"RIFF") and len(header) >= 12 and header[8:12] == b"WEBP"):
                raise ValueError("File content does not match WebP image signature.")

    def save_photo(
        self,
        stream: BinaryIO,
        content_type: str,
        size_hint: Optional[int] = None,
    ) -> Tuple[str, str, int]:
        """Stream photo to disk with bounded memory, size limit, and magic bytes enforcement."""
        clean_type = self.validate_content_type(content_type)

        if size_hint is not None and size_hint > self.max_size_bytes:
            raise ValueError(
                f"File size exceeds limit of {self.max_size_bytes // (1024 * 1024)} MB."
            )

        extension = ALLOWED_MIME_TYPES[clean_type]
        filename = f"{uuid4().hex}{extension}"
        destination = (self.upload_dir / filename).resolve()

        # Guard against path traversal
        if not str(destination).startswith(str(self.upload_dir)):
            raise ValueError("Unsafe filename path traversal detected.")

        total_bytes = 0
        is_first_chunk = True
        try:
            with open(destination, "wb") as dest:
                while True:
                    chunk = stream.read(CHUNK_SIZE)
                    if not chunk:
                        break
                    if is_first_chunk:
                        self.verify_magic_bytes(chunk[:16], clean_type)
                        is_first_chunk = False
                    total_bytes += len(chunk)
                    if total_bytes > self.max_size_bytes:
                        raise ValueError(
                            f"Uploaded file exceeds maximum allowed size of {self.max_size_bytes // (1024 * 1024)} MB."
                        )
                    dest.write(chunk)

            if total_bytes == 0:
                raise ValueError("Uploaded file is empty (0 bytes).")

            # Relative URL path safe for web/mobile consumption
            photo_url = f"{self.url_prefix}/{filename}"
            return photo_url, filename, total_bytes

        except Exception:
            # Clean up partial file on failure
            if destination.exists():
                try:
                    destination.unlink()
                except OSError:
                    pass
            raise

    def delete_photo(self, filename: str) -> bool:
        """Safely delete photo file by basename."""
        safe_name = Path(filename).name
        target = (self.upload_dir / safe_name).resolve()
        if not str(target).startswith(str(self.upload_dir)):
            return False
        if target.exists() and target.is_file():
            target.unlink()
            return True
        return False

    def read_photo(self, photo_url_or_filename: str) -> Optional[Tuple[bytes, str]]:
        """Safely read photo bytes and determine MIME type from storage.

        Guards against directory traversal and ensures the file is inside the configured directory.
        """
        if not photo_url_or_filename or not photo_url_or_filename.strip():
            return None

        safe_name = Path(photo_url_or_filename).name
        target = (self.upload_dir / safe_name).resolve()

        if not str(target).startswith(str(self.upload_dir)):
            return None

        if not target.exists() or not target.is_file():
            return None

        ext = target.suffix.lower()
        mime_map = {
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".png": "image/png",
            ".webp": "image/webp",
        }
        mime_type = mime_map.get(ext, "application/octet-stream")

        try:
            with open(target, "rb") as f:
                data = f.read()
            return data, mime_type
        except OSError:
            return None


# Singleton storage service instance (configurable via env)
_storage_dir_env = os.environ.get("FIELD_REPORT_UPLOAD_DIR")
_custom_dir = Path(_storage_dir_env) if _storage_dir_env else None
photo_storage_service = LocalStorageAdapter(upload_dir=_custom_dir)
