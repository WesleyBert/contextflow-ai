from pydantic import BaseModel


class ModelUsageResponse(BaseModel):
    provider: str
    model: str
    count: int


class AdminMetricsResponse(BaseModel):
    documents_total: int
    documents_ready: int
    documents_failed: int
    document_error_rate: float
    avg_document_processing_time_ms: float | None
    total_questions: int
    chat_error_rate: float
    avg_chat_response_time_ms: float | None
    estimated_token_cost_usd: float
    most_used_models: list[ModelUsageResponse]
