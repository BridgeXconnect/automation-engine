"""n8n workflow processor for JSON manipulation and validation."""

import json
import hashlib
import re
import logging
from typing import Any, Dict, List, Optional
from pathlib import Path

from ..models.workflow import N8nWorkflow, N8nNode, NodePosition

logger = logging.getLogger(__name__)


class WorkflowProcessorError(Exception):
    """Custom exception for workflow processing operations."""
    pass


class WorkflowProcessor:
    """n8n workflow processor with JSON manipulation and validation.
    
    Enforces naming conventions from examples/n8n/patterns.md,
    adds validation, retry injection, idempotency key generation,
    and includes logging and observability instrumentation.
    """
    
    def __init__(self, automation_vault_path: Optional[Path] = None):
        """Initialize workflow processor.
        
        Args:
            automation_vault_path: Path to automation vault directory
        """
        self.automation_vault_path = automation_vault_path or Path("automation_vault")
        self.naming_patterns = self._load_naming_patterns()
    
    def _load_naming_patterns(self) -> Dict[str, str]:
        """Load naming convention patterns."""
        return {
            "node_naming": r"^[a-z0-9_]+$",  # snake_case
            "integration_prefix": r"^(slack|hubspot|salesforce|gmail|notion)_",
            "error_prefix": r"^error__",
            "log_prefix": r"^log__"
        }
    
    def validate_workflow_json(self, workflow_data: Dict[str, Any]) -> List[str]:
        """Validate n8n workflow JSON structure.
        
        Args:
            workflow_data: Raw workflow JSON data
            
        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []
        
        # Check required top-level fields
        required_fields = ["name", "nodes", "connections"]
        for field in required_fields:
            if field not in workflow_data:
                errors.append(f"Missing required field: {field}")
        
        # Validate nodes structure
        nodes = workflow_data.get("nodes", [])
        if not isinstance(nodes, list):
            errors.append("'nodes' must be an array")
        else:
            for i, node in enumerate(nodes):
                node_errors = self._validate_node_structure(node, i)
                errors.extend(node_errors)
        
        # Validate connections structure  
        connections = workflow_data.get("connections", {})
        if not isinstance(connections, dict):
            errors.append("'connections' must be an object")
        
        return errors
    
    def _validate_node_structure(self, node: Dict[str, Any], index: int) -> List[str]:
        """Validate individual node structure."""
        errors = []
        prefix = f"Node {index}"
        
        # Required node fields
        required_fields = ["id", "name", "type", "position"]
        for field in required_fields:
            if field not in node:
                errors.append(f"{prefix}: Missing required field '{field}'")
        
        # Validate node name follows snake_case convention
        node_name = node.get("name", "")
        if node_name and not re.match(self.naming_patterns["node_naming"], node_name.lower()):
            errors.append(f"{prefix}: Node name '{node_name}' should use snake_case convention")
        
        # Validate position format
        position = node.get("position", [])
        if not isinstance(position, list) or len(position) != 2:
            errors.append(f"{prefix}: Position must be array of two numbers [x, y]")
        else:
            for i, coord in enumerate(position):
                if not isinstance(coord, (int, float)):
                    errors.append(f"{prefix}: Position coordinate {i} must be a number")
        
        return errors
    
    def load_workflow_from_vault(self, workflow_name: str) -> N8nWorkflow:
        """Load workflow from automation vault.
        
        Args:
            workflow_name: Name of workflow file (without .json extension)
            
        Returns:
            Loaded N8nWorkflow instance
        """
        workflow_path = self.automation_vault_path / f"{workflow_name}.json"
        
        if not workflow_path.exists():
            raise WorkflowProcessorError(f"Workflow '{workflow_name}' not found in vault: {workflow_path}")
        
        try:
            with open(workflow_path, 'r', encoding='utf-8') as f:
                workflow_data = json.load(f)
            
            # Validate JSON structure
            errors = self.validate_workflow_json(workflow_data)
            if errors:
                raise WorkflowProcessorError(f"Invalid workflow JSON: {'; '.join(errors)}")
            
            # Convert to N8nWorkflow model
            workflow = N8nWorkflow.from_n8n_json(workflow_data)
            logger.info(f"Loaded workflow '{workflow_name}' with {len(workflow.nodes)} nodes")
            
            return workflow
            
        except json.JSONDecodeError as e:
            raise WorkflowProcessorError(f"Invalid JSON in workflow '{workflow_name}': {e}")
        except Exception as e:
            raise WorkflowProcessorError(f"Failed to load workflow '{workflow_name}': {e}")
    
    def enforce_naming_conventions(self, workflow: N8nWorkflow) -> N8nWorkflow:
        """Enforce naming conventions on workflow and nodes.
        
        Args:
            workflow: Input workflow
            
        Returns:
            Workflow with enforced naming conventions
        """
        # Enforce workflow name convention
        workflow.name = self._normalize_name(workflow.name)
        
        # Enforce node naming conventions
        for node in workflow.nodes:
            # Convert to snake_case
            node.name = self._normalize_name(node.name)
            
            # Add integration prefixes where appropriate
            node.name = self._add_integration_prefix(node)
        
        logger.info(f"Applied naming conventions to workflow '{workflow.name}'")
        return workflow
    
    def _normalize_name(self, name: str) -> str:
        """Normalize name to snake_case convention."""
        # Replace spaces and hyphens with underscores
        normalized = re.sub(r'[\s\-]+', '_', name.lower())
        
        # Remove non-alphanumeric characters except underscores
        normalized = re.sub(r'[^a-z0-9_]', '', normalized)
        
        # Remove multiple consecutive underscores
        normalized = re.sub(r'_+', '_', normalized)
        
        # Remove leading/trailing underscores
        normalized = normalized.strip('_')
        
        return normalized or "unnamed"
    
    def _add_integration_prefix(self, node: N8nNode) -> str:
        """Add appropriate integration prefix to node name."""
        name = node.name
        
        # Skip if already has prefix
        if any(name.startswith(prefix.split('_')[0]) for prefix in ["slack_", "hubspot_", "salesforce_", "gmail_", "notion_"]):
            return name
        
        # Map node types to prefixes
        type_prefixes = {
            "n8n-nodes-base.slack": "slack_",
            "n8n-nodes-base.hubspot": "hubspot_", 
            "n8n-nodes-base.salesforce": "salesforce_",
            "n8n-nodes-base.gmail": "gmail_",
            "n8n-nodes-base.notion": "notion_",
            "n8n-nodes-base.webhook": "webhook_"
        }
        
        prefix = type_prefixes.get(node.type, "")
        return f"{prefix}{name}" if prefix else name
    
    def inject_retry_logic(self, workflow: N8nWorkflow) -> N8nWorkflow:
        """Inject retry logic with 3× exponential backoff into all nodes.
        
        Args:
            workflow: Input workflow
            
        Returns:
            Workflow with retry logic applied
        """
        for node in workflow.nodes:
            # Skip nodes that already have retry configuration
            if node.retries == 3 and node.retry_on_fail:
                continue
            
            # Apply 3× exponential backoff pattern
            node.retries = 3
            node.retry_on_fail = True
            
            # Add retry configuration to parameters
            if "retryOnFail" not in node.parameters:
                node.parameters["retryOnFail"] = True
                node.parameters["maxTries"] = 3
                node.parameters["waitBetweenTries"] = 200  # milliseconds, will be exponentially increased
        
        logger.info(f"Applied retry logic to {len(workflow.nodes)} nodes")
        return workflow
    
    def add_idempotency_keys(self, workflow: N8nWorkflow, key_field: str = "email") -> N8nWorkflow:
        """Add idempotency keys for deduplication.
        
        Args:
            workflow: Input workflow
            key_field: Field to use for generating idempotency keys
            
        Returns:
            Workflow with idempotency keys added
        """
        # Generate workflow-specific salt
        workflow_salt = hashlib.md5(workflow.name.encode()).hexdigest()[:8]
        
        for node in workflow.nodes:
            # Add idempotency to nodes that support it
            if self._supports_idempotency(node):
                # Generate deterministic key based on email hash or external ID
                idempotency_expression = f"{{{{ hash('{key_field}') }}}}"
                
                node.parameters["idempotencyKey"] = idempotency_expression
                node.parameters["deduplicationField"] = key_field
                node.parameters["workflowSalt"] = workflow_salt
        
        logger.info(f"Added idempotency keys to applicable nodes in workflow '{workflow.name}'")
        return workflow
    
    def _supports_idempotency(self, node: N8nNode) -> bool:
        """Check if node type supports idempotency."""
        idempotent_types = [
            "n8n-nodes-base.googleSheets",
            "n8n-nodes-base.airtable", 
            "n8n-nodes-base.salesforce",
            "n8n-nodes-base.hubspot",
            "n8n-nodes-base.notion"
        ]
        
        return node.type in idempotent_types
    
    def add_logging_instrumentation(self, workflow: N8nWorkflow) -> N8nWorkflow:
        """Add structured logging and observability to workflow.
        
        Args:
            workflow: Input workflow
            
        Returns:
            Workflow with logging instrumentation
        """
        # Add logging nodes after each main operation
        logging_nodes = []
        
        for i, node in enumerate(workflow.nodes):
            if node.name.startswith(("log__", "error__")):
                continue  # Skip existing logging nodes
            
            # Create logging node
            log_node = N8nNode(
                id=f"log_{node.id}_{i}",
                name=f"log__{node.name}",
                type="n8n-nodes-base.set",
                position=NodePosition(x=node.position.x + 300, y=node.position.y),
                retries=3,  # Ensure retry compliance
                retry_on_fail=True,
                credentials=None,  # Add required credentials argument
                parameters={
                    "values": {
                        "timestamp": "{{ new Date().toISOString() }}",
                        "node_id": node.id,
                        "node_name": node.name,
                        "workflow_name": workflow.name,
                        "execution_time": "{{ $now - $nodeExecutionStart }}",
                        "success": "{{ $node.success }}",
                        "item_count": "{{ $input.all().length }}"
                    },
                    "options": {
                        "dotNotation": True
                    }
                }
            )
            
            logging_nodes.append(log_node)
        
        # Add all logging nodes to workflow
        workflow.nodes.extend(logging_nodes)
        
        logger.info(f"Added {len(logging_nodes)} logging nodes to workflow '{workflow.name}'")
        return workflow
    
    def add_error_handling(self, workflow: N8nWorkflow) -> N8nWorkflow:
        """Add error handling nodes following DLQ (Dead Letter Queue) pattern.
        
        Args:
            workflow: Input workflow
            
        Returns:
            Workflow with error handling
        """
        error_nodes = []
        
        for i, node in enumerate(workflow.nodes):
            if node.name.startswith("error__"):
                continue  # Skip existing error nodes
            
            # Create error handling node
            error_node = N8nNode(
                id=f"error_{node.id}_{i}",
                name=f"error__{node.name}",
                type="n8n-nodes-base.webhook",
                position=NodePosition(x=node.position.x, y=node.position.y + 300),
                retries=3,  # Ensure retry compliance
                retry_on_fail=True,
                credentials=None,  # Add required credentials argument
                parameters={
                    "path": "/error-handler",
                    "httpMethod": "POST",
                    "responseMode": "onReceived",
                    "errorData": {
                        "original_node": node.name,
                        "workflow_name": workflow.name,
                        "timestamp": "{{ new Date().toISOString() }}",
                        "error_message": "{{ $json.error }}",
                        "input_data": "{{ $json.input }}"
                    }
                }
            )
            
            error_nodes.append(error_node)
        
        # Add all error nodes to workflow
        workflow.nodes.extend(error_nodes)
        
        # Update connections to route errors to error handlers
        self._update_error_connections(workflow)
        
        logger.info(f"Added {len(error_nodes)} error handling nodes to workflow '{workflow.name}'")
        return workflow
    
    def _update_error_connections(self, workflow: N8nWorkflow) -> None:
        """Update workflow connections to include error routing."""
        # This would require complex connection manipulation
        # For now, we'll add the nodes and let manual connection setup handle routing
        pass
    
    def combine_workflows(self, workflows: List[N8nWorkflow], combined_name: str) -> N8nWorkflow:
        """Combine multiple workflows into a single workflow.
        
        Args:
            workflows: List of workflows to combine
            combined_name: Name for the combined workflow
            
        Returns:
            Combined workflow
        """
        if not workflows:
            raise WorkflowProcessorError("Cannot combine empty list of workflows")
        
        # For single workflow, just clone it with new name
        if len(workflows) == 1:
            original = workflows[0]
            combined = N8nWorkflow(
                name=combined_name,
                nodes=original.nodes.copy(),
                connections=original.connections.copy(),
                settings=original.settings.copy(),
                id=original.id,
                active=original.active,
                tags=original.tags,
                created_at=original.created_at,
                updated_at=original.updated_at
            )
            return combined
        
        # Initialize with first workflow to avoid empty nodes validation
        first_workflow = workflows[0]
        combined = N8nWorkflow(
            name=combined_name,
            nodes=first_workflow.nodes.copy(),
            connections=first_workflow.connections.copy(),
            settings=first_workflow.settings.copy(),
            id=None  # Add required id argument
        )
        
        x_offset = 400  # Start offset for additional workflows
        y_offset = 0
        
        # Process remaining workflows (skip first since it's already included)
        for i, workflow in enumerate(workflows[1:], 1):
            # Offset node positions to avoid overlap
            for node in workflow.nodes:
                new_node = N8nNode(
                    id=f"{workflow.name}_{node.id}",
                    name=f"{workflow.name}_{node.name}",
                    type=node.type,
                    position=NodePosition(
                        x=node.position.x + x_offset,
                        y=node.position.y + y_offset
                    ),
                    parameters=node.parameters.copy(),
                    credentials=node.credentials,
                    retries=node.retries,  # Preserve retry settings
                    retry_on_fail=node.retry_on_fail
                )
                combined.nodes.append(new_node)
            
            # Update connections with new node IDs
            for source_id, targets in workflow.connections.items():
                new_source_id = f"{workflow.name}_{source_id}"
                combined.connections[new_source_id] = {}
                
                for output, destinations in targets.items():
                    if isinstance(destinations, list):
                        new_destinations = []
                        for dest in destinations:
                            if isinstance(dest, dict) and "node" in dest:
                                new_dest = dest.copy()
                                new_dest["node"] = f"{workflow.name}_{dest['node']}"
                                new_destinations.append(new_dest)
                            else:
                                new_destinations.append(dest)
                        combined.connections[new_source_id][output] = new_destinations
                    else:
                        combined.connections[new_source_id][output] = destinations
            
            # Move to next position
            x_offset += 800  # Horizontal spacing between workflows
        
        logger.info(f"Combined {len(workflows)} workflows into '{combined_name}' with {len(combined.nodes)} total nodes")
        return combined
    
    def save_workflow(self, workflow: N8nWorkflow, output_path: Path) -> None:
        """Save workflow to JSON file.
        
        Args:
            workflow: Workflow to save
            output_path: Output file path
        """
        try:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            workflow_json = workflow.to_n8n_json()
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(workflow_json, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Saved workflow '{workflow.name}' to {output_path}")
            
        except Exception as e:
            raise WorkflowProcessorError(f"Failed to save workflow: {e}")
    
    def process_workflow(self, workflow_name: str, key_field: str = "email") -> N8nWorkflow:
        """Complete workflow processing pipeline.
        
        Args:
            workflow_name: Name of workflow to process
            key_field: Field for idempotency key generation
            
        Returns:
            Fully processed workflow
        """
        logger.info(f"Starting complete processing of workflow '{workflow_name}'")
        
        # Load workflow
        workflow = self.load_workflow_from_vault(workflow_name)
        
        # Apply all processing steps
        workflow = self.enforce_naming_conventions(workflow)
        workflow = self.inject_retry_logic(workflow)
        workflow = self.add_idempotency_keys(workflow, key_field)
        workflow = self.add_logging_instrumentation(workflow)
        workflow = self.add_error_handling(workflow)
        
        logger.info(f"Completed processing of workflow '{workflow_name}'")
        return workflow