from abc import ABC, abstractmethod
from typing import List, Tuple
from src.models.chunk import LegalChunk

class BaseRetriever(ABC):
    """Abstract base class for legal statutory retrievers."""

    @abstractmethod
    def retrieve(self, query: str, top_k: int = 5, lang: str = "en") -> List[Tuple[LegalChunk, float]]:
        """Retrieve top_k legal chunks with relevance score."""
        pass

