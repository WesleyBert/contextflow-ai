from uuid import UUID

from src.infrastructure.queue.tasks import process_document_task


class CeleryTaskQueue:
    def enqueue_document_processing(self, document_id: UUID) -> None:
        process_document_task.delay(str(document_id))
