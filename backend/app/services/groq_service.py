# Backward compatibility — use ai_service instead.
from app.services.ai_service import process_code_with_ai

__all__ = ["process_code_with_ai"]
