"""
Storage abstraction for uploaded PDFs (papers-raw bucket in the Database
Design Document, Section 5.6). This build pass implements local disk
storage; a MinIO/S3-backed implementation can be dropped in later without
changing any caller, since both would satisfy the same interface.
"""
import uuid
from pathlib import Path

from app.config import get_settings

settings = get_settings()


class LocalDiskStorage:
    def __init__(self, root: str):
        self.root = Path(root)
        (self.root / "papers").mkdir(parents=True, exist_ok=True)

    async def save_paper_pdf(self, workspace_id: uuid.UUID, filename: str, content: bytes) -> str:
        safe_name = f"{uuid.uuid4().hex}_{Path(filename).name}"
        dest_dir = self.root / "papers" / str(workspace_id)
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest_path = dest_dir / safe_name
        dest_path.write_bytes(content)
        # storage_path is recorded relative to the storage root, matching the
        # "object key" style used by the SDD's MinIO/S3 design.
        return str(Path("papers") / str(workspace_id) / safe_name)


_storage_backend = LocalDiskStorage(settings.storage_root)


def get_storage() -> LocalDiskStorage:
    return _storage_backend
