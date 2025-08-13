"""Niche research module for automation opportunity discovery."""

import logging
import requests
import time
from typing import Any, Dict, List, Optional
from datetime import datetime
from dataclasses import dataclass
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


@dataclass
class PainPoint:
    """Represents a business pain point in a niche."""
    description: str
    impact_score: float  # 0.0 to 1.0 scale
    frequency: str  # "daily", "weekly", "monthly"
    existing_solutions: List[str]
    gaps: List[str]
    automation_potential: float  # 0.0 to 1.0 scale


@dataclass
class NicheProfile:
    """Profile information about a business niche."""
    name: str
    industry_size: str
    key_stakeholders: List[str]
    common_tools: List[str]
    budget_range: str
    tech_sophistication: str  # "low", "medium", "high"


class NicheBrief(BaseModel):
    """Structured output from niche research."""
    niche_name: str = Field(..., description="Name of the researched niche")
    profile: Dict[str, Any] = Field(..., description="Niche profile information")
    pain_points: List[Dict[str, Any]] = Field(..., description="Identified pain points")
    opportunities: List[Dict[str, Any]] = Field(..., description="Automation opportunities")
    competitive_landscape: List[str] = Field(default_factory=list, description="Existing solutions")
    market_size: str = Field(default="", description="Market size estimate")
    technology_adoption: str = Field(default="medium", description="Technology adoption level")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Quality metrics
    research_confidence: float = Field(default=0.5, description="Confidence in research findings (0-1)")
    data_sources: List[str] = Field(default_factory=list, description="Sources used for research")


class NicheResearcherError(Exception):
    """Custom exception for niche research operations."""
    pass


class NicheResearcher:
    """Niche research class with web scraping capabilities.
    
    Generates structured "Niche Brief" with pains/opportunities,
    includes data collection from multiple sources,
    outputs standardized research format.
    """
    
    def __init__(self, research_timeout: int = 30, max_sources: int = 5):
        """Initialize niche researcher.
        
        Args:
            research_timeout: Timeout for web requests in seconds
            max_sources: Maximum number of sources to research per niche
        """
        self.timeout = research_timeout
        self.max_sources = max_sources
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (compatible; AutomationResearcher/1.0)'
        })
        
        # Common business pain point patterns
        self.pain_indicators = [
            "manual process", "time consuming", "error prone", "repetitive task",
            "data entry", "copy paste", "multiple systems", "lack of integration",
            "workflow bottleneck", "resource intensive", "inefficient", "automation"
        ]
        
        # Research data sources (in real implementation, these would be actual APIs/endpoints)
        self.research_sources = {
            "industry_reports": "https://api.research-provider.com/industry",
            "business_forums": "https://api.business-forum.com/discussions",
            "job_postings": "https://api.job-board.com/search",
            "software_reviews": "https://api.review-site.com/software",
            "social_listening": "https://api.social-media.com/mentions"
        }
    
    def research_niche(self, niche_keyword: str) -> NicheBrief:
        """Research a business niche and generate comprehensive brief.
        
        Args:
            niche_keyword: Target niche to research (e.g., "logistics 3PL")
            
        Returns:
            Structured NicheBrief with findings
        """
        logger.info(f"Starting niche research for: {niche_keyword}")
        
        try:
            # Gather data from multiple sources
            research_data = self._collect_research_data(niche_keyword)
            
            # Analyze and structure findings
            profile = self._analyze_niche_profile(niche_keyword, research_data)
            pain_points = self._identify_pain_points(research_data)
            opportunities = self._map_automation_opportunities(pain_points)
            competitive_landscape = self._analyze_competition(niche_keyword, research_data)
            
            # Calculate research confidence based on data quality
            confidence = self._calculate_research_confidence(research_data)
            
            brief = NicheBrief(
                niche_name=niche_keyword,
                profile=profile,
                pain_points=[self._pain_point_to_dict(pp) for pp in pain_points],
                opportunities=[self._opportunity_to_dict(opp) for opp in opportunities],
                competitive_landscape=competitive_landscape,
                market_size=self._estimate_market_size(research_data),
                technology_adoption=self._assess_tech_adoption(research_data),
                research_confidence=confidence,
                data_sources=list(research_data.keys())
            )
            
            logger.info(f"Completed niche research for '{niche_keyword}' with confidence {confidence:.2f}")
            return brief
            
        except Exception as e:
            logger.error(f"Niche research failed for '{niche_keyword}': {e}")
            raise NicheResearcherError(f"Failed to research niche '{niche_keyword}': {e}")
    
    def _collect_research_data(self, niche: str) -> Dict[str, Any]:
        """Collect research data from multiple sources.
        
        Args:
            niche: Niche keyword to research
            
        Returns:
            Dictionary of research data by source
        """
        research_data = {}
        
        for source_name, endpoint in list(self.research_sources.items())[:self.max_sources]:
            try:
                data = self._fetch_source_data(source_name, endpoint, niche)
                if data:
                    research_data[source_name] = data
                    logger.info(f"Collected data from {source_name}")
                
                # Rate limiting
                time.sleep(1)
                
            except Exception as e:
                logger.warning(f"Failed to collect data from {source_name}: {e}")
                continue
        
        # Add simulated research data for demo purposes
        research_data.update(self._generate_simulated_data(niche))
        
        return research_data
    
    def _fetch_source_data(self, source: str, endpoint: str, niche: str) -> Optional[Dict[str, Any]]:
        """Fetch data from a research source.
        
        Args:
            source: Source name
            endpoint: API endpoint
            niche: Niche to research
            
        Returns:
            Research data or None if failed
        """
        try:
            # In a real implementation, this would make actual API calls
            # For now, we'll simulate data collection
            
            params = {"query": niche, "limit": "50"}
            response = self.session.get(endpoint, params=params, timeout=self.timeout)
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.warning(f"API request failed for {source}: {response.status_code}")
                return None
                
        except requests.RequestException as e:
            logger.warning(f"Request failed for {source}: {e}")
            return None
    
    def _generate_simulated_data(self, niche: str) -> Dict[str, Any]:
        """Generate simulated research data for demo purposes."""
        # This simulates realistic research findings
        simulated_data = {
            "simulated_industry_data": {
                "market_size": "Multi-billion dollar industry",
                "growth_rate": "5-10% annually", 
                "key_players": ["Company A", "Company B", "Company C"],
                "common_challenges": [
                    "Manual data entry processes",
                    "Lack of system integration", 
                    "Time-consuming reporting",
                    "Error-prone workflows",
                    "Multiple disconnected tools"
                ]
            },
            "simulated_pain_analysis": {
                "top_pain_points": [
                    {
                        "description": "Manual lead intake and qualification process",
                        "frequency": "daily",
                        "impact": "high",
                        "mentions": 45
                    },
                    {
                        "description": "Disconnected CRM and communication tools",
                        "frequency": "daily", 
                        "impact": "medium",
                        "mentions": 32
                    },
                    {
                        "description": "Time-consuming report generation",
                        "frequency": "weekly",
                        "impact": "high",
                        "mentions": 28
                    }
                ]
            },
            "simulated_tech_profile": {
                "common_tools": ["Excel", "CRM systems", "Email platforms", "Reporting tools"],
                "automation_readiness": "medium",
                "budget_range": "$1K-10K/month",
                "decision_makers": ["Operations Manager", "IT Director", "Business Owner"]
            }
        }
        
        return simulated_data
    
    def _analyze_niche_profile(self, niche: str, research_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze niche profile from research data."""
        profile = {
            "niche_name": niche,
            "industry_category": self._categorize_industry(niche),
            "business_model": self._infer_business_model(research_data),
            "typical_company_size": self._estimate_company_size(research_data),
            "key_stakeholders": self._identify_stakeholders(research_data),
            "common_tools": self._extract_common_tools(research_data),
            "budget_characteristics": self._analyze_budget_patterns(research_data),
            "geographic_distribution": self._analyze_geography(research_data)
        }
        
        return profile
    
    def _identify_pain_points(self, research_data: Dict[str, Any]) -> List[PainPoint]:
        """Identify and structure pain points from research data."""
        pain_points = []
        
        # Extract pain points from simulated data
        pain_data = research_data.get("simulated_pain_analysis", {}).get("top_pain_points", [])
        
        for pain_info in pain_data:
            # Calculate impact score based on frequency and mentions
            impact_score = self._calculate_pain_impact(pain_info)
            
            pain_point = PainPoint(
                description=pain_info["description"],
                impact_score=impact_score,
                frequency=pain_info["frequency"],
                existing_solutions=self._find_existing_solutions(pain_info["description"]),
                gaps=self._identify_solution_gaps(pain_info["description"]),
                automation_potential=self._assess_automation_potential(pain_info["description"])
            )
            
            pain_points.append(pain_point)
        
        return pain_points
    
    def _calculate_pain_impact(self, pain_info: Dict[str, Any]) -> float:
        """Calculate pain point impact score."""
        frequency_weights = {"daily": 1.0, "weekly": 0.7, "monthly": 0.4}
        impact_weights = {"high": 1.0, "medium": 0.6, "low": 0.3}
        
        frequency_score = frequency_weights.get(pain_info.get("frequency", "monthly"), 0.4)
        impact_score = impact_weights.get(pain_info.get("impact", "medium"), 0.6)
        mention_score = min(pain_info.get("mentions", 0) / 50.0, 1.0)  # Normalize to 0-1
        
        return (frequency_score * 0.4 + impact_score * 0.4 + mention_score * 0.2)
    
    def _map_automation_opportunities(self, pain_points: List[PainPoint]) -> List[Dict[str, Any]]:
        """Map pain points to specific automation opportunities."""
        opportunities = []
        
        for pain in pain_points:
            if pain.automation_potential > 0.6:  # Only high-potential opportunities
                opportunity = {
                    "title": self._generate_opportunity_title(pain),
                    "description": self._generate_opportunity_description(pain),
                    "automation_type": self._classify_automation_type(pain),
                    "complexity": self._assess_complexity(pain),
                    "roi_estimate": self._estimate_roi(pain),
                    "implementation_time": self._estimate_implementation_time(pain),
                    "required_integrations": self._identify_required_integrations(pain),
                    "success_metrics": self._define_success_metrics(pain)
                }
                opportunities.append(opportunity)
        
        return opportunities
    
    def _generate_opportunity_title(self, pain: PainPoint) -> str:
        """Generate automation opportunity title from pain point."""
        automation_verbs = {
            "manual": "Automate",
            "data entry": "Streamline", 
            "reporting": "Auto-generate",
            "communication": "Orchestrate",
            "qualification": "Intelligent"
        }
        
        for keyword, verb in automation_verbs.items():
            if keyword in pain.description.lower():
                return f"{verb} {pain.description.replace('Manual ', '').replace('manual ', '')}"
        
        return f"Automate {pain.description}"
    
    def _generate_opportunity_description(self, pain: PainPoint) -> str:
        """Generate detailed opportunity description from pain point."""
        base_desc = f"Automate the {pain.description.lower()}"
        
        # Add impact context
        if pain.impact_score > 0.8:
            impact_desc = "high-impact"
        elif pain.impact_score > 0.5:
            impact_desc = "medium-impact"
        else:
            impact_desc = "low-impact"
        
        # Add frequency context
        frequency_desc = f"{pain.frequency} occurrence"
        
        return (f"{base_desc}. This {impact_desc} process occurs {frequency_desc} "
                f"and has significant automation potential ({pain.automation_potential:.0%}). "
                f"Current gaps include: {', '.join(pain.gaps[:2])}")
    
    def _pain_point_to_dict(self, pain: PainPoint) -> Dict[str, Any]:
        """Convert PainPoint to dictionary."""
        return {
            "description": pain.description,
            "impact_score": pain.impact_score,
            "frequency": pain.frequency,
            "existing_solutions": pain.existing_solutions,
            "gaps": pain.gaps,
            "automation_potential": pain.automation_potential
        }
    
    def _opportunity_to_dict(self, opportunity: Dict[str, Any]) -> Dict[str, Any]:
        """Convert opportunity to standardized dictionary."""
        return opportunity  # Already in dict format
    
    # Utility methods for analysis (simplified implementations)
    def _categorize_industry(self, niche: str) -> str:
        categories = {
            "logistics": "Transportation & Logistics",
            "real estate": "Real Estate",
            "healthcare": "Healthcare",
            "finance": "Financial Services",
            "retail": "Retail & E-commerce"
        }
        
        for keyword, category in categories.items():
            if keyword in niche.lower():
                return category
        
        return "General Business"
    
    def _infer_business_model(self, research_data: Dict[str, Any]) -> str:
        return "B2B Service Provider"  # Simplified
    
    def _estimate_company_size(self, research_data: Dict[str, Any]) -> str:
        return "10-500 employees"  # Simplified
    
    def _identify_stakeholders(self, research_data: Dict[str, Any]) -> List[str]:
        tech_profile = research_data.get("simulated_tech_profile", {})
        return tech_profile.get("decision_makers", ["Operations Manager", "IT Director"])
    
    def _extract_common_tools(self, research_data: Dict[str, Any]) -> List[str]:
        tech_profile = research_data.get("simulated_tech_profile", {})
        return tech_profile.get("common_tools", ["Excel", "Email", "CRM"])
    
    def _analyze_budget_patterns(self, research_data: Dict[str, Any]) -> str:
        tech_profile = research_data.get("simulated_tech_profile", {})
        return tech_profile.get("budget_range", "$1K-5K/month")
    
    def _analyze_geography(self, research_data: Dict[str, Any]) -> str:
        return "North America, Europe"  # Simplified
    
    def _find_existing_solutions(self, description: str) -> List[str]:
        return ["Manual processes", "Basic software tools", "Spreadsheets"]  # Simplified
    
    def _identify_solution_gaps(self, description: str) -> List[str]:
        return ["No automation", "Poor integration", "Manual oversight required"]  # Simplified
    
    def _assess_automation_potential(self, description: str) -> float:
        # Higher potential for processes with automation keywords
        automation_keywords = [
            "manual", "repetitive", "data entry", "copy", "paste", 
            "time-consuming", "qualification", "intake", "processing",
            "disconnected", "integration", "reporting", "generation"
        ]
        
        description_lower = description.lower()
        score = sum(1 for keyword in automation_keywords if keyword in description_lower)
        
        # Base score from keyword matches
        base_score = min(score / 3, 1.0)  # Normalize to max 1.0, requiring fewer matches
        
        # Boost score for certain high-automation patterns
        if any(pattern in description_lower for pattern in ["manual", "time-consuming", "disconnected"]):
            base_score = max(base_score, 0.7)  # Ensure minimum viable automation potential
        
        return min(base_score, 1.0)
    
    def _analyze_competition(self, niche: str, research_data: Dict[str, Any]) -> List[str]:
        industry_data = research_data.get("simulated_industry_data", {})
        return industry_data.get("key_players", ["Existing Solution A", "Existing Solution B"])
    
    def _calculate_research_confidence(self, research_data: Dict[str, Any]) -> float:
        # Base confidence on number and quality of data sources
        source_count = len(research_data)
        base_confidence = min(source_count / 5.0, 0.8)  # Max 0.8 base confidence
        
        # Adjust based on data quality indicators
        quality_bonus = 0.0
        if "simulated_industry_data" in research_data:
            quality_bonus += 0.1
        if "simulated_pain_analysis" in research_data:
            quality_bonus += 0.1
        
        return min(base_confidence + quality_bonus, 1.0)
    
    def _estimate_market_size(self, research_data: Dict[str, Any]) -> str:
        industry_data = research_data.get("simulated_industry_data", {})
        return industry_data.get("market_size", "Multi-million dollar market")
    
    def _assess_tech_adoption(self, research_data: Dict[str, Any]) -> str:
        tech_profile = research_data.get("simulated_tech_profile", {})
        return tech_profile.get("automation_readiness", "medium")
    
    # Opportunity mapping utility methods
    def _classify_automation_type(self, pain: PainPoint) -> str:
        if "data" in pain.description.lower():
            return "Data Processing"
        elif "communication" in pain.description.lower():
            return "Communication Workflow"
        elif "report" in pain.description.lower():
            return "Reporting Automation"
        else:
            return "Process Automation"
    
    def _assess_complexity(self, pain: PainPoint) -> str:
        if pain.impact_score > 0.8 and len(pain.gaps) > 3:
            return "High"
        elif pain.impact_score > 0.5:
            return "Medium"
        else:
            return "Low"
    
    def _estimate_roi(self, pain: PainPoint) -> str:
        if pain.impact_score > 0.8:
            return "High ROI (>300% in 12 months)"
        elif pain.impact_score > 0.5:
            return "Medium ROI (150-300% in 12 months)"
        else:
            return "Low ROI (<150% in 12 months)"
    
    def _estimate_implementation_time(self, pain: PainPoint) -> str:
        complexity_map = {
            "High": "6-12 weeks",
            "Medium": "3-6 weeks", 
            "Low": "1-3 weeks"
        }
        complexity = self._assess_complexity(pain)
        return complexity_map.get(complexity, "4-8 weeks")
    
    def _identify_required_integrations(self, pain: PainPoint) -> List[str]:
        integrations = []
        description_lower = pain.description.lower()
        
        if "crm" in description_lower:
            integrations.append("CRM System")
        if "email" in description_lower or "communication" in description_lower:
            integrations.append("Email Platform")
        if "report" in description_lower:
            integrations.append("Reporting Tool")
        if "data" in description_lower:
            integrations.append("Database/Spreadsheet")
        
        return integrations or ["Standard Business Tools"]
    
    def _define_success_metrics(self, pain: PainPoint) -> List[str]:
        return [
            f"Reduce manual effort by {int(pain.automation_potential * 100)}%",
            f"Improve process speed by {int(pain.impact_score * 50) + 25}%",
            "Eliminate human errors in routine tasks",
            "Increase team productivity"
        ]