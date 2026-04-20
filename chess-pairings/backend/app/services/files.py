from pathlib import Path
from uuid import uuid4

from app.core.config import settings
from fastapi import UploadFile


class FileStorageService:
    def __init__(self) -> None:
        self.documents_dir = Path(settings.DOCUMENTS_DIR)
        self.documents_dir.mkdir(parents=True, exist_ok=True)

    async def save_bulletin(self, upload: UploadFile) -> str:
        extension = Path(upload.filename or "document.pdf").suffix or ".pdf"
        filename = f"{uuid4().hex}{extension}"
        destination = self.documents_dir / filename
        content = await upload.read()
        destination.write_bytes(content)
        return str(destination)

    def public_url(self, path: str | None) -> str | None:
        if not path:
            return None
        file_name = Path(path).name
        return f"{settings.FILES_BASE_URL}/files/documents/{file_name}"
