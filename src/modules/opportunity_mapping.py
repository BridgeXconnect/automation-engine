"""Opportunity mapping module for translating pain points to automation candidates."""

import logging
from typing import Dict, List, Any
from datetime import datetime
from dataclasses import dataclass
from pydantic import BaseModel, Field

from .niche_research import NicheBrief, PainPoint

logger = logging.getLogger(__name__)


@dataclass
class ROIEstimate:
    """ROI estimation for automation opportunity."""
    time_saved_hours_month: float
    cost_saved_monthly: float
    revenue_potential_monthly: float
    implementation_cost: float
    payback_months: float
    three_year_value: float


@dataclass 
class RiskAssessment:
    """Risk assessment for automation implementation."""
    technical_risk: float  # 0-1 scale
    business_risk: float   # 0-1 scale
    change_management_risk: float  # 0-1 scale
    overall_risk: float    # 0-1 scale
    mitigation_strategies: List[str]


class AutomationOpportunity(BaseModel):
    """Structured automation opportunity with ROI and risk analysis."""
    title: str = Field(..., description="Opportunity title")
    description: str = Field(..., description="Detailed description")
    pain_point_source: str = Field(..., description="Source pain point description")
    
    # Classification
    automation_type: str = Field(..., description="Type of automation")
    complexity_level: str = Field(..., description="Implementation complexity")
    priority_score: float = Field(..., description="Priority score (0-1)")
    
    # ROI Analysis
    roi_estimate: Dict[str, Any] = Field(..., description="ROI calculations")
    
    # Risk Assessment
    risk_assessment: Dict[str, Any] = Field(..., description="Risk analysis")
    
    # Implementation Details
    required_integrations: List[str] = Field(default_factory=list)
    estimated_timeline: str = Field(..., description="Implementation timeline")
    success_metrics: List[str] = Field(default_factory=list)
    dependencies: List[str] = Field(default_factory=list)
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)


class OpportunityMapperError(Exception):
    """Custom exception for opportunity mapping operations."""
    pass


class OpportunityMapper:
    """OpportunityMapper for pain→automation translation.
    
    Calculates ROI estimates (time saved, cost impact, revenue lift),
    assesses dependencies and risk factors,
    outputs ranked automation candidates.
    """
    
    def __init__(self):
        """Initialize opportunity mapper with estimation models."""
        # ROI calculation parameters
        self.hourly_rates = {
            "junior": 25,
            "mid": 45, 
            "senior": 75,
            "manager": 100
        }
        
        # Complexity multipliers for implementation cost
        self.complexity_multipliers = {
            "Low": 1.0,
            "Medium": 2.0,
            "High": 4.0
        }
        
        # Risk assessment factors
        self.risk_factors = {
            "technical_complexity": [0.1, 0.3, 0.6],  # Low, Medium, High
            "integration_count": [0.1, 0.25, 0.5],
            "change_scope": [0.15, 0.35, 0.7],
            "stakeholder_count": [0.05, 0.15, 0.3]
        }
    
    def map_opportunities(self, niche_brief: NicheBrief) -> List[AutomationOpportunity]:
        """Map niche brief pain points to ranked automation opportunities.
        
        Args:
            niche_brief: Research brief with identified pain points
            
        Returns:
            List of ranked automation opportunities
        """
        logger.info(f"Mapping opportunities for niche: {niche_brief.niche_name}")
        
        opportunities = []
        
        for pain_dict in niche_brief.pain_points:
            # Convert dict back to structured data
            pain_point = self._dict_to_pain_point(pain_dict)
            
            # Only process pain points with high automation potential
            if pain_point.automation_potential >= 0.5:
                opportunity = self._create_automation_opportunity(
                    pain_point, 
                    niche_brief.profile,
                    niche_brief.technology_adoption
                )
                opportunities.append(opportunity)
        
        # Rank opportunities by priority score
        ranked_opportunities = sorted(opportunities, key=lambda x: x.priority_score, reverse=True)
        
        logger.info(f"Generated {len(ranked_opportunities)} automation opportunities")
        return ranked_opportunities
    
    def _dict_to_pain_point(self, pain_dict: Dict[str, Any]) -> PainPoint:
        """Convert dictionary back to PainPoint object."""
        return PainPoint(
            description=pain_dict["description"],
            impact_score=pain_dict["impact_score"],
            frequency=pain_dict["frequency"],
            existing_solutions=pain_dict["existing_solutions"],
            gaps=pain_dict["gaps"],
            automation_potential=pain_dict["automation_potential"]
        )
    
    def _create_automation_opportunity(self, pain_point: PainPoint, 
                                     niche_profile: Dict[str, Any],
                                     tech_adoption: str) -> AutomationOpportunity:
        """Create structured automation opportunity from pain point."""
        
        # Generate opportunity details
        title = self._generate_opportunity_title(pain_point)
        description = self._generate_detailed_description(pain_point)
        automation_type = self._classify_automation_type(pain_point)
        complexity = self._assess_implementation_complexity(pain_point, tech_adoption)
        
        # Calculate ROI
        roi_estimate = self._calculate_roi(pain_point, niche_profile, complexity)
        
        # Assess risks
        risk_assessment = self._assess_risks(pain_point, complexity, niche_profile)
        
        # Calculate priority score
        priority_score = self._calculate_priority_score(pain_point, roi_estimate, risk_assessment)
        
        # Identify requirements
        integrations = self._identify_required_integrations(pain_point)
        timeline = self._estimate_timeline(complexity, len(integrations))
        dependencies = self._identify_dependencies(pain_point, integrations)
        
        return AutomationOpportunity(
            title=title,
            description=description,
            pain_point_source=pain_point.description,
            automation_type=automation_type,
            complexity_level=complexity,
            priority_score=priority_score,
            roi_estimate=self._roi_to_dict(roi_estimate),
            risk_assessment=self._risk_to_dict(risk_assessment),
            required_integrations=integrations,
            estimated_timeline=timeline,
            success_metrics=self._define_success_metrics(pain_point, roi_estimate),
            dependencies=dependencies
        )
    
    def _generate_opportunity_title(self, pain_point: PainPoint) -> str:
        """Generate compelling opportunity title."""
        automation_templates = {
            "manual": "Automate Manual {}",
            "data entry": "Streamline Data Entry for {}",
            "report": "Auto-Generate {} Reports",
            "communication": "Orchestrate {} Communications",
            "qualification": "Intelligent {} Qualification",
            "intake": "Automated {} Intake Process"
        }
        
        description_lower = pain_point.description.lower()
        
        for keyword, template in automation_templates.items():
            if keyword in description_lower:
                process_name = pain_point.description.replace("Manual ", "").replace("manual ", "")
                return template.format(process_name)
        
        return f"Automation Solution for {pain_point.description}"
    
    def _generate_detailed_description(self, pain_point: PainPoint) -> str:
        """Generate detailed opportunity description."""
        base_description = f"Automate the {pain_point.description.lower()}"
        
        # Add impact context
        if pain_point.impact_score > 0.8:
            impact_context = "high-impact"
        elif pain_point.impact_score > 0.5:
            impact_context = "medium-impact"
        else:
            impact_context = "low-impact"
        
        # Add frequency context  
        frequency_context = f"{pain_point.frequency} occurrence"
        
        return f"{base_description}. This {impact_context} process occurs {frequency_context} and has significant automation potential ({pain_point.automation_potential:.0%}). Current gaps include: {', '.join(pain_point.gaps[:3])}"
    
    def _classify_automation_type(self, pain_point: PainPoint) -> str:
        """Classify the type of automation needed."""
        description_lower = pain_point.description.lower()
        
        if any(keyword in description_lower for keyword in ["data", "entry", "input"]):
            return "Data Processing Automation"
        elif any(keyword in description_lower for keyword in ["communication", "email", "notification"]):
            return "Communication Workflow"
        elif any(keyword in description_lower for keyword in ["report", "analysis", "dashboard"]):
            return "Reporting & Analytics"
        elif any(keyword in description_lower for keyword in ["lead", "qualification", "intake"]):
            return "Lead Management Automation"
        elif any(keyword in description_lower for keyword in ["integration", "sync", "transfer"]):
            return "System Integration"
        else:
            return "Process Automation"
    
    def _assess_implementation_complexity(self, pain_point: PainPoint, tech_adoption: str) -> str:
        """Assess implementation complexity level."""
        complexity_score = 0.0
        
        # Factor in automation potential (inverse relationship)
        complexity_score += (1 - pain_point.automation_potential) * 0.3
        
        # Factor in number of gaps
        complexity_score += min(len(pain_point.gaps) / 5, 1.0) * 0.3
        
        # Factor in technology adoption level
        tech_multipliers = {"low": 1.3, "medium": 1.0, "high": 0.7}
        complexity_score *= tech_multipliers.get(tech_adoption.lower(), 1.0)
        
        # Factor in existing solutions count  
        complexity_score += min(len(pain_point.existing_solutions) / 3, 1.0) * 0.2
        
        if complexity_score > 0.7:
            return "High"
        elif complexity_score > 0.4:
            return "Medium"
        else:
            return "Low"
    
    def _calculate_roi(self, pain_point: PainPoint, niche_profile: Dict[str, Any], 
                      complexity: str) -> ROIEstimate:
        """Calculate comprehensive ROI estimate."""
        
        # Estimate time savings based on frequency and impact
        frequency_hours = {"daily": 22 * 5, "weekly": 22, "monthly": 5}  # Work hours per month
        base_hours = frequency_hours.get(pain_point.frequency, 22)
        
        time_saved_monthly = base_hours * pain_point.impact_score * pain_point.automation_potential
        
        # Calculate cost savings (assume mid-level hourly rate)
        hourly_rate = self.hourly_rates["mid"]
        cost_saved_monthly = time_saved_monthly * hourly_rate
        
        # Estimate revenue potential (productivity gains)
        revenue_potential_monthly = cost_saved_monthly * 0.5  # Conservative estimate
        
        # Calculate implementation cost
        base_implementation_cost = 5000  # Base cost in USD
        complexity_multiplier = self.complexity_multipliers[complexity]
        implementation_cost = base_implementation_cost * complexity_multiplier
        
        # Calculate payback period
        monthly_value = cost_saved_monthly + revenue_potential_monthly
        payback_months = implementation_cost / monthly_value if monthly_value > 0 else float('inf')
        
        # Calculate 3-year value
        three_year_value = (monthly_value * 36) - implementation_cost
        
        return ROIEstimate(
            time_saved_hours_month=time_saved_monthly,
            cost_saved_monthly=cost_saved_monthly,
            revenue_potential_monthly=revenue_potential_monthly,
            implementation_cost=implementation_cost,
            payback_months=payback_months,
            three_year_value=three_year_value
        )
    
    def _assess_risks(self, pain_point: PainPoint, complexity: str, 
                     niche_profile: Dict[str, Any]) -> RiskAssessment:
        """Assess implementation risks across multiple dimensions."""
        
        # Technical risk assessment
        complexity_risk_map = {"Low": 0.2, "Medium": 0.5, "High": 0.8}
        technical_risk = complexity_risk_map[complexity]
        
        # Business risk (based on impact and change scope)
        business_risk = 0.3 if pain_point.impact_score > 0.7 else 0.2
        
        # Change management risk (based on frequency - daily changes are harder)
        change_risk_map = {"daily": 0.7, "weekly": 0.5, "monthly": 0.3}
        change_management_risk = change_risk_map.get(pain_point.frequency, 0.5)
        
        # Calculate overall risk
        overall_risk = (technical_risk * 0.4 + business_risk * 0.3 + change_management_risk * 0.3)
        
        # Generate mitigation strategies
        mitigation_strategies = self._generate_risk_mitigations(
            technical_risk, business_risk, change_management_risk, complexity
        )
        
        return RiskAssessment(
            technical_risk=technical_risk,
            business_risk=business_risk,
            change_management_risk=change_management_risk,
            overall_risk=overall_risk,
            mitigation_strategies=mitigation_strategies
        )
    
    def _generate_risk_mitigations(self, tech_risk: float, business_risk: float, 
                                 change_risk: float, complexity: str) -> List[str]:
        """Generate risk mitigation strategies."""
        mitigations = []
        
        if tech_risk > 0.5:
            mitigations.append("Conduct technical proof of concept")
            mitigations.append("Engage specialized integration consultants")
        
        if business_risk > 0.5:
            mitigations.append("Implement phased rollout approach")
            mitigations.append("Establish clear success metrics and rollback plan")
        
        if change_risk > 0.5:
            mitigations.append("Invest in comprehensive user training")
            mitigations.append("Implement gradual change management process")
        
        if complexity == "High":
            mitigations.append("Break implementation into smaller phases")
            mitigations.append("Establish dedicated project team")
        
        return mitigations
    
    def _calculate_priority_score(self, pain_point: PainPoint, roi: ROIEstimate, 
                                risk: RiskAssessment) -> float:
        """Calculate overall priority score for ranking."""
        # Weighted scoring formula
        impact_score = pain_point.impact_score * 0.25
        automation_score = pain_point.automation_potential * 0.20
        roi_score = min(roi.three_year_value / 50000, 1.0) * 0.25  # Normalize ROI
        frequency_score = {"daily": 1.0, "weekly": 0.7, "monthly": 0.4}.get(pain_point.frequency, 0.5) * 0.15
        risk_score = (1 - risk.overall_risk) * 0.15  # Lower risk = higher score
        
        priority_score = impact_score + automation_score + roi_score + frequency_score + risk_score
        return min(priority_score, 1.0)
    
    def _identify_required_integrations(self, pain_point: PainPoint) -> List[str]:
        """Identify required system integrations."""
        integrations = set()
        
        description_lower = pain_point.description.lower()
        
        # Common integration patterns
        if any(term in description_lower for term in ["crm", "customer", "lead"]):
            integrations.add("CRM System (HubSpot/Salesforce)")
        
        if any(term in description_lower for term in ["email", "communication", "notify"]):
            integrations.add("Email Platform (Gmail/Outlook)")
        
        if any(term in description_lower for term in ["slack", "teams", "chat"]):
            integrations.add("Team Communication (Slack/Teams)")
        
        if any(term in description_lower for term in ["sheet", "excel", "data", "report"]):
            integrations.add("Spreadsheet/Database System")
        
        if any(term in description_lower for term in ["calendar", "schedule", "meeting"]):
            integrations.add("Calendar System")
        
        if any(term in description_lower for term in ["webhook", "api", "integration"]):
            integrations.add("Custom API Integration")
        
        return list(integrations) or ["Standard Business Tools"]
    
    def _estimate_timeline(self, complexity: str, integration_count: int) -> str:
        """Estimate implementation timeline."""
        base_weeks = {"Low": 2, "Medium": 4, "High": 8}
        weeks = base_weeks[complexity]
        
        # Add time for integrations
        weeks += integration_count * 1
        
        if weeks <= 3:
            return "1-3 weeks"
        elif weeks <= 6:
            return "3-6 weeks"
        elif weeks <= 12:
            return "6-12 weeks"
        else:
            return "3+ months"
    
    def _identify_dependencies(self, pain_point: PainPoint, integrations: List[str]) -> List[str]:
        """Identify implementation dependencies."""
        dependencies = []
        
        if len(integrations) > 1:
            dependencies.append("Multi-system integration coordination")
        
        if pain_point.frequency == "daily":
            dependencies.append("Minimal downtime deployment required")
        
        if pain_point.impact_score > 0.7:
            dependencies.append("Executive stakeholder approval needed")
        
        if len(pain_point.existing_solutions) > 0:
            dependencies.append("Migration from existing tools")
        
        return dependencies or ["Standard implementation requirements"]
    
    def _define_success_metrics(self, pain_point: PainPoint, roi: ROIEstimate) -> List[str]:
        """Define measurable success metrics."""
        metrics = []
        
        # Time savings metric
        metrics.append(f"Reduce manual time by {roi.time_saved_hours_month:.0f} hours/month")
        
        # Cost savings metric  
        metrics.append(f"Save ${roi.cost_saved_monthly:.0f}/month in operational costs")
        
        # Quality metrics
        if "error" in pain_point.description.lower() or "mistake" in pain_point.description.lower():
            metrics.append("Reduce human errors by 90%+")
        
        # Efficiency metrics
        if pain_point.frequency == "daily":
            metrics.append("Improve daily process efficiency by 60%+")
        
        # ROI metric
        if roi.payback_months < 12:
            metrics.append(f"Achieve ROI breakeven in {roi.payback_months:.1f} months")
        
        return metrics
    
    def _roi_to_dict(self, roi: ROIEstimate) -> Dict[str, Any]:
        """Convert ROIEstimate to dictionary."""
        return {
            "time_saved_hours_month": roi.time_saved_hours_month,
            "cost_saved_monthly": roi.cost_saved_monthly,
            "revenue_potential_monthly": roi.revenue_potential_monthly,
            "implementation_cost": roi.implementation_cost,
            "payback_months": roi.payback_months,
            "three_year_value": roi.three_year_value
        }
    
    def _risk_to_dict(self, risk: RiskAssessment) -> Dict[str, Any]:
        """Convert RiskAssessment to dictionary."""
        return {
            "technical_risk": risk.technical_risk,
            "business_risk": risk.business_risk,
            "change_management_risk": risk.change_management_risk,
            "overall_risk": risk.overall_risk,
            "mitigation_strategies": risk.mitigation_strategies
        }