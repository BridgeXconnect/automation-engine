"""Validation utilities for packages and workflows."""

import json
import logging
import re
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class ValidationResult:
    """Result from a validation check."""
    check_name: str
    passed: bool
    severity: str  # 'error', 'warning', 'info'
    message: str
    details: Optional[Dict[str, Any]] = None
    timestamp: Optional[datetime] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()

class ValidationError(Exception):
    """Custom exception for validation operations."""
    pass

class PackageValidator:
    """Package validator with comprehensive checks.
    
    Validates package structure, metadata, workflows, and documentation
    according to CLAUDE.md standards and quality gates.
    """
    
    def __init__(self):
        """Initialize package validator with rules and standards."""
        self.validation_rules = self._load_validation_rules()
        self.required_docs = [
            'implementation.md', 'configuration.md', 'runbook.md', 
            'sop.md', 'loom-outline.md', 'client-one-pager.md'
        ]
        
    def _load_validation_rules(self) -> Dict[str, Any]:
        """Load validation rules and quality standards."""
        return {
            # Package structure requirements
            'required_directories': ['workflows', 'docs', 'tests'],
            'required_files': ['metadata.json'],
            
            # Metadata requirements per CLAUDE.md
            'required_metadata_fields': [
                'name', 'slug', 'niche_tags', 'problem_statement', 
                'outcomes', 'roi_notes', 'inputs', 'outputs', 
                'dependencies', 'security_notes', 'last_validated'
            ],
            
            # Workflow validation
            'max_workflow_nodes': 50,
            'required_workflow_fields': ['name', 'nodes', 'connections'],
            'forbidden_hardcoded_secrets': True,
            
            # Documentation standards
            'min_doc_length': 100,  # characters
            'required_sections': ['overview', 'setup', 'usage'],
            
            # Security requirements
            'forbidden_patterns': [
                r'password\s*=\s*["\'][^"\']+["\']',  # Hardcoded passwords
                r'token\s*=\s*["\'][^"\']+["\']',     # Hardcoded tokens
                r'api_key\s*=\s*["\'][^"\']+["\']'    # Hardcoded API keys
            ]
        }
    
    def validate_package_directory(self, package_dir: Path) -> List[ValidationResult]:
        """Validate complete package directory structure and content.
        
        Args:
            package_dir: Path to package directory
            
        Returns:
            List of validation results
        """
        logger.info(f"Validating package directory: {package_dir}")
        results = []
        
        # Basic structure validation
        results.extend(self._validate_directory_structure(package_dir))
        
        # Metadata validation
        results.extend(self._validate_metadata(package_dir))
        
        # Workflow validation
        results.extend(self._validate_workflows(package_dir))
        
        # Documentation validation
        results.extend(self._validate_documentation(package_dir))
        
        # Security validation
        results.extend(self._validate_security(package_dir))
        
        # Test validation
        results.extend(self._validate_tests(package_dir))
        
        logger.info(f"Package validation completed: {len(results)} checks")
        return results
    
    def _validate_directory_structure(self, package_dir: Path) -> List[ValidationResult]:
        """Validate package directory structure."""
        results = []
        
        # Check if package directory exists
        if not package_dir.exists():
            results.append(ValidationResult(
                check_name="directory_exists",
                passed=False,
                severity="error",
                message=f"Package directory does not exist: {package_dir}"
            ))
            return results
        
        results.append(ValidationResult(
            check_name="directory_exists",
            passed=True,
            severity="info",
            message="Package directory exists"
        ))
        
        # Check required directories
        for req_dir in self.validation_rules['required_directories']:
            dir_path = package_dir / req_dir
            if not dir_path.exists():
                results.append(ValidationResult(
                    check_name=f"directory_{req_dir}",
                    passed=False,
                    severity="error",
                    message=f"Missing required directory: {req_dir}"
                ))
            elif not dir_path.is_dir():
                results.append(ValidationResult(
                    check_name=f"directory_{req_dir}",
                    passed=False,
                    severity="error", 
                    message=f"Path exists but is not a directory: {req_dir}"
                ))
            else:
                results.append(ValidationResult(
                    check_name=f"directory_{req_dir}",
                    passed=True,
                    severity="info",
                    message=f"Required directory present: {req_dir}"
                ))
        
        # Check required files
        for req_file in self.validation_rules['required_files']:
            file_path = package_dir / req_file
            if not file_path.exists():
                results.append(ValidationResult(
                    check_name=f"file_{req_file}",
                    passed=False,
                    severity="error",
                    message=f"Missing required file: {req_file}"
                ))
            else:
                results.append(ValidationResult(
                    check_name=f"file_{req_file}",
                    passed=True,
                    severity="info",
                    message=f"Required file present: {req_file}"
                ))
        
        return results
    
    def _validate_metadata(self, package_dir: Path) -> List[ValidationResult]:
        """Validate package metadata.json file."""
        results = []
        metadata_path = package_dir / 'metadata.json'
        
        if not metadata_path.exists():
            results.append(ValidationResult(
                check_name="metadata_exists",
                passed=False,
                severity="error",
                message="metadata.json file is missing"
            ))
            return results
        
        try:
            with open(metadata_path, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
        except json.JSONDecodeError as e:
            results.append(ValidationResult(
                check_name="metadata_json_valid",
                passed=False,
                severity="error",
                message=f"Invalid JSON in metadata.json: {e}"
            ))
            return results
        except Exception as e:
            results.append(ValidationResult(
                check_name="metadata_readable",
                passed=False,
                severity="error",
                message=f"Cannot read metadata.json: {e}"
            ))
            return results
        
        results.append(ValidationResult(
            check_name="metadata_json_valid",
            passed=True,
            severity="info",
            message="metadata.json is valid JSON"
        ))
        
        # Validate required fields per CLAUDE.md
        for field in self.validation_rules['required_metadata_fields']:
            if field not in metadata:
                results.append(ValidationResult(
                    check_name=f"metadata_field_{field}",
                    passed=False,
                    severity="error",
                    message=f"Missing required metadata field: {field}"
                ))
            elif not metadata[field]:  # Empty or None value
                results.append(ValidationResult(
                    check_name=f"metadata_field_{field}",
                    passed=False,
                    severity="warning",
                    message=f"Empty required metadata field: {field}"
                ))
            else:
                results.append(ValidationResult(
                    check_name=f"metadata_field_{field}",
                    passed=True,
                    severity="info",
                    message=f"Required metadata field present: {field}"
                ))
        
        # Validate field types and content
        if 'niche_tags' in metadata:
            if not isinstance(metadata['niche_tags'], list):
                results.append(ValidationResult(
                    check_name="metadata_niche_tags_type",
                    passed=False,
                    severity="error",
                    message="niche_tags must be an array"
                ))
            elif len(metadata['niche_tags']) == 0:
                results.append(ValidationResult(
                    check_name="metadata_niche_tags_empty",
                    passed=False,
                    severity="warning",
                    message="niche_tags array is empty"
                ))
            else:
                results.append(ValidationResult(
                    check_name="metadata_niche_tags_valid",
                    passed=True,
                    severity="info",
                    message=f"niche_tags contains {len(metadata['niche_tags'])} tags"
                ))
        
        # Validate slug format (alphanumeric and hyphens/underscores only)
        if 'slug' in metadata:
            slug = metadata['slug']
            if not re.match(r'^[a-zA-Z0-9_-]+$', slug):
                results.append(ValidationResult(
                    check_name="metadata_slug_format",
                    passed=False,
                    severity="error",
                    message="slug contains invalid characters (use only letters, numbers, hyphens, underscores)"
                ))
            else:
                results.append(ValidationResult(
                    check_name="metadata_slug_format",
                    passed=True,
                    severity="info",
                    message="slug format is valid"
                ))
        
        return results
    
    def _validate_workflows(self, package_dir: Path) -> List[ValidationResult]:
        """Validate workflow files in workflows/ directory."""
        results = []
        workflows_dir = package_dir / 'workflows'
        
        if not workflows_dir.exists():
            results.append(ValidationResult(
                check_name="workflows_dir_exists",
                passed=False,
                severity="error",
                message="workflows/ directory missing"
            ))
            return results
        
        # Find workflow JSON files
        workflow_files = list(workflows_dir.glob('*.json'))
        
        if not workflow_files:
            results.append(ValidationResult(
                check_name="workflows_present",
                passed=False,
                severity="error",
                message="No workflow JSON files found in workflows/ directory"
            ))
            return results
        
        results.append(ValidationResult(
            check_name="workflows_present",
            passed=True,
            severity="info",
            message=f"{len(workflow_files)} workflow files found"
        ))
        
        # Validate each workflow file
        for workflow_file in workflow_files:
            workflow_results = self._validate_workflow_file(workflow_file)
            results.extend(workflow_results)
        
        return results
    
    def _validate_workflow_file(self, workflow_file: Path) -> List[ValidationResult]:
        """Validate individual workflow JSON file."""
        results = []
        workflow_name = workflow_file.stem
        
        try:
            with open(workflow_file, 'r', encoding='utf-8') as f:
                workflow = json.load(f)
        except json.JSONDecodeError as e:
            results.append(ValidationResult(
                check_name=f"workflow_{workflow_name}_json",
                passed=False,
                severity="error",
                message=f"Invalid JSON in {workflow_file.name}: {e}"
            ))
            return results
        except Exception as e:
            results.append(ValidationResult(
                check_name=f"workflow_{workflow_name}_readable",
                passed=False,
                severity="error",
                message=f"Cannot read {workflow_file.name}: {e}"
            ))
            return results
        
        # Validate required workflow fields
        for field in self.validation_rules['required_workflow_fields']:
            if field not in workflow:
                results.append(ValidationResult(
                    check_name=f"workflow_{workflow_name}_field_{field}",
                    passed=False,
                    severity="error",
                    message=f"Missing required field '{field}' in {workflow_file.name}"
                ))
            else:
                results.append(ValidationResult(
                    check_name=f"workflow_{workflow_name}_field_{field}",
                    passed=True,
                    severity="info",
                    message=f"Required field '{field}' present in {workflow_file.name}"
                ))
        
        # Validate node count
        if 'nodes' in workflow:
            node_count = len(workflow['nodes']) if isinstance(workflow['nodes'], list) else 0
            max_nodes = self.validation_rules['max_workflow_nodes']
            
            if node_count > max_nodes:
                results.append(ValidationResult(
                    check_name=f"workflow_{workflow_name}_node_count",
                    passed=False,
                    severity="warning",
                    message=f"Workflow has {node_count} nodes (max recommended: {max_nodes})"
                ))
            else:
                results.append(ValidationResult(
                    check_name=f"workflow_{workflow_name}_node_count",
                    passed=True,
                    severity="info",
                    message=f"Workflow has {node_count} nodes (within limits)"
                ))
        
        # Check for hardcoded secrets
        workflow_str = json.dumps(workflow)
        hardcoded_secrets = self._find_hardcoded_secrets(workflow_str)
        
        if hardcoded_secrets:
            results.append(ValidationResult(
                check_name=f"workflow_{workflow_name}_secrets",
                passed=False,
                severity="error",
                message=f"Hardcoded secrets detected in {workflow_file.name}",
                details={"secrets": hardcoded_secrets}
            ))
        else:
            results.append(ValidationResult(
                check_name=f"workflow_{workflow_name}_secrets",
                passed=True,
                severity="info",
                message=f"No hardcoded secrets detected in {workflow_file.name}"
            ))
        
        return results
    
    def _validate_documentation(self, package_dir: Path) -> List[ValidationResult]:
        """Validate documentation files in docs/ directory."""
        results = []
        docs_dir = package_dir / 'docs'
        
        if not docs_dir.exists():
            results.append(ValidationResult(
                check_name="docs_dir_exists",
                passed=False,
                severity="error",
                message="docs/ directory missing"
            ))
            return results
        
        # Check for required documentation files per CLAUDE.md
        for doc_file in self.required_docs:
            doc_path = docs_dir / doc_file
            
            if not doc_path.exists():
                results.append(ValidationResult(
                    check_name=f"doc_{doc_file.replace('.', '_').replace('-', '_')}",
                    passed=False,
                    severity="warning",
                    message=f"Missing recommended documentation file: {doc_file}"
                ))
            else:
                # Check document length
                try:
                    content = doc_path.read_text(encoding='utf-8')
                    if len(content.strip()) < self.validation_rules['min_doc_length']:
                        results.append(ValidationResult(
                            check_name=f"doc_{doc_file.replace('.', '_').replace('-', '_')}_length",
                            passed=False,
                            severity="warning",
                            message=f"Documentation file {doc_file} is too short (< {self.validation_rules['min_doc_length']} chars)"
                        ))
                    else:
                        results.append(ValidationResult(
                            check_name=f"doc_{doc_file.replace('.', '_').replace('-', '_')}",
                            passed=True,
                            severity="info",
                            message=f"Documentation file {doc_file} is present and adequate"
                        ))
                except Exception as e:
                    results.append(ValidationResult(
                        check_name=f"doc_{doc_file.replace('.', '_').replace('-', '_')}_readable",
                        passed=False,
                        severity="warning",
                        message=f"Cannot read documentation file {doc_file}: {e}"
                    ))
        
        return results
    
    def _validate_security(self, package_dir: Path) -> List[ValidationResult]:
        """Validate security aspects of the package."""
        results = []
        
        # Scan all files for hardcoded secrets
        security_issues = self._scan_for_security_issues(package_dir)
        
        if security_issues:
            for issue in security_issues:
                results.append(ValidationResult(
                    check_name="security_scan",
                    passed=False,
                    severity="error",
                    message=f"Security issue: {issue['message']}",
                    details=issue
                ))
        else:
            results.append(ValidationResult(
                check_name="security_scan",
                passed=True,
                severity="info",
                message="No security issues detected"
            ))
        
        return results
    
    def _validate_tests(self, package_dir: Path) -> List[ValidationResult]:
        """Validate test files and fixtures."""
        results = []
        tests_dir = package_dir / 'tests'
        
        if not tests_dir.exists():
            results.append(ValidationResult(
                check_name="tests_dir_exists",
                passed=False,
                severity="warning",
                message="tests/ directory missing"
            ))
            return results
        
        # Look for test fixtures
        fixture_files = list(tests_dir.glob('*.json')) + list(tests_dir.glob('fixtures.*'))
        
        if fixture_files:
            results.append(ValidationResult(
                check_name="test_fixtures_present",
                passed=True,
                severity="info",
                message=f"{len(fixture_files)} test fixture files found"
            ))
        else:
            results.append(ValidationResult(
                check_name="test_fixtures_present",
                passed=False,
                severity="warning",
                message="No test fixture files found"
            ))
        
        return results
    
    def _find_hardcoded_secrets(self, content: str) -> List[str]:
        """Find potential hardcoded secrets in content."""
        secrets = []
        
        for pattern in self.validation_rules['forbidden_patterns']:
            matches = re.findall(pattern, content, re.IGNORECASE)
            if matches:
                secrets.extend(matches)
        
        return secrets
    
    def _scan_for_security_issues(self, package_dir: Path) -> List[Dict[str, Any]]:
        """Scan package for security issues."""
        issues = []
        
        # Scan all text files for secrets
        for file_path in package_dir.rglob('*'):
            if file_path.is_file() and file_path.suffix in ['.json', '.md', '.txt', '.yaml', '.yml']:
                try:
                    content = file_path.read_text(encoding='utf-8')
                    secrets = self._find_hardcoded_secrets(content)
                    
                    for secret in secrets:
                        issues.append({
                            'type': 'hardcoded_secret',
                            'file': str(file_path.relative_to(package_dir)),
                            'message': f"Potential hardcoded secret in {file_path.name}",
                            'secret_pattern': secret[:20] + "..." if len(secret) > 20 else secret
                        })
                        
                except Exception:
                    # Skip files that can't be read as text
                    continue
        
        return issues
    
    def generate_validation_report(self, results: List[ValidationResult]) -> Dict[str, Any]:
        """Generate comprehensive validation report."""
        total_checks = len(results)
        passed_checks = sum(1 for r in results if r.passed)
        failed_checks = total_checks - passed_checks
        
        # Group by severity
        by_severity = {'error': 0, 'warning': 0, 'info': 0}
        issues_by_severity: Dict[str, List[Dict[str, Any]]] = {'error': [], 'warning': [], 'info': []}
        
        for result in results:
            by_severity[result.severity] += 1
            if not result.passed:
                issues_by_severity[result.severity].append({
                    'check': result.check_name,
                    'message': result.message,
                    'details': result.details
                })
        
        # Determine overall status
        if by_severity['error'] > 0:
            overall_status = 'FAILED'
        elif by_severity['warning'] > 0:
            overall_status = 'WARNING' 
        else:
            overall_status = 'PASSED'
        
        return {
            'summary': {
                'total_checks': total_checks,
                'passed': passed_checks,
                'failed': failed_checks,
                'success_rate': passed_checks / total_checks if total_checks > 0 else 0,
                'overall_status': overall_status
            },
            'by_severity': by_severity,
            'issues': issues_by_severity,
            'generated_at': datetime.utcnow().isoformat(),
            'details': [
                {
                    'check_name': r.check_name,
                    'passed': r.passed,
                    'severity': r.severity,
                    'message': r.message,
                    'timestamp': r.timestamp.isoformat() if r.timestamp else None
                }
                for r in results
            ]
        }

class WorkflowValidator:
    """Specialized validator for n8n workflows."""
    
    def __init__(self):
        """Initialize workflow validator."""
        self.node_type_patterns = {
            'trigger': r'.*trigger.*|webhook|cron|schedule',
            'action': r'.*action.*|http.*request|database',
            'logic': r'if|switch|merge|set',
            'notification': r'slack|email|discord|teams'
        }
    
    def validate_workflow_logic(self, workflow_data: Dict[str, Any]) -> List[ValidationResult]:
        """Validate workflow logic and structure."""
        results = []
        
        # Validate workflow has at least one trigger
        if 'nodes' in workflow_data:
            trigger_nodes = self._find_nodes_by_type(workflow_data['nodes'], 'trigger')
            
            if not trigger_nodes:
                results.append(ValidationResult(
                    check_name="workflow_trigger_present",
                    passed=False,
                    severity="error",
                    message="Workflow must have at least one trigger node"
                ))
            else:
                results.append(ValidationResult(
                    check_name="workflow_trigger_present",
                    passed=True,
                    severity="info",
                    message=f"Workflow has {len(trigger_nodes)} trigger nodes"
                ))
        
        return results
    
    def _find_nodes_by_type(self, nodes: List[Dict[str, Any]], node_type: str) -> List[Dict[str, Any]]:
        """Find nodes matching a specific type pattern."""
        if node_type not in self.node_type_patterns:
            return []
        
        pattern = self.node_type_patterns[node_type]
        matching_nodes = []
        
        for node in nodes:
            node_type_str = node.get('type', '').lower()
            if re.search(pattern, node_type_str, re.IGNORECASE):
                matching_nodes.append(node)
        
        return matching_nodes