"""Tests for API integration clients (Notion and n8n)."""

import pytest
import json
import time
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

from notion_client import APIResponseError, APIErrorCode

from src.integrations.notion_client import NotionClient, NotionClientError
from src.integrations.n8n_processor import WorkflowProcessor, WorkflowProcessorError
from src.models.package import AutomationPackage, PackageStatus
from src.models.workflow import N8nWorkflow, N8nNode, NodePosition
from src.models.notion import LibraryDatabase, NotionBusinessOS


class TestNotionClient:
    """Test NotionClient integration functionality."""
    
    def test_notion_client_initialization_success(self, mock_environment_variables):
        """Test successful NotionClient initialization."""
        client = NotionClient()
        
        assert client.max_retries == 3
        assert client.retry_delay == 1.0
        assert hasattr(client, 'client')
    
    def test_notion_client_initialization_no_token(self):
        """Test NotionClient initialization without token."""
        with pytest.raises(NotionClientError) as exc_info:
            NotionClient(auth_token=None)
        
        assert "NOTION_TOKEN environment variable is required" in str(exc_info.value)
    
    def test_notion_client_custom_config(self):
        """Test NotionClient with custom configuration."""
        client = NotionClient(
            auth_token="test_token",
            max_retries=5,
            retry_delay=2.0
        )
        
        assert client.max_retries == 5
        assert client.retry_delay == 2.0
    
    @patch('src.integrations.notion_client.Client')
    def test_create_database_success(self, mock_client_class, mock_environment_variables):
        """Test successful database creation."""
        # Setup mock
        mock_client_instance = Mock()
        mock_client_class.return_value = mock_client_instance
        mock_client_instance.databases.create.return_value = {
            "id": "db_test_123",
            "title": [{"text": {"content": "Test Database"}}]
        }
        
        client = NotionClient()
        database_schema = LibraryDatabase()
        
        db_id = client.create_database("parent_page_123", database_schema)
        
        assert db_id == "db_test_123"
        mock_client_instance.databases.create.assert_called_once()
    
    @patch('src.integrations.notion_client.Client')
    def test_create_database_not_found_error(self, mock_client_class, mock_environment_variables):
        """Test database creation with parent page not found."""
        # Setup mock to raise not found error
        mock_client_instance = Mock()
        mock_client_class.return_value = mock_client_instance
        mock_client_instance.databases.create.side_effect = APIResponseError(
            response=Mock(status_code=404),
            message="Parent page not found",
            code=APIErrorCode.ObjectNotFound
        )
        
        client = NotionClient()
        database_schema = LibraryDatabase()
        
        with pytest.raises(NotionClientError) as exc_info:
            client.create_database("invalid_parent", database_schema)
        
        assert "Parent page invalid_parent not found" in str(exc_info.value)
    
    @patch('src.integrations.notion_client.Client')
    def test_query_database_success(self, mock_client_class, mock_environment_variables):
        """Test successful database query."""
        # Setup mock
        mock_client_instance = Mock()
        mock_client_class.return_value = mock_client_instance
        
        # Mock paginated response
        with patch('src.integrations.notion_client.collect_paginated_api') as mock_paginated:
            mock_paginated.return_value = [
                {"id": "page_1", "properties": {"Name": {"title": "Test 1"}}},
                {"id": "page_2", "properties": {"Name": {"title": "Test 2"}}}
            ]
            
            client = NotionClient()
            results = client.query_database("db_test_123")
            
            assert len(results) == 2
            assert results[0]["id"] == "page_1"
            mock_paginated.assert_called_once()
    
    @patch('src.integrations.notion_client.Client')
    def test_query_database_with_filters(self, mock_client_class, mock_environment_variables):
        """Test database query with filters and sorting."""
        mock_client_instance = Mock()
        mock_client_class.return_value = mock_client_instance
        
        with patch('src.integrations.notion_client.collect_paginated_api') as mock_paginated:
            mock_paginated.return_value = []
            
            client = NotionClient()
            filter_criteria = {"property": "Status", "select": {"equals": "Validated"}}
            sorts = [{"property": "Created", "direction": "descending"}]
            
            client.query_database("db_test_123", filter_criteria, sorts)
            
            # Verify the call was made with correct parameters
            call_args = mock_paginated.call_args
            assert call_args[1]["filter"] == filter_criteria
            assert call_args[1]["sorts"] == sorts
    
    @patch('src.integrations.notion_client.Client')
    def test_create_page_success(self, mock_client_class, mock_environment_variables):
        """Test successful page creation."""
        mock_client_instance = Mock()
        mock_client_class.return_value = mock_client_instance
        mock_client_instance.pages.create.return_value = {
            "id": "page_test_123",
            "properties": {"Name": {"title": "Test Page"}}
        }
        
        client = NotionClient()
        properties = {
            "Name": {"title": [{"text": {"content": "Test Page"}}]},
            "Status": {"select": {"name": "Active"}}
        }
        
        page_id = client.create_page("db_test_123", properties)
        
        assert page_id == "page_test_123"
        mock_client_instance.pages.create.assert_called_once()
    
    @patch('src.integrations.notion_client.Client')
    def test_update_page_success(self, mock_client_class, mock_environment_variables):
        """Test successful page update."""
        mock_client_instance = Mock()
        mock_client_class.return_value = mock_client_instance
        mock_client_instance.pages.update.return_value = {
            "id": "page_test_123",
            "properties": {"Status": {"select": {"name": "Updated"}}}
        }
        
        client = NotionClient()
        properties = {"Status": {"select": {"name": "Updated"}}}
        
        response = client.update_page("page_test_123", properties)
        
        assert response["id"] == "page_test_123"
        mock_client_instance.pages.update.assert_called_once_with(
            page_id="page_test_123",
            properties=properties
        )
    
    @patch('src.integrations.notion_client.Client')
    def test_retry_logic_success_after_failure(self, mock_client_class, mock_environment_variables):
        """Test retry logic succeeds after initial failure."""
        mock_client_instance = Mock()
        mock_client_class.return_value = mock_client_instance
        
        # First call fails, second succeeds
        mock_client_instance.databases.create.side_effect = [
            APIResponseError(
                response=Mock(status_code=429), 
                message="Rate limited",
                code=APIErrorCode.RateLimited
            ),
            {"id": "db_success_123"}
        ]
        
        client = NotionClient(retry_delay=0.01)  # Fast retry for testing
        database_schema = LibraryDatabase()
        
        with patch('time.sleep'):  # Mock sleep to speed up test
            db_id = client.create_database("parent_123", database_schema)
        
        assert db_id == "db_success_123"
        assert mock_client_instance.databases.create.call_count == 2
    
    @patch('src.integrations.notion_client.Client')
    def test_retry_logic_exhaustion(self, mock_client_class, mock_environment_variables):
        """Test retry logic exhaustion."""
        mock_client_instance = Mock()
        mock_client_class.return_value = mock_client_instance
        
        # Always fail
        mock_client_instance.databases.create.side_effect = APIResponseError(
            response=Mock(status_code=500),
            message="Internal server error",
            code=APIErrorCode.InternalServerError
        )
        
        client = NotionClient(max_retries=2, retry_delay=0.01)
        database_schema = LibraryDatabase()
        
        with patch('time.sleep'):  # Mock sleep
            with pytest.raises(APIResponseError):
                client.create_database("parent_123", database_schema)
        
        # Should try 3 times (initial + 2 retries)
        assert mock_client_instance.databases.create.call_count == 3
    
    @patch('src.integrations.notion_client.Client')
    def test_no_retry_for_unauthorized(self, mock_client_class, mock_environment_variables):
        """Test no retry for unauthorized errors."""
        mock_client_instance = Mock()
        mock_client_class.return_value = mock_client_instance
        
        mock_client_instance.databases.create.side_effect = APIResponseError(
            response=Mock(status_code=401),
            message="Unauthorized",
            code=APIErrorCode.Unauthorized
        )
        
        client = NotionClient()
        database_schema = LibraryDatabase()
        
        with pytest.raises(APIResponseError):
            client.create_database("parent_123", database_schema)
        
        # Should only try once (no retries for auth errors)
        assert mock_client_instance.databases.create.call_count == 1
    
    @patch('src.integrations.notion_client.Client')
    def test_create_business_os_success(self, mock_client_class, mock_environment_variables):
        """Test successful Business OS creation."""
        mock_client_instance = Mock()
        mock_client_class.return_value = mock_client_instance
        
        # Mock database creation responses
        create_call_count = 0
        def mock_create(**kwargs):
            nonlocal create_call_count
            create_call_count += 1
            return {"id": f"db_test_{create_call_count}"}
        
        mock_client_instance.databases.create.side_effect = mock_create
        
        client = NotionClient()
        database_ids = client.create_business_os("parent_page_123")
        
        assert len(database_ids) == 5  # All 5 databases created
        assert "library" in database_ids
        assert "automations" in database_ids
        assert "components" in database_ids
        assert "clients" in database_ids
        assert "deployments" in database_ids
    
    @patch('src.integrations.notion_client.Client')
    def test_create_library_record_success(self, mock_client_class, mock_environment_variables, sample_automation_package):
        """Test successful library record creation."""
        mock_client_instance = Mock()
        mock_client_class.return_value = mock_client_instance
        
        # Mock search response
        mock_client_instance.search.return_value = {
            "results": [{"id": "db_library_123", "title": "Library"}]
        }
        
        # Mock page creation
        mock_client_instance.pages.create.return_value = {
            "id": "page_record_123"
        }
        
        client = NotionClient()
        page_id = client.create_library_record(sample_automation_package)
        
        assert page_id == "page_record_123"
        mock_client_instance.search.assert_called_once_with(
            query="Library",
            filter={"value": "database", "property": "object"}
        )
        mock_client_instance.pages.create.assert_called_once()
    
    @patch('src.integrations.notion_client.Client')
    def test_verify_database_schema_success(self, mock_client_class, mock_environment_variables):
        """Test successful schema verification."""
        mock_client_instance = Mock()
        mock_client_class.return_value = mock_client_instance
        
        # Mock search to return all required databases
        mock_client_instance.search.return_value = {
            "results": [{"id": "db_123", "title": "Test Database"}]
        }
        
        client = NotionClient()
        result = client.verify_database_schema()
        
        assert result is True
        # Should search for each required database
        assert mock_client_instance.search.call_count == 5
    
    @patch('src.integrations.notion_client.Client')
    def test_verify_database_schema_missing_database(self, mock_client_class, mock_environment_variables):
        """Test schema verification with missing database."""
        mock_client_instance = Mock()
        mock_client_class.return_value = mock_client_instance
        
        # Mock search to return empty results for some databases
        def mock_search(query, **kwargs):
            if query == "Library":
                return {"results": [{"id": "db_123", "title": "Library"}]}
            else:
                return {"results": []}  # Missing database
        
        mock_client_instance.search.side_effect = mock_search
        
        client = NotionClient()
        
        with pytest.raises(NotionClientError) as exc_info:
            client.verify_database_schema()
        
        assert "Required database" in str(exc_info.value)
        assert "not found" in str(exc_info.value)


class TestWorkflowProcessor:
    """Test WorkflowProcessor functionality."""
    
    def test_workflow_processor_initialization(self, temp_directory):
        """Test WorkflowProcessor initialization."""
        processor = WorkflowProcessor(automation_vault_path=temp_directory)
        
        assert processor.automation_vault_path == temp_directory
        assert hasattr(processor, 'naming_patterns')
        assert isinstance(processor.naming_patterns, dict)
    
    def test_validate_workflow_json_success(self, temp_directory, sample_workflow_json):
        """Test successful workflow JSON validation."""
        processor = WorkflowProcessor(automation_vault_path=temp_directory)
        
        errors = processor.validate_workflow_json(sample_workflow_json)
        
        assert isinstance(errors, list)
        assert len(errors) == 0  # Should be valid
    
    def test_validate_workflow_json_errors(self, temp_directory):
        """Test workflow JSON validation with errors."""
        processor = WorkflowProcessor(automation_vault_path=temp_directory)
        
        # Invalid workflow JSON
        invalid_json = {
            "nodes": "not_an_array",  # Should be array
            "connections": []  # Should be object
            # Missing "name" field
        }
        
        errors = processor.validate_workflow_json(invalid_json)
        
        assert len(errors) > 0
        error_messages = " ".join(errors)
        assert "Missing required field: name" in error_messages
        assert "'nodes' must be an array" in error_messages
        assert "'connections' must be an object" in error_messages
    
    def test_validate_node_structure_success(self, temp_directory):
        """Test successful node structure validation."""
        processor = WorkflowProcessor(automation_vault_path=temp_directory)
        
        valid_node = {
            "id": "node_1",
            "name": "valid_node_name",
            "type": "n8n-nodes-base.webhook",
            "position": [100, 200],
            "parameters": {}
        }
        
        errors = processor._validate_node_structure(valid_node, 0)
        
        assert len(errors) == 0
    
    def test_validate_node_structure_errors(self, temp_directory):
        """Test node structure validation with errors."""
        processor = WorkflowProcessor(automation_vault_path=temp_directory)
        
        invalid_node = {
            "id": "node_1",
            "name": "Invalid Node Name!",  # Invalid naming
            "type": "n8n-nodes-base.webhook",
            "position": [100, "not_a_number"],  # Invalid position
            # Missing required fields
        }
        
        errors = processor._validate_node_structure(invalid_node, 0)
        
        assert len(errors) > 0
        error_messages = " ".join(errors)
        assert "snake_case" in error_messages
        assert "must be a number" in error_messages
    
    def test_load_workflow_from_vault_success(self, temp_directory, sample_workflow_file):
        """Test successful workflow loading from vault."""
        processor = WorkflowProcessor(automation_vault_path=temp_directory)
        
        # Get filename without extension
        workflow_name = sample_workflow_file.stem
        
        workflow = processor.load_workflow_from_vault(workflow_name)
        
        assert isinstance(workflow, N8nWorkflow)
        assert workflow.name == "sample_workflow"
        assert len(workflow.nodes) == 2
    
    def test_load_workflow_from_vault_not_found(self, temp_directory):
        """Test workflow loading with file not found."""
        processor = WorkflowProcessor(automation_vault_path=temp_directory)
        
        with pytest.raises(WorkflowProcessorError) as exc_info:
            processor.load_workflow_from_vault("nonexistent_workflow")
        
        assert "not found in vault" in str(exc_info.value)
    
    def test_load_workflow_from_vault_invalid_json(self, temp_directory):
        """Test workflow loading with invalid JSON."""
        processor = WorkflowProcessor(automation_vault_path=temp_directory)
        
        # Create invalid JSON file
        invalid_file = temp_directory / "invalid_workflow.json"
        with open(invalid_file, 'w') as f:
            f.write("{ invalid json }")
        
        with pytest.raises(WorkflowProcessorError) as exc_info:
            processor.load_workflow_from_vault("invalid_workflow")
        
        assert "Invalid JSON" in str(exc_info.value)
    
    def test_enforce_naming_conventions(self, temp_directory, sample_n8n_workflow):
        """Test naming convention enforcement."""
        processor = WorkflowProcessor(automation_vault_path=temp_directory)
        
        # Set invalid names
        sample_n8n_workflow.name = "Invalid Workflow Name!"
        sample_n8n_workflow.nodes[0].name = "Invalid Node Name!"
        
        updated_workflow = processor.enforce_naming_conventions(sample_n8n_workflow)
        
        # Names should be normalized
        assert updated_workflow.name == "invalid_workflow_name"
        assert updated_workflow.nodes[0].name == "invalid_node_name"
    
    def test_normalize_name(self, temp_directory):
        """Test name normalization."""
        processor = WorkflowProcessor(automation_vault_path=temp_directory)
        
        test_cases = [
            ("Valid Name", "valid_name"),
            ("has-hyphens-and spaces", "has_hyphens_and_spaces"),
            ("Special@#$%Characters", "specialcharacters"),
            ("Multiple___Underscores", "multiple_underscores"),
            ("", "unnamed")
        ]
        
        for input_name, expected in test_cases:
            result = processor._normalize_name(input_name)
            assert result == expected
    
    def test_add_integration_prefix(self, temp_directory):
        """Test integration prefix addition."""
        processor = WorkflowProcessor(automation_vault_path=temp_directory)
        
        # Test different node types
        test_cases = [
            ("n8n-nodes-base.slack", "test_node", "slack_test_node"),
            ("n8n-nodes-base.hubspot", "create_contact", "hubspot_create_contact"),
            ("n8n-nodes-base.webhook", "webhook_handler", "webhook_webhook_handler"),
            ("n8n-nodes-base.set", "data_processor", "data_processor")  # No prefix for set
        ]
        
        for node_type, node_name, expected in test_cases:
            node = N8nNode(
                id="test_1",
                name=node_name,
                type=node_type,
                position=NodePosition(x=0, y=0)
            )
            
            result = processor._add_integration_prefix(node)
            assert result == expected
    
    def test_inject_retry_logic(self, temp_directory, sample_n8n_workflow):
        """Test retry logic injection."""
        processor = WorkflowProcessor(automation_vault_path=temp_directory)
        
        # Remove retry config from sample workflow
        for node in sample_n8n_workflow.nodes:
            node.retries = 0
            node.retry_on_fail = False
        
        updated_workflow = processor.inject_retry_logic(sample_n8n_workflow)
        
        # All nodes should have retry logic
        for node in updated_workflow.nodes:
            assert node.retries == 3
            assert node.retry_on_fail is True
            assert node.parameters.get("retryOnFail") is True
            assert node.parameters.get("maxTries") == 3
    
    def test_add_idempotency_keys(self, temp_directory):
        """Test idempotency key addition.""" 
        processor = WorkflowProcessor(automation_vault_path=temp_directory)
        
        # Create workflow with idempotency-supporting nodes
        nodes = [
            N8nNode(
                id="hubspot_1",
                name="hubspot_node",
                type="n8n-nodes-base.hubspot",  # Supports idempotency
                position=NodePosition(x=100, y=100)
            ),
            N8nNode(
                id="webhook_1", 
                name="webhook_node",
                type="n8n-nodes-base.webhook",  # Doesn't support idempotency
                position=NodePosition(x=200, y=100)
            )
        ]
        
        workflow = N8nWorkflow(
            name="test_workflow",
            nodes=nodes,
            connections={}
        )
        
        updated_workflow = processor.add_idempotency_keys(workflow, "email")
        
        # Only HubSpot node should have idempotency key
        hubspot_node = next(n for n in updated_workflow.nodes if n.type == "n8n-nodes-base.hubspot")
        webhook_node = next(n for n in updated_workflow.nodes if n.type == "n8n-nodes-base.webhook")
        
        assert "idempotencyKey" in hubspot_node.parameters
        assert "deduplicationField" in hubspot_node.parameters
        assert "idempotencyKey" not in webhook_node.parameters
    
    def test_supports_idempotency(self, temp_directory):
        """Test idempotency support detection."""
        processor = WorkflowProcessor(automation_vault_path=temp_directory)
        
        idempotent_types = [
            "n8n-nodes-base.googleSheets",
            "n8n-nodes-base.airtable",
            "n8n-nodes-base.salesforce",
            "n8n-nodes-base.hubspot",
            "n8n-nodes-base.notion"
        ]
        
        non_idempotent_types = [
            "n8n-nodes-base.webhook",
            "n8n-nodes-base.set",
            "n8n-nodes-base.if"
        ]
        
        for node_type in idempotent_types:
            node = N8nNode(
                id="test_1",
                name="test_node",
                type=node_type,
                position=NodePosition(x=0, y=0)
            )
            assert processor._supports_idempotency(node) is True
        
        for node_type in non_idempotent_types:
            node = N8nNode(
                id="test_1", 
                name="test_node",
                type=node_type,
                position=NodePosition(x=0, y=0)
            )
            assert processor._supports_idempotency(node) is False
    
    def test_add_logging_instrumentation(self, temp_directory, sample_n8n_workflow):
        """Test logging instrumentation addition."""
        processor = WorkflowProcessor(automation_vault_path=temp_directory)
        
        original_node_count = len(sample_n8n_workflow.nodes)
        updated_workflow = processor.add_logging_instrumentation(sample_n8n_workflow)
        
        # Should have added logging nodes
        new_node_count = len(updated_workflow.nodes)
        assert new_node_count > original_node_count
        
        # Check for logging nodes
        logging_nodes = [n for n in updated_workflow.nodes if n.name.startswith("log__")]
        assert len(logging_nodes) == original_node_count
        
        # Check logging node structure
        log_node = logging_nodes[0]
        assert log_node.type == "n8n-nodes-base.set"
        assert "timestamp" in log_node.parameters["values"]
        assert "node_id" in log_node.parameters["values"]
    
    def test_add_error_handling(self, temp_directory, sample_n8n_workflow):
        """Test error handling addition."""
        processor = WorkflowProcessor(automation_vault_path=temp_directory)
        
        original_node_count = len(sample_n8n_workflow.nodes)
        updated_workflow = processor.add_error_handling(sample_n8n_workflow)
        
        # Should have added error nodes
        new_node_count = len(updated_workflow.nodes)
        assert new_node_count > original_node_count
        
        # Check for error nodes
        error_nodes = [n for n in updated_workflow.nodes if n.name.startswith("error__")]
        assert len(error_nodes) == original_node_count
        
        # Check error node structure
        error_node = error_nodes[0]
        assert error_node.type == "n8n-nodes-base.webhook"
        assert error_node.parameters["path"] == "/error-handler"
        assert error_node.parameters["httpMethod"] == "POST"
    
    def test_combine_workflows(self, temp_directory):
        """Test workflow combination."""
        processor = WorkflowProcessor(automation_vault_path=temp_directory)
        
        # Create two simple workflows
        workflow1 = N8nWorkflow(
            name="workflow_1",
            nodes=[N8nNode(
                id="node_1",
                name="webhook_1",
                type="n8n-nodes-base.webhook",
                position=NodePosition(x=100, y=100)
            )],
            connections={"node_1": {"main": []}}
        )
        
        workflow2 = N8nWorkflow(
            name="workflow_2", 
            nodes=[N8nNode(
                id="node_2",
                name="set_2",
                type="n8n-nodes-base.set",
                position=NodePosition(x=100, y=100)
            )],
            connections={"node_2": {"main": []}}
        )
        
        combined = processor.combine_workflows(
            [workflow1, workflow2],
            "combined_workflow"
        )
        
        assert combined.name == "combined_workflow"
        assert len(combined.nodes) == 2
        assert len(combined.connections) == 2
        
        # Check node ID prefixing
        node_ids = [n.id for n in combined.nodes]
        assert "workflow_1_node_1" in node_ids
        assert "workflow_2_node_2" in node_ids
    
    def test_combine_workflows_empty_list(self, temp_directory):
        """Test combining empty workflow list."""
        processor = WorkflowProcessor(automation_vault_path=temp_directory)
        
        with pytest.raises(WorkflowProcessorError) as exc_info:
            processor.combine_workflows([], "test")
        
        assert "Cannot combine empty list" in str(exc_info.value)
    
    def test_save_workflow(self, temp_directory, sample_n8n_workflow):
        """Test workflow saving."""
        processor = WorkflowProcessor(automation_vault_path=temp_directory)
        
        output_path = temp_directory / "saved_workflow.json"
        processor.save_workflow(sample_n8n_workflow, output_path)
        
        # Verify file was created
        assert output_path.exists()
        
        # Verify content
        with open(output_path, 'r') as f:
            saved_data = json.load(f)
        
        assert saved_data["name"] == sample_n8n_workflow.name
        assert len(saved_data["nodes"]) == len(sample_n8n_workflow.nodes)
    
    def test_process_workflow_complete_pipeline(self, temp_directory, sample_workflow_file):
        """Test complete workflow processing pipeline."""
        processor = WorkflowProcessor(automation_vault_path=temp_directory)
        
        workflow_name = sample_workflow_file.stem
        processed_workflow = processor.process_workflow(workflow_name, "email")
        
        assert isinstance(processed_workflow, N8nWorkflow)
        
        # Should have been processed (naming, retry logic, etc.)
        assert processed_workflow.name == "sample_workflow"  # Already valid
        
        # Should have logging and error nodes added
        node_names = [n.name for n in processed_workflow.nodes]
        log_nodes = [name for name in node_names if name.startswith("log__")]
        error_nodes = [name for name in node_names if name.startswith("error__")]
        
        assert len(log_nodes) > 0
        assert len(error_nodes) > 0


class TestIntegrationErrorHandling:
    """Test error handling across integrations."""
    
    def test_notion_client_network_error_handling(self, mock_environment_variables):
        """Test handling of network errors in Notion client."""
        with patch('src.integrations.notion_client.Client') as mock_client_class:
            mock_client_instance = Mock()
            mock_client_class.return_value = mock_client_instance
            
            # Simulate network error
            mock_client_instance.databases.create.side_effect = Exception("Network connection failed")
            
            client = NotionClient()
            database_schema = LibraryDatabase()
            
            with pytest.raises(NotionClientError) as exc_info:
                client.create_database("parent_123", database_schema)
            
            assert "Notion operation failed" in str(exc_info.value)
            assert "Network connection failed" in str(exc_info.value)
    
    def test_workflow_processor_file_system_errors(self, temp_directory):
        """Test handling of file system errors in workflow processor."""
        processor = WorkflowProcessor(automation_vault_path=temp_directory)
        
        # Test with read-only directory (simulated)
        with patch('pathlib.Path.mkdir') as mock_mkdir:
            mock_mkdir.side_effect = PermissionError("Permission denied")
            
            workflow = N8nWorkflow(
                name="test_workflow",
                nodes=[],
                connections={}
            )
            
            with pytest.raises(WorkflowProcessorError) as exc_info:
                processor.save_workflow(workflow, temp_directory / "test.json")
            
            assert "Failed to save workflow" in str(exc_info.value)
    
    def test_concurrent_access_handling(self, mock_environment_variables):
        """Test handling of concurrent access scenarios."""
        with patch('src.integrations.notion_client.Client') as mock_client_class:
            mock_client_instance = Mock()
            mock_client_class.return_value = mock_client_instance
            
            # Simulate race condition/conflict
            mock_client_instance.pages.update.side_effect = APIResponseError(
                response=Mock(status_code=409),
                message="Conflict - page was modified by another user",
                code=APIErrorCode.ConflictError
            )
            
            client = NotionClient(max_retries=1)
            
            with pytest.raises(APIResponseError):
                client.update_page("page_123", {"Status": {"select": {"name": "Updated"}}})
    
    def test_rate_limiting_scenarios(self, mock_environment_variables):
        """Test various rate limiting scenarios."""
        with patch('src.integrations.notion_client.Client') as mock_client_class:
            mock_client_instance = Mock()
            mock_client_class.return_value = mock_client_instance
            
            # Test exponential backoff with rate limiting
            rate_limit_error = APIResponseError(
                response=Mock(status_code=429),
                message="Rate limited",
                code=APIErrorCode.RateLimited
            )
            
            mock_client_instance.databases.query.side_effect = [
                rate_limit_error,
                rate_limit_error,
                {"results": []}  # Success on third try
            ]
            
            client = NotionClient(max_retries=2, retry_delay=0.01)
            
            with patch('time.sleep'):  # Mock sleep for fast testing
                results = client.query_database("db_123")
            
            assert results == []
            assert mock_client_instance.databases.query.call_count == 3


class TestIntegrationPerformance:
    """Test performance aspects of integrations."""
    
    def test_large_dataset_handling(self, mock_environment_variables):
        """Test handling of large datasets."""
        with patch('src.integrations.notion_client.Client') as mock_client_class:
            mock_client_instance = Mock()
            mock_client_class.return_value = mock_client_instance
            
            # Simulate large dataset
            large_dataset = [{"id": f"page_{i}", "title": f"Page {i}"} for i in range(1000)]
            
            with patch('src.integrations.notion_client.collect_paginated_api') as mock_paginated:
                mock_paginated.return_value = large_dataset
                
                client = NotionClient()
                results = client.query_database("db_123")
                
                assert len(results) == 1000
                # Verify pagination was used
                mock_paginated.assert_called_once()
    
    def test_workflow_processing_performance(self, temp_directory):
        """Test performance of workflow processing operations."""
        processor = WorkflowProcessor(automation_vault_path=temp_directory)
        
        # Create large workflow
        large_workflow = N8nWorkflow(
            name="large_workflow",
            nodes=[
                N8nNode(
                    id=f"node_{i}",
                    name=f"node_{i}",
                    type="n8n-nodes-base.set",
                    position=NodePosition(x=i*100, y=100)
                )
                for i in range(50)  # 50 nodes
            ],
            connections={}
        )
        
        # Time the processing
        import time
        start_time = time.time()
        
        processed = processor.inject_retry_logic(large_workflow)
        processed = processor.add_logging_instrumentation(processed)
        processed = processor.add_error_handling(processed)
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        # Should process in reasonable time (less than 1 second for 50 nodes)
        assert processing_time < 1.0
        assert len(processed.nodes) > 50  # Original + logging + error nodes
    
    def test_memory_efficiency(self, temp_directory):
        """Test memory efficiency of operations."""
        processor = WorkflowProcessor(automation_vault_path=temp_directory)
        
        # Test that we're not keeping unnecessary references
        workflow = N8nWorkflow(
            name="memory_test",
            nodes=[N8nNode(
                id="node_1",
                name="test_node", 
                type="n8n-nodes-base.set",
                position=NodePosition(x=100, y=100),
                parameters={"large_data": "x" * 10000}  # 10KB of data
            )],
            connections={}
        )
        
        # Process workflow multiple times
        for _ in range(10):
            processed = processor.inject_retry_logic(workflow)
            processed = processor.add_logging_instrumentation(processed)
            
        # Should not accumulate excessive memory (this is more of a regression test)
        assert len(processed.nodes) >= 2  # Original + logging node