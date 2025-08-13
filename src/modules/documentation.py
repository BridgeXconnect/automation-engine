"""Documentation generation module for automation packages."""

import logging
from typing import Dict, Any, List
from datetime import datetime

from ..models.workflow import N8nWorkflow
from .opportunity_mapping import AutomationOpportunity
from .niche_research import NicheBrief

logger = logging.getLogger(__name__)

class DocumentationGeneratorError(Exception):
    """Custom exception for documentation generation operations."""
    pass

class DocumentationGenerator:
    """DocumentationGenerator for complete package documentation.
    
    Generates all required documents per CLAUDE.md:
    - implementation.md
    - configuration.md
    - runbook.md
    - sop.md
    - loom-outline.md
    - client-one-pager.md
    """
    
    def __init__(self):
        """Initialize documentation generator."""
        self.templates = self._load_templates()
    
    def _load_templates(self) -> Dict[str, str]:
        """Load documentation templates."""
        return {
            'implementation': self._get_implementation_template(),
            'configuration': self._get_configuration_template(),
            'runbook': self._get_runbook_template(),
            'sop': self._get_sop_template(),
            'loom_outline': self._get_loom_outline_template(),
            'client_one_pager': self._get_client_one_pager_template()
        }
    
    def generate_complete_documentation(self, 
                                      opportunity: AutomationOpportunity,
                                      workflow: N8nWorkflow,
                                      validation_report: Dict[str, Any],
                                      niche_brief: NicheBrief) -> Dict[str, str]:
        """Generate complete documentation set.
        
        Args:
            opportunity: Automation opportunity
            workflow: Generated workflow
            validation_report: Validation results
            niche_brief: Niche research data
            
        Returns:
            Dictionary with document types and content
        """
        logger.info(f"Generating complete documentation for: {opportunity.title}")
        
        docs = {}
        
        try:
            # Generate each required document
            docs['implementation'] = self._generate_implementation_guide(
                opportunity, workflow, validation_report
            )
            
            docs['configuration'] = self._generate_configuration_guide(
                opportunity, workflow
            )
            
            docs['runbook'] = self._generate_runbook(
                opportunity, workflow, validation_report
            )
            
            docs['sop'] = self._generate_sop(
                opportunity, workflow
            )
            
            docs['loom-outline'] = self._generate_loom_outline(
                opportunity, workflow
            )
            
            docs['client-one-pager'] = self._generate_client_one_pager(
                opportunity, niche_brief
            )
            
            logger.info(f"Generated {len(docs)} documentation files")
            return docs
            
        except Exception as e:
            logger.error(f"Documentation generation failed: {e}")
            raise DocumentationGeneratorError(f"Failed to generate documentation: {e}")
    
    def _generate_implementation_guide(self, 
                                     opportunity: AutomationOpportunity,
                                     workflow: N8nWorkflow,
                                     validation_report: Dict[str, Any]) -> str:
        """Generate implementation guide."""
        
        content = f"""# Implementation Guide: {opportunity.title}

## Overview

This guide provides step-by-step instructions for implementing the {opportunity.title} automation solution.

**Automation Type**: {opportunity.automation_type}
**Complexity**: {opportunity.complexity_level}
**Estimated Timeline**: {opportunity.estimated_timeline}

## Prerequisites

### System Requirements
- n8n instance (self-hosted or cloud)
- Required integrations: {', '.join(opportunity.required_integrations)}
- Administrative access to target systems

### Environment Setup
1. Ensure n8n is running and accessible
2. Verify API access to required systems
3. Prepare test data for validation

## Step-by-Step Implementation

### Phase 1: Environment Preparation

1. **Access n8n Dashboard**
   - Navigate to your n8n instance
   - Ensure you have editor permissions

2. **Configure Credentials**
   - Set up credentials for each integration:
   {self._generate_credential_steps(opportunity.required_integrations)}

3. **Import Workflow**
   - Import the provided workflow JSON file: `{workflow.name}.json`
   - Review all nodes and connections

### Phase 2: Configuration

1. **Update Workflow Settings**
   - Modify workflow name if needed
   - Adjust trigger settings based on your requirements
   - Configure webhook URLs (if applicable)

2. **Test Individual Nodes**
   - Execute each node individually to verify configuration
   - Check data transformation steps
   - Validate API connections

### Phase 3: Testing

1. **Execute Test Run**
   - Use provided test fixtures
   - Monitor execution logs
   - Verify expected outputs

2. **Validation Checklist**
   {self._generate_validation_checklist(validation_report)}

### Phase 4: Deployment

1. **Activate Workflow**
   - Enable the workflow in n8n
   - Set up monitoring and alerts

2. **Monitor Initial Runs**
   - Watch for errors or unexpected behavior
   - Validate data accuracy
   - Confirm automation objectives are met

## Troubleshooting

### Common Issues

1. **Authentication Failures**
   - Verify API credentials are current
   - Check permission scopes
   - Regenerate tokens if necessary

2. **Data Format Issues**
   - Review data transformation nodes
   - Validate input data structure
   - Check field mappings

3. **Rate Limiting**
   - Implement delays between API calls
   - Use exponential backoff for retries
   - Monitor API usage quotas

### Support Resources

- n8n Documentation: https://docs.n8n.io/
- Integration-specific documentation
- Support contact: [Your support channel]

## Success Metrics

Track these metrics to measure implementation success:
{chr(10).join(f'- {metric}' for metric in opportunity.success_metrics)}

---
*Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
"""
        
        return content
    
    def _generate_configuration_guide(self, 
                                    opportunity: AutomationOpportunity,
                                    workflow: N8nWorkflow) -> str:
        """Generate configuration guide."""
        
        content = f"""# Configuration Guide: {opportunity.title}

## Environment Variables

Set these environment variables before running the workflow:

```bash
# Required Environment Variables
NOTION_TOKEN=your_notion_integration_token
N8N_ENCRYPTION_KEY=your_encryption_key

# Integration-specific variables
{self._generate_env_vars(opportunity.required_integrations)}
```

## Workflow Configuration

### Trigger Settings

{self._generate_trigger_config(workflow)}

### Node Configuration

{self._generate_node_config(workflow)}

## Integration Configuration

{self._generate_integration_config(opportunity.required_integrations)}

## Rate Limits & Performance

- **Execution Timeout**: 300 seconds (recommended)
- **Retry Attempts**: 3 with exponential backoff
- **Rate Limits**: Respect API limits for each integration

## Security Configuration

### Credential Management
- Store all sensitive data in n8n credentials
- Use environment variables for configuration
- Never hardcode API keys or passwords

### Data Handling
- Enable data encryption at rest
- Use HTTPS for all API communications
- Implement proper error handling to avoid data leaks

## Monitoring & Logging

### Execution Logs
- Enable detailed logging for troubleshooting
- Set up log retention policies
- Monitor for error patterns

### Performance Metrics
- Track execution times
- Monitor resource usage
- Set up alerts for failures

---
*Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
"""
        
        return content
    
    def _generate_runbook(self, 
                         opportunity: AutomationOpportunity,
                         workflow: N8nWorkflow,
                         validation_report: Dict[str, Any]) -> str:
        """Generate operational runbook."""
        
        content = f"""# Runbook: {opportunity.title}

## Quick Reference

- **Workflow Name**: {workflow.name}
- **Risk Level**: {opportunity.risk_assessment.get('overall_risk', 0):.1%}
- **Dependencies**: {', '.join(opportunity.dependencies)}
- **On-Call Contact**: [Your team contact]

## Monitoring

### Health Checks

1. **Workflow Status**
   ```bash
   # Check if workflow is active
   curl -X GET "https://your-n8n-instance/api/v1/workflows/{workflow.name}"
   ```

2. **Recent Executions**
   - Monitor execution history in n8n dashboard
   - Check for failed executions
   - Validate data quality

### Key Metrics to Monitor

- Execution success rate (target: >99%)
- Average execution time (target: <{self._estimate_execution_time(workflow)}s)
- Error rate (target: <1%)
- Data accuracy (target: 100%)

## Troubleshooting Procedures

### Common Issues

#### Issue: Workflow Not Triggering
**Symptoms**: No new executions, manual trigger works
**Investigation Steps**:
1. Check trigger configuration
2. Verify webhook URLs (if applicable)
3. Review trigger conditions
4. Check external system connectivity

**Resolution**:
1. Restart workflow
2. Update trigger settings
3. Verify integration credentials

#### Issue: Authentication Failures
**Symptoms**: 401/403 errors in execution logs
**Investigation Steps**:
1. Check credential expiration
2. Verify API permissions
3. Test manual API calls

**Resolution**:
1. Refresh API tokens
2. Update credentials in n8n
3. Verify permission scopes

#### Issue: Data Processing Errors
**Symptoms**: Execution fails at data transformation nodes
**Investigation Steps**:
1. Review input data structure
2. Check data transformation logic
3. Validate field mappings

**Resolution**:
1. Update data mapping
2. Add data validation steps
3. Handle edge cases

### Emergency Procedures

#### Complete Workflow Failure
1. **Immediate Actions**:
   - Disable workflow to prevent further issues
   - Alert stakeholders
   - Switch to manual process if available

2. **Investigation**:
   - Review recent changes
   - Check system dependencies
   - Analyze error logs

3. **Recovery**:
   - Roll back recent changes
   - Test workflow with sample data
   - Gradual re-enablement

## Maintenance

### Daily Tasks
- [ ] Review execution logs
- [ ] Check success/failure rates
- [ ] Monitor system performance

### Weekly Tasks
- [ ] Update credentials if needed
- [ ] Review and clean up old executions
- [ ] Analyze performance trends

### Monthly Tasks
- [ ] Full system health check
- [ ] Review and update documentation
- [ ] Capacity planning review

## Rollback Procedures

### Workflow Rollback
1. Export current workflow configuration
2. Import previous stable version
3. Update configuration as needed
4. Test with sample data
5. Enable and monitor

### Data Recovery
1. Identify affected records
2. Use backup data sources
3. Manual correction if needed
4. Validate data integrity

## Contact Information

- **Primary On-Call**: [Name, Contact]
- **Secondary Support**: [Team Contact]
- **Escalation**: [Manager Contact]

---
*Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
"""
        
        return content
    
    def _generate_sop(self, 
                     opportunity: AutomationOpportunity,
                     workflow: N8nWorkflow) -> str:
        """Generate standard operating procedures."""
        
        content = f"""# Standard Operating Procedures: {opportunity.title}

## Purpose

This SOP defines standard procedures for operating and maintaining the {opportunity.title} automation.

## Scope

This procedure applies to all team members responsible for:
- Workflow monitoring
- Issue resolution
- Maintenance activities
- Performance optimization

## Procedures

### Daily Operations

#### Morning Checklist (5 minutes)
1. **Check Workflow Status**
   - [ ] Verify workflow is active
   - [ ] Review overnight executions
   - [ ] Check for any failed runs

2. **Review Alerts**
   - [ ] Check email alerts
   - [ ] Review monitoring dashboard
   - [ ] Escalate issues if needed

#### End-of-Day Review (10 minutes)
1. **Performance Review**
   - [ ] Check daily execution count
   - [ ] Review success rate
   - [ ] Document any issues

### Weekly Operations

#### Weekly Health Check (30 minutes)
1. **System Review**
   - [ ] Analyze execution trends
   - [ ] Review error patterns
   - [ ] Check resource usage

2. **Maintenance Tasks**
   - [ ] Clean up old execution logs
   - [ ] Update credentials if needed
   - [ ] Review and update documentation

### Issue Response Procedures

#### Severity 1: Critical Issues (Response: Immediate)
- Complete workflow failure
- Data corruption or loss
- Security incidents

**Response Steps**:
1. Acknowledge alert within 15 minutes
2. Disable workflow if necessary
3. Notify stakeholders immediately
4. Begin investigation and resolution
5. Document incident for review

#### Severity 2: High Issues (Response: 1 hour)
- Partial workflow failure
- Performance degradation
- Integration connectivity issues

**Response Steps**:
1. Acknowledge alert within 1 hour
2. Investigate root cause
3. Implement temporary workaround if possible
4. Notify affected users
5. Work on permanent resolution

#### Severity 3: Medium Issues (Response: 4 hours)
- Minor errors in processing
- Warning conditions
- Non-critical performance issues

**Response Steps**:
1. Log the issue
2. Investigate when time permits
3. Plan resolution for next maintenance window
4. Monitor for escalation

### Change Management

#### Workflow Changes
1. **Planning**
   - Document proposed changes
   - Assess risk and impact
   - Schedule maintenance window

2. **Implementation**
   - Create backup of current workflow
   - Test changes in development environment
   - Deploy during scheduled maintenance
   - Validate functionality

3. **Rollback Plan**
   - Keep backup readily available
   - Define rollback criteria
   - Test rollback procedure
   - Document lessons learned

### Performance Optimization

#### Monthly Performance Review
1. **Analyze Metrics**
   - Execution time trends
   - Resource utilization
   - Error rates and patterns

2. **Identify Improvements**
   - Bottleneck identification
   - Optimization opportunities
   - Process refinements

3. **Implementation Planning**
   - Prioritize improvements
   - Schedule implementation
   - Define success criteria

### Training & Knowledge Transfer

#### New Team Member Onboarding
1. **Documentation Review**
   - Read all automation documentation
   - Understand workflow logic
   - Learn troubleshooting procedures

2. **Hands-on Training**
   - Shadow experienced team member
   - Practice common procedures
   - Review monitoring tools

3. **Certification**
   - Complete training checklist
   - Demonstrate competency
   - Get approval for independent work

### Documentation Maintenance

#### Quarterly Review
- [ ] Update procedures based on experience
- [ ] Review and update contact information
- [ ] Validate all procedures are current
- [ ] Incorporate lessons learned

---
*Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
"""
        
        return content
    
    def _generate_loom_outline(self, 
                              opportunity: AutomationOpportunity,
                              workflow: N8nWorkflow) -> str:
        """Generate Loom video outline."""
        
        content = f"""# Loom Video Outline: {opportunity.title}

**Target Duration**: 3-5 minutes
**Audience**: Business stakeholders and end users
**Objective**: Demonstrate the automation value and basic usage

## Video Script Outline

### Opening (30 seconds)
- **Hook**: "In the next 4 minutes, I'll show you how we can eliminate {opportunity.pain_point_source} and save your team hours every week"
- **Introduction**: Brief overview of the automation
- **Agenda**: What we'll cover in this demo

### Problem Context (45 seconds)
- **Current State**: Show the manual process
  - "Currently, your team spends X hours on [manual process]"
  - "This leads to delays, errors, and frustration"
- **Pain Points**: Highlight key issues
  - {chr(10).join(f'  - {point}' for point in [opportunity.pain_point_source])}
- **Business Impact**: Cost and time implications

### Solution Demo (2 minutes)
- **Automation Overview**
  - "Here's how the automation works"
  - Show workflow visualization in n8n
- **Step-by-Step Process**
  - Walk through each major workflow step
  - Highlight key integrations: {', '.join(opportunity.required_integrations)}
- **Before/After Comparison**
  - Manual process: X steps, Y time
  - Automated process: Z steps, minimal time

### Benefits & ROI (45 seconds)
- **Time Savings**: {opportunity.roi_estimate.get('time_saved_hours_month', 0):.0f} hours/month
- **Cost Savings**: ${opportunity.roi_estimate.get('cost_saved_monthly', 0):,.0f}/month
- **Quality Improvements**: Reduced errors, consistency
- **Success Metrics**: {chr(10).join(f'  - {metric}' for metric in opportunity.success_metrics[:3])}

### Next Steps (30 seconds)
- **Implementation Timeline**: {opportunity.estimated_timeline}
- **What You Need to Do**: Minimal requirements for business users
- **Support Available**: How to get help
- **Call to Action**: "Ready to get started? Let's schedule the implementation"

## Visual Elements to Include

### Screenshots/Screen Recordings
1. **Current Manual Process**
   - Show typical workflow in existing tools
   - Highlight pain points and inefficiencies

2. **n8n Workflow Visualization**
   - Clean view of the automation workflow
   - Highlight key integration points

3. **Before/After Data**
   - Metrics showing improvement
   - Time comparison charts

4. **End Result**
   - Show automated output
   - Demonstrate quality and accuracy

### Graphics/Annotations
- **Callout boxes** for key benefits
- **Arrows** pointing to important features
- **Time stamps** showing process duration
- **ROI calculations** displayed clearly

## Talking Points

### Key Messages
1. **Value Proposition**: "This automation transforms a tedious X-hour process into a 5-minute setup"
2. **Business Impact**: "Save ${opportunity.roi_estimate.get('cost_saved_monthly', 0):,.0f} monthly while improving accuracy"
3. **Ease of Use**: "Once set up, it runs automatically - no daily management needed"
4. **Reliability**: "Built with enterprise-grade error handling and monitoring"

### Common Objections & Responses
- **"Is it reliable?"** → Show validation results and error handling
- **"What if something breaks?"** → Explain monitoring and support procedures  
- **"How hard is it to maintain?"** → Demonstrate simple monitoring dashboard
- **"What's the ROI?"** → Present concrete numbers and payback timeline

## Recording Setup

### Environment Preparation
- [ ] Clean, distraction-free background
- [ ] High-quality microphone setup
- [ ] Screen recording software ready
- [ ] Demo data prepared and tested

### Technical Setup
- [ ] n8n instance with demo workflow
- [ ] Sample data for demonstration
- [ ] Integration systems accessible
- [ ] Backup recordings prepared

## Post-Production Checklist
- [ ] Add captions for accessibility
- [ ] Include clickable timestamps
- [ ] Add company branding
- [ ] Export in multiple formats (720p, 1080p)
- [ ] Test playback on different devices

## Distribution Strategy
- [ ] Upload to company video platform
- [ ] Share link with stakeholders
- [ ] Include in proposal presentations
- [ ] Add to knowledge base
- [ ] Create shorter clips for social media

---
*Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
"""
        
        return content
    
    def _generate_client_one_pager(self, 
                                  opportunity: AutomationOpportunity,
                                  niche_brief: NicheBrief) -> str:
        """Generate client-facing one-pager."""
        
        content = f"""# {opportunity.title}
*Automation Solution One-Pager*

---

## The Problem

**{opportunity.pain_point_source}**

Your {niche_brief.niche_name} team currently faces these challenges:
- Manual, time-consuming processes
- High error rates due to repetitive tasks  
- Disconnected systems requiring duplicate data entry
- Lack of real-time visibility into operations

**Business Impact**: Your team spends **{opportunity.roi_estimate.get('time_saved_hours_month', 40):.0f} hours/month** on manual work that could be automated.

---

## Our Solution

**{opportunity.title}** - A comprehensive automation that:

✅ **Eliminates Manual Work**: Automates the entire {opportunity.automation_type.lower()} process
✅ **Integrates Your Systems**: Connects {', '.join(opportunity.required_integrations[:3])}
✅ **Ensures Accuracy**: 99%+ accuracy with built-in validation
✅ **Provides Visibility**: Real-time monitoring and reporting

### How It Works
1. **Trigger**: Automatic detection of new {opportunity.automation_type.lower().split()[0]} events
2. **Process**: Intelligent data processing and validation
3. **Integrate**: Seamless updates across all connected systems
4. **Notify**: Automatic alerts and reporting to stakeholders

---

## Benefits & ROI

### Financial Impact
| Metric | Current State | With Automation | Improvement |
|--------|---------------|-----------------|-------------|
| **Monthly Time Spent** | {opportunity.roi_estimate.get('time_saved_hours_month', 40):.0f} hours | 5 hours | **{opportunity.roi_estimate.get('time_saved_hours_month', 40) - 5:.0f} hours saved** |
| **Monthly Cost** | ${opportunity.roi_estimate.get('cost_saved_monthly', 2000) + opportunity.roi_estimate.get('cost_saved_monthly', 2000):,.0f} | ${opportunity.roi_estimate.get('cost_saved_monthly', 2000):,.0f} | **${opportunity.roi_estimate.get('cost_saved_monthly', 2000):,.0f} saved** |
| **Error Rate** | 5-15% | <1% | **99%+ accuracy** |

### 3-Year Value: **${opportunity.roi_estimate.get('three_year_value', 50000):,.0f}**

### Additional Benefits
- **Faster Processing**: Reduce processing time by 85%
- **Better Compliance**: Automated audit trails and documentation
- **Scalability**: Handle 5x more volume without additional staff
- **Team Satisfaction**: Eliminate repetitive, frustrating tasks

---

## Implementation

### Timeline: **{opportunity.estimated_timeline}**

**Week 1-2**: Setup & Configuration
- Install and configure automation platform
- Connect existing systems and validate data flow
- Set up monitoring and alerting

**Week 3-4**: Testing & Deployment  
- Comprehensive testing with real data
- User training and change management
- Go-live with full monitoring

**Ongoing**: Optimization & Support
- Performance monitoring and optimization
- Regular maintenance and updates
- Dedicated support channel

### Your Investment
- **Implementation**: ${opportunity.roi_estimate.get('implementation_cost', 10000):,.0f}
- **Monthly Platform**: $200-500/month
- **Payback Period**: **{opportunity.roi_estimate.get('payback_months', 6):.1f} months**

---

## Why Choose Us

🏆 **Proven Expertise**: Specialized in {niche_brief.niche_name} automation solutions
🔒 **Enterprise Security**: Bank-level security and compliance standards
⚡ **Fast Implementation**: {opportunity.estimated_timeline} to full deployment
🎯 **Guaranteed Results**: {opportunity.success_metrics[0] if opportunity.success_metrics else 'Measurable ROI within 6 months'}

### Success Stories
*"We saved 25 hours per week and eliminated 95% of data entry errors within the first month."*
— Similar {niche_brief.niche_name} company

---

## Next Steps

Ready to transform your {opportunity.automation_type.lower()}?

**Option 1: Quick Start** 
- 30-minute discovery call
- Custom ROI analysis  
- Proof of concept demo

**Option 2: Deep Dive**
- Comprehensive process audit
- Detailed automation plan
- Pilot implementation

### Contact Information
📧 **Email**: automation@yourcompany.com
📞 **Phone**: (555) 123-4567
🗓️ **Schedule**: [calendly.com/yourcompany]

**Let's eliminate manual work and unlock your team's potential.**

---
*Document prepared on {datetime.now().strftime('%B %d, %Y')} | Confidential & Proprietary*
"""
        
        return content
    
    # Template methods
    def _get_implementation_template(self) -> str:
        """Get implementation guide template."""
        return "# Implementation Guide Template"
    
    def _get_configuration_template(self) -> str:
        """Get configuration guide template."""
        return "# Configuration Guide Template"
    
    def _get_runbook_template(self) -> str:
        """Get runbook template."""
        return "# Runbook Template"
    
    def _get_sop_template(self) -> str:
        """Get SOP template."""
        return "# SOP Template"
    
    def _get_loom_outline_template(self) -> str:
        """Get Loom outline template."""
        return "# Loom Outline Template"
    
    def _get_client_one_pager_template(self) -> str:
        """Get client one-pager template."""
        return "# Client One-Pager Template"
    
    # Helper methods
    def _generate_credential_steps(self, integrations: List[str]) -> str:
        """Generate credential setup steps."""
        steps = []
        for integration in integrations:
            steps.append(f"   - {integration}: Add API credentials in n8n credentials panel")
        return '\n'.join(steps)
    
    def _generate_validation_checklist(self, validation_report: Dict[str, Any]) -> str:
        """Generate validation checklist from report."""
        checklist = []
        if validation_report.get('summary', {}).get('overall_status') == 'PASS':
            checklist.append('   - [ ] All validation checks passed')
        else:
            checklist.append('   - [ ] Review and resolve validation issues')
            
        return '\n'.join(checklist)
    
    def _generate_env_vars(self, integrations: List[str]) -> str:
        """Generate environment variables for integrations."""
        env_vars = []
        for integration in integrations:
            clean_name = integration.upper().replace(' ', '_').replace('(', '').replace(')', '')
            env_vars.append(f"{clean_name}_API_KEY=your_api_key")
        return '\n'.join(env_vars)
    
    def _generate_trigger_config(self, workflow: N8nWorkflow) -> str:
        """Generate trigger configuration documentation."""
        return f"""
The workflow uses the following trigger configuration:
- **Trigger Type**: HTTP Webhook (recommended)
- **Path**: /{workflow.name.lower().replace(' ', '-')}
- **Methods**: POST
- **Response Mode**: Respond immediately
"""
    
    def _generate_node_config(self, workflow: N8nWorkflow) -> str:
        """Generate node configuration documentation."""
        return f"""
This workflow contains {len(workflow.nodes)} nodes:
- Data processing and validation nodes
- Integration nodes for external systems
- Error handling and logging nodes
"""
    
    def _generate_integration_config(self, integrations: List[str]) -> str:
        """Generate integration-specific configuration."""
        config = []
        for integration in integrations:
            config.append(f"""
### {integration}
- **Authentication**: API Key/OAuth (as required)
- **Rate Limits**: Respect service limits
- **Error Handling**: Automatic retry with exponential backoff
""")
        return '\n'.join(config)
    
    def _estimate_execution_time(self, workflow: N8nWorkflow) -> int:
        """Estimate workflow execution time in seconds."""
        # Simple estimation: 2 seconds per node
        return len(workflow.nodes) * 2