"""Documentation data models for automation packages."""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from enum import Enum


class DocumentationType(str, Enum):
    """Types of documentation that can be generated."""
    IMPLEMENTATION = "implementation"
    CONFIGURATION = "configuration" 
    RUNBOOK = "runbook"
    SOP = "sop"
    LOOM_OUTLINE = "loom-outline"
    CLIENT_ONE_PAGER = "client-one-pager"


class DocumentationAudience(str, Enum):
    """Target audience for documentation."""
    INTERNAL = "internal"
    CLIENT = "client"
    TECHNICAL = "technical"
    BUSINESS = "business"


class DocumentationModel(BaseModel):
    """Base model for all documentation types."""
    
    # Core Properties
    title: str = Field(..., description="Document title")
    doc_type: DocumentationType = Field(..., description="Type of documentation")
    audience: DocumentationAudience = Field(..., description="Target audience")
    content: str = Field(default="", description="Document content in Markdown")
    
    # Context and Variables
    template_variables: Dict[str, Any] = Field(default_factory=dict, description="Variables for template rendering")
    package_name: str = Field(..., description="Associated package name")
    package_slug: str = Field(..., description="Associated package slug")
    
    # Metadata
    version: str = Field(default="1.0.0", description="Document version")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    # Quality and Validation
    word_count: Optional[int] = Field(None, description="Approximate word count")
    estimated_read_time: Optional[int] = Field(None, description="Estimated read time in minutes")
    
    def calculate_metrics(self) -> None:
        """Calculate word count and estimated read time."""
        if self.content:
            words = len(self.content.split())
            self.word_count = words
            # Average reading speed: 200-250 words per minute
            self.estimated_read_time = max(1, round(words / 225))
    
    def get_filename(self) -> str:
        """Get the appropriate filename for this document."""
        return f"{self.doc_type.value}.md"
    
    def is_client_facing(self) -> bool:
        """Check if this document is intended for client consumption."""
        return self.audience in [DocumentationAudience.CLIENT, DocumentationAudience.BUSINESS]


class ImplementationGuide(DocumentationModel):
    """Step-by-step implementation documentation."""
    
    def __init__(self, **data):
        super().__init__(doc_type=DocumentationType.IMPLEMENTATION, **data)
    
    # Implementation-specific fields
    prerequisites: List[str] = Field(default_factory=list, description="Required prerequisites")
    installation_steps: List[str] = Field(default_factory=list, description="Step-by-step installation")
    configuration_steps: List[str] = Field(default_factory=list, description="Configuration instructions")
    testing_steps: List[str] = Field(default_factory=list, description="Testing and validation steps")


class ConfigurationGuide(DocumentationModel):
    """Environment variables, API keys, and configuration documentation."""
    
    def __init__(self, **data):
        super().__init__(doc_type=DocumentationType.CONFIGURATION, **data)
    
    # Configuration-specific fields
    environment_variables: Dict[str, str] = Field(default_factory=dict, description="Required env vars")
    api_keys_required: List[str] = Field(default_factory=list, description="Required API keys")
    rate_limits: Dict[str, Any] = Field(default_factory=dict, description="Rate limit information")
    integration_gotchas: List[str] = Field(default_factory=list, description="Common integration issues")


class Runbook(DocumentationModel):
    """Operations runbook for monitoring, troubleshooting, and rollback."""
    
    def __init__(self, **data):
        super().__init__(doc_type=DocumentationType.RUNBOOK, **data)
    
    # Runbook-specific fields
    monitoring_checklist: List[str] = Field(default_factory=list, description="What to monitor")
    troubleshooting_steps: Dict[str, List[str]] = Field(default_factory=dict, description="Problem -> solutions")
    rollback_procedure: List[str] = Field(default_factory=list, description="How to rollback changes")
    escalation_contacts: List[str] = Field(default_factory=list, description="Who to contact for issues")


class StandardOperatingProcedure(DocumentationModel):
    """Standard Operating Procedures for team members."""
    
    def __init__(self, **data):
        super().__init__(doc_type=DocumentationType.SOP, **data)
    
    # SOP-specific fields
    task_procedures: Dict[str, List[str]] = Field(default_factory=dict, description="Task -> step-by-step procedures")
    roles_responsibilities: Dict[str, str] = Field(default_factory=dict, description="Role -> responsibility mapping")
    quality_checks: List[str] = Field(default_factory=list, description="Quality validation checklist")


class LoomOutline(DocumentationModel):
    """Script outline for video walkthrough creation."""
    
    def __init__(self, **data):
        super().__init__(doc_type=DocumentationType.LOOM_OUTLINE, **data)
    
    # Loom-specific fields
    video_duration: int = Field(default=5, description="Target video duration in minutes")
    key_talking_points: List[str] = Field(default_factory=list, description="Main points to cover")
    screen_flow: List[str] = Field(default_factory=list, description="Screen-by-screen walkthrough")
    call_to_action: str = Field(default="", description="What viewer should do next")


class ClientOnePager(DocumentationModel):
    """Client-facing one-page summary with business focus."""
    
    def __init__(self, **data):
        super().__init__(
            doc_type=DocumentationType.CLIENT_ONE_PAGER,
            audience=DocumentationAudience.CLIENT,
            **data
        )
    
    # Client one-pager specific fields  
    problem_statement: str = Field(..., description="Clear problem statement")
    solution_summary: str = Field(..., description="How the automation solves the problem")
    key_benefits: List[str] = Field(default_factory=list, description="Primary business benefits")
    kpi_metrics: Dict[str, str] = Field(default_factory=dict, description="Key performance indicators")
    roi_projection: str = Field(default="", description="Return on investment estimate")
    implementation_timeline: str = Field(default="", description="Expected deployment timeline")


class DocumentationSuite(BaseModel):
    """Complete documentation suite for a package."""
    
    package_name: str = Field(..., description="Package name")
    package_slug: str = Field(..., description="Package slug")
    
    # All documentation types
    implementation_guide: Optional[ImplementationGuide] = None
    configuration_guide: Optional[ConfigurationGuide] = None  
    runbook: Optional[Runbook] = None
    sop: Optional[StandardOperatingProcedure] = None
    loom_outline: Optional[LoomOutline] = None
    client_one_pager: Optional[ClientOnePager] = None
    
    # Suite metadata
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    def get_all_documents(self) -> List[DocumentationModel]:
        """Get all non-null documents in the suite."""
        docs: List[DocumentationModel] = []
        for doc in [
            self.implementation_guide,
            self.configuration_guide,
            self.runbook,
            self.sop,
            self.loom_outline,
            self.client_one_pager
        ]:
            if doc is not None:
                docs.append(doc)
        return docs
    
    def get_client_documents(self) -> List[DocumentationModel]:
        """Get only client-facing documents."""
        return [doc for doc in self.get_all_documents() if doc.is_client_facing()]
    
    def get_internal_documents(self) -> List[DocumentationModel]:
        """Get only internal documents."""
        return [doc for doc in self.get_all_documents() if not doc.is_client_facing()]
    
    def calculate_total_content_metrics(self) -> Dict[str, int]:
        """Calculate total word count and read time for all documents."""
        total_words = 0
        total_read_time = 0
        
        for doc in self.get_all_documents():
            doc.calculate_metrics()
            if doc.word_count:
                total_words += doc.word_count
            if doc.estimated_read_time:
                total_read_time += doc.estimated_read_time
        
        return {
            "total_word_count": total_words,
            "total_read_time": total_read_time,
            "document_count": len(self.get_all_documents())
        }