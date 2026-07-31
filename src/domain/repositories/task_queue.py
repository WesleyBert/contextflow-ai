from typing import Protocol
from uuid import UUID


class TaskQueue(Protocol):
    def enqueue_document_processing(self, document_id: UUID) -> None: ...
