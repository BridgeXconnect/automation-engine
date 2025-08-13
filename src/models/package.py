"""Package data models for automation packages."""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, field_validator
from enum import Enum


class PackageStatus(str, Enum):
    """Status enum for automation packages."""
    DRAFT = "draft"
    VALIDATED = "validated"
    DEPLOYED = "deployed"
    DEPRECATED = "deprecated"


class AutomationPackage(BaseModel):
    """Core data model for automation packages.
    
    Includes metadata schema from CLAUDE.md requirements and 
    version management with timestamps.
    """
    
    # Core Identification
    name: str = Field(..., min_length=1, description="Human-readable package name")
    slug: str = Field(..., min_length=1, description="URL-safe identifier for package")
    
    # Classification and Context  
    niche_tags: List[str] = Field(default_factory=list, description="Industry/niche classifications")
    problem_statement: str = Field(..., min_length=1, description="Clear problem this package solves")
    outcomes: List[str] = Field(default_factory=list, description="Measurable business outcomes")
    roi_notes: str = Field(..., min_length=1, description="Time saved, cost impact, revenue potential")
    
    # Technical Specifications
    inputs: Dict[str, Any] = Field(default_factory=dict, description="Required inputs and format")
    outputs: Dict[str, Any] = Field(default_factory=dict, description="Expected outputs and format")
    dependencies: List[str] = Field(default_factory=list, description="Required integrations and connectors")
    security_notes: str = Field(default="", description="Security considerations and requirements")
    
    # Package Management
    status: PackageStatus = Field(default=PackageStatus.DRAFT, description="Current package status")
    version: str = Field(default="1.0.0", description="Semantic version number")
    last_validated: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Last validation timestamp")
    
    # Repository and Links
    repo_path: Optional[str] = Field(None, description="Repository path to package")
    n8n_export_path: Optional[str] = Field(None, description="Path to n8n workflow export")
    
    # Metadata
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    @field_validator("slug")
    @classmethod
    def validate_slug(cls, v: str) -> str:
        """Ensure slug is URL-safe."""
        # Check for invalid characters
        valid_chars = set('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_')
        if not all(c in valid_chars for c in v):
            raise ValueError("Slug must contain only alphanumeric characters, hyphens, and underscores")
        
        # Check for spaces and uppercase (which should be invalid)
        if ' ' in v or any(c.isupper() for c in v):
            raise ValueError("Slug must contain only alphanumeric characters, hyphens, and underscores")
            
        return v.lower()
    
    @field_validator("version")
    @classmethod
    def validate_version(cls, v: str) -> str:
        """Ensure version follows semantic versioning."""
        parts = v.split(".")
        if len(parts) != 3:
            raise ValueError("Version must follow semantic versioning (x.y.z)")
        for part in parts:
            if not part.isdigit():
                raise ValueError("Version parts must be numeric")
        return v
    
    def update_validation_timestamp(self):
        """Update the last validated timestamp to current time."""
        self.last_validated = datetime.now(timezone.utc)
        self.updated_at = datetime.now(timezone.utc)
    
    def to_metadata_dict(self) -> Dict[str, Any]:
        """Convert to metadata.json format for package output."""
        return {
            "name": self.name,
            "slug": self.slug,
            "niche_tags": self.niche_tags,
            "problem_statement": self.problem_statement,
            "outcomes": self.outcomes,
            "roi_notes": self.roi_notes,
            "inputs": self.inputs,
            "outputs": self.outputs,
            "dependencies": self.dependencies,
            "security_notes": self.security_notes,
            "status": self.status.value,
            "version": self.version,
            "last_validated": self.last_validated.isoformat(),
            "repo_path": self.repo_path,
            "n8n_export_path": self.n8n_export_path,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }