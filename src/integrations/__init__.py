"""Integration clients for external APIs and services."""

from .n8n_processor import WorkflowProcessor
from .research_client import ResearchClient

__all__ = ["WorkflowProcessor", "ResearchClient"]

# NotionClient is available when notion_client package is installed
try:
    from .notion_client import NotionClient
    __all__.append("NotionClient")
except ImportError:
    NotionClient = None  # type: ignore[misc,assignment]