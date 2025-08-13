"""n8n workflow data models and validation."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, field_validator
from datetime import datetime, timezone


class NodePosition(BaseModel):
    """Position coordinates for n8n nodes."""
    x: float = Field(..., description="X coordinate")
    y: float = Field(..., description="Y coordinate")


class N8nNode(BaseModel):
    """Individual n8n workflow node."""
    id: str = Field(..., description="Unique node identifier")
    name: str = Field(..., description="Node display name")
    type: str = Field(..., description="Node type (e.g., 'n8n-nodes-base.webhook')")
    position: NodePosition = Field(..., description="Node position on canvas")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Node configuration parameters")
    credentials: Optional[Dict[str, Any]] = Field(None, description="Node credentials reference")
    retries: int = Field(default=3, description="Number of retry attempts")
    retry_on_fail: bool = Field(default=True, description="Whether to retry on failure")
    
    @field_validator("name")
    @classmethod
    def validate_naming_convention(cls, v: str) -> str:
        """Enforce snake_case naming convention from examples/n8n/patterns.md."""
        # Check for invalid characters (anything other than letters, numbers, underscores)
        valid_chars = set('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_')
        if not all(c in valid_chars for c in v):
            raise ValueError("Node names should use snake_case convention")
        
        # Check for spaces, uppercase, or special characters
        if ' ' in v or any(c.isupper() for c in v) or any(c in '!@#$%^&*()-+={}[]|\\:;"<>?,./~`' for c in v):
            raise ValueError("Node names should use snake_case convention")
            
        return v
    
    @field_validator("retries")
    @classmethod
    def validate_retry_count(cls, v: int) -> int:
        """Ensure retry count follows 3× exponential backoff pattern."""
        if v != 3:
            raise ValueError("Nodes should use exactly 3 retries for exponential backoff pattern")
        return v


class WorkflowConnection(BaseModel):
    """Connection between workflow nodes."""
    source_node: str = Field(..., description="Source node ID")
    destination_node: str = Field(..., description="Destination node ID") 
    source_output: str = Field(default="main", description="Source output connection")
    destination_input: str = Field(default="main", description="Destination input connection")


class N8nWorkflow(BaseModel):
    """n8n workflow model with JSON validation.
    
    Mirrors patterns from examples/n8n/patterns.md including naming conventions,
    retry patterns, idempotency, logging, and observability.
    """
    
    # Core Workflow Properties
    name: str = Field(..., description="Workflow name")
    nodes: List[N8nNode] = Field(..., description="Workflow nodes")
    connections: Dict[str, Any] = Field(default_factory=dict, description="Node connections")
    settings: Dict[str, Any] = Field(default_factory=dict, description="Workflow settings")
    
    # Metadata
    id: Optional[str] = Field(None, description="Workflow ID")
    active: bool = Field(default=False, description="Whether workflow is active")
    tags: List[str] = Field(default_factory=list, description="Workflow tags")
    
    # Observability and Logging
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    @field_validator("name")
    @classmethod
    def validate_workflow_naming(cls, v: str) -> str:
        """Enforce snake_case naming convention."""
        # Normalize name first, then validate
        normalized = v.lower().replace(' ', '_').replace('-', '_')
        
        # Remove invalid characters and convert to snake_case
        valid_chars = set('abcdefghijklmnopqrstuvwxyz0123456789_')
        normalized = ''.join(c if c in valid_chars else '_' for c in normalized)
        
        # Clean up multiple underscores
        import re
        normalized = re.sub(r'_+', '_', normalized).strip('_')
        
        return normalized
    
    @field_validator("nodes")
    @classmethod
    def validate_required_nodes(cls, v: List[N8nNode]) -> List[N8nNode]:
        """Ensure workflow has required nodes."""
        if not v or len(v) == 0:
            raise ValueError("Workflow must contain at least one node")
        return v
    
    def validate_node_connections(self) -> List[str]:
        """Validate that all node connections are valid.
        
        Returns:
            List of validation error messages, empty if valid
        """
        errors = []
        node_ids = {node.id for node in self.nodes}
        
        for source_id, connections in self.connections.items():
            if source_id not in node_ids:
                errors.append(f"Connection source node '{source_id}' not found in workflow")
                continue
                
            for output_name, destinations in connections.items():
                if not isinstance(destinations, list):
                    destinations = [destinations]
                    
                for dest in destinations:
                    if isinstance(dest, dict):
                        dest_node = dest.get("node")
                        if dest_node and dest_node not in node_ids:
                            errors.append(f"Connection destination node '{dest_node}' not found in workflow")
        
        return errors
    
    def add_idempotency_keys(self, key_field: str = "email") -> None:
        """Add idempotency keys to nodes that support it.
        
        Args:
            key_field: Field to use for generating idempotency keys
        """
        for node in self.nodes:
            if node.type in ["n8n-nodes-base.googleSheets", "n8n-nodes-base.airtable"]:
                if "parameters" not in node.parameters:
                    node.parameters["parameters"] = {}
                
                # Add email hash or external ID for deduplication
                node.parameters["idempotencyKey"] = f"hash({key_field})"
    
    def add_logging_instrumentation(self) -> None:
        """Add structured logging to all nodes."""
        for i, node in enumerate(self.nodes):
            # Add timestamp and node ID tracking
            logging_node = N8nNode(
                id=f"log_{node.id}",
                name=f"log__{node.name}",
                type="n8n-nodes-base.set",
                position=NodePosition(x=node.position.x + 200, y=node.position.y),
                parameters={
                    "values": {
                        "timestamp": "{{ new Date().toISOString() }}",
                        "node_id": node.id,
                        "execution_time": "{{ $now - $nodeExecutionStart }}"
                    }
                },
                credentials=None
            )
            
            # Insert logging node after each main node
            self.nodes.insert(i + 1, logging_node)
    
    def add_error_handling(self) -> None:
        """Add error handling nodes following DLQ pattern."""
        error_nodes = []
        
        for node in self.nodes:
            if not node.name.startswith("error__"):
                error_node = N8nNode(
                    id=f"error_{node.id}",
                    name=f"error__{node.name}",
                    type="n8n-nodes-base.webhook",
                    position=NodePosition(x=node.position.x, y=node.position.y + 200),
                    parameters={
                        "path": "/error-handler",
                        "httpMethod": "POST",
                        "responseMode": "onReceived"
                    },
                    credentials=None
                )
                error_nodes.append(error_node)
        
        self.nodes.extend(error_nodes)
    
    def to_n8n_json(self) -> Dict[str, Any]:
        """Convert to n8n-compatible JSON format."""
        return {
            "name": self.name,
            "nodes": [
                {
                    "id": node.id,
                    "name": node.name,
                    "type": node.type,
                    "position": [node.position.x, node.position.y],
                    "parameters": node.parameters,
                    **({"credentials": node.credentials} if node.credentials else {})
                }
                for node in self.nodes
            ],
            "connections": self.connections,
            "settings": self.settings,
            "active": self.active,
            "tags": self.tags,
            **({"id": self.id} if self.id else {})
        }
    
    @classmethod
    def from_n8n_json(cls, data: Dict[str, Any]) -> "N8nWorkflow":
        """Create workflow from n8n JSON export."""
        nodes = []
        for node_data in data.get("nodes", []):
            position = node_data.get("position", [0, 0])
            nodes.append(N8nNode(
                id=node_data["id"],
                name=node_data["name"],
                type=node_data["type"],
                position=NodePosition(x=position[0], y=position[1]),
                parameters=node_data.get("parameters", {}),
                credentials=node_data.get("credentials")
            ))
        
        return cls(
            name=data["name"],
            nodes=nodes,
            connections=data.get("connections", {}),
            settings=data.get("settings", {}),
            id=data.get("id"),
            active=data.get("active", False),
            tags=data.get("tags", [])
        )
    
    def to_n8n_format(self) -> Dict[str, Any]:
        """Convert workflow to n8n JSON format.
        
        Returns:
            Dictionary in n8n export format
        """
        nodes_data: List[Dict[str, Any]] = []
        for node in self.nodes:
            node_data: Dict[str, Any] = {
                "id": node.id,
                "name": node.name,
                "type": node.type,
                "position": [node.position.x, node.position.y],
                "parameters": node.parameters
            }
            if node.credentials:
                node_data["credentials"] = node.credentials
            if node.retries != 3:  # Only include if different from default
                node_data["retries"] = node.retries
            if not node.retry_on_fail:  # Only include if different from default
                node_data["retryOnFail"] = node.retry_on_fail
            nodes_data.append(node_data)
        
        return {
            "name": self.name,
            "nodes": nodes_data,
            "connections": self.connections,
            "settings": self.settings,
            "id": self.id,
            "active": self.active,
            "tags": self.tags,
            "createdAt": self.created_at.isoformat() if self.created_at else None,
            "updatedAt": self.updated_at.isoformat() if self.updated_at else None
        }