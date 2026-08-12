from prometheus_client import Counter, Histogram

http_requests_total = Counter(
    "http_requests_total",
    "Total de requisições HTTP concluídas",
    ["method", "path", "status_code"],
)

http_request_duration_seconds = Histogram(
    "http_request_duration_seconds",
    "Duração das requisições HTTP, em segundos",
    ["method", "path"],
)

document_processing_total = Counter(
    "document_processing_total",
    "Total de processamentos de documento concluídos, por status final",
    ["status"],
)

document_processing_duration_seconds = Histogram(
    "document_processing_duration_seconds",
    "Duração do processamento de documentos (extração + chunking + embeddings), em segundos",
)
