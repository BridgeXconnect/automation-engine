"""Tests for all Pydantic model validation and functionality."""

import pytest
import json
from datetime import datetime
from pathlib import Path
from pydantic import ValidationError

from src.models.package import AutomationPackage, PackageStatus
from src.models.workflow import N8nWorkflow, N8nNode, NodePosition, WorkflowConnection
from src.models.documentation import (
    DocumentationSuite, ImplementationGuide, ConfigurationGuide, 
    Runbook, StandardOperatingProcedure, LoomOutline, ClientOnePager,
    DocumentationType, DocumentationAudience
)
from src.models.notion import (
    LibraryDatabase, AutomationsDatabase, ComponentsDatabase, 
    ClientsDatabase, DeploymentsDatabase, NotionBusinessOS,
    NotionProperty, NotionPropertyType
)


class TestAutomationPackage:
    """Test AutomationPackage model validation and functionality."""
    
    def test_valid_package_creation(self, sample_automation_package):
        """Test creating a valid automation package."""
        assert sample_automation_package.name == "Lead Qualification Automation"
        assert sample_automation_package.slug == "lead-qualification-automation"
        assert sample_automation_package.status == PackageStatus.VALIDATED
        assert sample_automation_package.version == "1.2.0"
        assert len(sample_automation_package.niche_tags) == 3
        
    def test_slug_validation_success(self):
        """Test successful slug validation."""
        valid_slugs = [
            "simple-slug", 
            "with_underscores", 
            "mixed-slug_format",
            "numbers123",
            "all-lowercase-valid"
        ]
        
        for slug in valid_slugs:
            package = AutomationPackage(
                name="Test Package",
                slug=slug,
                problem_statement="Test problem",
                roi_notes="Test ROI"
            )
            assert package.slug == slug.lower()
    
    def test_slug_validation_failure(self):
        """Test slug validation with invalid formats."""
        invalid_slugs = [
            "Invalid Slug!",
            "has@symbols",
            "has spaces",
            "UPPERCASE",
            "special&chars"
        ]
        
        for slug in invalid_slugs:
            with pytest.raises(ValidationError) as exc_info:
                AutomationPackage(
                    name="Test Package",
                    slug=slug,
                    problem_statement="Test problem", 
                    roi_notes="Test ROI"
                )
            assert "Slug must contain only alphanumeric characters" in str(exc_info.value)
    
    def test_version_validation_success(self):
        """Test successful semantic version validation."""
        valid_versions = ["1.0.0", "2.5.10", "0.1.0", "10.20.30"]
        
        for version in valid_versions:
            package = AutomationPackage(
                name="Test Package",
                slug="test-package",
                problem_statement="Test problem",
                roi_notes="Test ROI",
                version=version
            )
            assert package.version == version
    
    def test_version_validation_failure(self):
        """Test version validation with invalid formats."""
        invalid_versions = ["1.0", "1.0.0.1", "v1.0.0", "1.0.0-alpha", "invalid"]
        
        for version in invalid_versions:
            with pytest.raises(ValidationError) as exc_info:
                AutomationPackage(
                    name="Test Package",
                    slug="test-package", 
                    problem_statement="Test problem",
                    roi_notes="Test ROI",
                    version=version
                )
            assert "Version must follow semantic versioning" in str(exc_info.value) or \
                   "Version parts must be numeric" in str(exc_info.value)
    
    def test_update_validation_timestamp(self, sample_automation_package):
        """Test updating validation timestamp."""
        original_timestamp = sample_automation_package.last_validated
        original_updated = sample_automation_package.updated_at
        
        # Wait a tiny bit to ensure timestamp difference
        import time
        time.sleep(0.01)
        
        sample_automation_package.update_validation_timestamp()
        
        assert sample_automation_package.last_validated > original_timestamp
        assert sample_automation_package.updated_at > original_updated
    
    def test_to_metadata_dict(self, sample_automation_package):
        """Test conversion to metadata dictionary."""
        metadata = sample_automation_package.to_metadata_dict()
        
        # Check all required fields are present
        required_fields = [
            "name", "slug", "niche_tags", "problem_statement", "outcomes",
            "roi_notes", "inputs", "outputs", "dependencies", "security_notes",
            "status", "version", "last_validated", "created_at", "updated_at"
        ]
        
        for field in required_fields:
            assert field in metadata
        
        # Check specific values
        assert metadata["name"] == sample_automation_package.name
        assert metadata["status"] == sample_automation_package.status.value
        assert isinstance(metadata["last_validated"], str)  # ISO format
        assert isinstance(metadata["niche_tags"], list)
    
    def test_package_status_enum(self):
        """Test PackageStatus enum values."""
        assert PackageStatus.DRAFT == "draft"
        assert PackageStatus.VALIDATED == "validated" 
        assert PackageStatus.DEPLOYED == "deployed"
        assert PackageStatus.DEPRECATED == "deprecated"
    
    def test_required_fields_validation(self):
        """Test validation of required fields."""
        # Missing name
        with pytest.raises(ValidationError) as exc_info:
            AutomationPackage(
                slug="test-package",
                problem_statement="Test problem",
                roi_notes="Test ROI"
            )
        assert "name" in str(exc_info.value)
        
        # Missing slug
        with pytest.raises(ValidationError) as exc_info:
            AutomationPackage(
                name="Test Package",
                problem_statement="Test problem",
                roi_notes="Test ROI"
            )
        assert "slug" in str(exc_info.value)


class TestN8nWorkflowModels:
    """Test n8n workflow model validation and functionality."""
    
    def test_node_position_creation(self):
        """Test NodePosition model creation."""
        position = NodePosition(x=100.5, y=200.0)
        assert position.x == 100.5
        assert position.y == 200.0
    
    def test_n8n_node_creation(self, sample_n8n_node):
        """Test N8nNode model creation."""
        assert sample_n8n_node.id == "webhook_node_1"
        assert sample_n8n_node.name == "webhook_trigger"
        assert sample_n8n_node.type == "n8n-nodes-base.webhook"
        assert sample_n8n_node.retries == 3
        assert sample_n8n_node.retry_on_fail is True
    
    def test_node_naming_convention_validation(self):
        """Test node naming convention validation."""
        # Valid names
        valid_names = ["webhook_trigger", "data_processor", "send_email"]
        for name in valid_names:
            node = N8nNode(
                id="test_1",
                name=name,
                type="n8n-nodes-base.webhook",
                position=NodePosition(x=0, y=0)
            )
            assert node.name == name
        
        # Invalid names should raise validation error
        invalid_names = ["Invalid Name!", "has-special@chars", "Uppercase"]
        for name in invalid_names:
            with pytest.raises(ValidationError):
                N8nNode(
                    id="test_1",
                    name=name,
                    type="n8n-nodes-base.webhook",
                    position=NodePosition(x=0, y=0)
                )
    
    def test_retry_count_validation(self):
        """Test retry count validation."""
        # Valid retry count (must be exactly 3)
        node = N8nNode(
            id="test_1",
            name="test_node",
            type="n8n-nodes-base.webhook",
            position=NodePosition(x=0, y=0),
            retries=3
        )
        assert node.retries == 3
        
        # Invalid retry counts
        for invalid_retries in [0, 1, 2, 4, 5]:
            with pytest.raises(ValidationError) as exc_info:
                N8nNode(
                    id="test_1", 
                    name="test_node",
                    type="n8n-nodes-base.webhook",
                    position=NodePosition(x=0, y=0),
                    retries=invalid_retries
                )
            assert "3 retries for exponential backoff" in str(exc_info.value)
    
    def test_workflow_connection_model(self):
        """Test WorkflowConnection model."""
        connection = WorkflowConnection(
            source_node="node_1",
            destination_node="node_2",
            source_output="main",
            destination_input="main"
        )
        
        assert connection.source_node == "node_1"
        assert connection.destination_node == "node_2"
        assert connection.source_output == "main"
        assert connection.destination_input == "main"
    
    def test_n8n_workflow_creation(self, sample_n8n_workflow):
        """Test N8nWorkflow model creation."""
        assert sample_n8n_workflow.name == "lead_qualification_workflow"
        assert len(sample_n8n_workflow.nodes) == 3
        assert sample_n8n_workflow.active is True
        assert "lead" in sample_n8n_workflow.tags
    
    def test_workflow_naming_convention_validation(self):
        """Test workflow naming convention."""
        # Valid workflow names
        valid_names = ["lead_qualification", "data_processor", "webhook_handler"]
        for name in valid_names:
            workflow = N8nWorkflow(
                name=name,
                nodes=[N8nNode(
                    id="test_1",
                    name="test_node", 
                    type="n8n-nodes-base.webhook",
                    position=NodePosition(x=0, y=0)
                )],
                connections={}
            )
            assert workflow.name == name
        
        # Invalid names get normalized
        workflow = N8nWorkflow(
            name="Invalid Workflow Name!",
            nodes=[N8nNode(
                id="test_1",
                name="test_node",
                type="n8n-nodes-base.webhook", 
                position=NodePosition(x=0, y=0)
            )],
            connections={}
        )
        assert workflow.name == "invalid_workflow_name"
    
    def test_workflow_node_validation(self):
        """Test workflow node validation."""
        # Empty nodes should raise validation error
        with pytest.raises(ValidationError) as exc_info:
            N8nWorkflow(
                name="test_workflow",
                nodes=[],
                connections={}
            )
        assert "at least one node" in str(exc_info.value)
    
    def test_validate_node_connections(self, sample_n8n_workflow):
        """Test node connection validation."""
        errors = sample_n8n_workflow.validate_node_connections()
        assert len(errors) == 0  # Should be valid
        
        # Add invalid connection
        sample_n8n_workflow.connections["invalid_source"] = {
            "main": [{"node": "nonexistent_node", "type": "main", "index": 0}]
        }
        
        errors = sample_n8n_workflow.validate_node_connections()
        assert len(errors) >= 1
        assert "not found in workflow" in errors[0]
    
    def test_workflow_to_n8n_json(self, sample_n8n_workflow):
        """Test conversion to n8n JSON format."""
        json_data = sample_n8n_workflow.to_n8n_json()
        
        assert json_data["name"] == sample_n8n_workflow.name
        assert len(json_data["nodes"]) == len(sample_n8n_workflow.nodes)
        assert "connections" in json_data
        assert json_data["active"] == sample_n8n_workflow.active
        
        # Check node structure
        node = json_data["nodes"][0]
        assert "id" in node
        assert "name" in node
        assert "type" in node
        assert "position" in node and len(node["position"]) == 2
    
    def test_workflow_from_n8n_json(self, sample_workflow_json):
        """Test creating workflow from n8n JSON."""
        workflow = N8nWorkflow.from_n8n_json(sample_workflow_json)
        
        assert workflow.name == sample_workflow_json["name"]
        assert len(workflow.nodes) == len(sample_workflow_json["nodes"])
        assert workflow.active == sample_workflow_json["active"]
        
        # Check first node
        first_node = workflow.nodes[0]
        first_node_json = sample_workflow_json["nodes"][0]
        assert first_node.id == first_node_json["id"]
        assert first_node.name == first_node_json["name"]
        assert first_node.type == first_node_json["type"]


class TestDocumentationModels:
    """Test documentation model validation and functionality."""
    
    def test_documentation_type_enum(self):
        """Test DocumentationType enum values."""
        assert DocumentationType.IMPLEMENTATION == "implementation"
        assert DocumentationType.CONFIGURATION == "configuration"
        assert DocumentationType.RUNBOOK == "runbook"
        assert DocumentationType.SOP == "sop"
        assert DocumentationType.LOOM_OUTLINE == "loom-outline"
        assert DocumentationType.CLIENT_ONE_PAGER == "client-one-pager"
    
    def test_documentation_audience_enum(self):
        """Test DocumentationAudience enum values."""
        assert DocumentationAudience.INTERNAL == "internal"
        assert DocumentationAudience.CLIENT == "client"
        assert DocumentationAudience.TECHNICAL == "technical"
        assert DocumentationAudience.BUSINESS == "business"
    
    def test_implementation_guide_creation(self):
        """Test ImplementationGuide model creation."""
        guide = ImplementationGuide(
            title="Test Implementation Guide",
            audience=DocumentationAudience.TECHNICAL,
            package_name="Test Package",
            package_slug="test-package",
            content="# Test Content",
            prerequisites=["Requirement 1", "Requirement 2"],
            installation_steps=["Step 1", "Step 2"]
        )
        
        assert guide.doc_type == DocumentationType.IMPLEMENTATION
        assert guide.title == "Test Implementation Guide"
        assert len(guide.prerequisites) == 2
        assert len(guide.installation_steps) == 2
    
    def test_configuration_guide_creation(self):
        """Test ConfigurationGuide model creation.""" 
        guide = ConfigurationGuide(
            title="Test Configuration Guide",
            audience=DocumentationAudience.TECHNICAL,
            package_name="Test Package",
            package_slug="test-package",
            environment_variables={
                "API_KEY": "Test API key",
                "SECRET": "Test secret"
            },
            api_keys_required=["Service 1", "Service 2"]
        )
        
        assert guide.doc_type == DocumentationType.CONFIGURATION
        assert len(guide.environment_variables) == 2
        assert len(guide.api_keys_required) == 2
    
    def test_client_one_pager_creation(self):
        """Test ClientOnePager model creation."""
        one_pager = ClientOnePager(
            title="Test One Pager",
            package_name="Test Package",
            package_slug="test-package", 
            problem_statement="Test problem",
            solution_summary="Test solution",
            key_benefits=["Benefit 1", "Benefit 2"],
            roi_projection="300% ROI in 6 months"
        )
        
        assert one_pager.doc_type == DocumentationType.CLIENT_ONE_PAGER
        assert one_pager.audience == DocumentationAudience.CLIENT  # Auto-set
        assert one_pager.problem_statement == "Test problem"
        assert len(one_pager.key_benefits) == 2
    
    def test_calculate_metrics(self):
        """Test document metrics calculation."""
        content = "This is a test document with exactly twenty five words to test the word counting functionality properly for validation and comprehensive testing purposes today successfully."
        
        doc = ImplementationGuide(
            title="Test Guide",
            audience=DocumentationAudience.TECHNICAL,
            package_name="Test Package",
            package_slug="test-package",
            content=content
        )
        
        doc.calculate_metrics()
        assert doc.word_count == 25
        assert doc.estimated_read_time == 1  # Minimum 1 minute
    
    def test_get_filename(self):
        """Test filename generation."""
        guide = ImplementationGuide(
            title="Test Guide",
            audience=DocumentationAudience.TECHNICAL,
            package_name="Test Package",
            package_slug="test-package"
        )
        
        assert guide.get_filename() == "implementation.md"
    
    def test_is_client_facing(self):
        """Test client-facing document detection."""
        # Client-facing document
        client_doc = ClientOnePager(
            title="Client Doc",
            package_name="Test Package", 
            package_slug="test-package",
            problem_statement="Test",
            solution_summary="Test",
            key_benefits=[]
        )
        assert client_doc.is_client_facing() is True
        
        # Internal document
        internal_doc = ImplementationGuide(
            title="Internal Guide",
            audience=DocumentationAudience.TECHNICAL,
            package_name="Test Package",
            package_slug="test-package"
        )
        assert internal_doc.is_client_facing() is False
    
    def test_documentation_suite(self, sample_documentation_suite):
        """Test DocumentationSuite functionality."""
        suite = sample_documentation_suite
        
        # Test get_all_documents
        all_docs = suite.get_all_documents()
        assert len(all_docs) == 2  # Implementation and Configuration guides
        
        # Test get_client_documents  
        client_docs = suite.get_client_documents()
        assert len(client_docs) == 0  # No client docs in sample
        
        # Test get_internal_documents
        internal_docs = suite.get_internal_documents()
        assert len(internal_docs) == 2
        
        # Test calculate_total_content_metrics
        metrics = suite.calculate_total_content_metrics()
        assert "total_word_count" in metrics
        assert "total_read_time" in metrics
        assert "document_count" in metrics
        assert metrics["document_count"] == 2


class TestNotionModels:
    """Test Notion database model validation and functionality."""
    
    def test_notion_property_type_enum(self):
        """Test NotionPropertyType enum values."""
        assert NotionPropertyType.TITLE == "title"
        assert NotionPropertyType.RICH_TEXT == "rich_text"
        assert NotionPropertyType.SELECT == "select"
        assert NotionPropertyType.MULTI_SELECT == "multi_select"
        assert NotionPropertyType.RELATION == "relation"
    
    def test_notion_property_creation(self):
        """Test NotionProperty model creation."""
        prop = NotionProperty(
            name="Test Property",
            type=NotionPropertyType.TITLE,
            config={"some": "config"}
        )
        
        assert prop.name == "Test Property"
        assert prop.type == NotionPropertyType.TITLE
        assert prop.config["some"] == "config"
    
    def test_library_database_creation(self, sample_notion_database):
        """Test LibraryDatabase creation and schema."""
        db = sample_notion_database
        
        assert db.title == "Library - Canonical Packages"
        assert "Name" in db.properties
        assert "Status" in db.properties
        assert "Version" in db.properties
        
        # Check property types
        assert db.properties["Name"].type == NotionPropertyType.TITLE
        assert db.properties["Status"].type == NotionPropertyType.SELECT
        assert db.properties["Niche Tags"].type == NotionPropertyType.MULTI_SELECT
    
    def test_add_property_to_database(self):
        """Test adding properties to database."""
        db = LibraryDatabase()
        
        db.add_property("Custom Field", NotionPropertyType.RICH_TEXT, {"config": "value"})
        
        assert "Custom Field" in db.properties
        assert db.properties["Custom Field"].type == NotionPropertyType.RICH_TEXT
        assert db.properties["Custom Field"].config["config"] == "value"
    
    def test_add_relation_to_database(self):
        """Test adding relation properties."""
        db = LibraryDatabase()
        target_db_id = "target_db_123"
        
        db.add_relation("Related Database", target_db_id)
        
        assert "Related Database" in db.properties
        assert db.properties["Related Database"].type == NotionPropertyType.RELATION
        assert db.relations["Related Database"] == target_db_id
    
    def test_database_to_notion_schema(self, sample_notion_database):
        """Test conversion to Notion API schema format."""
        schema = sample_notion_database.to_notion_schema()
        
        assert "title" in schema
        assert "properties" in schema
        assert isinstance(schema["properties"], dict)
        
        # Check specific property format
        name_prop = schema["properties"]["Name"]
        assert "title" in name_prop
        
        status_prop = schema["properties"]["Status"] 
        assert "select" in status_prop
    
    def test_automations_database_creation(self):
        """Test AutomationsDatabase with relations."""
        automations_db = AutomationsDatabase(
            library_db_id="lib_123",
            clients_db_id="clients_123", 
            deployments_db_id="deploy_123"
        )
        
        assert automations_db.title == "Automations - Client Instances"
        assert "Library Package" in automations_db.properties
        assert "Client" in automations_db.properties
        assert "Deployments" in automations_db.properties
        
        # Check relations
        assert automations_db.library_db_id == "lib_123"
        assert automations_db.clients_db_id == "clients_123"
        assert automations_db.deployments_db_id == "deploy_123"
    
    def test_notion_business_os_creation(self, sample_notion_business_os):
        """Test NotionBusinessOS creation."""
        business_os = sample_notion_business_os
        
        assert business_os.library is not None
        assert business_os.automations is not None
        assert business_os.components is not None
        assert business_os.clients is not None
        assert business_os.deployments is not None
    
    def test_business_os_database_relations(self):
        """Test Business OS database relation updates."""
        business_os = NotionBusinessOS.create_default_schema()
        
        # Test relation ID updates
        database_ids = {
            "library": "lib_real_123",
            "clients": "clients_real_123",
            "automations": "auto_real_123",
            "deployments": "deploy_real_123"
        }
        
        business_os.update_relation_ids(database_ids)
        
        assert business_os.automations.library_db_id == "lib_real_123"
        assert business_os.automations.clients_db_id == "clients_real_123"
        assert business_os.deployments.automations_db_id == "auto_real_123"
    
    def test_get_all_databases(self, sample_notion_business_os):
        """Test getting all databases from Business OS."""
        databases = sample_notion_business_os.get_all_databases()
        
        assert len(databases) == 5
        database_titles = [db.title for db in databases]
        
        assert "Library - Canonical Packages" in database_titles
        assert "Automations - Client Instances" in database_titles
        assert "Components - Reusable Subflows" in database_titles
        assert "Clients - Accounts & Engagement" in database_titles
        assert "Deployments - Environment Details" in database_titles


class TestModelEdgeCases:
    """Test edge cases and error conditions for all models."""
    
    def test_empty_string_validations(self):
        """Test handling of empty strings in required fields."""
        with pytest.raises(ValidationError):
            AutomationPackage(
                name="",  # Empty name should fail
                slug="test-slug",
                problem_statement="Test problem", 
                roi_notes="Test ROI"
            )
    
    def test_extremely_long_content(self):
        """Test handling of very long content."""
        long_content = "a" * 100000  # 100k characters
        
        doc = ImplementationGuide(
            title="Long Content Test",
            audience=DocumentationAudience.TECHNICAL,
            package_name="Test Package",
            package_slug="test-package",
            content=long_content
        )
        
        doc.calculate_metrics()
        assert doc.word_count > 0
        assert doc.estimated_read_time > 0
    
    def test_special_characters_in_content(self):
        """Test handling of special characters and unicode."""
        special_content = "Content with émojis 🚀 and ñoñ-ASCII chars: 中文"
        
        package = AutomationPackage(
            name="Special Chars Test",
            slug="special-chars-test",
            problem_statement=special_content,
            roi_notes="ROI with special chars: €100k+",
            security_notes=special_content
        )
        
        assert package.problem_statement == special_content
        assert "€" in package.roi_notes
    
    def test_datetime_handling(self):
        """Test datetime field handling."""
        package = AutomationPackage(
            name="Datetime Test",
            slug="datetime-test", 
            problem_statement="Test problem",
            roi_notes="Test ROI"
        )
        
        # Check that timestamps are set
        assert isinstance(package.created_at, datetime)
        assert isinstance(package.updated_at, datetime) 
        assert isinstance(package.last_validated, datetime)
        
        # Test metadata dict has ISO format timestamps
        metadata = package.to_metadata_dict()
        assert isinstance(metadata["created_at"], str)
        assert "T" in metadata["created_at"]  # ISO format indicator
    
    def test_none_value_handling(self):
        """Test handling of None values in optional fields."""
        package = AutomationPackage(
            name="None Test",
            slug="none-test",
            problem_statement="Test problem",
            roi_notes="Test ROI",
            repo_path=None,  # Optional field
            n8n_export_path=None  # Optional field
        )
        
        assert package.repo_path is None
        assert package.n8n_export_path is None
        
        # Should still serialize properly
        metadata = package.to_metadata_dict()
        assert metadata["repo_path"] is None