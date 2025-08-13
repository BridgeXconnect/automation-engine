"""End-to-end tests for complete automation package pipeline."""

import pytest
import json
import time
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from src.models.package import AutomationPackage, PackageStatus
from src.models.workflow import N8nWorkflow
from src.models.documentation import DocumentationSuite
from src.modules.niche_research import NicheResearcher, NicheBrief
from src.modules.opportunity_mapping import OpportunityMapper
from src.modules.assembly import WorkflowAssembler
from src.modules.validation import WorkflowValidator, ValidationResult
from src.integrations.notion_client import NotionClient
from src.integrations.n8n_processor import WorkflowProcessor


class TestCompletePackageGenerationPipeline:
    """Test complete end-to-end package generation pipeline."""
    
    @pytest.fixture
    def pipeline_components(self, temp_directory, mock_environment_variables):
        """Set up all pipeline components with mocks."""
        # Real instances with temp directory
        assembler = WorkflowAssembler(automation_vault_path=temp_directory)
        validator = WorkflowValidator(fixtures_path=temp_directory)
        processor = WorkflowProcessor(automation_vault_path=temp_directory)
        
        # Mock external services
        with patch('src.integrations.notion_client.Client'):
            notion_client = NotionClient()
        
        researcher = Mock(spec=NicheResearcher)
        mapper = Mock(spec=OpportunityMapper)
        
        return {
            'researcher': researcher,
            'mapper': mapper,
            'assembler': assembler,
            'validator': validator,
            'processor': processor,
            'notion_client': notion_client
        }
    
    def test_research_to_package_complete_flow(self, pipeline_components, temp_directory):
        """Test complete flow from niche research to package creation."""
        components = pipeline_components
        
        # 1. Mock niche research
        mock_niche_brief = NicheBrief(
            niche_name="e-commerce_automation",
            profile={
                "industry": "E-commerce",
                "company_size": "SMB",
                "tech_sophistication": "medium"
            },
            pain_points=[
                {
                    "description": "Manual order processing takes 5-10 minutes per order",
                    "impact_score": 0.85,
                    "frequency": "daily",
                    "automation_potential": 0.9,
                    "existing_solutions": ["Manual spreadsheets"],
                    "gaps": ["No automation", "Error prone"]
                }
            ],
            opportunities=[
                {
                    "title": "Automated Order Processing",
                    "description": "Streamline order intake and fulfillment",
                    "automation_type": "E-commerce Integration",
                    "complexity": "Medium",
                    "roi_estimate": "High ROI (>400% in 8 months)",
                    "implementation_time": "3-4 weeks",
                    "required_integrations": ["Shopify", "Slack", "Gmail"]
                }
            ],
            research_confidence=0.88
        )
        
        components['researcher'].research_niche.return_value = mock_niche_brief
        
        # 2. Mock opportunity mapping
        mapped_opportunities = [
            {
                "title": "E-commerce Order Automation",
                "description": "Fully automated order processing pipeline",
                "automation_type": "E-commerce Integration",
                "complexity": "Medium",
                "roi_estimate": "High ROI (>400% in 8 months)",
                "implementation_time": "3-4 weeks",
                "required_integrations": ["Shopify", "Slack", "Gmail"],
                "success_metrics": [
                    "Reduce order processing time by 90%",
                    "Eliminate order processing errors",
                    "Increase order throughput by 3x"
                ],
                "business_value": "Enables scaling without proportional staff increase"
            }
        ]
        
        components['mapper'].map_opportunities.return_value = mapped_opportunities
        
        # 3. Execute complete pipeline
        
        # Research phase
        niche_brief = components['researcher'].research_niche("e-commerce automation")
        assert niche_brief.niche_name == "e-commerce_automation"
        assert niche_brief.research_confidence > 0.8
        
        # Opportunity mapping phase  
        opportunities = components['mapper'].map_opportunities(niche_brief)
        assert len(opportunities) == 1
        best_opportunity = opportunities[0]
        
        # Assembly phase
        package = components['assembler'].assemble_package(best_opportunity)
        assert isinstance(package, AutomationPackage)
        assert package.name == "E-commerce Order Automation"
        assert package.slug == "e-commerce-order-automation"
        assert "Shopify" in package.dependencies
        
        # Package structure generation
        package_path = components['assembler'].generate_package_structure(package)
        assert package_path.exists()
        assert (package_path / "workflows").exists()
        assert (package_path / "docs").exists()
        assert (package_path / "metadata.json").exists()
        
        # Validation phase
        validation_results = components['validator'].validate_package(package)
        assert len(validation_results) > 0
        
        # Should have some successful validations
        passed_validations = [r for r in validation_results if r.passed]
        assert len(passed_validations) > 0
        
        # Generate validation report
        report = components['validator'].generate_validation_report(validation_results)
        assert report["summary"]["total_checks"] > 0
        assert "by_level" in report
    
    def test_workflow_customization_and_validation_flow(self, pipeline_components, temp_directory):
        """Test workflow customization and validation flow."""
        components = pipeline_components
        
        # Create sample workflow template  
        template_workflow_data = {
            "name": "ecommerce_order_template",
            "nodes": [
                {
                    "id": "shopify_webhook",
                    "name": "order_webhook",
                    "type": "n8n-nodes-base.webhook",
                    "position": [100, 100],
                    "parameters": {
                        "path": "/shopify/order",
                        "httpMethod": "POST"
                    }
                },
                {
                    "id": "order_validator",
                    "name": "validate_order_data",
                    "type": "n8n-nodes-base.set",
                    "position": [300, 100],
                    "parameters": {
                        "values": {
                            "order_validated": "true",
                            "processing_timestamp": "{{ new Date().toISOString() }}"
                        }
                    }
                },
                {
                    "id": "slack_notification",
                    "name": "notify_fulfillment_team",
                    "type": "n8n-nodes-base.slack",
                    "position": [500, 100],
                    "parameters": {
                        "channel": "#fulfillment",
                        "text": "New order received: {{ $json.order_number }}"
                    }
                }
            ],
            "connections": {
                "shopify_webhook": {
                    "main": [{"node": "order_validator", "type": "main", "index": 0}]
                },
                "order_validator": {
                    "main": [{"node": "slack_notification", "type": "main", "index": 0}]
                }
            },
            "active": false
        }
        
        # Save template workflow
        template_file = temp_directory / "ecommerce_order_template.json"
        with open(template_file, 'w') as f:
            json.dump(template_workflow_data, f, indent=2)
        
        # Load and customize workflow
        base_workflow = components['processor'].load_workflow_from_vault("ecommerce_order_template")
        assert isinstance(base_workflow, N8nWorkflow)
        assert len(base_workflow.nodes) == 3
        
        # Apply processing enhancements
        enhanced_workflow = components['processor'].process_workflow("ecommerce_order_template")
        
        # Validate enhanced workflow
        validation_results = components['validator'].validate_workflow(enhanced_workflow)
        
        # Should have various validation checks
        assert len(validation_results) > 5
        
        # Check for specific validation types
        validation_levels = [r.level for r in validation_results]
        assert "schema" in validation_levels
        assert "security" in validation_levels
        assert "performance" in validation_levels
        
        # Generate comprehensive report
        report = components['validator'].generate_validation_report(validation_results)
        assert report["summary"]["total_checks"] > 5
        
        # Should be mostly passing validations for a well-formed workflow
        success_rate = report["summary"]["success_rate"] 
        assert success_rate > 0.5  # At least 50% should pass
    
    def test_notion_integration_complete_flow(self, pipeline_components, sample_automation_package):
        """Test complete Notion integration flow."""
        components = pipeline_components
        notion_client = components['notion_client']
        
        # Mock Notion operations
        with patch.object(notion_client, 'create_business_os') as mock_create_os:
            with patch.object(notion_client, 'create_library_record') as mock_create_record:
                with patch.object(notion_client, 'verify_database_schema') as mock_verify:
                    
                    # Mock return values
                    mock_create_os.return_value = {
                        "library": "db_lib_123",
                        "automations": "db_auto_123", 
                        "components": "db_comp_123",
                        "clients": "db_clients_123",
                        "deployments": "db_deploy_123"
                    }
                    mock_create_record.return_value = "page_record_456"
                    mock_verify.return_value = True
                    
                    # Execute Notion integration flow
                    
                    # 1. Create Business OS schema
                    database_ids = notion_client.create_business_os("parent_page_123")
                    assert len(database_ids) == 5
                    assert "library" in database_ids
                    
                    # 2. Verify schema
                    schema_valid = notion_client.verify_database_schema()
                    assert schema_valid is True
                    
                    # 3. Create library record
                    record_id = notion_client.create_library_record(sample_automation_package)
                    assert record_id == "page_record_456"
                    
                    # Verify all operations were called
                    mock_create_os.assert_called_once_with("parent_page_123")
                    mock_verify.assert_called_once()
                    mock_create_record.assert_called_once_with(sample_automation_package)
    
    def test_documentation_generation_flow(self, pipeline_components, temp_directory):
        """Test documentation generation flow."""
        components = pipeline_components
        
        # Create automation package
        package = AutomationPackage(
            name="Customer Onboarding Automation",
            slug="customer-onboarding-automation",
            niche_tags=["crm", "onboarding", "customer-success"],
            problem_statement="Manual customer onboarding takes 2-3 hours per customer and is error-prone",
            outcomes=[
                "Reduce onboarding time to under 15 minutes",
                "Eliminate onboarding errors",
                "Standardize onboarding experience"
            ],
            roi_notes="Customer Success team saves 20 hours/week. Improved customer experience increases retention by 15%",
            inputs={
                "customer_email": "string",
                "subscription_tier": "string",
                "company_name": "string"
            },
            outputs={
                "onboarding_completed": "boolean",
                "account_setup": "boolean",
                "welcome_email_sent": "boolean"
            },
            dependencies=["CRM", "Email Platform", "Knowledge Base"],
            security_notes="Handles customer PII. All communications encrypted."
        )
        
        # Generate package structure with docs
        package_path = components['assembler'].generate_package_structure(package)
        docs_path = package_path / "docs"
        
        # Generate documentation suite
        doc_suite = components['assembler'].generate_documentation_suite(package)
        assert isinstance(doc_suite, DocumentationSuite)
        
        # Verify documentation components
        assert doc_suite.implementation_guide is not None
        assert doc_suite.configuration_guide is not None
        assert doc_suite.runbook is not None
        
        # Check content quality
        impl_guide = doc_suite.implementation_guide
        assert len(impl_guide.content) > 100  # Substantial content
        assert "customer onboarding" in impl_guide.content.lower()
        
        config_guide = doc_suite.configuration_guide
        assert len(config_guide.environment_variables) > 0
        assert len(config_guide.api_keys_required) > 0
        
        # Calculate documentation metrics
        metrics = doc_suite.calculate_total_content_metrics()
        assert metrics["total_word_count"] > 200
        assert metrics["document_count"] >= 3
        
        # Save documentation files
        for doc in doc_suite.get_all_documents():
            doc_file = docs_path / doc.get_filename()
            doc_file.write_text(doc.content)
            assert doc_file.exists()
            assert doc_file.stat().st_size > 50  # Non-empty files


class TestErrorRecoveryScenarios:
    """Test error recovery and resilience scenarios."""
    
    def test_partial_failure_recovery(self, temp_directory, mock_environment_variables):
        """Test recovery from partial pipeline failures."""
        # Simulate a scenario where some operations fail but others succeed
        
        # Mock components with mixed success/failure
        researcher = Mock(spec=NicheResearcher)
        researcher.research_niche.side_effect = Exception("API rate limit exceeded")
        
        assembler = WorkflowAssembler(automation_vault_path=temp_directory)
        validator = WorkflowValidator(fixtures_path=temp_directory)
        
        # Test graceful degradation
        with pytest.raises(Exception) as exc_info:
            researcher.research_niche("test_niche")
        
        assert "API rate limit exceeded" in str(exc_info.value)
        
        # But other components should still work
        test_opportunity = {
            "title": "Test Automation",
            "description": "Test description",
            "automation_type": "Test",
            "complexity": "Low",
            "required_integrations": ["Test Service"]
        }
        
        # Assembly should work without research data
        package = assembler.assemble_package(test_opportunity)
        assert isinstance(package, AutomationPackage)
        
        # Validation should work independently
        validation_results = validator.validate_package(package)
        assert len(validation_results) > 0
    
    def test_data_corruption_handling(self, temp_directory):
        """Test handling of corrupted data files."""
        processor = WorkflowProcessor(automation_vault_path=temp_directory)
        
        # Create corrupted workflow file
        corrupted_file = temp_directory / "corrupted_workflow.json"
        with open(corrupted_file, 'w') as f:
            f.write('{ "name": "test", "nodes": [ { "id": "incomplete"')  # Incomplete JSON
        
        # Should handle corrupted data gracefully
        with pytest.raises(WorkflowProcessorError) as exc_info:
            processor.load_workflow_from_vault("corrupted_workflow")
        
        assert "Invalid JSON" in str(exc_info.value)
    
    def test_concurrent_access_scenarios(self, temp_directory):
        """Test handling of concurrent access to resources."""
        assembler1 = WorkflowAssembler(automation_vault_path=temp_directory)
        assembler2 = WorkflowAssembler(automation_vault_path=temp_directory)
        
        # Create packages with same slug simultaneously
        opportunity = {
            "title": "Concurrent Test Package",
            "description": "Testing concurrent creation",
            "automation_type": "Test",
            "complexity": "Low",
            "required_integrations": []
        }
        
        package1 = assembler1.assemble_package(opportunity)
        package2 = assembler2.assemble_package(opportunity)
        
        # Both should create valid packages
        assert package1.slug == package2.slug
        assert isinstance(package1, AutomationPackage)
        assert isinstance(package2, AutomationPackage)
        
        # But package structure creation should handle conflicts
        path1 = assembler1.generate_package_structure(package1)
        path2 = assembler2.generate_package_structure(package2)
        
        # Both paths should exist and be valid
        assert path1.exists()
        assert path2.exists()
    
    def test_resource_exhaustion_scenarios(self, temp_directory):
        """Test behavior under resource constraints.""" 
        processor = WorkflowProcessor(automation_vault_path=temp_directory)
        
        # Create workflow with many nodes to test memory usage
        large_workflow_data = {
            "name": "resource_test_workflow",
            "nodes": [
                {
                    "id": f"node_{i}",
                    "name": f"node_{i}",
                    "type": "n8n-nodes-base.set",
                    "position": [i * 50, 100],
                    "parameters": {
                        "values": {
                            f"data_{j}": f"value_{j}" * 100  # Large parameter values
                            for j in range(10)
                        }
                    }
                }
                for i in range(100)  # 100 nodes with large parameters
            ],
            "connections": {}
        }
        
        # Save large workflow
        large_workflow_file = temp_directory / "resource_test_workflow.json"
        with open(large_workflow_file, 'w') as f:
            json.dump(large_workflow_data, f)
        
        # Should handle large workflow without excessive resource usage
        start_time = time.time()
        workflow = processor.load_workflow_from_vault("resource_test_workflow")
        load_time = time.time() - start_time
        
        assert isinstance(workflow, N8nWorkflow)
        assert len(workflow.nodes) == 100
        # Should load reasonably quickly (less than 2 seconds)
        assert load_time < 2.0


class TestPerformanceScenarios:
    """Test performance under various load conditions."""
    
    def test_high_volume_package_generation(self, temp_directory):
        """Test generating many packages efficiently."""
        assembler = WorkflowAssembler(automation_vault_path=temp_directory)
        
        # Generate multiple packages
        opportunities = [
            {
                "title": f"Package {i}",
                "description": f"Test package {i}",
                "automation_type": "Test",
                "complexity": "Low",
                "required_integrations": ["Service A"]
            }
            for i in range(20)
        ]
        
        start_time = time.time()
        packages = []
        
        for opportunity in opportunities:
            package = assembler.assemble_package(opportunity)
            packages.append(package)
        
        generation_time = time.time() - start_time
        
        # Should generate packages efficiently
        assert len(packages) == 20
        assert generation_time < 5.0  # Less than 5 seconds for 20 packages
        
        # All packages should be valid
        for package in packages:
            assert isinstance(package, AutomationPackage)
            assert package.name.startswith("Package")
    
    def test_large_workflow_processing_performance(self, temp_directory):
        """Test processing performance with large workflows."""
        processor = WorkflowProcessor(automation_vault_path=temp_directory)
        validator = WorkflowValidator(fixtures_path=temp_directory)
        
        # Create complex workflow
        complex_workflow_data = {
            "name": "complex_performance_test",
            "nodes": [
                {
                    "id": f"node_{i}",
                    "name": f"process_node_{i}",
                    "type": "n8n-nodes-base.set" if i % 3 == 0 else "n8n-nodes-base.if",
                    "position": [i * 100, (i % 5) * 100],
                    "parameters": {
                        "values" if i % 3 == 0 else "conditions": {
                            f"param_{j}": f"complex_value_{j}_for_node_{i}"
                            for j in range(5)
                        }
                    }
                }
                for i in range(75)  # 75 nodes
            ],
            "connections": {
                f"node_{i}": {
                    "main": [{"node": f"node_{i+1}", "type": "main", "index": 0}]
                }
                for i in range(74)  # Connect nodes in sequence
            }
        }
        
        # Save complex workflow
        complex_file = temp_directory / "complex_performance_test.json"
        with open(complex_file, 'w') as f:
            json.dump(complex_workflow_data, f)
        
        # Test loading performance
        start_time = time.time()
        workflow = processor.load_workflow_from_vault("complex_performance_test")
        load_time = time.time() - start_time
        
        assert load_time < 1.0  # Should load quickly
        assert len(workflow.nodes) == 75
        
        # Test processing performance
        start_time = time.time()
        processed_workflow = processor.process_workflow("complex_performance_test")
        processing_time = time.time() - start_time
        
        assert processing_time < 3.0  # Should process in reasonable time
        assert len(processed_workflow.nodes) > 75  # Should have added nodes
        
        # Test validation performance
        start_time = time.time()
        validation_results = validator.validate_workflow(processed_workflow)
        validation_time = time.time() - start_time
        
        assert validation_time < 2.0  # Should validate quickly
        assert len(validation_results) > 10  # Should have multiple validation checks
    
    def test_concurrent_validation_performance(self, temp_directory):
        """Test validation performance with concurrent operations."""
        validator = WorkflowValidator(fixtures_path=temp_directory)
        
        # Create multiple test packages
        packages = [
            AutomationPackage(
                name=f"Concurrent Test Package {i}",
                slug=f"concurrent-test-package-{i}",
                problem_statement=f"Test problem {i}",
                roi_notes=f"Test ROI {i}"
            )
            for i in range(15)
        ]
        
        # Validate all packages
        start_time = time.time()
        all_results = []
        
        for package in packages:
            results = validator.validate_package(package)
            all_results.extend(results)
        
        total_time = time.time() - start_time
        
        # Should validate efficiently
        assert len(all_results) > 30  # Multiple validations per package
        assert total_time < 3.0  # Should complete quickly
        
        # All validations should be meaningful
        for result in all_results[:10]:  # Check first 10
            assert isinstance(result, ValidationResult)
            assert hasattr(result, 'passed')
            assert len(result.message) > 10  # Meaningful messages


class TestDataIntegrityScenarios:
    """Test data integrity across the pipeline."""
    
    def test_package_metadata_consistency(self, temp_directory):
        """Test consistency of package metadata throughout pipeline."""
        assembler = WorkflowAssembler(automation_vault_path=temp_directory)
        
        opportunity = {
            "title": "Data Integrity Test Package",
            "description": "Testing data consistency through pipeline",
            "automation_type": "Data Processing",
            "complexity": "Medium",
            "required_integrations": ["Service A", "Service B", "Service C"],
            "roi_estimate": "High ROI (>300% in 6 months)",
            "implementation_time": "4-6 weeks"
        }
        
        # Create package
        package = assembler.assemble_package(opportunity)
        
        # Verify data consistency
        assert package.name == opportunity["title"]
        assert package.slug == "data-integrity-test-package"
        assert all(dep in package.dependencies for dep in opportunity["required_integrations"])
        assert opportunity["roi_estimate"] in package.roi_notes
        
        # Generate package structure
        package_path = assembler.generate_package_structure(package)
        
        # Check metadata file consistency
        metadata_file = package_path / "metadata.json"
        assert metadata_file.exists()
        
        with open(metadata_file, 'r') as f:
            saved_metadata = json.load(f)
        
        # Verify metadata matches package
        assert saved_metadata["name"] == package.name
        assert saved_metadata["slug"] == package.slug
        assert saved_metadata["dependencies"] == package.dependencies
        assert saved_metadata["roi_notes"] == package.roi_notes
    
    def test_workflow_integrity_through_processing(self, temp_directory):
        """Test workflow integrity through processing pipeline."""
        processor = WorkflowProcessor(automation_vault_path=temp_directory)
        
        # Create original workflow
        original_workflow_data = {
            "name": "integrity_test_workflow",
            "nodes": [
                {
                    "id": "original_webhook",
                    "name": "webhook_start",
                    "type": "n8n-nodes-base.webhook",
                    "position": [100, 100],
                    "parameters": {"path": "/test", "httpMethod": "POST"}
                },
                {
                    "id": "original_processor",
                    "name": "data_processor",
                    "type": "n8n-nodes-base.set",
                    "position": [300, 100],
                    "parameters": {
                        "values": {"processed": "true", "important_data": "preserve_this"}
                    }
                }
            ],
            "connections": {
                "original_webhook": {
                    "main": [{"node": "original_processor", "type": "main", "index": 0}]
                }
            }
        }
        
        # Save original workflow
        workflow_file = temp_directory / "integrity_test_workflow.json"
        with open(workflow_file, 'w') as f:
            json.dump(original_workflow_data, f)
        
        # Load and process workflow
        workflow = processor.load_workflow_from_vault("integrity_test_workflow")
        processed_workflow = processor.process_workflow("integrity_test_workflow")
        
        # Verify core data integrity
        original_nodes = {n.id: n for n in workflow.nodes}
        processed_nodes = {n.id: n for n in processed_workflow.nodes if not n.id.startswith(('log_', 'error_'))}
        
        # Original nodes should still exist with core data intact
        assert "original_webhook" in processed_nodes
        assert "original_processor" in processed_nodes
        
        webhook_node = processed_nodes["original_webhook"]
        processor_node = processed_nodes["original_processor"]
        
        # Core parameters should be preserved
        assert webhook_node.parameters["path"] == "/test"
        assert webhook_node.parameters["httpMethod"] == "POST"
        assert processor_node.parameters["values"]["important_data"] == "preserve_this"
        
        # But processing enhancements should be added
        assert webhook_node.retries == 3  # Retry logic added
        assert webhook_node.retry_on_fail is True
    
    def test_cross_module_data_consistency(self, temp_directory):
        """Test data consistency across different modules."""
        # Create consistent test data
        test_opportunity = {
            "title": "Cross Module Test",
            "description": "Testing data consistency across modules",
            "automation_type": "Integration",
            "complexity": "Medium",
            "required_integrations": ["CRM", "Email"],
            "roi_estimate": "Medium ROI (200% in 12 months)"
        }
        
        # Test data flow through multiple modules
        assembler = WorkflowAssembler(automation_vault_path=temp_directory)
        validator = WorkflowValidator(fixtures_path=temp_directory)
        
        # Assembly phase
        package = assembler.assemble_package(test_opportunity)
        
        # Validation phase should see consistent data
        validation_results = validator.validate_package(package)
        
        # Generate documentation
        doc_suite = assembler.generate_documentation_suite(package)
        
        # Verify consistency across all outputs
        assert package.name == test_opportunity["title"]
        
        # Documentation should reference correct package data
        impl_guide = doc_suite.implementation_guide
        assert package.name.lower() in impl_guide.content.lower()
        assert package.slug in impl_guide.package_slug
        
        # Validation should reference correct package
        validation_messages = [r.message for r in validation_results]
        # Should have validated the correct package (no error messages about wrong package)
        assert not any("wrong" in msg.lower() for msg in validation_messages)


class TestRegressionScenarios:
    """Test scenarios to prevent regression of known issues."""
    
    def test_slug_generation_edge_cases(self, temp_directory):
        """Test edge cases in slug generation that previously caused issues."""
        assembler = WorkflowAssembler(automation_vault_path=temp_directory)
        
        edge_case_opportunities = [
            {
                "title": "Package With Special Characters!@#$%",
                "description": "Testing special character handling",
                "automation_type": "Test", "complexity": "Low",
                "required_integrations": []
            },
            {
                "title": "Package    With    Extra    Spaces",
                "description": "Testing space handling",
                "automation_type": "Test", "complexity": "Low",
                "required_integrations": []
            },
            {
                "title": "PACKAGE WITH ALL CAPS",
                "description": "Testing case handling",
                "automation_type": "Test", "complexity": "Low",
                "required_integrations": []
            },
            {
                "title": "Package-with-hyphens-and_underscores",
                "description": "Testing mixed separators",
                "automation_type": "Test", "complexity": "Low", 
                "required_integrations": []
            }
        ]
        
        expected_slugs = [
            "package-with-special-characters",
            "package-with-extra-spaces",
            "package-with-all-caps",
            "package-with-hyphens-and-underscores"
        ]
        
        for opportunity, expected_slug in zip(edge_case_opportunities, expected_slugs):
            package = assembler.assemble_package(opportunity)
            assert package.slug == expected_slug, f"Expected {expected_slug}, got {package.slug}"
    
    def test_validation_result_serialization(self, temp_directory):
        """Test that validation results can be properly serialized."""
        validator = WorkflowValidator(fixtures_path=temp_directory)
        
        package = AutomationPackage(
            name="Serialization Test",
            slug="serialization-test",
            problem_statement="Test problem",
            roi_notes="Test ROI"
        )
        
        results = validator.validate_package(package)
        report = validator.generate_validation_report(results)
        
        # Should be JSON serializable
        try:
            json.dumps(report)
            json_serializable = True
        except (TypeError, ValueError):
            json_serializable = False
        
        assert json_serializable, "Validation report should be JSON serializable"
        
        # Check specific fields are serializable
        assert isinstance(report["generated_at"], str)
        assert isinstance(report["summary"]["success_rate"], (int, float))
    
    def test_file_path_handling_edge_cases(self, temp_directory):
        """Test edge cases in file path handling."""
        assembler = WorkflowAssembler(automation_vault_path=temp_directory)
        
        # Test with package name that could cause file system issues
        problematic_package = AutomationPackage(
            name="Package/With\\Problematic:Characters",
            slug="package-with-problematic-characters",
            problem_statement="Test problem", 
            roi_notes="Test ROI"
        )
        
        # Should handle problematic characters gracefully
        package_path = assembler.generate_package_structure(problematic_package)
        
        assert package_path.exists()
        assert package_path.is_dir()
        # Path should not contain problematic characters
        assert "/" not in package_path.name
        assert "\\" not in package_path.name
        assert ":" not in package_path.name