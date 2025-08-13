"""Package generation module for creating complete automation packages."""

import logging
from typing import Dict, Any
from datetime import datetime, timezone

from ..models.package import AutomationPackage
from ..models.workflow import N8nWorkflow
from .opportunity_mapping import AutomationOpportunity
from .niche_research import NicheBrief

logger = logging.getLogger(__name__)

class PackageGeneratorError(Exception):
    """Custom exception for package generation operations."""
    pass

class PackageGenerator:
    """PackageGenerator for complete automation package creation.
    
    Creates AutomationPackage instances following CLAUDE.md standards
    with all required metadata, ROI notes, and dependencies.
    """
    
    def __init__(self):
        """Initialize package generator."""
        pass
    
    def generate_package(self, 
                        opportunity: AutomationOpportunity,
                        workflow: N8nWorkflow,
                        niche_brief: NicheBrief,
                        validation_report: Dict[str, Any]) -> AutomationPackage:
        """Generate complete automation package.
        
        Args:
            opportunity: Automation opportunity with ROI analysis
            workflow: Generated n8n workflow
            niche_brief: Niche research data
            validation_report: Validation results
            
        Returns:
            Complete automation package
        """
        logger.info(f"Generating automation package for: {opportunity.title}")
        
        try:
            # Generate package slug from opportunity title
            slug = self._generate_package_slug(opportunity.title)
            
            # Create package
            package = AutomationPackage(
                name=opportunity.title,
                slug=slug,
                niche_tags=self._extract_niche_tags(niche_brief),
                problem_statement=self._generate_problem_statement(opportunity, niche_brief),
                outcomes=self._define_measurable_outcomes(opportunity),
                roi_notes=self._generate_roi_notes(opportunity),
                inputs=self._define_package_inputs(opportunity, workflow),
                outputs=self._define_package_outputs(opportunity, workflow),
                dependencies=self._extract_dependencies(opportunity, workflow),
                security_notes=self._generate_security_notes(opportunity),
                last_validated=datetime.now(timezone.utc),
                repo_path=None,
                n8n_export_path=None
            )
            
            logger.info(f"Generated package: {package.slug} with {len(package.dependencies)} dependencies")
            return package
            
        except Exception as e:
            logger.error(f"Package generation failed: {e}")
            raise PackageGeneratorError(f"Failed to generate package: {e}")
    
    def _generate_package_slug(self, title: str) -> str:
        """Generate URL-friendly package slug."""
        import re
        slug = title.lower()
        slug = re.sub(r'[^\w\s-]', '', slug)
        slug = re.sub(r'[-\s]+', '-', slug)
        slug = slug.strip('-')
        
        if len(slug) > 50:
            slug = slug[:50].rstrip('-')
        
        return slug or "automation-package"
    
    def _extract_niche_tags(self, niche_brief: NicheBrief) -> list:
        """Extract relevant niche tags."""
        tags = [niche_brief.niche_name.lower()]
        
        # Add technology adoption level
        tags.append(f"tech-{niche_brief.technology_adoption.lower()}")
        
        # Add market size indicator
        if "billion" in niche_brief.market_size.lower():
            tags.append("large-market")
        elif "million" in niche_brief.market_size.lower():
            tags.append("medium-market")
        else:
            tags.append("small-market")
        
        # Add common industry keywords
        industry_keywords = ["automation", "workflow", "integration"]
        tags.extend(industry_keywords)
        
        return tags
    
    def _generate_problem_statement(self, opportunity: AutomationOpportunity, niche_brief: NicheBrief) -> str:
        """Generate clear problem statement."""
        return (
            f"{niche_brief.niche_name} organizations struggle with {opportunity.pain_point_source.lower()}, "
            f"leading to inefficiencies and increased operational costs. "
            f"This {opportunity.automation_type.lower()} challenge affects productivity and requires "
            f"significant manual effort that could be automated."
        )
    
    def _define_measurable_outcomes(self, opportunity: AutomationOpportunity) -> list:
        """Define measurable outcomes and success metrics."""
        outcomes = []
        
        # Time savings outcome
        time_saved = opportunity.roi_estimate.get('time_saved_hours_month', 0)
        if time_saved > 0:
            outcomes.append(f"Reduce manual processing time by {time_saved:.0f} hours per month")
        
        # Cost savings outcome
        cost_saved = opportunity.roi_estimate.get('cost_saved_monthly', 0)
        if cost_saved > 0:
            outcomes.append(f"Save ${cost_saved:,.0f} monthly in operational costs")
        
        # Error reduction outcome
        outcomes.append("Reduce processing errors by 90%+ through automation")
        
        # Efficiency outcome
        outcomes.append("Improve process efficiency by 60-85%")
        
        # Add opportunity-specific success metrics
        outcomes.extend(opportunity.success_metrics)
        
        return outcomes
    
    def _generate_roi_notes(self, opportunity: AutomationOpportunity) -> str:
        """Generate comprehensive ROI notes."""
        roi = opportunity.roi_estimate
        
        roi_notes = f"""
**Financial Impact Analysis:**

• **Time Savings**: {roi.get('time_saved_hours_month', 0):.0f} hours/month recovered
• **Cost Savings**: ${roi.get('cost_saved_monthly', 0):,.0f}/month in operational cost reduction
• **Revenue Potential**: ${roi.get('revenue_potential_monthly', 0):,.0f}/month from productivity gains
• **Implementation Investment**: ${roi.get('implementation_cost', 0):,.0f} one-time cost

**ROI Metrics:**
• **Payback Period**: {roi.get('payback_months', 0):.1f} months
• **3-Year Value**: ${roi.get('three_year_value', 0):,.0f} net value creation
• **Monthly ROI**: {(roi.get('cost_saved_monthly', 0) + roi.get('revenue_potential_monthly', 0)) / max(roi.get('implementation_cost', 1), 1) * 100:.0f}% return on investment

**Value Drivers:**
• Elimination of manual, repetitive tasks
• Reduced human error and rework costs  
• Faster processing and improved cycle times
• Enhanced data accuracy and consistency
• Freed capacity for higher-value activities

**Risk Mitigation Value:**
• Reduced compliance and audit risks
• Improved process reliability and consistency
• Better visibility and control over operations
• Scalable solution that grows with business needs
        """.strip()
        
        return roi_notes
    
    def _define_package_inputs(self, opportunity: AutomationOpportunity, workflow: N8nWorkflow) -> dict:
        """Define required inputs for the automation."""
        inputs: Dict[str, Any] = {
            "system_inputs": [],
            "configuration_inputs": [],
            "authentication_inputs": []
        }
        
        # System inputs based on integrations
        for integration in opportunity.required_integrations:
            if "CRM" in integration:
                inputs["system_inputs"].extend([
                    "CRM contact records",
                    "Lead qualification data",
                    "Customer interaction history"
                ])
            elif "Email" in integration:
                inputs["system_inputs"].extend([
                    "Email templates",
                    "Recipient contact lists",
                    "Message scheduling preferences"
                ])
            elif "Spreadsheet" in integration or "Database" in integration:
                inputs["system_inputs"].extend([
                    "Data records for processing",
                    "Field mapping configurations",
                    "Data validation rules"
                ])
            elif "Calendar" in integration:
                inputs["system_inputs"].extend([
                    "Meeting scheduling preferences",
                    "Calendar availability windows",
                    "Attendee notification settings"
                ])
            else:
                inputs["system_inputs"].append(f"{integration} data and configuration")
        
        # Configuration inputs
        inputs["configuration_inputs"].extend([
            "Workflow trigger conditions",
            "Business rule configurations", 
            "Error handling preferences",
            "Notification and alert settings"
        ])
        
        # Authentication inputs
        inputs["authentication_inputs"].extend([
            "API credentials for integrated systems",
            "System access permissions",
            "Security configuration settings"
        ])
        
        # Remove duplicates from each category
        for category in inputs:
            inputs[category] = list(set(inputs[category]))
        
        return inputs
    
    def _define_package_outputs(self, opportunity: AutomationOpportunity, workflow: N8nWorkflow) -> dict:
        """Define expected outputs from the automation."""
        outputs: Dict[str, Any] = {
            "primary_outputs": [],
            "data_outputs": [],
            "system_outputs": [],
            "business_outcomes": []
        }
        
        # Primary automation outputs
        outputs["primary_outputs"].append(f"Automated {opportunity.automation_type.lower()} processing")
        
        # Data outputs based on automation type
        if "Data Processing" in opportunity.automation_type:
            outputs["data_outputs"].extend([
                "Processed and validated data records",
                "Data quality reports",
                "Processing summary statistics"
            ])
        elif "Communication" in opportunity.automation_type:
            outputs["data_outputs"].extend([
                "Automated message delivery",
                "Communication tracking logs", 
                "Delivery confirmation reports"
            ])
        elif "Reporting" in opportunity.automation_type:
            outputs["data_outputs"].extend([
                "Generated reports and dashboards",
                "Data analysis summaries",
                "Scheduled report distributions"
            ])
        elif "Lead Management" in opportunity.automation_type:
            outputs["data_outputs"].extend([
                "Qualified lead records",
                "Lead scoring and prioritization",
                "Automated follow-up sequences"
            ])
        
        # System outputs
        outputs["system_outputs"].extend([
            "Updated records in integrated systems",
            "Audit trails and processing logs",
            "Performance metrics and monitoring data",
            "Error reports and exception handling"
        ])
        
        # Business outcomes
        outputs["business_outcomes"].extend([
            f"Time savings of {opportunity.roi_estimate.get('time_saved_hours_month', 0):.0f} hours/month",
            f"Cost savings of ${opportunity.roi_estimate.get('cost_saved_monthly', 0):,.0f}/month",
            "Improved process accuracy and consistency",
            "Enhanced operational visibility and control"
        ])
        
        return outputs
    
    def _extract_dependencies(self, opportunity: AutomationOpportunity, workflow: N8nWorkflow) -> list:
        """Extract system and integration dependencies."""
        dependencies = []
        
        # Platform dependencies
        dependencies.append("n8n automation platform (v0.190.0+)")
        
        # Integration dependencies
        for integration in opportunity.required_integrations:
            dependencies.append(f"{integration} API access and credentials")
        
        # Technical dependencies
        dependencies.extend([
            "Stable internet connection",
            "JSON/REST API compatibility",
            "Webhook endpoint capability"
        ])
        
        # Business dependencies from opportunity analysis
        dependencies.extend(opportunity.dependencies)
        
        # Security dependencies
        dependencies.extend([
            "SSL/TLS encryption for data transmission",
            "API rate limit compliance",
            "Data privacy and security controls"
        ])
        
        # Operational dependencies
        dependencies.extend([
            "Monitoring and alerting system",
            "Backup and recovery procedures",
            "Change management processes"
        ])
        
        return list(set(dependencies))  # Remove duplicates
    
    def _generate_security_notes(self, opportunity: AutomationOpportunity) -> str:
        """Generate security considerations and notes."""
        risk_level = opportunity.risk_assessment.get('overall_risk', 0)
        
        if risk_level > 0.7:
            security_level = "High Security"
            requirements = [
                "Multi-factor authentication required for all system access",
                "End-to-end encryption for all data transmissions", 
                "Comprehensive audit logging and monitoring",
                "Regular security assessments and penetration testing",
                "SOC 2 Type II compliance validation"
            ]
        elif risk_level > 0.4:
            security_level = "Medium Security"
            requirements = [
                "Strong password policies and regular rotation",
                "TLS 1.2+ encryption for all API communications",
                "Access controls and permission management",
                "Regular security updates and patch management",
                "Data backup and recovery procedures"
            ]
        else:
            security_level = "Standard Security"
            requirements = [
                "Basic authentication and access controls",
                "HTTPS encryption for web communications",
                "Regular credential rotation",
                "Standard backup and monitoring procedures"
            ]
        
        security_notes = f"""
**Security Classification**: {security_level}
**Risk Level**: {risk_level:.1%}

**Security Requirements:**
{chr(10).join(f'• {req}' for req in requirements)}

**Data Handling:**
• All sensitive data encrypted at rest and in transit
• No credentials or secrets stored in workflow configurations
• Environment variables used for all authentication tokens
• PII handling compliant with applicable privacy regulations

**Integration Security:**
{chr(10).join(f'• {integration}: Secure API authentication and authorization' for integration in opportunity.required_integrations)}

**Monitoring & Compliance:**
• Real-time security monitoring and alerting
• Comprehensive audit trails for all data processing
• Regular compliance assessments and reporting
• Incident response procedures documented and tested

**Risk Mitigation:**
{chr(10).join(f'• {strategy}' for strategy in opportunity.risk_assessment.get('mitigation_strategies', []))}
        """.strip()
        
        return security_notes