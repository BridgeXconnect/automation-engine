#!/usr/bin/env python3
"""
Main CLI interface for the Automation Package Generator.

This orchestrates all 6 modules in sequence following CLAUDE.md standards:
- Niche Research
- Opportunity Mapping  
- Assembly
- Validation
- Documentation
- Package Generation
"""

import click
import logging
import sys
import time
from pathlib import Path
from datetime import datetime

from .utils.file_manager import PackageFileManager
from .utils.validators import PackageValidator
from .utils.helpers import generate_slug, setup_logging
from .integrations.research_client import ResearchClient

# Import all modules
from .modules.niche_research import NicheResearcher
from .modules.opportunity_mapping import OpportunityMapper
from .modules.assembly import WorkflowAssembler
from .modules.validation import WorkflowValidator

logger = logging.getLogger(__name__)

@click.group()
@click.option('--debug', is_flag=True, help='Enable debug logging')
@click.option('--output-dir', default='packages', help='Output directory for packages')
@click.pass_context
def cli(ctx, debug: bool, output_dir: str):
    """Automation Package Generator CLI - Orchestrate all 6 modules."""
    # Setup logging
    log_level = logging.DEBUG if debug else logging.INFO
    setup_logging(log_level)
    
    # Initialize context
    ctx.ensure_object(dict)
    ctx.obj['debug'] = debug
    ctx.obj['output_dir'] = Path(output_dir)
    ctx.obj['start_time'] = datetime.utcnow()
    
    # Ensure output directory exists
    ctx.obj['output_dir'].mkdir(exist_ok=True)
    
    logger.info(f"🚀 Automation Package Generator started - Output: {output_dir}")


@cli.command()
@click.argument('niche_keyword')
@click.option('--vault-path', default='automation_vault', help='Path to automation vault directory')
@click.option('--research-timeout', default=30, help='Research timeout in seconds')
@click.option('--max-opportunities', default=3, help='Maximum opportunities to process')
@click.option('--generate-tests', is_flag=True, help='Generate test fixtures')
@click.option('--validate-only', is_flag=True, help='Only validate, do not create package')
@click.pass_context
def generate(ctx, niche_keyword: str, vault_path: str, research_timeout: int, 
             max_opportunities: int, generate_tests: bool, validate_only: bool):
    """
    Generate complete automation package for a niche.
    
    This orchestrates all 6 modules in sequence:
    1. Niche Research
    2. Opportunity Mapping
    3. Workflow Assembly
    4. Validation
    5. Documentation Generation
    6. Package Creation
    """
    output_dir = ctx.obj['output_dir']
    start_time = time.time()
    
    try:
        # Initialize components
        file_manager = PackageFileManager(output_dir)
        ResearchClient(timeout=research_timeout)  # Initialize research client
        
        # Progress tracking
        total_steps = 6
        current_step = 0
        
        click.echo(f"\n🎯 Generating automation package for niche: {niche_keyword}")
        click.echo(f"📁 Output directory: {output_dir}")
        click.echo(f"⚙️  Vault path: {vault_path}")
        click.echo("=" * 60)
        
        # STEP 1: Niche Research
        current_step += 1
        click.echo(f"\n[{current_step}/{total_steps}] 🔍 Conducting niche research...")
        
        researcher = NicheResearcher(research_timeout=research_timeout)
        niche_brief = researcher.research_niche(niche_keyword)
        
        logger.info(f"Research completed - Confidence: {niche_brief.research_confidence:.2f}")
        click.echo(f"  ✅ Research completed - {len(niche_brief.pain_points)} pain points identified")
        click.echo(f"  📊 Confidence Score: {niche_brief.research_confidence:.2%}")
        
        # STEP 2: Opportunity Mapping
        current_step += 1
        click.echo(f"\n[{current_step}/{total_steps}] 🎯 Mapping automation opportunities...")
        
        mapper = OpportunityMapper()
        opportunities = mapper.map_opportunities(niche_brief)
        
        # Limit opportunities processed
        opportunities = opportunities[:max_opportunities]
        
        click.echo(f"  ✅ {len(opportunities)} automation opportunities identified")
        for i, opp in enumerate(opportunities[:3], 1):
            click.echo(f"  {i}. {opp.title} (Priority: {opp.priority_score:.2f})")
        
        if not opportunities:
            click.echo("  ⚠️  No viable automation opportunities found")
            return
        
        # Process each opportunity
        for opp_idx, opportunity in enumerate(opportunities, 1):
            click.echo(f"\n{'='*20} Processing Opportunity {opp_idx}/{len(opportunities)} {'='*20}")
            click.echo(f"🎯 {opportunity.title}")
            click.echo(f"💰 ROI: ${opportunity.roi_estimate.get('three_year_value', 0):,.0f} (3-year)")
            click.echo(f"⚠️  Risk: {opportunity.risk_assessment.get('overall_risk', 0):.1%}")
            
            # Generate package slug
            package_slug = generate_slug(opportunity.title)
            
            # Create package directory structure
            package_dir = file_manager.create_package_directory(package_slug)
            click.echo(f"📁 Package directory: {package_dir}")
            
            # STEP 3: Workflow Assembly
            current_step = 3
            click.echo(f"\n[{current_step}/{total_steps}] 🔧 Assembling workflows...")
            
            assembler = WorkflowAssembler(Path(vault_path))
            available_workflows = assembler.get_available_workflows()
            
            if not available_workflows:
                click.echo(f"  ⚠️  No workflows found in {vault_path}")
                # Create placeholder workflow for demo
                workflow_names = ["placeholder_workflow"]
            else:
                # Select relevant workflows (simplified selection)
                workflow_names = available_workflows[:2]  # Use first 2 for demo
            
            try:
                assembled_workflow = assembler.assemble_workflows(workflow_names, opportunity)
                click.echo(f"  ✅ Workflow assembled: {assembled_workflow.name}")
                click.echo(f"  🔗 Nodes: {len(assembled_workflow.nodes)}, Connections: {len(assembled_workflow.connections)}")
            except Exception as e:
                logger.error(f"Workflow assembly failed: {e}")
                click.echo(f"  ❌ Workflow assembly failed: {e}")
                continue
            
            # STEP 4: Validation
            current_step = 4
            click.echo(f"\n[{current_step}/{total_steps}] ✅ Validating workflow...")
            
            validator = WorkflowValidator()
            validation_results = validator.validate_workflow(assembled_workflow)
            
            # Generate validation report
            validation_report = validator.generate_validation_report(validation_results)
            passed_checks = validation_report['summary']['passed']
            total_checks = validation_report['summary']['total_checks']
            success_rate = validation_report['summary']['success_rate']
            
            click.echo(f"  📊 Validation: {passed_checks}/{total_checks} checks passed ({success_rate:.1%})")
            
            if validation_report['summary']['overall_status'] == 'FAIL':
                click.echo("  ⚠️  Validation issues detected:")
                for level, data in validation_report['by_level'].items():
                    if data['failed'] > 0:
                        click.echo(f"    - {level}: {data['failed']} failures")
            else:
                click.echo("  ✅ All validations passed")
            
            # Save validation report
            validation_file = package_dir / "validation_report.json"
            file_manager.save_json(validation_report, validation_file)
            
            if validate_only:
                click.echo("  🛑 Validation-only mode - stopping here")
                continue
            
            # STEP 5: Documentation Generation
            current_step = 5
            click.echo(f"\n[{current_step}/{total_steps}] 📝 Generating documentation...")
            
            from .modules.documentation import DocumentationGenerator
            doc_generator = DocumentationGenerator()
            
            try:
                # Generate all required documents
                docs = doc_generator.generate_complete_documentation(
                    opportunity, assembled_workflow, validation_report, niche_brief
                )
                
                # Save documentation
                docs_dir = package_dir / "docs"
                docs_dir.mkdir(exist_ok=True)
                
                doc_count = 0
                for doc_type, content in docs.items():
                    doc_file = docs_dir / f"{doc_type}.md"
                    file_manager.save_text(content, doc_file)
                    doc_count += 1
                
                click.echo(f"  ✅ {doc_count} documentation files generated")
                
            except Exception as e:
                logger.error(f"Documentation generation failed: {e}")
                click.echo(f"  ❌ Documentation generation failed: {e}")
                continue
            
            # STEP 6: Package Creation
            current_step = 6
            click.echo(f"\n[{current_step}/{total_steps}] 📦 Creating package...")
            
            from .modules.package_generator import PackageGenerator
            pkg_generator = PackageGenerator()
            
            try:
                # Create automation package
                package = pkg_generator.generate_package(
                    opportunity=opportunity,
                    workflow=assembled_workflow,
                    niche_brief=niche_brief,
                    validation_report=validation_report
                )
                
                # Save package metadata
                metadata_file = package_dir / "metadata.json"
                file_manager.save_json(package.model_dump(), metadata_file)
                
                # Save workflow
                workflow_dir = package_dir / "workflows"
                workflow_dir.mkdir(exist_ok=True)
                workflow_file = workflow_dir / f"{assembled_workflow.name}.json"
                file_manager.save_json(assembled_workflow.to_n8n_format(), workflow_file)
                
                # Generate test fixtures if requested
                if generate_tests:
                    test_dir = package_dir / "tests"
                    test_dir.mkdir(exist_ok=True)
                    
                    test_fixtures = {
                        "sample_input": {"test": "data"},
                        "expected_output": {"success": True}
                    }
                    fixtures_file = test_dir / "fixtures.json"
                    file_manager.save_json(test_fixtures, fixtures_file)
                    
                    click.echo("  🧪 Test fixtures generated")
                
                click.echo(f"  ✅ Package created: {package.slug}")
                click.echo(f"  📋 Package Name: {package.name}")
                click.echo(f"  💰 ROI Notes: {package.roi_notes}")
                
            except Exception as e:
                logger.error(f"Package creation failed: {e}")
                click.echo(f"  ❌ Package creation failed: {e}")
                continue
        
        # Summary
        elapsed_time = time.time() - start_time
        click.echo(f"\n{'='*60}")
        click.echo("🎉 Package generation completed!")
        click.echo(f"⏱️  Total time: {elapsed_time:.1f} seconds")
        click.echo(f"📦 Packages created: {len(opportunities)}")
        click.echo(f"📁 Output directory: {output_dir}")
        
    except Exception as e:
        logger.error(f"Package generation failed: {e}", exc_info=True)
        click.echo(f"❌ Error: {e}")
        sys.exit(1)


@cli.command()
@click.argument('package_path', type=click.Path(exists=True))
@click.pass_context
def validate(ctx, package_path: str):
    """Validate an existing automation package."""
    package_path_obj = Path(package_path)
    
    click.echo(f"🔍 Validating package: {package_path_obj}")
    
    try:
        validator = PackageValidator()
        results = validator.validate_package_directory(package_path_obj)
        
        for result in results:
            status = "✅" if result.passed else "❌"
            click.echo(f"  {status} {result.message}")
        
        passed = sum(1 for r in results if r.passed)
        total = len(results)
        click.echo(f"\n📊 Results: {passed}/{total} checks passed")
        
        if passed == total:
            click.echo("🎉 Package validation successful!")
        else:
            click.echo("⚠️  Package validation failed!")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"Validation failed: {e}")
        click.echo(f"❌ Error: {e}")
        sys.exit(1)


@cli.command()
@click.argument('niche_keyword')
@click.option('--timeout', default=30, help='Research timeout in seconds')
@click.pass_context
def research(ctx, niche_keyword: str, timeout: int):
    """Research a niche and display findings."""
    click.echo(f"🔍 Researching niche: {niche_keyword}")
    
    try:
        researcher = NicheResearcher(research_timeout=timeout)
        niche_brief = researcher.research_niche(niche_keyword)
        
        click.echo("\n📊 Research Results:")
        click.echo(f"  Niche: {niche_brief.niche_name}")
        click.echo(f"  Confidence: {niche_brief.research_confidence:.2%}")
        click.echo(f"  Market Size: {niche_brief.market_size}")
        click.echo(f"  Tech Adoption: {niche_brief.technology_adoption}")
        
        click.echo(f"\n🎯 Pain Points ({len(niche_brief.pain_points)}):")
        for i, pain in enumerate(niche_brief.pain_points[:5], 1):
            click.echo(f"  {i}. {pain['description']}")
            click.echo(f"     Impact: {pain['impact_score']:.2f}, Automation: {pain['automation_potential']:.2%}")
        
        click.echo(f"\n🚀 Opportunities ({len(niche_brief.opportunities)}):")
        for i, opp in enumerate(niche_brief.opportunities[:3], 1):
            click.echo(f"  {i}. {opp['title']}")
            click.echo(f"     Complexity: {opp['complexity']}, ROI: {opp['roi_estimate']}")
            
    except Exception as e:
        logger.error(f"Research failed: {e}")
        click.echo(f"❌ Error: {e}")
        sys.exit(1)


@cli.command()
@click.pass_context
def list_packages(ctx):
    """List all generated packages."""
    output_dir = ctx.obj['output_dir']
    
    if not output_dir.exists():
        click.echo("No packages directory found.")
        return
    
    packages = []
    for pkg_dir in output_dir.iterdir():
        if pkg_dir.is_dir():
            metadata_file = pkg_dir / "metadata.json"
            if metadata_file.exists():
                try:
                    import json
                    with open(metadata_file) as f:
                        metadata = json.load(f)
                    packages.append((pkg_dir.name, metadata))
                except Exception:
                    packages.append((pkg_dir.name, {}))
    
    if not packages:
        click.echo("No packages found.")
        return
    
    click.echo(f"📦 Found {len(packages)} packages:\n")
    
    for slug, metadata in packages:
        name = metadata.get('name', slug)
        problem = metadata.get('problem_statement', 'N/A')
        roi = metadata.get('roi_notes', 'N/A')
        validated = metadata.get('last_validated', 'Never')
        
        click.echo(f"  📋 {name} ({slug})")
        click.echo(f"     Problem: {problem[:80]}...")
        click.echo(f"     ROI: {roi[:60]}...")
        click.echo(f"     Last Validated: {validated}")
        click.echo()


@cli.command()
@click.option('--agent', type=click.Choice(['niche', 'opportunity', 'assembly', 'validation', 'docs', 'package']), 
              help='Start with specific agent')
@click.option('--session-id', help='Load specific session ID')
@click.option('--vault-path', default='automation_vault', help='Path to automation vault directory')
@click.pass_context
def chat(ctx, agent: str, session_id: str, vault_path: str):
    """Interactive chat interface with Pydantic agents."""
    from .chat.agents import AGENT_REGISTRY, AGENT_NAMES, ChatSession
    
    output_dir = ctx.obj['output_dir']
    sessions_dir = output_dir / "sessions"
    sessions_dir.mkdir(exist_ok=True)
    
    # Load or create session
    if session_id:
        session_file = sessions_dir / f"{session_id}.json"
        if session_file.exists():
            session = ChatSession.load_session(session_file)
            click.echo(f"📂 Loaded session: {session_id}")
        else:
            click.echo(f"❌ Session {session_id} not found. Creating new session.")
            session = ChatSession(session_id)
    else:
        session = ChatSession()
        
    # Welcome message
    click.echo("\n" + "="*60)
    click.echo("🤖 AUTOMATION PACKAGE GENERATOR - AGENT CHAT")
    click.echo("="*60)
    click.echo(f"Session ID: {session.session_id}")
    click.echo("\n💡 Available Agents:")
    for key, name in AGENT_NAMES.items():
        status = "🟢" if key == agent else "⚪"
        click.echo(f"  {status} {key}: {name}")
    
    click.echo("\n🔧 Global Commands:")
    click.echo("  • switch <agent> - Switch to different agent")
    click.echo("  • session - Show session information")  
    click.echo("  • save - Save current session")
    click.echo("  • quit - Exit chat")
    click.echo("="*60)
    
    # Initialize current agent
    current_agent_key = agent or 'niche'
    current_agent = None
    
    try:
        while True:
            # Create agent instance if needed
            if current_agent is None or session.current_agent != current_agent_key:
                session.current_agent = current_agent_key
                agent_class = AGENT_REGISTRY[current_agent_key]
                
                # Pass vault_path to assembly agent
                if current_agent_key == 'assembly':
                    current_agent = agent_class(session, vault_path)
                else:
                    current_agent = agent_class(session)
                
                # Show agent greeting
                click.echo(f"\n🤖 {AGENT_NAMES[current_agent_key]}")
                click.echo("-" * 60)
                click.echo(current_agent.get_greeting())
                click.echo("-" * 60)
            
            # Get user input
            try:
                user_input = input(f"\n[{current_agent_key}] ➤ ").strip()
            except (EOFError, KeyboardInterrupt):
                click.echo("\n\n👋 Goodbye!")
                break
                
            if not user_input:
                continue
                
            # Handle global commands
            if user_input.lower() == 'quit':
                click.echo("👋 Goodbye!")
                break
                
            elif user_input.lower() == 'save':
                session.save_session(sessions_dir)
                click.echo(f"💾 Session saved: {session.session_id}")
                continue
                
            elif user_input.lower() == 'session':
                click.echo(f"\n📊 **Session Information**")
                click.echo(f"Session ID: {session.session_id}")
                click.echo(f"Current Agent: {AGENT_NAMES.get(session.current_agent, 'None')}")
                click.echo(f"Messages: {len(session.history)}")
                click.echo(f"Context Keys: {list(session.context.keys())}")
                continue
                
            elif user_input.lower().startswith('switch'):
                parts = user_input.split()
                if len(parts) > 1:
                    new_agent = parts[1].lower()
                    if new_agent in AGENT_REGISTRY:
                        current_agent_key = new_agent
                        current_agent = None  # Will be recreated
                        click.echo(f"🔄 Switching to {AGENT_NAMES[new_agent]}...")
                        continue
                    else:
                        click.echo(f"❌ Unknown agent '{new_agent}'. Available: {', '.join(AGENT_REGISTRY.keys())}")
                        continue
                else:
                    click.echo("Please specify agent: switch <agent_name>")
                    continue
            
            # Process with current agent
            try:
                response = current_agent.process_input(user_input)
                current_agent.log_interaction(user_input, response)
                
                # Display response
                click.echo(f"\n{response['message']}")
                
            except Exception as e:
                logger.error(f"Agent processing error: {e}", exc_info=True)
                click.echo(f"❌ Error: {str(e)}")
                
    except KeyboardInterrupt:
        click.echo("\n\n👋 Goodbye!")
        
    finally:
        # Auto-save session
        try:
            session.save_session(sessions_dir)
            click.echo(f"💾 Session auto-saved: {session.session_id}")
        except Exception as e:
            logger.warning(f"Failed to auto-save session: {e}")


@cli.command()
@click.pass_context  
def version(ctx):
    """Show version information."""
    click.echo("Automation Package Generator v1.0.0")
    click.echo("Built with Claude Code SuperClaude Framework")
    click.echo("Following CLAUDE.md standards and quality gates")


if __name__ == '__main__':
    cli()