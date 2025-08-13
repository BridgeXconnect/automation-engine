"""Test configuration with pytest fixtures for automation package testing."""

import pytest
import json
import tempfile
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List
from unittest.mock import Mock, MagicMock

from src.models.package import AutomationPackage, PackageStatus
from src.models.workflow import N8nWorkflow, N8nNode, NodePosition
from src.models.documentation import DocumentationSuite, ImplementationGuide, ConfigurationGuide
from src.models.notion import LibraryDatabase, NotionBusinessOS
from src.integrations.notion_client import NotionClient
from src.integrations.n8n_processor import WorkflowProcessor
from src.modules.niche_research import NicheResearcher, NicheBrief
from src.modules.validation import WorkflowValidator


# ================================
# Sample Package Fixtures
# ================================

@pytest.fixture
def sample_automation_package():
    """Sample automation package for testing."""
    return AutomationPackage(
        name="Lead Qualification Automation",
        slug="lead-qualification-automation",
        niche_tags=["sales", "crm", "lead-generation"],
        problem_statement="Manual lead qualification process takes 15-20 minutes per lead",
        outcomes=[
            "Reduce qualification time by 80%",
            "Improve lead scoring accuracy",
            "Automate follow-up sequences"
        ],
        roi_notes="Saves 12 hours/week for sales team, increases qualified leads by 40%",
        inputs={
            "lead_email": "string",
            "lead_source": "string", 
            "company_size": "integer",
            "industry": "string"
        },
        outputs={
            "qualification_score": "integer (0-100)",
            "next_action": "string",
            "assigned_rep": "string"
        },
        dependencies=["HubSpot CRM", "Slack", "Gmail"],
        security_notes="Handles PII data, requires encryption at rest",
        status=PackageStatus.VALIDATED,
        version="1.2.0"
    )


@pytest.fixture
def invalid_automation_package():
    """Invalid automation package for testing validation."""
    return AutomationPackage(
        name="",  # Invalid: empty name
        slug="invalid slug!",  # Invalid: contains special characters
        niche_tags=[],
        problem_statement="",  # Invalid: empty problem statement
        roi_notes="",  # Invalid: empty ROI notes
        version="1.2"  # Invalid: not semantic versioning
    )


# ================================
# Workflow Fixtures
# ================================

@pytest.fixture
def sample_n8n_node():
    """Sample n8n node for testing."""
    return N8nNode(
        id="webhook_node_1",
        name="webhook_trigger",
        type="n8n-nodes-base.webhook",
        position=NodePosition(x=100, y=200),
        parameters={
            "path": "/webhook/lead-intake",
            "httpMethod": "POST",
            "responseMode": "onReceived"
        },
        retries=3,
        retry_on_fail=True
    )


@pytest.fixture
def sample_n8n_workflow():
    """Sample n8n workflow for testing."""
    nodes = [
        N8nNode(
            id="webhook_1",
            name="lead_intake_webhook",
            type="n8n-nodes-base.webhook",
            position=NodePosition(x=100, y=100),
            parameters={
                "path": "/lead-intake",
                "httpMethod": "POST"
            }
        ),
        N8nNode(
            id="hubspot_1",
            name="hubspot_create_contact",
            type="n8n-nodes-base.hubspot",
            position=NodePosition(x=300, y=100),
            parameters={
                "operation": "create",
                "resource": "contact"
            }
        ),
        N8nNode(
            id="slack_1",
            name="slack_notify_team",
            type="n8n-nodes-base.slack",
            position=NodePosition(x=500, y=100),
            parameters={
                "channel": "#sales",
                "text": "New lead qualified"
            }
        )
    ]
    
    connections = {
        "webhook_1": {
            "main": [{"node": "hubspot_1", "type": "main", "index": 0}]
        },
        "hubspot_1": {
            "main": [{"node": "slack_1", "type": "main", "index": 0}]
        }
    }
    
    return N8nWorkflow(
        name="lead_qualification_workflow",
        nodes=nodes,
        connections=connections,
        active=True,
        tags=["lead", "qualification", "automation"]
    )


@pytest.fixture
def invalid_n8n_workflow():
    """Invalid n8n workflow for testing validation."""
    return N8nWorkflow(
        name="Invalid Workflow!",  # Invalid: contains special characters
        nodes=[],  # Invalid: no nodes
        connections={}
    )


@pytest.fixture
def sample_workflow_json():
    """Sample n8n workflow JSON data."""
    return {
        "name": "sample_workflow",
        "nodes": [
            {
                "id": "webhook_1",
                "name": "webhook_trigger",
                "type": "n8n-nodes-base.webhook",
                "position": [100, 100],
                "parameters": {
                    "path": "/webhook",
                    "httpMethod": "POST"
                }
            },
            {
                "id": "set_1", 
                "name": "data_processor",
                "type": "n8n-nodes-base.set",
                "position": [300, 100],
                "parameters": {
                    "values": {
                        "processed": "true",
                        "timestamp": "{{ new Date().toISOString() }}"
                    }
                }
            }
        ],
        "connections": {
            "webhook_1": {
                "main": [{"node": "set_1", "type": "main", "index": 0}]
            }
        },
        "active": False,
        "tags": ["test", "sample"]
    }


# ================================
# Documentation Fixtures
# ================================

@pytest.fixture
def sample_documentation_suite():
    """Sample documentation suite for testing."""
    impl_guide = ImplementationGuide(
        title="Lead Qualification Implementation",
        audience="technical",
        package_name="Lead Qualification Automation",
        package_slug="lead-qualification-automation",
        content="# Implementation Guide\n\nStep-by-step implementation...",
        prerequisites=["HubSpot API access", "Slack workspace admin"],
        installation_steps=[
            "Configure HubSpot API credentials",
            "Set up Slack bot permissions",
            "Import n8n workflow",
            "Test with sample data"
        ]
    )
    
    config_guide = ConfigurationGuide(
        title="Lead Qualification Configuration",
        audience="technical", 
        package_name="Lead Qualification Automation",
        package_slug="lead-qualification-automation",
        content="# Configuration Guide\n\nEnvironment variables...",
        environment_variables={
            "HUBSPOT_API_KEY": "HubSpot API key for CRM integration",
            "SLACK_BOT_TOKEN": "Slack bot token for notifications",
            "WEBHOOK_SECRET": "Secret for webhook validation"
        },
        api_keys_required=["HubSpot", "Slack"],
        rate_limits={"HubSpot": "100 requests/10 seconds", "Slack": "1 message/second"}
    )
    
    return DocumentationSuite(
        package_name="Lead Qualification Automation",
        package_slug="lead-qualification-automation",
        implementation_guide=impl_guide,
        configuration_guide=config_guide
    )


# ================================
# Notion Fixtures
# ================================

@pytest.fixture
def sample_notion_database():
    """Sample Notion database for testing."""
    return LibraryDatabase()


@pytest.fixture
def sample_notion_business_os():
    """Sample Notion Business OS for testing."""
    return NotionBusinessOS.create_default_schema()


@pytest.fixture
def mock_notion_client():
    """Mock Notion client for testing."""
    mock = Mock(spec=NotionClient)
    
    # Mock successful database creation
    mock.create_database.return_value = "db_123456789"
    
    # Mock successful page creation
    mock.create_page.return_value = "page_123456789"
    
    # Mock successful query
    mock.query_database.return_value = [
        {
            "id": "page_1",
            "properties": {
                "Name": {"title": [{"text": {"content": "Test Package"}}]},
                "Status": {"select": {"name": "Validated"}}
            }
        }
    ]
    
    # Mock successful schema verification
    mock.verify_database_schema.return_value = True
    
    return mock


# ================================
# Integration Fixtures  
# ================================

@pytest.fixture
def mock_workflow_processor():
    """Mock workflow processor for testing."""
    mock = Mock(spec=WorkflowProcessor)
    
    # Mock successful workflow loading
    sample_workflow = N8nWorkflow(
        name="test_workflow",
        nodes=[],
        connections={}
    )
    mock.load_workflow_from_vault.return_value = sample_workflow
    mock.process_workflow.return_value = sample_workflow
    
    return mock


@pytest.fixture
def mock_niche_researcher():
    """Mock niche research for testing."""
    mock = Mock(spec=NicheResearcher)
    
    # Mock research results
    mock.research_niche.return_value = NicheBrief(
        niche_name="test_niche",
        profile={"industry": "Technology", "size": "SMB"},
        pain_points=[
            {
                "description": "Manual data entry",
                "impact_score": 0.8,
                "frequency": "daily",
                "existing_solutions": ["Excel", "Manual process"],
                "gaps": ["No automation", "Error prone"],
                "automation_potential": 0.9
            }
        ],
        opportunities=[
            {
                "title": "Automate data entry workflow",
                "description": "Reduce manual work by 80%",
                "roi_estimate": "High ROI (>300% in 12 months)"
            }
        ],
        research_confidence=0.85,
        technology_adoption="medium"
    )
    
    return mock


@pytest.fixture
def mock_validator():
    """Mock workflow validator for testing."""
    from src.modules.validation import ValidationResult
    
    mock = Mock(spec=WorkflowValidator)
    
    # Mock successful validation
    mock.validate_workflow.return_value = [
        ValidationResult(True, "schema", "Workflow structure is valid"),
        ValidationResult(True, "security", "No security issues found"),
        ValidationResult(True, "performance", "Performance within acceptable limits")
    ]
    
    mock.validate_package.return_value = [
        ValidationResult(True, "metadata", "Package metadata is complete")
    ]
    
    return mock


# ================================
# File and Path Fixtures
# ================================

@pytest.fixture
def temp_directory():
    """Temporary directory for testing file operations."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)


@pytest.fixture
def sample_fixtures_directory():
    """Sample fixtures directory with test data."""
    fixtures_path = Path(__file__).parent / "fixtures"
    fixtures_path.mkdir(exist_ok=True)
    return fixtures_path


@pytest.fixture
def sample_workflow_file(temp_directory, sample_workflow_json):
    """Sample workflow JSON file for testing."""
    workflow_file = temp_directory / "test_workflow.json"
    with open(workflow_file, 'w') as f:
        json.dump(sample_workflow_json, f, indent=2)
    return workflow_file


# ================================
# Environment and Configuration Fixtures
# ================================

@pytest.fixture
def mock_environment_variables(monkeypatch):
    """Mock environment variables for testing."""
    test_env_vars = {
        "NOTION_TOKEN": "test_notion_token_123",
        "HUBSPOT_API_KEY": "test_hubspot_key_123", 
        "SLACK_BOT_TOKEN": "test_slack_token_123",
        "N8N_API_URL": "http://localhost:5678/api/v1",
        "N8N_API_KEY": "test_n8n_key_123"
    }
    
    for key, value in test_env_vars.items():
        monkeypatch.setenv(key, value)
    
    return test_env_vars


# ================================
# Test Data Fixtures
# ================================

@pytest.fixture
def sample_test_data():
    """Sample test data for workflow simulation."""
    return {
        "webhook_data": {
            "email": "test@example.com",
            "name": "John Doe",
            "company": "Test Company",
            "source": "website_form"
        },
        "crm_response": {
            "contact_id": "12345",
            "status": "created",
            "qualification_score": 85
        },
        "expected_outputs": {
            "qualified": True,
            "next_action": "schedule_demo",
            "assigned_rep": "sales_rep_1"
        }
    }


@pytest.fixture
def performance_test_data():
    """Test data for performance testing."""
    return {
        "small_dataset": [{"id": i, "name": f"item_{i}"} for i in range(10)],
        "medium_dataset": [{"id": i, "name": f"item_{i}"} for i in range(100)],
        "large_dataset": [{"id": i, "name": f"item_{i}"} for i in range(1000)]
    }


# ================================
# Error Simulation Fixtures
# ================================

@pytest.fixture
def api_error_responses():
    """Simulated API error responses for testing."""
    return {
        "notion_unauthorized": {
            "status": 401,
            "code": "unauthorized",
            "message": "The bearer token is not valid."
        },
        "notion_not_found": {
            "status": 404,
            "code": "object_not_found", 
            "message": "Could not find database with ID: 12345"
        },
        "notion_rate_limit": {
            "status": 429,
            "code": "rate_limited",
            "message": "Rate limited. Please retry after 60 seconds."
        },
        "hubspot_error": {
            "status": 400,
            "message": "Invalid API key"
        },
        "n8n_execution_error": {
            "status": 500,
            "message": "Workflow execution failed"
        }
    }


# ================================
# Validation Test Fixtures
# ================================

@pytest.fixture
def validation_test_cases():
    """Test cases for comprehensive validation testing."""
    return {
        "valid_package": {
            "name": "Valid Package",
            "slug": "valid-package", 
            "problem_statement": "Clear problem definition",
            "roi_notes": "Clear ROI calculation",
            "version": "1.0.0"
        },
        "invalid_packages": [
            {
                "name": "",
                "error": "Name is required"
            },
            {
                "slug": "invalid slug!",
                "error": "Slug must be URL-safe"
            },
            {
                "version": "1.0",
                "error": "Version must follow semantic versioning"
            }
        ],
        "security_violations": [
            {
                "type": "hardcoded_password",
                "content": '{"password": "secret123"}',
                "error": "Hardcoded credentials detected"
            },
            {
                "type": "missing_env_vars",
                "content": '{"api_key": "hardcoded_key"}',
                "error": "Should use environment variables"
            }
        ]
    }