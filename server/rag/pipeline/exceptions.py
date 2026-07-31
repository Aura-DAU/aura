class RAGPipelineError(Exception):
    # Raised when a stage in the RAG pipeline fails due to API errors, rate limits, or timeouts.
    pass


class ContextLengthExceeded(RAGPipelineError):
    """Input + reserved output exceeds the model's context window.

    Distinct from the soft-failure apology path (AURA-GEN-00x / CHAT-05): this
    carries ``code=AURA-CTX-001`` so operators can attribute context-window
    overflows separately from generic generation failures. Callers should map
    it to a structured 4xx response, never a 500.
    """

    code = "AURA-CTX-001"

    def __init__(
        self,
        message: str = (
            "Request exceeds the model's context window after budgeting. "
            "Try a shorter question or a new conversation."
        ),
        *,
        stats: dict | None = None,
    ):
        super().__init__(message)
        self.stats = dict(stats or {})
