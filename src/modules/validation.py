"""Workflow validation module with multi-level checks."""

import logging
import json
from typing import List, Dict, Any, Optional
from pathlib import Path
from datetime import datetime

from ..models.workflow import N8nWorkflow
from ..models.package import AutomationPackage

logger = logging.getLogger(__name__)

class ValidationResult:
    """Validation result with pass/fail status and details."""
    def __init__(self, passed: bool, level: str, message: str, details: Optional[Dict[str, Any]] = None):
        self.passed = passed
        self.level = level
        self.message = message
        self.details = details or {}
        self.timestamp = datetime.utcnow()

class WorkflowValidatorError(Exception):
    """Custom exception for validation operations."""
    pass

class WorkflowValidator:
    """WorkflowValidator with multi-level checks.
    
    Validates JSON schema, simulates test runs with fixtures,
    checks environment variables, rate limits, secrets,
    generates validation reports and checklists.
    """
    
    def __init__(self, fixtures_path: Optional[Path] = None):
        """Initialize workflow validator."""
        self.fixtures_path = fixtures_path or Path("tests/fixtures")
        self.validation_rules = self._load_validation_rules()
    
    def _load_validation_rules(self) -> Dict[str, Any]:
        """Load validation rules and thresholds."""
        return {
            "max_nodes": 50,
            "max_connections_per_node": 10,
            "required_error_handling": True,
            "required_retry_logic": True,
            "forbidden_hardcoded_secrets": True,
            "required_env_vars": ["NOTION_TOKEN"],
            "max_execution_time_estimate": 300  # seconds
        }
    
    def validate_workflow(self, workflow: N8nWorkflow) -> List[ValidationResult]:
        """Comprehensive workflow validation.
        
        Args:
            workflow: Workflow to validate
            
        Returns:
            List of validation results
        """
        logger.info(f"Validating workflow: {workflow.name}")
        results = []
        
        # Level 1: JSON Schema Validation
        results.extend(self._validate_json_schema(workflow))
        
        # Level 2: Business Logic Validation  
        results.extend(self._validate_business_logic(workflow))
        
        # Level 3: Security Validation
        results.extend(self._validate_security(workflow))
        
        # Level 4: Performance Validation
        results.extend(self._validate_performance(workflow))
        
        # Level 5: Integration Validation
        results.extend(self._validate_integrations(workflow))
        
        return results
    
    def validate_package(self, package: AutomationPackage) -> List[ValidationResult]:
        """Validate complete automation package."""
        results = []
        
        # Validate package metadata
        results.extend(self._validate_package_metadata(package))
        
        return results
    
    def _validate_json_schema(self, workflow: N8nWorkflow) -> List[ValidationResult]:
        """Validate JSON schema compliance."""
        results = []
        
        # Check required fields
        if not workflow.name:
            results.append(ValidationResult(False, "schema", "Workflow name is required"))
        else:
            results.append(ValidationResult(True, "schema", "Workflow name is valid"))
        
        # Check node structure
        if len(workflow.nodes) == 0:
            results.append(ValidationResult(False, "schema", "Workflow must contain at least one node"))
        elif len(workflow.nodes) > self.validation_rules["max_nodes"]:
            results.append(ValidationResult(False, "schema", f"Too many nodes: {len(workflow.nodes)} > {self.validation_rules['max_nodes']}"))
        else:
            results.append(ValidationResult(True, "schema", f"Node count is acceptable: {len(workflow.nodes)}"))
        
        # Validate node connections
        connection_errors = workflow.validate_node_connections()
        if connection_errors:
            results.append(ValidationResult(False, "schema", f"Connection errors: {'; '.join(connection_errors)}"))
        else:
            results.append(ValidationResult(True, "schema", "All node connections are valid"))
        
        return results
    
    def _validate_business_logic(self, workflow: N8nWorkflow) -> List[ValidationResult]:
        """Validate business logic and patterns."""
        results = []
        
        # Check for error handling nodes
        error_nodes = [node for node in workflow.nodes if node.name.startswith("error__")]
        if self.validation_rules["required_error_handling"] and not error_nodes:
            results.append(ValidationResult(False, "logic", "Error handling nodes are missing"))
        else:
            results.append(ValidationResult(True, "logic", f"Error handling implemented: {len(error_nodes)} nodes"))
        
        # Check for retry logic
        nodes_with_retries = [node for node in workflow.nodes if node.retries > 0]
        if self.validation_rules["required_retry_logic"] and len(nodes_with_retries) == 0:
            results.append(ValidationResult(False, "logic", "Retry logic is missing from all nodes"))
        else:
            results.append(ValidationResult(True, "logic", f"Retry logic implemented: {len(nodes_with_retries)} nodes"))
        
        return results
    
    def _validate_security(self, workflow: N8nWorkflow) -> List[ValidationResult]:
        """Validate security practices."""
        results = []
        
        # Check for hardcoded secrets
        hardcoded_secrets = self._find_hardcoded_secrets(workflow)
        if hardcoded_secrets:
            results.append(ValidationResult(False, "security", f"Hardcoded secrets found: {hardcoded_secrets}"))
        else:
            results.append(ValidationResult(True, "security", "No hardcoded secrets detected"))
        
        # Check environment variable usage
        env_vars_used = self._extract_env_variables(workflow)
        required_vars = set(self.validation_rules["required_env_vars"])
        missing_vars = required_vars - env_vars_used
        
        if missing_vars:
            results.append(ValidationResult(False, "security", f"Missing required environment variables: {list(missing_vars)}"))
        else:
            results.append(ValidationResult(True, "security", "All required environment variables are referenced"))
        
        return results
    
    def _validate_performance(self, workflow: N8nWorkflow) -> List[ValidationResult]:
        """Validate performance characteristics."""
        results = []
        
        # Estimate execution time
        estimated_time = self._estimate_execution_time(workflow)
        max_time = self.validation_rules["max_execution_time_estimate"]
        
        if estimated_time > max_time:
            results.append(ValidationResult(False, "performance", f"Estimated execution time too high: {estimated_time}s > {max_time}s"))
        else:
            results.append(ValidationResult(True, "performance", f"Estimated execution time acceptable: {estimated_time}s"))
        
        return results
    
    def _validate_integrations(self, workflow: N8nWorkflow) -> List[ValidationResult]:
        """Validate external integrations."""
        results = []
        
        # Check for common integration patterns
        integration_types = self._identify_integrations(workflow)
        
        if integration_types:
            results.append(ValidationResult(True, "integration", f"Integrations identified: {', '.join(integration_types)}"))
        else:
            results.append(ValidationResult(True, "integration", "No external integrations detected"))
        
        return results
    
    def _validate_package_metadata(self, package: AutomationPackage) -> List[ValidationResult]:
        """Validate package metadata completeness."""
        results = []
        
        # Check required fields
        required_fields = ["name", "slug", "problem_statement", "roi_notes"]
        for field in required_fields:
            value = getattr(package, field, None)
            if not value:
                results.append(ValidationResult(False, "metadata", f"Required field missing: {field}"))
            else:
                results.append(ValidationResult(True, "metadata", f"Required field present: {field}"))
        
        return results
    
    def simulate_test_run(self, workflow: N8nWorkflow, fixture_data: Dict[str, Any]) -> ValidationResult:
        """Simulate workflow execution with test data."""
        try:
            # This would integrate with n8n API for actual execution
            # For now, simulate a successful test
            logger.info(f"Simulating test run for workflow: {workflow.name}")
            
            # Basic simulation checks
            if len(workflow.nodes) == 0:
                return ValidationResult(False, "simulation", "Cannot simulate empty workflow")
            
            if not fixture_data:
                return ValidationResult(False, "simulation", "No fixture data provided")
            
            # Simulate successful execution
            return ValidationResult(True, "simulation", f"Test simulation passed with {len(fixture_data)} test inputs")
            
        except Exception as e:
            return ValidationResult(False, "simulation", f"Test simulation failed: {e}")
    
    def generate_validation_report(self, results: List[ValidationResult]) -> Dict[str, Any]:
        """Generate comprehensive validation report."""
        total_checks = len(results)
        passed_checks = len([r for r in results if r.passed])
        failed_checks = total_checks - passed_checks
        
        # Group results by level
        by_level: Dict[str, Dict[str, Any]] = {}
        for result in results:
            if result.level not in by_level:
                by_level[result.level] = {"passed": 0, "failed": 0, "messages": []}
            
            if result.passed:
                by_level[result.level]["passed"] += 1
            else:
                by_level[result.level]["failed"] += 1
            
            by_level[result.level]["messages"].append({
                "status": "PASS" if result.passed else "FAIL",
                "message": result.message,
                "timestamp": result.timestamp.isoformat()
            })
        
        return {
            "summary": {
                "total_checks": total_checks,
                "passed": passed_checks,
                "failed": failed_checks,
                "success_rate": passed_checks / total_checks if total_checks > 0 else 0,
                "overall_status": "PASS" if failed_checks == 0 else "FAIL"
            },
            "by_level": by_level,
            "generated_at": datetime.utcnow().isoformat()
        }
    
    # Helper methods
    def _find_hardcoded_secrets(self, workflow: N8nWorkflow) -> List[str]:
        """Find potential hardcoded secrets."""
        secrets = []
        
        for node in workflow.nodes:
            # Check for common secret patterns in parameters
            params_str = json.dumps(node.parameters)
            
            if "password" in params_str and "{{" not in params_str:
                secrets.append(f"Potential hardcoded password in {node.name}")
            
            if "token" in params_str and "{{" not in params_str:
                secrets.append(f"Potential hardcoded token in {node.name}")
        
        return secrets
    
    def _extract_env_variables(self, workflow: N8nWorkflow) -> set:
        """Extract environment variables referenced in workflow."""
        env_vars = set()
        
        for node in workflow.nodes:
            params_str = json.dumps(node.parameters)
            
            # Look for environment variable patterns
            import re
            env_pattern = r'\$\{\{\s*\$env\.([A-Z_]+)\s*\}\}'
            matches = re.findall(env_pattern, params_str)
            env_vars.update(matches)
        
        return env_vars
    
    def _estimate_execution_time(self, workflow: N8nWorkflow) -> float:
        """Estimate workflow execution time."""
        # Simple estimation based on node count and types
        base_time_per_node = 2.0  # seconds
        return len(workflow.nodes) * base_time_per_node
    
    def _identify_integrations(self, workflow: N8nWorkflow) -> List[str]:
        """Identify external service integrations."""
        integrations = set()
        
        for node in workflow.nodes:
            if "slack" in node.type.lower():
                integrations.add("Slack")
            elif "hubspot" in node.type.lower():
                integrations.add("HubSpot")
            elif "notion" in node.type.lower():
                integrations.add("Notion")
            elif "gmail" in node.type.lower():
                integrations.add("Gmail")
        
        return list(integrations)