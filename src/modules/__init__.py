"""Business logic modules for the automation engine."""

from .niche_research import NicheResearcher
from .opportunity_mapping import OpportunityMapper
from .assembly import WorkflowAssembler
from .validation import WorkflowValidator
from .documentation import DocumentationGenerator

__all__ = [
    "NicheResearcher",
    "OpportunityMapper", 
    "WorkflowAssembler",
    "WorkflowValidator",
    "DocumentationGenerator"
]