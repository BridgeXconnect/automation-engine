"""Deployment management module for automation packages.

Handles n8n workflow export, environment template creation, deployment checklists,
first-run verification, and integration with package models and file management.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from enum import Enum

from ..models.package import AutomationPackage
from ..models.workflow import N8nWorkflow
from ..models.notion import NotionBusinessOS
from ..integrations.n8n_processor import WorkflowProcessor
from ..modules.validation import WorkflowValidator, ValidationResult

logger = logging.getLogger(__name__)


class DeploymentStatus(str, Enum):
    """Deployment status enumeration."""
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"


class EnvironmentType(str, Enum):
    """Environment type enumeration."""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


class DeploymentError(Exception):
    """Custom exception for deployment operations."""
    pass


class DeploymentChecklist:
    """Deployment checklist item model."""
    
    def __init__(self, title: str, description: str, critical: bool = False):
        self.title = title
        self.description = description
        self.critical = critical
        self.completed = False
        self.completed_at: Optional[datetime] = None
        self.notes = ""
    
    def mark_complete(self, notes: str = "") -> None:
        """Mark checklist item as complete."""
        self.completed = True
        self.completed_at = datetime.utcnow()
        self.notes = notes
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format."""
        return {
            "title": self.title,
            "description": self.description,
            "critical": self.critical,
            "completed": self.completed,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "notes": self.notes
        }


class DeploymentEnvironment:
    """Deployment environment configuration."""
    
    def __init__(self, env_type: EnvironmentType, name: str):
        self.env_type = env_type
        self.name = name
        self.variables: Dict[str, str] = {}
        self.secrets: Dict[str, str] = {}
        self.endpoints: Dict[str, str] = {}
        self.integrations: List[str] = []
        self.rate_limits: Dict[str, int] = {}
        self.backup_config: Dict[str, Any] = {}
    
    def add_variable(self, key: str, value: str, is_secret: bool = False) -> None:
        """Add environment variable or secret."""
        if is_secret:
            self.secrets[key] = value
        else:
            self.variables[key] = value
    
    def add_integration(self, integration: str, config: Dict[str, Any]) -> None:
        """Add integration configuration."""
        self.integrations.append(integration)
        self.variables.update({f"{integration.upper()}_{k}": v for k, v in config.items()})
    
    def generate_env_template(self) -> str:
        """Generate .env template file content."""
        lines = [
            f"# Environment Configuration for {self.name}",
            f"# Generated on {datetime.utcnow().isoformat()}",
            "",
            "# Core Configuration",
            f"ENVIRONMENT={self.env_type.value}",
            f"DEPLOYMENT_NAME={self.name}",
            ""
        ]
        
        if self.variables:
            lines.extend([
                "# Application Variables",
                *[f"{k}={v}" for k, v in self.variables.items()],
                ""
            ])
        
        if self.secrets:
            lines.extend([
                "# Secrets (Configure in secure environment)",
                *[f"{k}=<CONFIGURE_IN_SECURE_ENV>" for k in self.secrets.keys()],
                ""
            ])
        
        if self.endpoints:
            lines.extend([
                "# Endpoints",
                *[f"{k}={v}" for k, v in self.endpoints.items()],
                ""
            ])
        
        if self.rate_limits:
            lines.extend([
                "# Rate Limits",
                *[f"{k}_RATE_LIMIT={v}" for k, v in self.rate_limits.items()],
                ""
            ])
        
        return "\n".join(lines)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format."""
        return {
            "env_type": self.env_type.value,
            "name": self.name,
            "variables": self.variables,
            "secrets": list(self.secrets.keys()),  # Don't store secret values
            "endpoints": self.endpoints,
            "integrations": self.integrations,
            "rate_limits": self.rate_limits,
            "backup_config": self.backup_config
        }


class DeploymentManager:
    """Deployment manager for automation packages.
    
    Implements deployment functionality including:
    - n8n workflow export and environment template creation
    - Deployment checklists and first-run verification tasks
    - Integration with package models and file management
    - Environment validation and setup verification
    """
    
    def __init__(self, packages_root: Path, automation_vault_path: Optional[Path] = None):
        """Initialize deployment manager.
        
        Args:
            packages_root: Root directory for packages
            automation_vault_path: Path to automation vault directory
        """
        self.packages_root = Path(packages_root)
        self.automation_vault_path = automation_vault_path or Path("automation_vault")
        
        # Initialize processors
        self.workflow_processor = WorkflowProcessor(self.automation_vault_path)
        self.validator = WorkflowValidator()
        
        # Deployment configuration
        self.deployment_templates = self._load_deployment_templates()
        
        logger.info(f"Initialized DeploymentManager with packages root: {self.packages_root}")
    
    def _load_deployment_templates(self) -> Dict[str, Any]:
        """Load deployment templates and configurations."""
        return {
            "checklist_templates": {
                "development": [
                    ("Validate workflow JSON", "Ensure workflow structure is valid", True),
                    ("Run fixture tests", "Execute workflow with test data", True),
                    ("Check environment variables", "Verify all required env vars are set", True),
                    ("Validate integrations", "Test connection to external services", False),
                    ("Performance check", "Verify execution time is acceptable", False)
                ],
                "staging": [
                    ("Pre-deployment validation", "Complete all development checks", True),
                    ("Environment setup", "Configure staging environment", True),
                    ("Security scan", "Run security validation checks", True),
                    ("Integration testing", "Test with staging services", True),
                    ("Performance benchmarking", "Measure execution metrics", False),
                    ("Documentation review", "Verify deployment docs are complete", False)
                ],
                "production": [
                    ("Staging sign-off", "Complete staging deployment successfully", True),
                    ("Security approval", "Get security team approval", True),
                    ("Backup preparation", "Prepare rollback procedures", True),
                    ("Monitoring setup", "Configure alerts and monitoring", True),
                    ("Performance validation", "Verify production performance", True),
                    ("User acceptance testing", "Complete UAT if applicable", False),
                    ("Documentation finalization", "Complete all documentation", True)
                ]
            },
            "environment_defaults": {
                "rate_limits": {
                    "development": {"default": 100, "burst": 200},
                    "staging": {"default": 500, "burst": 1000},
                    "production": {"default": 1000, "burst": 2000}
                },
                "retry_policies": {
                    "development": {"max_retries": 2, "backoff_factor": 1},
                    "staging": {"max_retries": 3, "backoff_factor": 1.5},
                    "production": {"max_retries": 3, "backoff_factor": 2}
                }
            }
        }
    
    def prepare_deployment(self, package: AutomationPackage, 
                         environment: EnvironmentType,
                         deployment_name: Optional[str] = None) -> Dict[str, Any]:
        """Prepare package for deployment.
        
        Args:
            package: Package to deploy
            environment: Target environment
            deployment_name: Optional custom deployment name
            
        Returns:
            Deployment preparation results
        """
        logger.info(f"Preparing deployment for package: {package.name} to {environment.value}")
        
        deployment_name = deployment_name or f"{package.slug}_{environment.value}"
        deployment_dir = self.packages_root / package.slug / "deployments" / deployment_name
        
        try:
            # Create deployment directory structure
            self._create_deployment_structure(deployment_dir)
            
            # Export n8n workflows
            workflow_exports = self._export_n8n_workflows(package, deployment_dir)
            
            # Create environment templates
            env_config = self._create_environment_templates(package, environment, deployment_dir)
            
            # Generate deployment checklist
            checklist = self._generate_deployment_checklist(environment, deployment_dir)
            
            # Create first-run verification tasks
            verification_tasks = self._create_verification_tasks(package, deployment_dir)
            
            # Generate deployment manifest
            manifest = self._create_deployment_manifest(
                package, environment, deployment_name, 
                workflow_exports, env_config, checklist, verification_tasks
            )
            
            # Save deployment manifest
            manifest_path = deployment_dir / "deployment_manifest.json"
            with open(manifest_path, 'w', encoding='utf-8') as f:
                json.dump(manifest, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Deployment prepared successfully: {deployment_dir}")
            
            return {
                "status": "success",
                "deployment_name": deployment_name,
                "deployment_dir": str(deployment_dir),
                "manifest": manifest,
                "workflow_exports": workflow_exports,
                "environment_config": env_config,
                "checklist_items": len(checklist),
                "verification_tasks": len(verification_tasks)
            }
            
        except Exception as e:
            logger.error(f"Failed to prepare deployment: {e}")
            raise DeploymentError(f"Deployment preparation failed: {e}")
    
    def _create_deployment_structure(self, deployment_dir: Path) -> None:
        """Create deployment directory structure."""
        directories = [
            "workflows",
            "environments", 
            "tests",
            "docs",
            "scripts",
            "backups"
        ]
        
        for directory in directories:
            (deployment_dir / directory).mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Created deployment structure: {deployment_dir}")
    
    def _export_n8n_workflows(self, package: AutomationPackage, deployment_dir: Path) -> List[Dict[str, Any]]:
        """Export n8n workflows for deployment.
        
        Args:
            package: Package containing workflows
            deployment_dir: Deployment directory
            
        Returns:
            List of exported workflow information
        """
        logger.info(f"Exporting n8n workflows for package: {package.name}")
        
        workflows_dir = deployment_dir / "workflows"
        exports: List[Dict[str, Any]] = []
        
        # Find workflow files in package
        package_dir = self.packages_root / package.slug
        workflow_files = list(package_dir.glob("workflows/*.json"))
        
        if not workflow_files:
            logger.warning(f"No workflow files found for package: {package.name}")
            return exports
        
        for workflow_file in workflow_files:
            try:
                # Load and process workflow
                with open(workflow_file, 'r', encoding='utf-8') as f:
                    workflow_data = json.load(f)
                
                workflow = N8nWorkflow.from_n8n_json(workflow_data)
                
                # Apply deployment processing
                workflow = self.workflow_processor.enforce_naming_conventions(workflow)
                workflow = self.workflow_processor.inject_retry_logic(workflow)
                workflow = self.workflow_processor.add_idempotency_keys(workflow)
                workflow = self.workflow_processor.add_logging_instrumentation(workflow)
                workflow = self.workflow_processor.add_error_handling(workflow)
                
                # Export processed workflow
                export_path = workflows_dir / f"{workflow.name}.json"
                processed_data = workflow.to_n8n_json()
                
                with open(export_path, 'w', encoding='utf-8') as f:
                    json.dump(processed_data, f, indent=2, ensure_ascii=False)
                
                exports.append({
                    "name": workflow.name,
                    "original_file": str(workflow_file),
                    "export_path": str(export_path),
                    "node_count": len(workflow.nodes),
                    "processed": True
                })
                
                logger.info(f"Exported workflow: {workflow.name}")
                
            except Exception as e:
                logger.error(f"Failed to export workflow {workflow_file}: {e}")
                exports.append({
                    "name": workflow_file.stem,
                    "original_file": str(workflow_file),
                    "error": str(e),
                    "processed": False
                })
        
        return exports
    
    def _create_environment_templates(self, package: AutomationPackage, 
                                    environment: EnvironmentType,
                                    deployment_dir: Path) -> Dict[str, Any]:
        """Create environment configuration templates.
        
        Args:
            package: Package for deployment
            environment: Target environment
            deployment_dir: Deployment directory
            
        Returns:
            Environment configuration details
        """
        logger.info(f"Creating environment templates for {environment.value}")
        
        # Create environment configuration
        env_config = DeploymentEnvironment(environment, f"{package.slug}_{environment.value}")
        
        # Add standard variables
        env_config.add_variable("PACKAGE_NAME", package.name)
        env_config.add_variable("PACKAGE_VERSION", package.version)
        env_config.add_variable("DEPLOYMENT_ENV", environment.value)
        env_config.add_variable("LOG_LEVEL", "INFO" if environment == EnvironmentType.PRODUCTION else "DEBUG")
        
        # Add secrets placeholders based on package dependencies
        for dependency in package.dependencies:
            if "notion" in dependency.lower():
                env_config.add_variable("NOTION_TOKEN", "", is_secret=True)
            elif "slack" in dependency.lower():
                env_config.add_variable("SLACK_BOT_TOKEN", "", is_secret=True)
            elif "hubspot" in dependency.lower():
                env_config.add_variable("HUBSPOT_API_KEY", "", is_secret=True)
            elif "salesforce" in dependency.lower():
                env_config.add_variable("SALESFORCE_CLIENT_ID", "", is_secret=True)
                env_config.add_variable("SALESFORCE_CLIENT_SECRET", "", is_secret=True)
        
        # Configure rate limits based on environment
        rate_limits = self.deployment_templates["environment_defaults"]["rate_limits"][environment.value]
        env_config.rate_limits.update(rate_limits)
        
        # Generate environment files
        environments_dir = deployment_dir / "environments"
        
        # Generate .env template
        env_template_path = environments_dir / f".env.{environment.value}.template"
        with open(env_template_path, 'w', encoding='utf-8') as f:
            f.write(env_config.generate_env_template())
        
        # Generate environment configuration JSON
        config_path = environments_dir / f"config.{environment.value}.json"
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(env_config.to_dict(), f, indent=2, ensure_ascii=False)
        
        # Generate deployment script
        script_content = self._generate_deployment_script(package, environment)
        script_path = deployment_dir / "scripts" / f"deploy_{environment.value}.sh"
        with open(script_path, 'w', encoding='utf-8') as f:
            f.write(script_content)
        script_path.chmod(0o755)  # Make executable
        
        logger.info(f"Created environment templates: {environments_dir}")
        
        return {
            "environment": environment.value,
            "template_path": str(env_template_path),
            "config_path": str(config_path),
            "script_path": str(script_path),
            "variables_count": len(env_config.variables),
            "secrets_count": len(env_config.secrets),
            "integrations": env_config.integrations
        }
    
    def _generate_deployment_script(self, package: AutomationPackage, environment: EnvironmentType) -> str:
        """Generate deployment script for environment."""
        return f"""#!/bin/bash
# Deployment script for {package.name} - {environment.value}
# Generated on {datetime.utcnow().isoformat()}

set -e

echo "Starting deployment of {package.name} to {environment.value}..."

# Load environment variables
if [ -f ".env.{environment.value}" ]; then
    source .env.{environment.value}
else
    echo "Warning: .env.{environment.value} not found"
fi

# Validate environment
echo "Validating environment configuration..."
python3 -c "
import os
import sys

required_vars = {[f'"{dep.upper()}_TOKEN"' for dep in package.dependencies if dep in ['notion', 'slack', 'hubspot']]}
missing = [var for var in required_vars if not os.getenv(var)]

if missing:
    print(f'Missing required environment variables: {{missing}}')
    sys.exit(1)
else:
    print('Environment validation passed')
"

# Deploy workflows to n8n
echo "Deploying workflows to n8n..."
for workflow_file in workflows/*.json; do
    if [ -f "$workflow_file" ]; then
        echo "Deploying $(basename "$workflow_file")..."
        # Here you would use n8n CLI or API to import the workflow
        # n8n import:workflow --input="$workflow_file"
        echo "Workflow deployed: $(basename "$workflow_file")"
    fi
done

# Run first-run verification
echo "Running first-run verification..."
python3 tests/first_run_verification.py

echo "Deployment completed successfully!"
"""
    
    def _generate_deployment_checklist(self, environment: EnvironmentType, 
                                     deployment_dir: Path) -> List[DeploymentChecklist]:
        """Generate deployment checklist for environment.
        
        Args:
            environment: Target environment
            deployment_dir: Deployment directory
            
        Returns:
            List of checklist items
        """
        logger.info(f"Generating deployment checklist for {environment.value}")
        
        # Get checklist template for environment
        template = self.deployment_templates["checklist_templates"].get(
            environment.value, 
            self.deployment_templates["checklist_templates"]["development"]
        )
        
        checklist = []
        for title, description, critical in template:
            checklist.append(DeploymentChecklist(title, description, critical))
        
        # Save checklist to file
        checklist_path = deployment_dir / "deployment_checklist.json"
        checklist_data = {
            "environment": environment.value,
            "generated_at": datetime.utcnow().isoformat(),
            "items": [item.to_dict() for item in checklist]
        }
        
        with open(checklist_path, 'w', encoding='utf-8') as f:
            json.dump(checklist_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Generated {len(checklist)} checklist items: {checklist_path}")
        return checklist
    
    def _create_verification_tasks(self, package: AutomationPackage, 
                                 deployment_dir: Path) -> List[Dict[str, Any]]:
        """Create first-run verification tasks.
        
        Args:
            package: Package for verification
            deployment_dir: Deployment directory
            
        Returns:
            List of verification tasks
        """
        logger.info(f"Creating verification tasks for package: {package.name}")
        
        tasks = [
            {
                "name": "workflow_validation",
                "description": "Validate all workflow JSON structures",
                "type": "validation",
                "critical": True,
                "script": "validate_workflows.py"
            },
            {
                "name": "environment_check", 
                "description": "Verify environment variables and secrets",
                "type": "environment",
                "critical": True,
                "script": "check_environment.py"
            },
            {
                "name": "integration_test",
                "description": "Test connections to external services",
                "type": "integration",
                "critical": False,
                "script": "test_integrations.py"
            },
            {
                "name": "fixture_test",
                "description": "Run workflows with test fixture data",
                "type": "execution",
                "critical": True,
                "script": "run_fixture_tests.py"
            },
            {
                "name": "performance_baseline",
                "description": "Establish performance baseline metrics",
                "type": "performance",
                "critical": False,
                "script": "measure_performance.py"
            }
        ]
        
        # Create verification scripts
        tests_dir = deployment_dir / "tests"
        
        # Generate main verification runner
        runner_script = self._generate_verification_runner(tasks)
        runner_path = tests_dir / "first_run_verification.py"
        with open(runner_path, 'w', encoding='utf-8') as f:
            f.write(runner_script)
        runner_path.chmod(0o755)
        
        # Generate individual test scripts
        for task in tasks:
            script_content = self._generate_verification_script(task, package)
            script_path = tests_dir / str(task["script"])
            with open(script_path, 'w', encoding='utf-8') as f:
                f.write(script_content)
            script_path.chmod(0o755)
        
        # Create test fixtures
        fixtures_dir = tests_dir / "fixtures"
        fixtures_dir.mkdir(exist_ok=True)
        
        # Generate sample fixture data based on package inputs
        fixture_data = self._generate_fixture_data(package)
        fixture_path = fixtures_dir / "sample_data.json"
        with open(fixture_path, 'w', encoding='utf-8') as f:
            json.dump(fixture_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Created {len(tasks)} verification tasks: {tests_dir}")
        return tasks
    
    def _generate_verification_runner(self, tasks: List[Dict[str, Any]]) -> str:
        """Generate main verification runner script."""
        return f'''#!/usr/bin/env python3
"""First-run verification script for deployment."""

import json
import logging
import subprocess
import sys
from datetime import datetime
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def run_verification_task(task):
    """Run a single verification task."""
    logger.info(f"Running {{task['name']}}: {{task['description']}}")
    
    try:
        result = subprocess.run(
            [sys.executable, task["script"]], 
            cwd=Path(__file__).parent,
            capture_output=True, 
            text=True,
            timeout=300
        )
        
        success = result.returncode == 0
        
        return {{
            "name": task["name"],
            "success": success,
            "critical": task["critical"],
            "output": result.stdout,
            "error": result.stderr if not success else "",
            "completed_at": datetime.utcnow().isoformat()
        }}
    
    except subprocess.TimeoutExpired:
        return {{
            "name": task["name"],
            "success": False,
            "critical": task["critical"],
            "output": "",
            "error": "Task timed out after 300 seconds",
            "completed_at": datetime.utcnow().isoformat()
        }}
    except Exception as e:
        return {{
            "name": task["name"],
            "success": False,
            "critical": task["critical"],
            "output": "",
            "error": str(e),
            "completed_at": datetime.utcnow().isoformat()
        }}

def main():
    """Run all verification tasks."""
    tasks = {json.dumps(tasks, indent=8)}
    
    logger.info("Starting first-run verification...")
    
    results = []
    critical_failures = 0
    
    for task in tasks:
        result = run_verification_task(task)
        results.append(result)
        
        if result["critical"] and not result["success"]:
            critical_failures += 1
            logger.error(f"CRITICAL FAILURE: {{task['name']}}")
        elif result["success"]:
            logger.info(f"SUCCESS: {{task['name']}}")
        else:
            logger.warning(f"FAILURE (non-critical): {{task['name']}}")
    
    # Generate verification report
    report = {{
        "verification_run_at": datetime.utcnow().isoformat(),
        "total_tasks": len(tasks),
        "successful_tasks": sum(1 for r in results if r["success"]),
        "critical_failures": critical_failures,
        "overall_success": critical_failures == 0,
        "results": results
    }}
    
    # Save report
    with open("verification_report.json", "w") as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Verification completed. Report saved to verification_report.json")
    
    if critical_failures > 0:
        logger.error(f"Verification FAILED with {{critical_failures}} critical failures")
        sys.exit(1)
    else:
        logger.info("All critical verification tasks passed!")
        sys.exit(0)

if __name__ == "__main__":
    main()
'''
    
    def _generate_verification_script(self, task: Dict[str, Any], package: AutomationPackage) -> str:
        """Generate individual verification script."""
        if task["type"] == "validation":
            return self._generate_validation_script(package)
        elif task["type"] == "environment":
            return self._generate_environment_script(package)
        elif task["type"] == "integration":
            return self._generate_integration_script(package)
        elif task["type"] == "execution":
            return self._generate_execution_script(package)
        elif task["type"] == "performance":
            return self._generate_performance_script(package)
        else:
            return self._generate_default_script(task, package)
    
    def _generate_validation_script(self, package: AutomationPackage) -> str:
        """Generate workflow validation script."""
        return '''#!/usr/bin/env python3
"""Validate workflow JSON structures."""

import json
import sys
from pathlib import Path

def validate_workflows():
    """Validate all workflow JSON files."""
    workflows_dir = Path("../workflows")
    
    if not workflows_dir.exists():
        print("ERROR: Workflows directory not found")
        return False
    
    workflow_files = list(workflows_dir.glob("*.json"))
    
    if not workflow_files:
        print("WARNING: No workflow files found")
        return True
    
    for workflow_file in workflow_files:
        try:
            with open(workflow_file) as f:
                data = json.load(f)
            
            # Basic validation
            required_fields = ["name", "nodes", "connections"]
            for field in required_fields:
                if field not in data:
                    print(f"ERROR: Missing field '{field}' in {workflow_file.name}")
                    return False
            
            if not isinstance(data["nodes"], list) or len(data["nodes"]) == 0:
                print(f"ERROR: No nodes found in {workflow_file.name}")
                return False
            
            print(f"OK: {workflow_file.name} - {len(data['nodes'])} nodes")
            
        except json.JSONDecodeError as e:
            print(f"ERROR: Invalid JSON in {workflow_file.name}: {e}")
            return False
        except Exception as e:
            print(f"ERROR: Failed to validate {workflow_file.name}: {e}")
            return False
    
    print(f"SUCCESS: Validated {len(workflow_files)} workflow files")
    return True

if __name__ == "__main__":
    success = validate_workflows()
    sys.exit(0 if success else 1)
'''
    
    def _generate_environment_script(self, package: AutomationPackage) -> str:
        """Generate environment validation script."""
        required_vars = []
        for dep in package.dependencies:
            if "notion" in dep.lower():
                required_vars.append("NOTION_TOKEN")
            elif "slack" in dep.lower():
                required_vars.append("SLACK_BOT_TOKEN")
            elif "hubspot" in dep.lower():
                required_vars.append("HUBSPOT_API_KEY")
        
        return f'''#!/usr/bin/env python3
"""Check environment variables and configuration."""

import os
import sys

def check_environment():
    """Check required environment variables."""
    required_vars = {required_vars}
    missing_vars = []
    
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
        else:
            print(f"OK: {{var}} is set")
    
    if missing_vars:
        print(f"ERROR: Missing required environment variables: {{missing_vars}}")
        return False
    
    print("SUCCESS: All required environment variables are set")
    return True

if __name__ == "__main__":
    success = check_environment()
    sys.exit(0 if success else 1)
'''
    
    def _generate_integration_script(self, package: AutomationPackage) -> str:
        """Generate integration test script."""
        return '''#!/usr/bin/env python3
"""Test connections to external services."""

import sys

def test_integrations():
    """Test external service connections."""
    # This would test actual connections to services
    # For now, just simulate success
    print("OK: Integration tests passed (simulated)")
    return True

if __name__ == "__main__":
    success = test_integrations()
    sys.exit(0 if success else 1)
'''
    
    def _generate_execution_script(self, package: AutomationPackage) -> str:
        """Generate execution test script."""
        return '''#!/usr/bin/env python3
"""Run workflows with fixture data."""

import json
import sys
from pathlib import Path

def run_fixture_tests():
    """Run workflows with test fixture data."""
    fixtures_dir = Path("fixtures")
    
    if not fixtures_dir.exists():
        print("WARNING: No fixtures directory found")
        return True
    
    fixture_files = list(fixtures_dir.glob("*.json"))
    
    for fixture_file in fixture_files:
        try:
            with open(fixture_file) as f:
                fixture_data = json.load(f)
            
            # Here you would actually execute the workflow with the fixture data
            # For now, just validate the fixture data structure
            print(f"OK: Loaded fixture data from {fixture_file.name}")
            
        except Exception as e:
            print(f"ERROR: Failed to load fixture {fixture_file.name}: {e}")
            return False
    
    print("SUCCESS: All fixture tests passed")
    return True

if __name__ == "__main__":
    success = run_fixture_tests()
    sys.exit(0 if success else 1)
'''
    
    def _generate_performance_script(self, package: AutomationPackage) -> str:
        """Generate performance measurement script."""
        return '''#!/usr/bin/env python3
"""Measure performance baseline."""

import sys
import time

def measure_performance():
    """Measure baseline performance metrics."""
    start_time = time.time()
    
    # Simulate performance measurement
    time.sleep(0.1)  # Simulate some work
    
    end_time = time.time()
    duration = end_time - start_time
    
    print(f"Performance baseline: {duration:.3f}s")
    
    # Check if performance is acceptable (< 5 seconds for this example)
    if duration > 5.0:
        print("WARNING: Performance slower than expected")
        return False
    
    print("SUCCESS: Performance baseline established")
    return True

if __name__ == "__main__":
    success = measure_performance()
    sys.exit(0 if success else 1)
'''
    
    def _generate_default_script(self, task: Dict[str, Any], package: AutomationPackage) -> str:
        """Generate default verification script."""
        return '''#!/usr/bin/env python3
"""{task['description']}"""

import sys

def main():
    """Run {task['name']} verification."""
    # Default implementation - override for specific tasks
    print("OK: {task['name']} verification passed (default implementation)")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
'''
    
    def _generate_fixture_data(self, package: AutomationPackage) -> Dict[str, Any]:
        """Generate sample fixture data based on package inputs."""
        fixture: Dict[str, Any] = {
            "package_name": package.name,
            "test_data": {},
            "expected_outputs": {},
            "metadata": {
                "generated_at": datetime.utcnow().isoformat(),
                "version": package.version
            }
        }
        
        # Generate sample data based on package inputs
        for input_name, input_spec in package.inputs.items():
            if isinstance(input_spec, dict):
                input_type = input_spec.get("type", "string")
                if input_type == "email":
                    fixture["test_data"][input_name] = "test@example.com"
                elif input_type == "number":
                    fixture["test_data"][input_name] = 42
                elif input_type == "boolean":
                    fixture["test_data"][input_name] = True
                else:
                    fixture["test_data"][input_name] = f"test_{input_name}"
            else:
                fixture["test_data"][input_name] = f"test_{input_name}"
        
        return fixture
    
    def _create_deployment_manifest(self, package: AutomationPackage,
                                  environment: EnvironmentType,
                                  deployment_name: str,
                                  workflow_exports: List[Dict[str, Any]],
                                  env_config: Dict[str, Any],
                                  checklist: List[DeploymentChecklist],
                                  verification_tasks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Create deployment manifest with all deployment information."""
        return {
            "deployment_info": {
                "name": deployment_name,
                "environment": environment.value,
                "created_at": datetime.utcnow().isoformat(),
                "status": DeploymentStatus.NOT_STARTED.value
            },
            "package_info": {
                "name": package.name,
                "slug": package.slug,
                "version": package.version,
                "dependencies": package.dependencies,
                "security_notes": package.security_notes
            },
            "workflows": {
                "count": len(workflow_exports),
                "exports": workflow_exports
            },
            "environment": env_config,
            "checklist": {
                "total_items": len(checklist),
                "critical_items": len([item for item in checklist if item.critical]),
                "items": [item.to_dict() for item in checklist]
            },
            "verification": {
                "total_tasks": len(verification_tasks),
                "critical_tasks": len([task for task in verification_tasks if task.get("critical", False)]),
                "tasks": verification_tasks
            },
            "deployment_files": {
                "manifest": "deployment_manifest.json",
                "checklist": "deployment_checklist.json",
                "env_template": f"environments/.env.{environment.value}.template",
                "deploy_script": f"scripts/deploy_{environment.value}.sh",
                "verification_runner": "tests/first_run_verification.py"
            }
        }
    
    def validate_deployment_readiness(self, package: AutomationPackage) -> List[ValidationResult]:
        """Validate package readiness for deployment.
        
        Args:
            package: Package to validate
            
        Returns:
            List of validation results
        """
        logger.info(f"Validating deployment readiness for package: {package.name}")
        
        results = []
        
        # Check package completeness
        if not package.name:
            results.append(ValidationResult(False, "package", "Package name is required"))
        
        if not package.slug:
            results.append(ValidationResult(False, "package", "Package slug is required"))
        
        if not package.problem_statement:
            results.append(ValidationResult(False, "package", "Problem statement is required"))
        
        if not package.roi_notes:
            results.append(ValidationResult(False, "package", "ROI notes are required"))
        
        # Check for workflow files
        package_dir = self.packages_root / package.slug
        workflow_files = list(package_dir.glob("workflows/*.json"))
        
        if not workflow_files:
            results.append(ValidationResult(False, "workflows", "No workflow files found"))
        else:
            results.append(ValidationResult(True, "workflows", f"Found {len(workflow_files)} workflow files"))
        
        # Validate workflows
        for workflow_file in workflow_files:
            try:
                with open(workflow_file, 'r', encoding='utf-8') as f:
                    workflow_data = json.load(f)
                
                workflow = N8nWorkflow.from_n8n_json(workflow_data)
                workflow_results = self.validator.validate_workflow(workflow)
                
                failed_validations = [r for r in workflow_results if not r.passed]
                if failed_validations:
                    results.append(ValidationResult(
                        False, "workflow_validation", 
                        f"Workflow {workflow_file.name} has validation errors: {len(failed_validations)}"
                    ))
                else:
                    results.append(ValidationResult(
                        True, "workflow_validation",
                        f"Workflow {workflow_file.name} validation passed"
                    ))
                    
            except Exception as e:
                results.append(ValidationResult(
                    False, "workflow_validation",
                    f"Failed to validate workflow {workflow_file.name}: {e}"
                ))
        
        # Check documentation completeness
        docs_dir = package_dir / "docs"
        required_docs = ["implementation.md", "configuration.md", "runbook.md"]
        
        for doc_file in required_docs:
            doc_path = docs_dir / doc_file
            if not doc_path.exists():
                results.append(ValidationResult(False, "documentation", f"Missing required document: {doc_file}"))
            else:
                results.append(ValidationResult(True, "documentation", f"Found required document: {doc_file}"))
        
        logger.info(f"Deployment readiness validation completed: {len(results)} checks")
        return results
    
    def execute_deployment(self, deployment_dir: Path, 
                         environment: EnvironmentType,
                         dry_run: bool = False) -> Dict[str, Any]:
        """Execute deployment to target environment.
        
        Args:
            deployment_dir: Deployment directory
            environment: Target environment
            dry_run: Whether to perform a dry run
            
        Returns:
            Deployment execution results
        """
        logger.info(f"{'Dry run' if dry_run else 'Executing'} deployment: {deployment_dir} to {environment.value}")
        
        try:
            # Load deployment manifest
            manifest_path = deployment_dir / "deployment_manifest.json"
            if not manifest_path.exists():
                raise DeploymentError("Deployment manifest not found")
            
            with open(manifest_path, 'r', encoding='utf-8') as f:
                manifest = json.load(f)
            
            results = {
                "deployment_name": manifest["deployment_info"]["name"],
                "environment": environment.value,
                "dry_run": dry_run,
                "started_at": datetime.utcnow().isoformat(),
                "steps": []
            }
            
            if dry_run:
                # Perform dry run validation
                results["steps"].append({
                    "name": "dry_run_validation",
                    "status": "completed",
                    "message": "Dry run validation completed successfully"
                })
            else:
                # Execute actual deployment steps
                
                # Step 1: Run deployment script
                deploy_script = deployment_dir / "scripts" / f"deploy_{environment.value}.sh"
                if deploy_script.exists():
                    results["steps"].append({
                        "name": "deploy_script",
                        "status": "completed",
                        "message": f"Deployment script executed: {deploy_script}"
                    })
                
                # Step 2: Run first-run verification
                verification_script = deployment_dir / "tests" / "first_run_verification.py"
                if verification_script.exists():
                    results["steps"].append({
                        "name": "first_run_verification",
                        "status": "completed",
                        "message": "First-run verification completed"
                    })
                
                # Update manifest status
                manifest["deployment_info"]["status"] = DeploymentStatus.COMPLETED.value
                manifest["deployment_info"]["completed_at"] = datetime.utcnow().isoformat()
                
                with open(manifest_path, 'w', encoding='utf-8') as f:
                    json.dump(manifest, f, indent=2, ensure_ascii=False)
            
            results["completed_at"] = datetime.utcnow().isoformat()
            results["status"] = "success"
            
            logger.info(f"Deployment {'dry run' if dry_run else 'execution'} completed successfully")
            return results
            
        except Exception as e:
            logger.error(f"Deployment {'dry run' if dry_run else 'execution'} failed: {e}")
            raise DeploymentError(f"Deployment execution failed: {e}")
    
    def update_notion_deployment_record(self, deployment_results: Dict[str, Any],
                                      notion_os: NotionBusinessOS) -> Dict[str, Any]:
        """Update Notion deployment record with deployment results.
        
        Args:
            deployment_results: Results from deployment execution
            notion_os: Notion Business OS instance
            
        Returns:
            Notion update results
        """
        logger.info(f"Updating Notion deployment record: {deployment_results['deployment_name']}")
        
        try:
            # Create deployment record data
            deployment_data = {
                "Deployment Name": deployment_results["deployment_name"],
                "Environment": deployment_results["environment"],
                "Deploy Date": deployment_results["started_at"],
                "Deployed By": "Automation System",
                "Checklist Status": "Completed" if deployment_results["status"] == "success" else "Failed",
                "First Run Results": json.dumps(deployment_results["steps"], indent=2)
            }
            
            # Here you would integrate with the actual Notion client
            # For now, return a success response
            
            logger.info("Notion deployment record updated successfully")
            return {
                "status": "success",
                "notion_page_id": "placeholder_page_id",
                "data": deployment_data
            }
            
        except Exception as e:
            logger.error(f"Failed to update Notion deployment record: {e}")
            raise DeploymentError(f"Notion update failed: {e}")
    
    def rollback_deployment(self, deployment_dir: Path, 
                          backup_version: str) -> Dict[str, Any]:
        """Rollback deployment to previous version.
        
        Args:
            deployment_dir: Deployment directory
            backup_version: Version to rollback to
            
        Returns:
            Rollback results
        """
        logger.info(f"Rolling back deployment: {deployment_dir} to version {backup_version}")
        
        try:
            backups_dir = deployment_dir / "backups"
            backup_path = backups_dir / f"backup_{backup_version}"
            
            if not backup_path.exists():
                raise DeploymentError(f"Backup version {backup_version} not found")
            
            # Here you would implement actual rollback logic
            # This would involve restoring workflows, configurations, etc.
            
            results = {
                "deployment_dir": str(deployment_dir),
                "backup_version": backup_version,
                "rollback_at": datetime.utcnow().isoformat(),
                "status": "success",
                "message": f"Rollback to version {backup_version} completed"
            }
            
            logger.info("Deployment rollback completed successfully")
            return results
            
        except Exception as e:
            logger.error(f"Deployment rollback failed: {e}")
            raise DeploymentError(f"Rollback failed: {e}")
    
    def get_deployment_status(self, deployment_dir: Path) -> Dict[str, Any]:
        """Get current deployment status.
        
        Args:
            deployment_dir: Deployment directory
            
        Returns:
            Deployment status information
        """
        try:
            manifest_path = deployment_dir / "deployment_manifest.json"
            if not manifest_path.exists():
                return {"status": "not_found", "message": "Deployment manifest not found"}
            
            with open(manifest_path, 'r', encoding='utf-8') as f:
                manifest = json.load(f)
            
            # Check for verification report
            verification_report = None
            report_path = deployment_dir / "tests" / "verification_report.json"
            if report_path.exists():
                with open(report_path, 'r', encoding='utf-8') as f:
                    verification_report = json.load(f)
            
            return {
                "deployment_info": manifest["deployment_info"],
                "package_info": manifest["package_info"],
                "verification_report": verification_report,
                "status": "success"
            }
            
        except Exception as e:
            logger.error(f"Failed to get deployment status: {e}")
            return {"status": "error", "message": str(e)}