import uuid
from pathlib import Path

from src.infrastructure.config import get_settings


class LocalFileStorage:
    """Guarda arquivos no disco local. Trocável por S3/Blob Storage no futuro
    sem tocar em application/domain, desde que a nova implementação exponha
    os mesmos métodos save()/delete()."""

    def __init__(self) -> None:
        self._base_dir = Path(get_settings().upload_dir)
        self._base_dir.mkdir(parents=True, exist_ok=True)

    def save(self, owner_id: uuid.UUID, filename: str, content: bytes) -> str:
        owner_dir = self._base_dir / str(owner_id)
        owner_dir.mkdir(parents=True, exist_ok=True)

        safe_name = f"{uuid.uuid4()}_{Path(filename).name}"
        path = owner_dir / safe_name
        path.write_bytes(content)
        return str(path)

    def delete(self, storage_path: str) -> None:
        path = Path(storage_path)
        if path.exists():
            path.unlink()
