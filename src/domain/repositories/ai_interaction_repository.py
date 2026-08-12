from dataclasses import dataclass
from typing import Protocol
from uuid import UUID

from src.domain.entities.ai_interaction import AiInteraction


@dataclass
class ModelUsage:
    provider: str
    model: str
    count: int


@dataclass
class ChatStats:
    total: int
    succeeded: int
    avg_duration_ms: float | None
    total_cost_estimate_usd: float
    most_used_models: list[ModelUsage]


class AiInteractionRepository(Protocol):
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
    ) -> AiInteraction: ...

    async def chat_stats(self) -> ChatStats: ...
