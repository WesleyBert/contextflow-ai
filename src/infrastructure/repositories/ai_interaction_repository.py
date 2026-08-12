from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entities.ai_interaction import AiInteraction
from src.domain.repositories.ai_interaction_repository import ChatStats, ModelUsage
from src.infrastructure.database.models.ai_interaction import AiInteractionModel

_MOST_USED_MODELS_LIMIT = 5


def _to_entity(model: AiInteractionModel) -> AiInteraction:
    return AiInteraction(
        id=model.id,
        owner_id=model.owner_id,
        conversation_id=model.conversation_id,
        provider=model.provider,
        model=model.model,
        prompt_tokens_estimate=model.prompt_tokens_estimate,
        completion_tokens_estimate=model.completion_tokens_estimate,
        cost_estimate_usd=model.cost_estimate_usd,
        duration_ms=model.duration_ms,
        succeeded=model.succeeded,
        created_at=model.created_at,
    )


class SqlAlchemyAiInteractionRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

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
        db_model = AiInteractionModel(
            owner_id=owner_id,
            conversation_id=conversation_id,
            provider=provider,
            model=model,
            prompt_tokens_estimate=prompt_tokens_estimate,
            completion_tokens_estimate=completion_tokens_estimate,
            cost_estimate_usd=cost_estimate_usd,
            duration_ms=duration_ms,
            succeeded=succeeded,
        )
        self._session.add(db_model)
        await self._session.commit()
        await self._session.refresh(db_model)
        return _to_entity(db_model)

    async def chat_stats(self) -> ChatStats:
        total = await self._session.scalar(select(func.count()).select_from(AiInteractionModel))
        succeeded = await self._session.scalar(
            select(func.count())
            .select_from(AiInteractionModel)
            .where(AiInteractionModel.succeeded.is_(True))
        )
        avg_duration_ms = await self._session.scalar(
            select(func.avg(AiInteractionModel.duration_ms)).where(
                AiInteractionModel.succeeded.is_(True)
            )
        )
        total_cost = await self._session.scalar(
            select(func.coalesce(func.sum(AiInteractionModel.cost_estimate_usd), 0.0))
        )

        result = await self._session.execute(
            select(
                AiInteractionModel.provider,
                AiInteractionModel.model,
                func.count().label("usage_count"),
            )
            .group_by(AiInteractionModel.provider, AiInteractionModel.model)
            .order_by(func.count().desc())
            .limit(_MOST_USED_MODELS_LIMIT)
        )
        most_used_models = [
            ModelUsage(provider=provider, model=model, count=count)
            for provider, model, count in result.all()
        ]

        return ChatStats(
            total=total or 0,
            succeeded=succeeded or 0,
            avg_duration_ms=round(avg_duration_ms, 2) if avg_duration_ms is not None else None,
            total_cost_estimate_usd=round(float(total_cost or 0.0), 6),
            most_used_models=most_used_models,
        )
