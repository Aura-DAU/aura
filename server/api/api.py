# Compatibility entrypoint — prefer `uvicorn api.app:app`; this keeps `api.api:app`.
from api.app import app

__all__ = ["app"]
