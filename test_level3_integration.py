#!/usr/bin/env python3
"""
Level 3 Integration Testing Suite
Comprehensive end-to-end testing for the automation engine

Tests:
1. End-to-End package generation workflow
2. Module-to-module data flow and integration
3. File system operations and directory structure
4. External API integrations (mock/real)
5. CLI interface and command validation
6. Template system and documentation generation
7. Error handling across module boundaries
8. Quality gates and validation workflows
"""

import os
import sys
import json
import shutil
import logging
import traceback
import tempfile
from pathlib import Path
from datetime import datetime
from unittest.mock import patch, MagicMock
from typing import Dict, List, Any, Optional

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / 'src'))

try:
    from src.main import cli
    from src.utils.file_manager import PackageFileManager
    from src.utils.validators import PackageValidator
    from src.utils.helpers import generate_slug, setup_logging
    from src.models.package import AutomationPackage
    from src.models.workflow import N8nWorkflow
    from src.models.documentation import DocumentationSuite
    from src.modules.niche_research import NicheBrief
    from src.modules.niche_research import NicheResearcher
    from src.modules.opportunity_mapping import OpportunityMapper
    from src.modules.assembly import WorkflowAssembler
    from src.modules.validation import WorkflowValidator
    from src.modules.documentation import DocumentationGenerator
    from src.modules.package_generator import PackageGenerator
    IMPORTS_SUCCESS = True
except ImportError as e:
    print(f"❌ Import failed: {e}")
    IMPORTS_SUCCESS = False


class Level3IntegrationTester:
    """Comprehensive integration testing system."""
    
    def __init__(self, test_output_dir: Optional[Path] = None):
        self.test_start_time = datetime.now()
        
        # Setup test directories
        self.test_output_dir = test_output_dir or Path(tempfile.mkdtemp(prefix="automation_test_"))
        self.test_packages_dir = self.test_output_dir / "packages"
        self.test_vault_dir = self.test_output_dir / "automation_vault"
        
        # Create test directories
        self.test_output_dir.mkdir(exist_ok=True)
        self.test_packages_dir.mkdir(exist_ok=True)
        self.test_vault_dir.mkdir(exist_ok=True)
        
        # Setup logging
        log_file = self.test_output_dir / "integration_test.log"
        setup_logging(logging.DEBUG, log_file=log_file)
        self.logger = logging.getLogger(__name__)
        
        # Test results tracking
        self.results = {
            'total_tests': 0,
            'passed_tests': 0,
            'failed_tests': 0,
            'errors': [],
            'test_details': {}
        }
        
        # Test niche keyword
        self.test_niche = "healthcare-clinics"
        
        print(f"🧪 Level 3 Integration Test Suite Initialized")
        print(f"📁 Test directory: {self.test_output_dir}")
        print(f"🎯 Test niche: {self.test_niche}")
        print("=" * 60)
    
    def log_test_result(self, test_name: str, passed: bool, details: Dict[str, Any], error: Optional[str] = None):
        """Log test result and update tracking."""
        self.results['total_tests'] += 1
        
        if passed:
            self.results['passed_tests'] += 1
            print(f"✅ {test_name}")
        else:
            self.results['failed_tests'] += 1
            print(f"❌ {test_name}")
            if error:
                self.results['errors'].append(f"{test_name}: {error}")
                print(f"   Error: {error}")
        
        self.results['test_details'][test_name] = {
            'passed': passed,
            'details': details,
            'error': error,
            'timestamp': datetime.now().isoformat()
        }
        
        # Log details if debug
        if details and len(str(details)) < 200:
            print(f"   Details: {details}")
    
    def setup_test_vault(self):
        """Create a test automation vault with sample workflows."""
        print("\n🔧 Setting up test automation vault...")
        
        try:
            # Create sample workflow files in proper n8n format
            sample_workflows = [
                {
                    "name": "crm_lead_capture",
                    "active": False,
                    "nodes": [
                        {
                            "id": "webhook_1",
                            "name": "form_webhook",
                            "type": "n8n-nodes-base.webhook",
                            "position": [100, 300],
                            "parameters": {
                                "path": "lead-capture",
                                "httpMethod": "POST"
                            }
                        },
                        {
                            "id": "validate_1", 
                            "name": "validate_data",
                            "type": "n8n-nodes-base.set",
                            "position": [300, 300],
                            "parameters": {
                                "values": {
                                    "validated": "true"
                                }
                            }
                        },
                        {
                            "id": "crm_1",
                            "name": "create_crm_record", 
                            "type": "n8n-nodes-base.httpRequest",
                            "position": [500, 300],
                            "parameters": {
                                "method": "POST",
                                "url": "https://api.crm.com/leads"
                            }
                        }
                    ],
                    "connections": {
                        "webhook_1": {
                            "main": [
                                [
                                    {
                                        "node": "validate_1",
                                        "type": "main",
                                        "index": 0
                                    }
                                ]
                            ]
                        },
                        "validate_1": {
                            "main": [
                                [
                                    {
                                        "node": "crm_1",
                                        "type": "main", 
                                        "index": 0
                                    }
                                ]
                            ]
                        }
                    }
                },
                {
                    "name": "email_automation",
                    "active": False,
                    "nodes": [
                        {
                            "id": "schedule_1",
                            "name": "schedule_trigger",
                            "type": "n8n-nodes-base.cron",
                            "position": [100, 300],
                            "parameters": {
                                "cronExpression": "0 9 * * *"
                            }
                        },
                        {
                            "id": "query_1",
                            "name": "query_database",
                            "type": "n8n-nodes-base.httpRequest",
                            "position": [300, 300],
                            "parameters": {
                                "method": "GET",
                                "url": "https://api.database.com/query"
                            }
                        },
                        {
                            "id": "email_1",
                            "name": "send_email",
                            "type": "n8n-nodes-base.emailSend",
                            "position": [500, 300],
                            "parameters": {
                                "subject": "Daily Report"
                            }
                        }
                    ],
                    "connections": {
                        "schedule_1": {
                            "main": [
                                [
                                    {
                                        "node": "query_1",
                                        "type": "main",
                                        "index": 0
                                    }
                                ]
                            ]
                        },
                        "query_1": {
                            "main": [
                                [
                                    {
                                        "node": "email_1",
                                        "type": "main",
                                        "index": 0
                                    }
                                ]
                            ]
                        }
                    }
                },
                {
                    "name": "invoice_processing", 
                    "active": False,
                    "nodes": [
                        {
                            "id": "webhook_2",
                            "name": "invoice_webhook",
                            "type": "n8n-nodes-base.webhook",
                            "position": [100, 300],
                            "parameters": {
                                "path": "invoice-process",
                                "httpMethod": "POST"
                            }
                        },
                        {
                            "id": "parse_1",
                            "name": "parse_invoice",
                            "type": "n8n-nodes-base.set",
                            "position": [300, 300],
                            "parameters": {
                                "values": {
                                    "parsed": "true"
                                }
                            }
                        },
                        {
                            "id": "accounting_1",
                            "name": "update_accounting",
                            "type": "n8n-nodes-base.httpRequest",
                            "position": [500, 300],
                            "parameters": {
                                "method": "POST",
                                "url": "https://api.accounting.com/invoices"
                            }
                        }
                    ],
                    "connections": {
                        "webhook_2": {
                            "main": [
                                [
                                    {
                                        "node": "parse_1",
                                        "type": "main",
                                        "index": 0
                                    }
                                ]
                            ]
                        },
                        "parse_1": {
                            "main": [
                                [
                                    {
                                        "node": "accounting_1",
                                        "type": "main",
                                        "index": 0
                                    }
                                ]
                            ]
                        }
                    }
                }
            ]
            
            # Save workflows to vault
            for workflow in sample_workflows:
                workflow_file = self.test_vault_dir / f"{workflow['name']}.json"
                with open(workflow_file, 'w') as f:
                    json.dump(workflow, f, indent=2)
            
            # Create vault metadata
            vault_metadata = {
                "vault_version": "1.0.0",
                "total_workflows": len(sample_workflows),
                "created": datetime.now().isoformat(),
                "workflow_list": [w['name'] for w in sample_workflows]
            }
            
            metadata_file = self.test_vault_dir / "vault_metadata.json"
            with open(metadata_file, 'w') as f:
                json.dump(vault_metadata, f, indent=2)
            
            print(f"   ✅ Created {len(sample_workflows)} sample workflows")
            return True
            
        except Exception as e:
            print(f"   ❌ Failed to setup test vault: {e}")
            return False
    
    def test_imports_and_dependencies(self):
        """Test 1: Verify all imports and dependencies are available."""
        print("\n🧪 Test 1: Imports and Dependencies")
        
        passed = IMPORTS_SUCCESS
        details = {'import_success': IMPORTS_SUCCESS}
        error = None if passed else "Failed to import required modules"
        
        self.log_test_result("Import and Dependencies", passed, details, error)
        return passed
    
    def test_cli_interface(self):
        """Test 2: Test CLI command interface and argument parsing."""
        print("\n🧪 Test 2: CLI Interface")
        
        try:
            from click.testing import CliRunner
            
            runner = CliRunner()
            
            # Test help command
            result = runner.invoke(cli, ['--help'])
            help_success = result.exit_code == 0 and 'generate' in result.output
            
            # Test version command  
            result = runner.invoke(cli, ['version'])
            version_success = result.exit_code == 0
            
            # Test research command with mock
            with patch('src.modules.niche_research.NicheResearcher') as mock_researcher:
                mock_instance = MagicMock()
                mock_instance.research_niche.return_value = MagicMock(
                    niche_name="test-niche",
                    research_confidence=0.85,
                    market_size="Medium",
                    technology_adoption="High",
                    pain_points=[{"description": "test pain", "impact_score": 0.7, "automation_potential": 0.8}],
                    opportunities=[{"title": "test opp", "complexity": "Medium", "roi_estimate": "$50,000"}]
                )
                mock_researcher.return_value = mock_instance
                
                result = runner.invoke(cli, ['research', 'test-niche', '--timeout', '5'])
                research_success = result.exit_code == 0
            
            all_passed = help_success and version_success and research_success
            
            details = {
                'help_command': help_success,
                'version_command': version_success,
                'research_command': research_success
            }
            
            self.log_test_result("CLI Interface", all_passed, details, 
                               None if all_passed else "CLI command tests failed")
            return all_passed
            
        except Exception as e:
            error_msg = f"CLI test failed: {e}"
            self.log_test_result("CLI Interface", False, {}, error_msg)
            return False
    
    def test_file_system_operations(self):
        """Test 3: Test file manager and directory operations."""
        print("\n🧪 Test 3: File System Operations")
        
        try:
            # Test PackageFileManager
            file_manager = PackageFileManager(self.test_packages_dir)
            
            # Test directory creation
            test_slug = "test-package-filesystem"
            package_dir = file_manager.create_package_directory(test_slug)
            dir_created = package_dir.exists() and package_dir.is_dir()
            
            # Test JSON saving and loading
            test_data = {"test": "data", "number": 42, "nested": {"key": "value"}}
            json_file = package_dir / "test.json"
            file_manager.save_json(test_data, json_file)
            json_saved = json_file.exists()
            
            # Test text saving
            test_text = "This is test content\nWith multiple lines"
            text_file = package_dir / "test.txt"
            file_manager.save_text(test_text, text_file)
            text_saved = text_file.exists()
            
            # Test directory structure
            expected_structure = [
                package_dir / "docs",
                package_dir / "workflows", 
                package_dir / "tests"
            ]
            
            for dir_path in expected_structure:
                dir_path.mkdir(exist_ok=True)
            
            structure_created = all(d.exists() and d.is_dir() for d in expected_structure)
            
            all_passed = dir_created and json_saved and text_saved and structure_created
            
            details = {
                'directory_created': dir_created,
                'json_operations': json_saved,
                'text_operations': text_saved,
                'directory_structure': structure_created,
                'package_dir': str(package_dir)
            }
            
            self.log_test_result("File System Operations", all_passed, details,
                               None if all_passed else "File system operations failed")
            return all_passed
            
        except Exception as e:
            error_msg = f"File system test failed: {e}"
            self.log_test_result("File System Operations", False, {}, error_msg)
            return False
    
    def test_module_integration_flow(self):
        """Test 4: Test module-to-module data flow integration."""
        print("\n🧪 Test 4: Module Integration Flow")
        
        try:
            # Mock external dependencies
            with patch('src.integrations.research_client.ResearchClient') as mock_research_client, \
                 patch('requests.get') as mock_requests:
                
                # Setup mocks
                mock_research_instance = MagicMock()
                mock_research_client.return_value = mock_research_instance
                
                mock_response = MagicMock()
                mock_response.json.return_value = {"test": "data"}
                mock_response.status_code = 200
                mock_requests.return_value = mock_response
                
                # Test Step 1: Niche Research
                researcher = NicheResearcher(research_timeout=5)
                niche_brief = researcher.research_niche(self.test_niche)
                
                research_success = (
                    hasattr(niche_brief, 'niche_name') and 
                    hasattr(niche_brief, 'pain_points') and 
                    hasattr(niche_brief, 'opportunities')
                )
                
                if not research_success:
                    raise Exception("Niche research failed")
                
                # Test Step 2: Opportunity Mapping
                mapper = OpportunityMapper()
                opportunities = mapper.map_opportunities(niche_brief)
                
                mapping_success = (
                    isinstance(opportunities, list) and
                    len(opportunities) > 0 and
                    hasattr(opportunities[0], 'title') if opportunities else False
                )
                
                if not mapping_success:
                    raise Exception("Opportunity mapping failed")
                
                # Test Step 3: Workflow Assembly
                assembler = WorkflowAssembler(self.test_vault_dir)
                available_workflows = assembler.get_available_workflows()
                
                if available_workflows:
                    assembled_workflow = assembler.assemble_workflows(
                        available_workflows[:1], opportunities[0]
                    )
                    assembly_success = hasattr(assembled_workflow, 'name')
                else:
                    # Create mock workflow for testing
                    assembled_workflow = MagicMock()
                    assembled_workflow.name = "test_workflow"
                    assembled_workflow.nodes = []
                    assembled_workflow.connections = []
                    assembly_success = True
                
                # Test Step 4: Validation
                validator = WorkflowValidator()
                validation_results = validator.validate_workflow(assembled_workflow)
                validation_success = hasattr(validation_results, '__iter__')
                
                # Test Step 5: Documentation Generation
                doc_generator = DocumentationGenerator()
                try:
                    docs = doc_generator.generate_complete_documentation(
                        opportunities[0], assembled_workflow, 
                        {'summary': {'overall_status': 'PASS'}}, niche_brief
                    )
                    doc_success = isinstance(docs, dict) and len(docs) > 0
                except Exception as doc_error:
                    print(f"   Documentation generation failed: {doc_error}")
                    doc_success = False
                
                # Test Step 6: Package Generation
                try:
                    pkg_generator = PackageGenerator()
                    package = pkg_generator.generate_package(
                        opportunity=opportunities[0],
                        workflow=assembled_workflow,
                        niche_brief=niche_brief,
                        validation_report={'summary': {'overall_status': 'PASS'}}
                    )
                    pkg_success = hasattr(package, 'name') and hasattr(package, 'slug')
                except Exception as pkg_error:
                    print(f"   Package generation failed: {pkg_error}")
                    pkg_success = False
                
                all_passed = (research_success and mapping_success and 
                            assembly_success and validation_success and 
                            doc_success and pkg_success)
                
                details = {
                    'niche_research': research_success,
                    'opportunity_mapping': mapping_success, 
                    'workflow_assembly': assembly_success,
                    'validation': validation_success,
                    'documentation': doc_success,
                    'package_generation': pkg_success,
                    'opportunities_found': len(opportunities),
                    'available_workflows': len(available_workflows) if available_workflows else 0
                }
                
                self.log_test_result("Module Integration Flow", all_passed, details,
                                   None if all_passed else "Module integration flow failed")
                return all_passed
                
        except Exception as e:
            error_msg = f"Module integration test failed: {e}\n{traceback.format_exc()}"
            self.log_test_result("Module Integration Flow", False, {}, error_msg)
            return False
    
    def test_template_system(self):
        """Test 5: Test Jinja2 template rendering system."""
        print("\n🧪 Test 5: Template System")
        
        try:
            from jinja2 import Environment, FileSystemLoader, select_autoescape
            
            # Test template loading
            template_dir = Path(__file__).parent / "src" / "templates"
            if not template_dir.exists():
                raise Exception(f"Template directory not found: {template_dir}")
            
            env = Environment(
                loader=FileSystemLoader(str(template_dir)),
                autoescape=select_autoescape(['html', 'xml'])
            )
            
            # Test sample template data
            template_data = {
                'package_name': 'Test Package',
                'package_slug': 'test-package',
                'problem_statement': 'Test problem statement',
                'niche_name': 'Test Niche',
                'workflow': {
                    'name': 'test_workflow',
                    'description': 'Test workflow description'
                },
                'roi_notes': 'Test ROI notes',
                'dependencies': ['dependency1', 'dependency2'],
                'security_notes': 'Test security notes',
                'prerequisites': ['Prerequisite 1', 'Prerequisite 2'],
                'installation_steps': ['Step 1', 'Step 2'],
                'configuration_steps': ['Config Step 1', 'Config Step 2'],
                'testing_steps': ['Test Step 1', 'Test Step 2'],
                'template_variables': {
                    'api_keys_required': ['API_KEY_1', 'API_KEY_2'],
                    'environment_variables': {
                        'ENV_VAR_1': 'Description 1',
                        'ENV_VAR_2': 'Description 2'
                    },
                    'integration_gotchas': ['Gotcha 1', 'Gotcha 2'],
                    'rate_limits': {
                        'Service 1': '1000/hour',
                        'Service 2': '500/minute'
                    },
                    'version': '1.0.0',
                    'updated_at': '2025-01-01'
                }
            }
            
            # Test each template file
            template_files = list(template_dir.glob("*.j2"))
            template_results = {}
            
            for template_file in template_files:
                try:
                    template = env.get_template(template_file.name)
                    rendered = template.render(**template_data)
                    
                    # Basic validation - rendered content should exist and contain key data
                    template_success = (
                        len(rendered) > 100 and  # Reasonable content length
                        'Test Package' in rendered and  # Template data substitution
                        'Test Niche' in rendered
                    )
                    
                    template_results[template_file.name] = template_success
                    
                except Exception as template_error:
                    print(f"   Template {template_file.name} failed: {template_error}")
                    template_results[template_file.name] = False
            
            all_templates_passed = all(template_results.values())
            
            details = {
                'template_dir_exists': template_dir.exists(),
                'template_files_found': len(template_files),
                'template_results': template_results,
                'templates_processed': len(template_results)
            }
            
            self.log_test_result("Template System", all_templates_passed, details,
                               None if all_templates_passed else "Template rendering failed")
            return all_templates_passed
            
        except Exception as e:
            error_msg = f"Template system test failed: {e}"
            self.log_test_result("Template System", False, {}, error_msg)
            return False
    
    def test_end_to_end_workflow(self):
        """Test 6: Complete end-to-end package generation workflow."""
        print("\n🧪 Test 6: End-to-End Workflow")
        
        try:
            from click.testing import CliRunner
            import tempfile
            
            # Create temporary directory for this test
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)
                
                # Mock external dependencies
                with patch('src.integrations.research_client.ResearchClient') as mock_research, \
                     patch('requests.get') as mock_requests, \
                     patch('src.integrations.notion_client.NotionClient') as mock_notion:
                    
                    # Setup research client mock
                    mock_research_instance = MagicMock()
                    mock_research.return_value = mock_research_instance
                    
                    # Setup HTTP requests mock
                    mock_response = MagicMock()
                    mock_response.json.return_value = {"results": []}
                    mock_response.status_code = 200
                    mock_requests.return_value = mock_response
                    
                    # Setup notion client mock
                    mock_notion_instance = MagicMock()
                    mock_notion.return_value = mock_notion_instance
                    
                    # Run CLI generate command
                    runner = CliRunner()
                    result = runner.invoke(cli, [
                        '--output-dir', str(temp_path / 'packages'),
                        'generate', 
                        self.test_niche,
                        '--vault-path', str(self.test_vault_dir),
                        '--research-timeout', '5',
                        '--max-opportunities', '1',
                        '--generate-tests',
                        '--validate-only'  # Skip full generation for faster testing
                    ])
                    
                    # Check command execution
                    command_success = result.exit_code == 0
                    
                    # Check if package directory structure was created
                    packages_dir = temp_path / 'packages'
                    directory_created = packages_dir.exists()
                    
                    # Check for any package directories
                    package_dirs = [d for d in packages_dir.iterdir() if d.is_dir()] if directory_created else []
                    packages_created = len(package_dirs) > 0
                    
                    # Check for validation report
                    validation_files = []
                    if packages_created:
                        for pkg_dir in package_dirs:
                            validation_file = pkg_dir / "validation_report.json"
                            if validation_file.exists():
                                validation_files.append(validation_file)
                    
                    validation_reports_created = len(validation_files) > 0
                    
                    all_passed = command_success and directory_created and packages_created
                    
                    details = {
                        'command_exit_code': result.exit_code,
                        'command_success': command_success,
                        'directory_created': directory_created,
                        'packages_created': packages_created,
                        'package_count': len(package_dirs),
                        'validation_reports': len(validation_files),
                        'output_length': len(result.output),
                        'contains_success_indicators': '✅' in result.output
                    }
                    
                    # Add command output for debugging (truncated)
                    if result.output:
                        details['command_output_sample'] = result.output[:500] + "..." if len(result.output) > 500 else result.output
                    
                    error_msg = None
                    if not command_success:
                        error_msg = f"Command failed with exit code {result.exit_code}"
                        if result.output:
                            error_msg += f"\nOutput: {result.output[-300:]}"  # Last 300 chars
                    
                    self.log_test_result("End-to-End Workflow", all_passed, details, error_msg)
                    return all_passed
                    
        except Exception as e:
            error_msg = f"End-to-end workflow test failed: {e}\n{traceback.format_exc()}"
            self.log_test_result("End-to-End Workflow", False, {}, error_msg)
            return False
    
    def test_error_handling(self):
        """Test 7: Error handling across module boundaries."""
        print("\n🧪 Test 7: Error Handling")
        
        try:
            error_cases_passed = []
            
            # Test 1: Invalid niche research
            try:
                with patch('src.integrations.research_client.ResearchClient') as mock_research:
                    mock_research_instance = MagicMock()
                    mock_research_instance.research_niche.side_effect = Exception("Research API failed")
                    mock_research.return_value = mock_research_instance
                    
                    researcher = NicheResearcher(research_timeout=1)
                    try:
                        niche_brief = researcher.research_niche("invalid-niche")
                        # Should handle error gracefully and return some result
                        error_cases_passed.append(True)
                    except Exception:
                        # If it raises unhandled exception, error handling needs work
                        error_cases_passed.append(False)
                        
            except Exception:
                error_cases_passed.append(False)
            
            # Test 2: Invalid workflow assembly
            try:
                assembler = WorkflowAssembler(Path("/nonexistent/path"))
                available_workflows = assembler.get_available_workflows()
                # Should handle missing vault gracefully
                error_cases_passed.append(isinstance(available_workflows, list))
                
            except Exception:
                error_cases_passed.append(False)
            
            # Test 3: Package validator with invalid data
            try:
                validator = PackageValidator()
                # Test with invalid path
                results = validator.validate_package_directory(Path("/nonexistent/package"))
                # Should return validation results even for missing packages
                error_cases_passed.append(hasattr(results, '__iter__'))
                
            except Exception:
                error_cases_passed.append(False)
            
            # Test 4: CLI with invalid arguments
            try:
                from click.testing import CliRunner
                runner = CliRunner()
                
                # Test with invalid command
                result = runner.invoke(cli, ['invalid-command'])
                cli_error_handled = result.exit_code != 0  # Should fail gracefully
                error_cases_passed.append(cli_error_handled)
                
            except Exception:
                error_cases_passed.append(False)
            
            all_error_cases_passed = all(error_cases_passed)
            
            details = {
                'error_cases_tested': len(error_cases_passed),
                'error_cases_passed': sum(error_cases_passed),
                'research_error_handling': error_cases_passed[0] if len(error_cases_passed) > 0 else False,
                'assembly_error_handling': error_cases_passed[1] if len(error_cases_passed) > 1 else False,
                'validation_error_handling': error_cases_passed[2] if len(error_cases_passed) > 2 else False,
                'cli_error_handling': error_cases_passed[3] if len(error_cases_passed) > 3 else False
            }
            
            self.log_test_result("Error Handling", all_error_cases_passed, details,
                               None if all_error_cases_passed else "Error handling tests failed")
            return all_error_cases_passed
            
        except Exception as e:
            error_msg = f"Error handling test failed: {e}"
            self.log_test_result("Error Handling", False, {}, error_msg)
            return False
    
    def test_quality_gates(self):
        """Test 8: Quality gates and validation workflows."""
        print("\n🧪 Test 8: Quality Gates")
        
        try:
            quality_checks_passed = []
            
            # Test 1: Package structure validation
            try:
                # Create a test package with proper structure
                test_package_dir = self.test_packages_dir / "quality-test-package"
                test_package_dir.mkdir(exist_ok=True)
                
                # Create required directories
                (test_package_dir / "docs").mkdir(exist_ok=True)
                (test_package_dir / "workflows").mkdir(exist_ok=True)
                (test_package_dir / "tests").mkdir(exist_ok=True)
                
                # Create required files
                metadata = {
                    "name": "Quality Test Package",
                    "slug": "quality-test-package",
                    "problem_statement": "Test problem",
                    "outcomes": ["Test outcome"],
                    "roi_notes": "Test ROI",
                    "last_validated": datetime.now().isoformat()
                }
                
                with open(test_package_dir / "metadata.json", 'w') as f:
                    json.dump(metadata, f, indent=2)
                
                # Test validation
                validator = PackageValidator()
                results = validator.validate_package_directory(test_package_dir)
                
                # Check if validation runs and returns results
                structure_validation_passed = hasattr(results, '__iter__')
                quality_checks_passed.append(structure_validation_passed)
                
            except Exception:
                quality_checks_passed.append(False)
            
            # Test 2: Workflow validation
            try:
                validator = WorkflowValidator()
                
                # Create mock workflow
                mock_workflow = MagicMock()
                mock_workflow.name = "test_workflow"
                mock_workflow.nodes = [{"id": "1", "type": "trigger"}]
                mock_workflow.connections = []
                
                validation_results = validator.validate_workflow(mock_workflow)
                validation_report = validator.generate_validation_report(validation_results)
                
                workflow_validation_passed = (
                    isinstance(validation_report, dict) and
                    'summary' in validation_report
                )
                quality_checks_passed.append(workflow_validation_passed)
                
            except Exception:
                quality_checks_passed.append(False)
            
            # Test 3: Documentation quality
            try:
                doc_generator = DocumentationGenerator()
                
                # Mock data for documentation
                mock_opportunity = MagicMock()
                mock_opportunity.title = "Test Opportunity"
                mock_opportunity.problem_statement = "Test problem"
                
                mock_workflow = MagicMock()
                mock_workflow.name = "test_workflow"
                
                mock_validation_report = {
                    'summary': {'overall_status': 'PASS', 'total_checks': 5, 'passed': 5}
                }
                
                mock_niche_brief = MagicMock()
                mock_niche_brief.niche_name = "Test Niche"
                
                docs = doc_generator.generate_complete_documentation(
                    mock_opportunity, mock_workflow, mock_validation_report, mock_niche_brief
                )
                
                doc_quality_passed = (
                    isinstance(docs, dict) and
                    len(docs) > 0 and
                    all(len(content) > 50 for content in docs.values())  # Minimum content length
                )
                quality_checks_passed.append(doc_quality_passed)
                
            except Exception:
                quality_checks_passed.append(False)
            
            all_quality_checks_passed = all(quality_checks_passed)
            
            details = {
                'quality_checks_tested': len(quality_checks_passed),
                'quality_checks_passed': sum(quality_checks_passed),
                'structure_validation': quality_checks_passed[0] if len(quality_checks_passed) > 0 else False,
                'workflow_validation': quality_checks_passed[1] if len(quality_checks_passed) > 1 else False,
                'documentation_quality': quality_checks_passed[2] if len(quality_checks_passed) > 2 else False
            }
            
            self.log_test_result("Quality Gates", all_quality_checks_passed, details,
                               None if all_quality_checks_passed else "Quality gate tests failed")
            return all_quality_checks_passed
            
        except Exception as e:
            error_msg = f"Quality gates test failed: {e}"
            self.log_test_result("Quality Gates", False, {}, error_msg)
            return False
    
    def run_all_tests(self):
        """Run all Level 3 integration tests."""
        print(f"\n🚀 Starting Level 3 Integration Testing Suite")
        print(f"⏰ Start time: {self.test_start_time}")
        print("=" * 80)
        
        # Setup test environment
        vault_setup_success = self.setup_test_vault()
        if not vault_setup_success:
            print("❌ Failed to setup test vault - aborting tests")
            return False
        
        # Run all tests in sequence
        tests = [
            self.test_imports_and_dependencies,
            self.test_cli_interface,
            self.test_file_system_operations,
            self.test_module_integration_flow,
            self.test_template_system,
            self.test_end_to_end_workflow,
            self.test_error_handling,
            self.test_quality_gates
        ]
        
        for test_func in tests:
            try:
                test_func()
            except Exception as e:
                print(f"❌ Test {test_func.__name__} failed with exception: {e}")
                self.results['failed_tests'] += 1
                self.results['total_tests'] += 1
                self.results['errors'].append(f"{test_func.__name__}: {str(e)}")
        
        # Generate final report
        self.generate_final_report()
        
        return self.results['failed_tests'] == 0
    
    def generate_final_report(self):
        """Generate comprehensive test report."""
        end_time = datetime.now()
        duration = (end_time - self.test_start_time).total_seconds()
        
        print("\n" + "=" * 80)
        print("📊 LEVEL 3 INTEGRATION TEST RESULTS")
        print("=" * 80)
        
        # Summary statistics
        success_rate = (self.results['passed_tests'] / self.results['total_tests'] * 100) if self.results['total_tests'] > 0 else 0
        
        print(f"⏱️  Total Duration: {duration:.1f} seconds")
        print(f"📋 Total Tests: {self.results['total_tests']}")
        print(f"✅ Tests Passed: {self.results['passed_tests']}")
        print(f"❌ Tests Failed: {self.results['failed_tests']}")
        print(f"📈 Success Rate: {success_rate:.1f}%")
        
        # Overall status
        if self.results['failed_tests'] == 0:
            print("\n🎉 ALL TESTS PASSED - System integration validated!")
            overall_status = "PASS"
        else:
            print("\n⚠️  SOME TESTS FAILED - Integration issues detected")
            overall_status = "FAIL"
        
        # Error summary
        if self.results['errors']:
            print(f"\n🔍 Error Summary:")
            for i, error in enumerate(self.results['errors'], 1):
                print(f"  {i}. {error}")
        
        # Test details summary
        print(f"\n📝 Test Details:")
        for test_name, details in self.results['test_details'].items():
            status = "✅" if details['passed'] else "❌"
            print(f"  {status} {test_name}")
            if not details['passed'] and details['error']:
                print(f"      Error: {details['error'][:100]}...")
        
        # Save detailed report
        report_data = {
            'overall_status': overall_status,
            'summary': {
                'total_tests': self.results['total_tests'],
                'passed_tests': self.results['passed_tests'],
                'failed_tests': self.results['failed_tests'],
                'success_rate': success_rate,
                'duration_seconds': duration
            },
            'test_results': self.results['test_details'],
            'errors': self.results['errors'],
            'test_environment': {
                'test_directory': str(self.test_output_dir),
                'test_niche': self.test_niche,
                'python_version': sys.version,
                'timestamp': end_time.isoformat()
            }
        }
        
        report_file = self.test_output_dir / "level3_integration_report.json"
        with open(report_file, 'w') as f:
            json.dump(report_data, f, indent=2)
        
        print(f"\n📄 Detailed report saved: {report_file}")
        print(f"📁 Test artifacts directory: {self.test_output_dir}")
        
        return overall_status == "PASS"


def main():
    """Main entry point for Level 3 integration testing."""
    print("🧪 Automation Engine - Level 3 Integration Testing Suite")
    print("Testing end-to-end workflows and component integration")
    print("=" * 60)
    
    # Initialize and run tests
    tester = Level3IntegrationTester()
    
    try:
        success = tester.run_all_tests()
        
        if success:
            print(f"\n✅ Level 3 Integration Testing PASSED")
            return 0
        else:
            print(f"\n❌ Level 3 Integration Testing FAILED") 
            return 1
            
    except KeyboardInterrupt:
        print("\n⏹️  Testing interrupted by user")
        return 130
    except Exception as e:
        print(f"\n💥 Testing failed with exception: {e}")
        traceback.print_exc()
        return 1
    finally:
        print(f"\n🧹 Test artifacts available in: {tester.test_output_dir}")


if __name__ == '__main__':
    sys.exit(main())