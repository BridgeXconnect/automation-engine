# DocumentationGenerator Module

The `DocumentationGenerator` class provides comprehensive documentation generation for automation packages using Jinja2 templates. It creates all required documentation types following PRP requirements and style guide patterns.

## Features

- **Template-based Generation**: Uses Jinja2 templates for consistent, customizable documentation
- **Complete Documentation Suite**: Generates all 6 required document types
- **Client/Internal Separation**: Automatically separates content for different audiences
- **Package Integration**: Seamlessly integrates with `AutomationPackage` models
- **Metrics Calculation**: Provides word count and read time estimates
- **Variable Substitution**: Supports complex template variables and custom filters

## Required Document Types

1. **Implementation Guide** - Technical step-by-step instructions
2. **Configuration Guide** - Environment setup and API configuration
3. **Runbook** - Operations monitoring and troubleshooting
4. **Standard Operating Procedures** - Team workflows and quality checks
5. **Loom Outline** - Video script for client presentations
6. **Client One-Pager** - Business-focused benefits summary

## Usage

```python
from src.modules.documentation import DocumentationGenerator
from src.models.package import AutomationPackage

# Create package
package = AutomationPackage(
    name="Lead Scoring Automation",
    slug="lead-scoring-automation",
    problem_statement="Manual lead scoring is time-intensive and inconsistent",
    roi_notes="Save 15 hours per week, improve conversion by 25%",
    # ... other fields
)

# Initialize generator
doc_gen = DocumentationGenerator()

# Generate complete suite
suite = doc_gen.generate_documentation_suite(
    package=package,
    template_variables={
        "prerequisites": ["CRM access", "API keys"],
        "integration_gotchas": ["Rate limits apply"]
    }
)

# Save to files
output_dir = Path(f"./packages/{package.slug}/docs")
saved_files = doc_gen.save_documentation_suite(suite, output_dir)
```

## Template Variables

The generator uses these standard variables from package data:

### Package Core Data
- `package_name` - Human readable name
- `package_slug` - URL-safe identifier
- `problem_statement` - Business problem being solved
- `roi_notes` - Return on investment details
- `version` - Package version number

### Technical Specifications
- `inputs` - Required input data and formats
- `outputs` - Expected output data and formats
- `dependencies` - Required integrations and APIs
- `security_notes` - Security considerations

### Additional Variables
You can provide additional context through `template_variables`:

- `prerequisites` - Required setup before implementation
- `installation_steps` - Step-by-step installation instructions
- `configuration_steps` - Configuration and setup steps
- `testing_steps` - Testing and validation procedures
- `integration_gotchas` - Common issues and solutions

## Custom Templates

Templates are stored in `src/templates/docs/` and use the `.j2` extension:

- `implementation.md.j2` - Implementation guide template
- `configuration.md.j2` - Configuration guide template
- `runbook.md.j2` - Runbook template
- `sop.md.j2` - Standard operating procedures template
- `loom-outline.md.j2` - Video outline template
- `client-one-pager.md.j2` - Client summary template

### Template Structure

```jinja2
# {{ package_name }} - Implementation Guide

## Purpose
{{ problem_statement }}

## Prerequisites
{% for prereq in prerequisites -%}
- {{ prereq }}
{% endfor %}

## Dependencies
{{ dependencies | format_list }}

## Generated Metadata
- **Version**: {{ version }}
- **Generated**: {{ generated_at | format_datetime }}
```

## Custom Filters

The generator includes these Jinja2 filters:

- `format_datetime` - Format datetime objects for documentation
- `word_count` - Count words in text
- `format_list` - Format Python lists as markdown bullets
- `format_dict_table` - Format dictionaries as markdown tables
- `client_safe` - Remove technical details from client-facing content

## Content Separation

The system automatically separates content by audience:

### Client-Facing Documents
- **Audience**: Business stakeholders, decision makers
- **Focus**: Problems, solutions, benefits, ROI
- **Language**: Business-friendly, minimal jargon
- **Documents**: Loom outline, client one-pager

### Internal Documents
- **Audience**: Technical team, implementers
- **Focus**: Implementation details, configuration, operations
- **Language**: Technical precision, detailed instructions
- **Documents**: Implementation guide, configuration guide, runbook, SOPs

## Metrics and Validation

Each document includes:
- **Word count** - Total words in content
- **Read time** - Estimated reading time (225 words/minute)
- **Audience classification** - Client vs internal
- **Document type** - Structured enumeration

Suite-level metrics:
- Total document count
- Combined word count
- Total estimated read time
- Client vs internal document breakdown

## PRP Integration

The DocumentationGenerator integrates with PRP workflows:

1. **Package Input**: Receives `AutomationPackage` from PRP process
2. **Template Variables**: Accepts PRP context and additional details
3. **Documentation Suite**: Generates complete documentation set
4. **File Output**: Saves to standard package directory structure
5. **Notion Sync**: Prepares data for Notion database integration

## File Structure

Generated documentation follows this structure:
```
packages/{package-slug}/
  docs/
    implementation.md
    configuration.md
    runbook.md
    sop.md
    loom-outline.md
    client-one-pager.md
```

## Error Handling

The generator includes comprehensive error handling:

- **Template Errors**: Catches Jinja2 template errors with context
- **File I/O Errors**: Handles file system operations gracefully
- **Validation Errors**: Validates package data and template variables
- **Custom Exceptions**: Uses `DocumentationGeneratorError` for specific issues

## Performance

- **Template Caching**: Jinja2 templates are compiled and cached
- **Batch Generation**: All documents generated in single operation
- **Memory Efficient**: Minimal memory footprint for large packages
- **Fast Rendering**: Sub-second generation for typical packages

## Quality Standards

The generator enforces these quality standards:

- **Consistency**: All documents follow same formatting patterns
- **Completeness**: All required sections included in each document type
- **Accuracy**: Package data correctly integrated into templates
- **Readability**: Content optimized for target audience
- **Maintainability**: Template-based approach allows easy updates

## Extension Points

The system is designed for extensibility:

- **Custom Templates**: Add new templates for additional document types
- **Custom Filters**: Extend Jinja2 with domain-specific filters
- **Document Types**: Add new document types to the enumeration
- **Audience Types**: Support additional audience classifications
- **Variable Sources**: Integrate additional data sources for template variables