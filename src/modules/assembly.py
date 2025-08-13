"""Workflow assembly module for combining and adapting n8n workflows."""

import logging
from typing import List, Optional
from pathlib import Path

from ..models.workflow import N8nWorkflow
from ..integrations.n8n_processor import WorkflowProcessor
from .opportunity_mapping import AutomationOpportunity

logger = logging.getLogger(__name__)

class WorkflowAssemblerError(Exception):
    """Custom exception for workflow assembly operations."""
    pass

class WorkflowAssembler:
    """WorkflowAssembler for n8n workflow combination.
    
    Pulls workflows from automation_vault/ directory,
    adapts naming, injects retries, adds idempotency keys,
    validates workflow compatibility and connections.
    """
    
    def __init__(self, automation_vault_path: Optional[Path] = None):
        """Initialize workflow assembler."""
        self.vault_path = automation_vault_path or Path("automation_vault")
        self.processor = WorkflowProcessor(self.vault_path)
        
    def assemble_workflows(self, workflow_names: List[str], 
                         opportunity: AutomationOpportunity) -> N8nWorkflow:
        """Assemble multiple workflows into a complete automation solution.
        
        Args:
            workflow_names: List of workflow names from vault
            opportunity: Target automation opportunity
            
        Returns:
            Combined and processed workflow
        """
        logger.info(f"Assembling workflows for opportunity: {opportunity.title}")
        
        try:
            # Load workflows from vault
            workflows = []
            for name in workflow_names:
                workflow = self.processor.load_workflow_from_vault(name)
                workflows.append(workflow)
            
            # Combine workflows
            combined_name = self._generate_workflow_name(opportunity)
            combined_workflow = self.processor.combine_workflows(workflows, combined_name)
            
            # Apply processing pipeline
            combined_workflow = self.processor.enforce_naming_conventions(combined_workflow)
            combined_workflow = self.processor.inject_retry_logic(combined_workflow)
            combined_workflow = self.processor.add_idempotency_keys(combined_workflow)
            combined_workflow = self.processor.add_logging_instrumentation(combined_workflow)
            combined_workflow = self.processor.add_error_handling(combined_workflow)
            
            # Validate compatibility
            validation_errors = combined_workflow.validate_node_connections()
            if validation_errors:
                logger.warning(f"Connection validation warnings: {validation_errors}")
            
            logger.info(f"Successfully assembled workflow '{combined_name}' with {len(combined_workflow.nodes)} nodes")
            return combined_workflow
            
        except Exception as e:
            raise WorkflowAssemblerError(f"Failed to assemble workflows: {e}")
    
    def _generate_workflow_name(self, opportunity: AutomationOpportunity) -> str:
        """Generate workflow name from opportunity."""
        # Convert opportunity title to snake_case
        name = opportunity.title.lower()
        name = name.replace(" ", "_").replace("-", "_")
        name = "".join(c for c in name if c.isalnum() or c == "_")
        return f"{name}_automation"
    
    def get_available_workflows(self) -> List[str]:
        """Get list of available workflows in vault."""
        if not self.vault_path.exists():
            return []
        
        workflows = []
        for file_path in self.vault_path.glob("*.json"):
            workflows.append(file_path.stem)
        
        return workflows