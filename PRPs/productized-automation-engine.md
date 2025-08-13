name: "Productized Automation Agency - Internal Delivery Engine PRP"
description: |
  Comprehensive PRP for building an internal engine that transforms raw n8n workflows 
  into market-ready automation packages with documentation, testing, and Notion integration.

---

## Goal
Build a Python-based internal delivery engine that automates the transformation of raw automation components (n8n workflows, research data, templates) into complete, sellable automation packages. The engine should produce standardized packages with documentation, testing, metadata, and Notion database integration within ≤1 hour of operator time.

## Why
- **Business Value**: Accelerate productization of custom automation workflows by 90%+ (from days to hours)
- **Scalability**: Create reusable, vertical-agnostic packages deployable across multiple client niches
- **Quality Assurance**: Standardize documentation, testing, and deployment processes
- **Market Readiness**: Generate client-facing materials and technical documentation automatically
- **Operations Excellence**: Integrate with Notion Business OS for package lifecycle management

## What
A modular Python engine with 6 core capabilities that processes niche research, assembles workflows, validates functionality, generates comprehensive documentation, and packages everything for deployment. Each package includes n8n workflows, documentation suite, test fixtures, environment templates, and Notion database records.

### Success Criteria
- [ ] Generate ≥1 complete, validated package from niche input in ≤1 hour operator time
- [ ] All documentation auto-generated and deployment-ready without manual editing
- [ ] 80% code reusability across different vertical niches with ≤20% customization needed
- [ ] All packages pass "new engineer can deploy in one sitting" test
- [ ] Notion databases automatically populated with package metadata and relationships
- [ ] Comprehensive test coverage with automated validation gates

## All Needed Context

### Documentation & References
```yaml
# MUST READ - Include these in your context window
- url: https://docs.n8n.io/workflows/export-import/
  why: n8n workflow JSON structure, export/import patterns, validation requirements
  
- url: https://docs.n8n.io/data/data-structure/  
  why: Node data flow, transformation patterns, connection specifications
  
- url: https://github.com/ramnes/notion-sdk-py
  why: Database operations, relations, rollups, CRUD patterns for Notion integration
  section: Database creation, property management, query operations, pagination
  critical: Authentication with NOTION_TOKEN, error handling, relation management
  
- file: examples/agent/plan_and_validate.md
  why: Stepwise planning methodology and validation gate patterns
  
- file: examples/n8n/patterns.md  
  why: Naming conventions, retry patterns, idempotency, logging, observability
  
- file: examples/config/env_template.md
  why: Environment variable structure and secrets management patterns
  
- file: examples/docs/style_guide.md
  why: Documentation formatting, client vs internal content, ROI presentation
  
- file: examples/tests/fixtures.md
  why: Test data structure, validation assertions, fixture patterns
  
- docfile: CLAUDE.md
  why: Project rules, metadata standards, Notion schema requirements, quality gates

- url: https://docs.python.org/3/library/json.html
  why: JSON manipulation for n8n workflow processing and validation
  
- url: https://docs.python-requests.org/en/latest/
  why: HTTP requests for niche research and external API integration
```

### Current Codebase Structure
```bash
/Users/roymkhabela/automation-engine/
├── CLAUDE.md                    # Project rules and standards
├── INITIAL.md                   # Feature specification
├── PRPs/
│   ├── templates/
│   │   └── prp_base.md         # PRP template structure
├── examples/                    # Pattern files (created)
│   ├── agent/
│   │   └── plan_and_validate.md
│   ├── config/
│   │   └── env_template.md
│   ├── docs/
│   │   └── style_guide.md
│   ├── n8n/
│   │   └── patterns.md
│   └── tests/
│       └── fixtures.md
└── use-cases/                   # Reference implementations
    ├── mcp-server/             # TypeScript MCP patterns
    └── pydantic-ai/            # Python agent patterns
```

### Desired Codebase Structure
```bash
# New files to be created:
src/
├── __init__.py                 # Package initialization
├── main.py                     # CLI entry point and orchestration
├── models/
│   ├── __init__.py
│   ├── package.py              # Package data models
│   ├── workflow.py             # n8n workflow models  
│   ├── documentation.py        # Documentation models
│   └── notion.py               # Notion database models
├── modules/
│   ├── __init__.py
│   ├── niche_research.py       # Module 1: Niche research
│   ├── opportunity_mapping.py  # Module 2: Opportunity mapping
│   ├── assembly.py             # Module 3: Workflow assembly
│   ├── validation.py           # Module 4: Validation
│   ├── documentation.py        # Module 5: Documentation & packaging
│   └── deployment.py           # Module 6: Deployment
├── integrations/
│   ├── __init__.py
│   ├── notion_client.py        # Notion API client
│   ├── n8n_processor.py        # n8n workflow processor
│   └── research_client.py      # Web research client
├── templates/                  # Document generation templates
│   ├── implementation.md.j2
│   ├── configuration.md.j2
│   ├── runbook.md.j2
│   ├── sop.md.j2
│   ├── loom-outline.md.j2
│   └── client-one-pager.md.j2
└── utils/
    ├── __init__.py
    ├── file_manager.py         # File operations
    ├── validators.py           # Validation utilities
    └── helpers.py              # Common utilities

tests/
├── __init__.py
├── conftest.py                 # Test configuration
├── fixtures/                   # Test data
│   ├── workflows/              # Sample n8n workflows
│   ├── packages/               # Sample package structures
│   └── notion/                 # Sample Notion responses
├── test_models.py              # Model validation tests
├── test_modules.py             # Module functionality tests
├── test_integrations.py        # API integration tests
└── test_end_to_end.py         # Full pipeline tests

packages/                       # Generated packages output
automation_vault/               # Source workflow repository
requirements.txt                # Python dependencies
pytest.ini                     # Test configuration
.env.example                   # Environment template
```

### Known Gotchas & Library Quirks
```python
# CRITICAL: Notion SDK requires authentication via environment variable
# NOTION_TOKEN must be set before initializing client
import os
from notion_client import Client
notion = Client(auth=os.environ["NOTION_TOKEN"])

# CRITICAL: n8n workflow JSON structure validation
# Workflows must have: name, nodes (array), connections (object)
# Each node requires: id, name, type, position, parameters
workflow_schema = {
    "name": str,
    "nodes": [{"id": str, "name": str, "type": str, "position": [x, y]}],
    "connections": {}
}

# CRITICAL: Pydantic v2 syntax for models (not v1)
from pydantic import BaseModel, Field, validator
class PackageModel(BaseModel):
    name: str = Field(..., description="Package name")
    # Use model_validate() not parse_obj() in v2

# CRITICAL: File path handling for cross-platform compatibility  
from pathlib import Path
package_path = Path("packages") / package_slug / "workflows"
package_path.mkdir(parents=True, exist_ok=True)

# CRITICAL: JSON serialization for n8n workflows
# Use indent=2 and ensure_ascii=False for human-readable output
import json
with open("workflow.json", "w") as f:
    json.dump(workflow_data, f, indent=2, ensure_ascii=False)
```

## Implementation Blueprint

### Data Models and Structure

Create type-safe data models using Pydantic v2 for all package components:

```python
# Core models for package management
class AutomationPackage(BaseModel):
    name: str
    slug: str  
    niche_tags: List[str]
    problem_statement: str
    outcomes: List[str]
    roi_notes: str
    inputs: Dict[str, Any]
    outputs: Dict[str, Any]  
    dependencies: List[str]
    security_notes: str
    version: str
    last_validated: datetime

class N8nWorkflow(BaseModel):
    name: str
    nodes: List[Dict[str, Any]]
    connections: Dict[str, Any] 
    settings: Dict[str, Any]
    
class NotionDatabase(BaseModel):
    database_id: str
    properties: Dict[str, Any]
    relations: Dict[str, str]
```

### Implementation Tasks (Sequential Order)

```yaml
Task 1: Project Setup and Dependencies
CREATE requirements.txt:
  - INCLUDE: notion-client>=2.2.1, pydantic>=2.0.0, jinja2>=3.1.0, requests>=2.31.0, pytest>=7.0.0
  - INCLUDE: python-dotenv>=1.0.0, click>=8.1.0, pathlib>=1.0.0

CREATE .env.example:  
  - MIRROR pattern from: examples/config/env_template.md
  - ADD Notion and research API keys
  - INCLUDE data residency options

Task 2: Core Data Models
CREATE src/models/package.py:
  - IMPLEMENT AutomationPackage model with validation
  - INCLUDE metadata schema from CLAUDE.md requirements
  - ADD version management and timestamps

CREATE src/models/workflow.py:
  - IMPLEMENT N8nWorkflow model for JSON validation
  - MIRROR patterns from: examples/n8n/patterns.md
  - INCLUDE node validation and connection checks

CREATE src/models/notion.py:
  - IMPLEMENT NotionDatabase models for all required databases
  - REFERENCE schema from: CLAUDE.md Notion Business OS section
  - INCLUDE relation and rollup field definitions

Task 3: Notion Integration Client
CREATE src/integrations/notion_client.py:
  - IMPLEMENT NotionClient wrapper class
  - MIRROR patterns from: ramnes/notion-sdk-py documentation
  - INCLUDE error handling and retry logic
  - ADD database creation, query, and update methods

Task 4: n8n Workflow Processor  
CREATE src/integrations/n8n_processor.py:
  - IMPLEMENT WorkflowProcessor for JSON manipulation
  - ENFORCE naming conventions from examples/n8n/patterns.md
  - ADD validation, retry injection, idempotency key generation
  - INCLUDE logging and observability instrumentation

Task 5: Niche Research Module
CREATE src/modules/niche_research.py:
  - IMPLEMENT NicheResearcher class with web scraping
  - GENERATE structured "Niche Brief" with pains/opportunities  
  - INCLUDE data collection from multiple sources
  - OUTPUT standardized research format

Task 6: Opportunity Mapping Module
CREATE src/modules/opportunity_mapping.py:
  - IMPLEMENT OpportunityMapper for pain→automation translation
  - CALCULATE ROI estimates (time saved, cost impact, revenue lift)
  - ASSESS dependencies and risk factors
  - OUTPUT ranked automation candidates

Task 7: Assembly Module  
CREATE src/modules/assembly.py:
  - IMPLEMENT WorkflowAssembler for n8n workflow combination
  - PULL workflows from automation_vault/ directory
  - ADAPT naming, inject retries, add idempotency keys
  - VALIDATE workflow compatibility and connections

Task 8: Validation Module
CREATE src/modules/validation.py:
  - IMPLEMENT WorkflowValidator with multi-level checks
  - VALIDATE JSON schema, simulate test runs with fixtures
  - CHECK environment variables, rate limits, secrets
  - GENERATE validation reports and checklists

Task 9: Documentation Generation
CREATE src/modules/documentation.py:
  - IMPLEMENT DocumentationGenerator with Jinja2 templates
  - GENERATE all required docs from examples/docs/style_guide.md
  - CREATE implementation, config, runbook, SOP, and client materials
  - ENSURE client vs internal content separation

Task 10: Template System
CREATE src/templates/*.j2:
  - MIRROR structure from: examples/docs/style_guide.md  
  - IMPLEMENT Jinja2 templates for all document types
  - INCLUDE variable substitution and conditional content
  - ENSURE consistent formatting and style

Task 11: CLI Orchestration  
CREATE src/main.py:
  - IMPLEMENT Click-based CLI with command structure
  - ORCHESTRATE all 6 modules in sequence
  - INCLUDE progress tracking and error handling
  - ADD package generation and validation commands

Task 12: File Management System
CREATE src/utils/file_manager.py:
  - IMPLEMENT PackageFileManager for directory creation  
  - ENFORCE structure from CLAUDE.md requirements
  - HANDLE cross-platform path operations
  - INCLUDE cleanup and backup functionality
```

### Integration Points
```yaml
NOTION_DATABASES:
  - create: Library, Automations, Components, Clients, Deployments
  - properties: All fields from CLAUDE.md Notion Business OS schema
  - relations: Link Automations→Library, Deployments→Automations
  
WORKFLOW_VALIDATION:
  - schema: Validate against n8n workflow JSON requirements  
  - runtime: Simulate execution with test fixtures
  - security: Check for hardcoded secrets, validate env var usage
  
FILE_GENERATION:
  - structure: /packages/<slug>/ with workflows/, docs/, tests/, metadata.json
  - templates: Jinja2-based generation with variable substitution
  - validation: Check all required files present and formatted correctly
```

## Validation Loop

### Level 1: Syntax & Style  
```bash
# Run these FIRST - fix any errors before proceeding
ruff check src/ --fix           # Auto-fix formatting issues
mypy src/                       # Type checking with Pydantic models
python -m pytest tests/test_models.py -v  # Model validation tests

# Expected: No errors. If errors, READ the error and fix code.
```

### Level 2: Module Unit Tests
```python
# CREATE comprehensive test suite for each module
def test_niche_research_integration():
    """Niche research produces valid structured output"""
    researcher = NicheResearcher()
    brief = researcher.research_niche("logistics 3PL")
    assert isinstance(brief, NicheBrief)
    assert len(brief.pain_points) >= 3
    assert all(pain.impact_score > 0 for pain in brief.pain_points)

def test_workflow_assembly_validation():
    """Assembled workflows pass validation"""
    assembler = WorkflowAssembler()
    workflows = assembler.assemble_workflows(
        ["hubspot_lead_capture", "salesforce_insert"]
    )
    for workflow in workflows:
        assert validator.validate_workflow(workflow)
        assert all(node.get("retries") == 3 for node in workflow.nodes)

def test_notion_integration():
    """Notion databases created and populated correctly"""  
    client = NotionClient()
    package = AutomationPackage(name="Test Package", ...)
    record_id = client.create_library_record(package)
    assert record_id is not None
    retrieved = client.get_library_record(record_id)
    assert retrieved.name == package.name
```

```bash
# Run and iterate until passing:
python -m pytest tests/ -v --tb=short
# If failing: Read error, understand root cause, fix code, re-run
```

### Level 3: Integration Tests
```bash
# Full pipeline test with real data
python -m pytest tests/test_end_to_end.py -v

# Test package generation  
python src/main.py generate --niche "logistics 3PL" --validate

# Expected output structure:
# packages/logistics_3pl_lead_automation/
#   workflows/hubspot_lead_capture.json  
#   docs/implementation.md
#   tests/fixtures.json
#   metadata.json
```

### Level 4: Quality Gates Validation
```bash
# Validate generated package meets all requirements
python src/main.py validate --package logistics_3pl_lead_automation

# Check Notion integration
python -c "
from src.integrations.notion_client import NotionClient
client = NotionClient()
assert client.verify_database_schema()
print('✅ Notion integration validated')
"

# Test fixture validation
cd packages/logistics_3pl_lead_automation
python -m pytest tests/ -v
```

## Final Validation Checklist
- [ ] All unit tests pass: `python -m pytest tests/ -v`
- [ ] No linting errors: `ruff check src/`  
- [ ] No type errors: `mypy src/`
- [ ] Package generation successful: `python src/main.py generate --niche "test"`
- [ ] Notion databases created and populated
- [ ] Generated documentation follows style guide  
- [ ] Test fixtures execute successfully
- [ ] Environment template complete and secure
- [ ] All quality gates from CLAUDE.md satisfied

---

## Anti-Patterns to Avoid
- ❌ Don't hardcode API keys or secrets in source code
- ❌ Don't skip validation steps to save time - they prevent production issues  
- ❌ Don't generate workflows without retry/idempotency patterns
- ❌ Don't create client-facing docs with internal technical details
- ❌ Don't bypass Pydantic model validation for performance
- ❌ Don't ignore cross-platform file path compatibility
- ❌ Don't commit generated packages to source control
- ❌ Don't mix synchronous and asynchronous code patterns inconsistently

**PRP Confidence Score: 9/10**

This PRP provides comprehensive context including:
- ✅ Complete external API documentation (Notion SDK, n8n workflows)  
- ✅ Detailed implementation blueprint with sequential tasks
- ✅ All necessary patterns and examples from codebase
- ✅ Executable validation gates for quality assurance
- ✅ Clear error handling and debugging strategies
- ✅ Anti-patterns and common gotchas explicitly documented
- ✅ Full integration testing approach
- ✅ Business requirements alignment with technical implementation

**Potential Risk**: Complex integration requirements may need iterative refinement, but comprehensive validation gates should catch issues early.