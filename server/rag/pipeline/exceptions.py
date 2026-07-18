class RAGPipelineError(Exception):
    # Raised when a stage in the RAG pipeline fails due to API errors, rate limits, or timeouts.
    pass
