"""Notion database models for Business OS integration."""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from enum import Enum


class NotionPropertyType(str, Enum):
    """Notion database property types."""
    TITLE = "title"
    RICH_TEXT = "rich_text"
    NUMBER = "number"
    SELECT = "select"
    MULTI_SELECT = "multi_select"
    DATE = "date"
    CHECKBOX = "checkbox"
    URL = "url"
    EMAIL = "email"
    PHONE_NUMBER = "phone_number"
    RELATION = "relation"
    ROLLUP = "rollup"
    CREATED_TIME = "created_time"
    CREATED_BY = "created_by"
    LAST_EDITED_TIME = "last_edited_time"
    LAST_EDITED_BY = "last_edited_by"


class NotionProperty(BaseModel):
    """Notion database property configuration."""
    name: str = Field(..., description="Property name")
    type: NotionPropertyType = Field(..., description="Property type")
    config: Dict[str, Any] = Field(default_factory=dict, description="Type-specific configuration")


class NotionDatabase(BaseModel):
    """Base Notion database model."""
    database_id: Optional[str] = Field(None, description="Notion database ID")
    title: str = Field(..., description="Database title")
    properties: Dict[str, NotionProperty] = Field(default_factory=dict, description="Database properties")
    relations: Dict[str, str] = Field(default_factory=dict, description="Relations to other databases")
    
    def add_property(self, name: str, prop_type: NotionPropertyType, config: Optional[Dict[str, Any]] = None) -> None:
        """Add a property to the database schema."""
        self.properties[name] = NotionProperty(
            name=name,
            type=prop_type,
            config=config or {}
        )
    
    def add_relation(self, property_name: str, target_database_id: str) -> None:
        """Add a relation property to another database."""
        self.relations[property_name] = target_database_id
        self.add_property(
            property_name,
            NotionPropertyType.RELATION,
            {"relation": {"database_id": target_database_id}}
        )
    
    def to_notion_schema(self) -> Dict[str, Any]:
        """Convert to Notion API database schema format."""
        properties_schema = {}
        
        for prop_name, prop in self.properties.items():
            property_config = {prop.type.value: prop.config}
            properties_schema[prop_name] = property_config
        
        return {
            "title": [{"type": "text", "text": {"content": self.title}}],
            "properties": properties_schema
        }


class LibraryDatabase(NotionDatabase):
    """Library database for canonical automation packages.
    
    Properties from CLAUDE.md: Name, Slug, Niche Tags, Problem Statement, 
    Outcomes, Inputs, Outputs, Dependencies, Security Notes, Status, Version, 
    Links (Repo path, n8n export), ROI Notes, Last Validated.
    """
    
    def __init__(self, **data):
        super().__init__(title="Library - Canonical Packages", **data)
        self._setup_schema()
    
    def _setup_schema(self):
        """Set up the Library database schema."""
        # Core identification
        self.add_property("Name", NotionPropertyType.TITLE)
        self.add_property("Slug", NotionPropertyType.RICH_TEXT)
        
        # Classification
        self.add_property("Niche Tags", NotionPropertyType.MULTI_SELECT)
        self.add_property("Problem Statement", NotionPropertyType.RICH_TEXT)
        self.add_property("Outcomes", NotionPropertyType.RICH_TEXT)
        self.add_property("ROI Notes", NotionPropertyType.RICH_TEXT)
        
        # Technical specs
        self.add_property("Inputs", NotionPropertyType.RICH_TEXT)
        self.add_property("Outputs", NotionPropertyType.RICH_TEXT)
        self.add_property("Dependencies", NotionPropertyType.MULTI_SELECT)
        self.add_property("Security Notes", NotionPropertyType.RICH_TEXT)
        
        # Package management
        self.add_property("Status", NotionPropertyType.SELECT, {
            "options": [
                {"name": "Draft", "color": "gray"},
                {"name": "Validated", "color": "yellow"},
                {"name": "Deployed", "color": "green"},
                {"name": "Deprecated", "color": "red"}
            ]
        })
        self.add_property("Version", NotionPropertyType.RICH_TEXT)
        self.add_property("Last Validated", NotionPropertyType.DATE)
        
        # Links and references
        self.add_property("Repo Path", NotionPropertyType.URL)
        self.add_property("N8n Export", NotionPropertyType.URL)


class AutomationsDatabase(NotionDatabase):
    """Automations database for client-specific instances.
    
    Relates to Library, Clients, and Deployments.
    """
    
    library_db_id: str = Field(..., description="Library database ID for relations")
    clients_db_id: str = Field(..., description="Clients database ID for relations") 
    deployments_db_id: str = Field(..., description="Deployments database ID for relations")
    
    def __init__(self, library_db_id: str, clients_db_id: str, deployments_db_id: str, **data):
        super().__init__(title="Automations - Client Instances", **data)
        self.library_db_id = library_db_id
        self.clients_db_id = clients_db_id
        self.deployments_db_id = deployments_db_id
        self._setup_schema()
    
    def _setup_schema(self):
        """Set up the Automations database schema."""
        self.add_property("Name", NotionPropertyType.TITLE)
        self.add_property("Status", NotionPropertyType.SELECT, {
            "options": [
                {"name": "Planned", "color": "gray"},
                {"name": "In Progress", "color": "yellow"}, 
                {"name": "Deployed", "color": "green"},
                {"name": "Paused", "color": "orange"},
                {"name": "Cancelled", "color": "red"}
            ]
        })
        
        # Relations
        self.add_relation("Library Package", self.library_db_id)
        self.add_relation("Client", self.clients_db_id)
        self.add_relation("Deployments", self.deployments_db_id)
        
        # Instance-specific fields
        self.add_property("Implementation Date", NotionPropertyType.DATE)
        self.add_property("Custom Configuration", NotionPropertyType.RICH_TEXT)
        self.add_property("Performance Metrics", NotionPropertyType.RICH_TEXT)


class ComponentsDatabase(NotionDatabase):
    """Components database for reusable subflows/connectors.
    
    Tracks ownership, versions, and tests.
    """
    
    def __init__(self, **data):
        super().__init__(title="Components - Reusable Subflows", **data)
        self._setup_schema()
    
    def _setup_schema(self):
        """Set up the Components database schema."""
        self.add_property("Name", NotionPropertyType.TITLE)
        self.add_property("Type", NotionPropertyType.SELECT, {
            "options": [
                {"name": "Subflow", "color": "blue"},
                {"name": "Connector", "color": "green"},
                {"name": "Utility", "color": "yellow"},
                {"name": "Template", "color": "purple"}
            ]
        })
        
        # Ownership and management
        self.add_property("Owner", NotionPropertyType.RICH_TEXT)
        self.add_property("Version", NotionPropertyType.RICH_TEXT)
        self.add_property("Test Status", NotionPropertyType.SELECT, {
            "options": [
                {"name": "Not Tested", "color": "gray"},
                {"name": "Testing", "color": "yellow"},
                {"name": "Tested", "color": "green"},
                {"name": "Failed", "color": "red"}
            ]
        })
        
        # Technical details
        self.add_property("Description", NotionPropertyType.RICH_TEXT)
        self.add_property("Dependencies", NotionPropertyType.MULTI_SELECT)
        self.add_property("Usage Count", NotionPropertyType.NUMBER)
        self.add_property("Last Updated", NotionPropertyType.DATE)


class ClientsDatabase(NotionDatabase):
    """Clients database for accounts and engagement details.
    
    Tracks installed packages and KPIs.
    """
    
    def __init__(self, **data):
        super().__init__(title="Clients - Accounts & Engagement", **data)
        self._setup_schema()
    
    def _setup_schema(self):
        """Set up the Clients database schema."""
        self.add_property("Client Name", NotionPropertyType.TITLE)
        self.add_property("Owner", NotionPropertyType.RICH_TEXT)
        self.add_property("Stage", NotionPropertyType.SELECT, {
            "options": [
                {"name": "Prospect", "color": "gray"},
                {"name": "Onboarding", "color": "yellow"},
                {"name": "Active", "color": "green"},
                {"name": "Churned", "color": "red"}
            ]
        })
        
        # Contact information
        self.add_property("Primary Contact", NotionPropertyType.RICH_TEXT)
        self.add_property("Email", NotionPropertyType.EMAIL)
        self.add_property("Phone", NotionPropertyType.PHONE_NUMBER)
        
        # Business details
        self.add_property("Industry", NotionPropertyType.SELECT)
        self.add_property("Company Size", NotionPropertyType.SELECT)
        self.add_property("Monthly Value", NotionPropertyType.NUMBER)
        
        # Package tracking
        self.add_property("Installed Packages", NotionPropertyType.RICH_TEXT)
        self.add_property("KPIs", NotionPropertyType.RICH_TEXT)
        self.add_property("Success Metrics", NotionPropertyType.RICH_TEXT)


class DeploymentsDatabase(NotionDatabase):
    """Deployments database for environment details.
    
    Environment details, dates, checklist status, first-run results.
    """
    
    # Add missing field as class attribute
    automations_db_id: str = Field(..., description="Automations database ID for relations")
    
    def __init__(self, automations_db_id: str, **data):
        super().__init__(title="Deployments - Environment Details", **data)
        self.automations_db_id = automations_db_id
        self._setup_schema()
    
    def _setup_schema(self):
        """Set up the Deployments database schema."""
        self.add_property("Deployment Name", NotionPropertyType.TITLE)
        self.add_property("Environment", NotionPropertyType.SELECT, {
            "options": [
                {"name": "Development", "color": "gray"},
                {"name": "Staging", "color": "yellow"},
                {"name": "Production", "color": "green"}
            ]
        })
        
        # Relations
        self.add_relation("Automation", self.automations_db_id)
        
        # Deployment details
        self.add_property("Deploy Date", NotionPropertyType.DATE)
        self.add_property("Deployed By", NotionPropertyType.RICH_TEXT)
        self.add_property("Checklist Status", NotionPropertyType.SELECT, {
            "options": [
                {"name": "Not Started", "color": "gray"},
                {"name": "In Progress", "color": "yellow"},
                {"name": "Completed", "color": "green"},
                {"name": "Failed", "color": "red"}
            ]
        })
        
        # Results and monitoring
        self.add_property("First Run Results", NotionPropertyType.RICH_TEXT)
        self.add_property("Performance Metrics", NotionPropertyType.RICH_TEXT)
        self.add_property("Incidents", NotionPropertyType.RICH_TEXT)
        self.add_property("Rollback Plan", NotionPropertyType.RICH_TEXT)


class NotionBusinessOS(BaseModel):
    """Complete Notion Business OS schema with all databases."""
    
    # Database instances
    library: LibraryDatabase
    automations: AutomationsDatabase
    components: ComponentsDatabase
    clients: ClientsDatabase
    deployments: DeploymentsDatabase
    
    # Metadata
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    workspace_id: Optional[str] = Field(None, description="Notion workspace ID")
    
    @classmethod
    def create_default_schema(cls) -> "NotionBusinessOS":
        """Create a default Business OS schema with proper relations."""
        # Create databases (IDs will be set when created in Notion)
        library = LibraryDatabase()
        components = ComponentsDatabase()
        clients = ClientsDatabase()
        
        # Create databases that need relation IDs (placeholder IDs for now)
        automations = AutomationsDatabase(
            library_db_id="library_placeholder",
            clients_db_id="clients_placeholder", 
            deployments_db_id="deployments_placeholder"
        )
        
        deployments = DeploymentsDatabase(
            automations_db_id="automations_placeholder"
        )
        
        return cls(
            library=library,
            automations=automations,
            components=components,
            clients=clients,
            deployments=deployments,
            workspace_id=None
        )
    
    def update_relation_ids(self, database_ids: Dict[str, str]) -> None:
        """Update database relation IDs after creation in Notion."""
        # Update automations relations
        if "library" in database_ids:
            self.automations.library_db_id = database_ids["library"]
        if "clients" in database_ids:
            self.automations.clients_db_id = database_ids["clients"]
        if "deployments" in database_ids:
            self.automations.deployments_db_id = database_ids["deployments"]
        
        # Update deployments relations  
        if "automations" in database_ids:
            self.deployments.automations_db_id = database_ids["automations"]
        
        # Rebuild schemas with correct relation IDs
        self.automations._setup_schema()
        self.deployments._setup_schema()
    
    def get_all_databases(self) -> List[NotionDatabase]:
        """Get all databases in the Business OS."""
        return [
            self.library,
            self.automations,
            self.components,
            self.clients,
            self.deployments
        ]