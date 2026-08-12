"""Implementações em memória dos Protocols de repositório, usadas só nos testes
unitários dos services — sem tocar banco, pra isolar a lógica de aplicação."""

from datetime import UTC, datetime
from uuid import UUID, uuid4

from src.domain.entities.ai_interaction import AiInteraction
from src.domain.entities.conversation import (
    Conversation,
    Message,
    MessageFeedback,
    MessageRole,
    MessageSource,
)
from src.domain.entities.document import Document, DocumentStatus
from src.domain.entities.document_chunk import DocumentChunk, RetrievedChunk
from src.domain.entities.user import User
from src.domain.repositories.ai_interaction_repository import ChatStats, ModelUsage
from src.domain.repositories.conversation_repository import ConversationOrderBy
from src.domain.repositories.document_repository import DocumentOrderBy, DocumentProcessingStats


class FakeDocumentRepository:
    def __init__(self) -> None:
        self.documents: dict[UUID, Document] = {}

    async def create(
        self,
        owner_id: UUID,
        filename: str,
        content_type: str,
        size_bytes: int,
        storage_path: str,
    ) -> Document:
        document = Document(
            id=uuid4(),
            owner_id=owner_id,
            filename=filename,
            content_type=content_type,
            size_bytes=size_bytes,
            storage_path=storage_path,
            status="pending",
            created_at=datetime.now(UTC),
        )
        self.documents[document.id] = document
        return document

    async def get_by_id(self, document_id: UUID) -> Document | None:
        return self.documents.get(document_id)

    async def list_by_owner(
        self,
        owner_id: UUID,
        *,
        status: DocumentStatus | None = None,
        search: str | None = None,
        order_by: DocumentOrderBy = "created_at_desc",
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list[Document], int]:
        matching = [d for d in self.documents.values() if d.owner_id == owner_id]
        if status is not None:
            matching = [d for d in matching if d.status == status]
        if search:
            matching = [d for d in matching if search.lower() in d.filename.lower()]

        reverse = order_by.endswith("_desc")
        sort_key = (lambda d: d.created_at) if "created_at" in order_by else (lambda d: d.filename)
        matching.sort(key=sort_key, reverse=reverse)

        total = len(matching)
        return matching[offset : offset + limit], total

    async def delete(self, document_id: UUID) -> None:
        self.documents.pop(document_id, None)

    async def update_status(
        self,
        document_id: UUID,
        status: DocumentStatus,
        *,
        started_at: datetime | None = None,
        finished_at: datetime | None = None,
    ) -> None:
        document = self.documents[document_id]
        self.documents[document_id] = Document(
            id=document.id,
            owner_id=document.owner_id,
            filename=document.filename,
            content_type=document.content_type,
            size_bytes=document.size_bytes,
            storage_path=document.storage_path,
            status=status,
            created_at=document.created_at,
            processing_started_at=started_at or document.processing_started_at,
            processing_finished_at=finished_at or document.processing_finished_at,
        )

    async def processing_stats(self) -> DocumentProcessingStats:
        documents = list(self.documents.values())
        ready = [d for d in documents if d.status == "ready"]
        failed = [d for d in documents if d.status == "failed"]
        durations = [
            (d.processing_finished_at - d.processing_started_at).total_seconds() * 1000
            for d in ready
            if d.processing_started_at and d.processing_finished_at
        ]
        avg = sum(durations) / len(durations) if durations else None
        return DocumentProcessingStats(
            total=len(documents), ready=len(ready), failed=len(failed), avg_processing_time_ms=avg
        )


class FakeUserRepository:
    def __init__(self) -> None:
        self.users_by_id: dict[UUID, User] = {}

    async def get_by_email(self, email: str) -> User | None:
        return next((u for u in self.users_by_id.values() if u.email == email), None)

    async def get_by_id(self, user_id: UUID) -> User | None:
        return self.users_by_id.get(user_id)

    async def create(self, email: str, hashed_password: str) -> User:
        user = User(
            id=uuid4(), email=email, hashed_password=hashed_password, created_at=datetime.now(UTC)
        )
        self.users_by_id[user.id] = user
        return user


class FakeConversationRepository:
    def __init__(self) -> None:
        self.conversations: dict[UUID, Conversation] = {}
        self.messages: dict[UUID, list[Message]] = {}

    async def create(self, owner_id: UUID, title: str) -> Conversation:
        conversation = Conversation(
            id=uuid4(), owner_id=owner_id, title=title, created_at=datetime.now(UTC)
        )
        self.conversations[conversation.id] = conversation
        self.messages[conversation.id] = []
        return conversation

    async def get_by_id(self, conversation_id: UUID) -> Conversation | None:
        return self.conversations.get(conversation_id)

    async def list_by_owner(
        self,
        owner_id: UUID,
        *,
        search: str | None = None,
        order_by: ConversationOrderBy = "created_at_desc",
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list[Conversation], int]:
        matching = [c for c in self.conversations.values() if c.owner_id == owner_id]
        if search:
            matching = [c for c in matching if search.lower() in c.title.lower()]

        reverse = order_by.endswith("_desc")
        sort_key = (lambda c: c.created_at) if "created_at" in order_by else (lambda c: c.title)
        matching.sort(key=sort_key, reverse=reverse)

        total = len(matching)
        return matching[offset : offset + limit], total

    async def add_message(
        self,
        conversation_id: UUID,
        role: MessageRole,
        content: str,
        sources: list[MessageSource] | None = None,
    ) -> Message:
        message = Message(
            id=uuid4(),
            conversation_id=conversation_id,
            role=role,
            content=content,
            created_at=datetime.now(UTC),
            sources=sources or [],
        )
        self.messages[conversation_id].append(message)
        return message

    async def list_messages(self, conversation_id: UUID) -> list[Message]:
        return list(self.messages.get(conversation_id, []))

    async def get_message_by_id(self, message_id: UUID) -> Message | None:
        for messages in self.messages.values():
            for message in messages:
                if message.id == message_id:
                    return message
        return None

    async def set_message_feedback(
        self, message_id: UUID, feedback: MessageFeedback
    ) -> Message | None:
        for messages in self.messages.values():
            for index, message in enumerate(messages):
                if message.id == message_id:
                    updated = Message(
                        id=message.id,
                        conversation_id=message.conversation_id,
                        role=message.role,
                        content=message.content,
                        created_at=message.created_at,
                        sources=message.sources,
                        feedback=feedback,
                    )
                    messages[index] = updated
                    return updated
        return None


class FakeAiInteractionRepository:
    def __init__(self) -> None:
        self.interactions: list[AiInteraction] = []

    async def create(
        self,
        owner_id: UUID,
        conversation_id: UUID,
        provider: str,
        model: str,
        prompt_tokens_estimate: int,
        completion_tokens_estimate: int,
        cost_estimate_usd: float,
        duration_ms: float,
        succeeded: bool,
    ) -> AiInteraction:
        interaction = AiInteraction(
            id=uuid4(),
            owner_id=owner_id,
            conversation_id=conversation_id,
            provider=provider,
            model=model,
            prompt_tokens_estimate=prompt_tokens_estimate,
            completion_tokens_estimate=completion_tokens_estimate,
            cost_estimate_usd=cost_estimate_usd,
            duration_ms=duration_ms,
            succeeded=succeeded,
            created_at=datetime.now(UTC),
        )
        self.interactions.append(interaction)
        return interaction

    async def chat_stats(self) -> ChatStats:
        succeeded = [i for i in self.interactions if i.succeeded]
        durations = [i.duration_ms for i in succeeded]
        avg = sum(durations) / len(durations) if durations else None
        total_cost = sum(i.cost_estimate_usd for i in self.interactions)

        counts: dict[tuple[str, str], int] = {}
        for interaction in self.interactions:
            key = (interaction.provider, interaction.model)
            counts[key] = counts.get(key, 0) + 1
        most_used = sorted(counts.items(), key=lambda item: item[1], reverse=True)

        return ChatStats(
            total=len(self.interactions),
            succeeded=len(succeeded),
            avg_duration_ms=avg,
            total_cost_estimate_usd=total_cost,
            most_used_models=[
                ModelUsage(provider=provider, model=model, count=count)
                for (provider, model), count in most_used
            ],
        )


class FakeDocumentChunkRepository:
    def __init__(self) -> None:
        self.chunks: list[DocumentChunk] = []
        self.search_results: list[RetrievedChunk] = []
        self.create_many_calls: list[tuple[UUID, UUID, list[str], list[list[float]]]] = []
        self.deleted_document_ids: list[UUID] = []

    async def create_many(
        self, document_id: UUID, owner_id: UUID, chunks: list[str], embeddings: list[list[float]]
    ) -> list[DocumentChunk]:
        self.create_many_calls.append((document_id, owner_id, chunks, embeddings))
        created = [
            DocumentChunk(
                id=uuid4(),
                document_id=document_id,
                owner_id=owner_id,
                chunk_index=index,
                content=content,
                embedding=embedding,
                created_at=datetime.now(UTC),
            )
            for index, (content, embedding) in enumerate(zip(chunks, embeddings, strict=True))
        ]
        self.chunks.extend(created)
        return created

    async def search_similar(
        self, owner_id: UUID, query_embedding: list[float], top_k: int
    ) -> list[RetrievedChunk]:
        return self.search_results[:top_k]

    async def delete_by_document(self, document_id: UUID) -> None:
        self.deleted_document_ids.append(document_id)
        self.chunks = [c for c in self.chunks if c.document_id != document_id]
