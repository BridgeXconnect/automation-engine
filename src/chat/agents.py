#!/usr/bin/env python3
"""
Conversational wrapper classes for all Pydantic agents.

Provides a consistent chat interface for interacting with each agent,
with session state management and data passing capabilities.
"""

import json
import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List, Optional, Type
from datetime import datetime

from ..modules.niche_research import NicheResearcher
from ..modules.opportunity_mapping import OpportunityMapper  
from ..modules.assembly import WorkflowAssembler
from ..modules.validation import WorkflowValidator
from ..modules.documentation import DocumentationGenerator
from ..modules.package_generator import PackageGenerator

logger = logging.getLogger(__name__)


class ChatSession:
    """Manages conversation state across agents."""
    
    def __init__(self, session_id: str = None):
        self.session_id = session_id or f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.context: Dict[str, Any] = {}
        self.history: List[Dict[str, Any]] = []
        self.current_agent: Optional[str] = None
        
    def add_message(self, agent: str, role: str, content: str, data: Any = None):
        """Add a message to the conversation history."""
        message = {
            "timestamp": datetime.now().isoformat(),
            "agent": agent,
            "role": role,  # 'user' or 'agent'
            "content": content,
            "data": data
        }
        self.history.append(message)
        
    def set_context(self, key: str, value: Any):
        """Store data in session context for agent sharing."""
        self.context[key] = value
        
    def get_context(self, key: str, default: Any = None):
        """Retrieve data from session context."""
        return self.context.get(key, default)
        
    def save_session(self, session_dir: Path):
        """Save session state to disk."""
        session_dir.mkdir(exist_ok=True)
        session_file = session_dir / f"{self.session_id}.json"
        
        session_data = {
            "session_id": self.session_id,
            "context": self.context,
            "history": self.history,
            "current_agent": self.current_agent
        }
        
        with open(session_file, 'w') as f:
            json.dump(session_data, f, indent=2, default=str)
            
        logger.info(f"Session saved: {session_file}")
        
    @classmethod
    def load_session(cls, session_file: Path) -> "ChatSession":
        """Load session state from disk."""
        with open(session_file) as f:
            data = json.load(f)
            
        session = cls(data["session_id"])
        session.context = data.get("context", {})
        session.history = data.get("history", [])
        session.current_agent = data.get("current_agent")
        
        logger.info(f"Session loaded: {session_file}")
        return session


class BaseChatAgent(ABC):
    """Base class for all conversational agents."""
    
    def __init__(self, session: ChatSession):
        self.session = session
        self.agent_name = self.__class__.__name__.replace('Chat', '')
        
    @abstractmethod
    def get_greeting(self) -> str:
        """Return agent's greeting message."""
        pass
        
    @abstractmethod
    def process_input(self, user_input: str) -> Dict[str, Any]:
        """Process user input and return response."""
        pass
        
    @abstractmethod
    def get_help(self) -> str:
        """Return help text for this agent."""
        pass
        
    def log_interaction(self, user_input: str, response: Dict[str, Any]):
        """Log the interaction to session history."""
        self.session.add_message(self.agent_name, "user", user_input)
        self.session.add_message(
            self.agent_name, 
            "agent", 
            response.get("message", ""), 
            response.get("data")
        )


class ChatNicheResearcher(BaseChatAgent):
    """Conversational wrapper for NicheResearcher agent."""
    
    def __init__(self, session: ChatSession, research_timeout: int = 30):
        super().__init__(session)
        self.researcher = NicheResearcher(research_timeout=research_timeout)
        
    def get_greeting(self) -> str:
        return """👋 Hi! I'm the Niche Research Agent.

I specialize in researching business niches to identify pain points and automation opportunities.

**What I can help you with:**
• Research any business niche or industry
• Identify key pain points and challenges  
• Discover automation opportunities
• Assess market size and tech adoption
• Analyze research confidence scores

**Commands:**
• `research <niche_keyword>` - Research a specific niche
• `status` - Show current research data
• `help` - Show this message
• `switch` - Switch to another agent
• `quit` - Exit chat

What niche would you like me to research?"""

    def process_input(self, user_input: str) -> Dict[str, Any]:
        """Process user input for niche research."""
        try:
            parts = user_input.strip().split()
            command = parts[0].lower() if parts else ""
            
            if command == "help":
                return {"message": self.get_help()}
                
            elif command == "status":
                niche_data = self.session.get_context("niche_brief")
                if niche_data:
                    return {
                        "message": f"""📊 **Current Research Status:**

**Niche:** {niche_data.niche_name}
**Confidence:** {niche_data.research_confidence:.1%}
**Market Size:** {niche_data.market_size}
**Tech Adoption:** {niche_data.technology_adoption}

**Pain Points Found:** {len(niche_data.pain_points)}
**Opportunities Found:** {len(niche_data.opportunities)}

Use `switch opportunity` to work with the Opportunity Mapper next!""",
                        "data": niche_data
                    }
                else:
                    return {"message": "No research data available. Research a niche first using `research <keyword>`."}
                    
            elif command == "research":
                if len(parts) < 2:
                    return {"message": "Please specify a niche keyword: `research <keyword>`"}
                    
                niche_keyword = " ".join(parts[1:])
                
                # Perform research
                niche_brief = self.researcher.research_niche(niche_keyword)
                
                # Store in session context for other agents
                self.session.set_context("niche_brief", niche_brief)
                self.session.set_context("last_niche_keyword", niche_keyword)
                
                # Format response
                response_msg = f"""✅ **Research completed for '{niche_keyword}'**

📊 **Overview:**
• Confidence Score: {niche_brief.research_confidence:.1%}
• Market Size: {niche_brief.market_size}
• Tech Adoption: {niche_brief.technology_adoption}

🎯 **Top Pain Points:**"""
                
                for i, pain in enumerate(niche_brief.pain_points[:3], 1):
                    response_msg += f"\n{i}. {pain['description']}"
                    response_msg += f"\n   Impact: {pain['impact_score']:.2f} | Automation Potential: {pain['automation_potential']:.1%}"
                
                response_msg += f"\n\n🚀 **Automation Opportunities:**"
                for i, opp in enumerate(niche_brief.opportunities[:3], 1):
                    response_msg += f"\n{i}. {opp['title']}"
                    response_msg += f"\n   Complexity: {opp['complexity']} | ROI: {opp['roi_estimate']}"
                
                response_msg += f"\n\n💡 **Next Steps:**\n• Use `switch opportunity` to map these into packages\n• Use `status` to review this data anytime"
                
                return {
                    "message": response_msg,
                    "data": niche_brief
                }
                
            else:
                return {
                    "message": f"I don't understand '{user_input}'. Type `help` for available commands."
                }
                
        except Exception as e:
            logger.error(f"NicheResearcher error: {e}", exc_info=True)
            return {
                "message": f"❌ Research failed: {str(e)}\n\nPlease try again or type `help` for available commands."
            }
    
    def get_help(self) -> str:
        return self.get_greeting()


class ChatOpportunityMapper(BaseChatAgent):
    """Conversational wrapper for OpportunityMapper agent."""
    
    def __init__(self, session: ChatSession):
        super().__init__(session)
        self.mapper = OpportunityMapper()
        
    def get_greeting(self) -> str:
        return """🎯 Hi! I'm the Opportunity Mapping Agent.

I take niche research data and convert it into actionable automation opportunities with detailed ROI analysis.

**What I can help you with:**
• Map pain points to automation opportunities
• Calculate ROI estimates and risk assessments
• Prioritize opportunities by impact and feasibility
• Generate detailed opportunity specifications

**Commands:**
• `map` - Map current niche research to opportunities
• `opportunities` - List current opportunities
• `detail <number>` - Get detailed info on opportunity
• `help` - Show this message
• `switch` - Switch to another agent
• `quit` - Exit chat

Do you have niche research data ready to map?"""

    def process_input(self, user_input: str) -> Dict[str, Any]:
        """Process user input for opportunity mapping."""
        try:
            parts = user_input.strip().split()
            command = parts[0].lower() if parts else ""
            
            if command == "help":
                return {"message": self.get_help()}
                
            elif command == "opportunities":
                opportunities = self.session.get_context("opportunities", [])
                if opportunities:
                    response_msg = f"📋 **Current Opportunities ({len(opportunities)}):**\n\n"
                    for i, opp in enumerate(opportunities, 1):
                        response_msg += f"**{i}. {opp.title}**\n"
                        response_msg += f"   Priority: {opp.priority_score:.2f} | "
                        response_msg += f"ROI: ${opp.roi_estimate.get('three_year_value', 0):,.0f}\n"
                        response_msg += f"   Risk: {opp.risk_assessment.get('overall_risk', 0):.1%}\n\n"
                    
                    response_msg += "Use `detail <number>` for more info on any opportunity!"
                    return {"message": response_msg}
                else:
                    return {"message": "No opportunities mapped yet. Use `map` to create opportunities from research data."}
                    
            elif command == "detail":
                if len(parts) < 2:
                    return {"message": "Please specify opportunity number: `detail <number>`"}
                    
                try:
                    opp_num = int(parts[1]) - 1
                    opportunities = self.session.get_context("opportunities", [])
                    
                    if 0 <= opp_num < len(opportunities):
                        opp = opportunities[opp_num]
                        
                        response_msg = f"""📋 **Detailed Opportunity Analysis**

**{opp.title}**

🎯 **Problem Statement:**
{opp.problem_statement}

💰 **ROI Analysis:**
• 3-Year Value: ${opp.roi_estimate.get('three_year_value', 0):,.0f}
• Payback Period: {opp.roi_estimate.get('payback_period', 'N/A')} months
• Annual Savings: ${opp.roi_estimate.get('annual_savings', 0):,.0f}

⚠️ **Risk Assessment:**
• Overall Risk: {opp.risk_assessment.get('overall_risk', 0):.1%}
• Technical Risk: {opp.risk_assessment.get('technical_risk', 'N/A')}
• Business Risk: {opp.risk_assessment.get('business_risk', 'N/A')}

🔧 **Implementation:**
• Complexity: {opp.implementation_complexity}
• Priority Score: {opp.priority_score:.2f}

📊 **Inputs:** {', '.join(opp.inputs)}
📤 **Outputs:** {', '.join(opp.outputs)}

💡 **Next:** Use `switch assembly` to build this into a workflow!"""
                        
                        return {"message": response_msg, "data": opp}
                    else:
                        return {"message": f"Opportunity {parts[1]} not found. Use `opportunities` to see available options."}
                        
                except ValueError:
                    return {"message": "Please provide a valid number: `detail <number>`"}
                    
            elif command == "map":
                niche_brief = self.session.get_context("niche_brief")
                if not niche_brief:
                    return {
                        "message": "No niche research data found. Please use the Niche Research agent first!\n\nUse `switch niche` to go back and research a niche."
                    }
                
                # Map opportunities
                opportunities = self.mapper.map_opportunities(niche_brief)
                
                # Store in session context
                self.session.set_context("opportunities", opportunities)
                
                response_msg = f"✅ **Opportunity mapping completed!**\n\n"
                response_msg += f"📊 **{len(opportunities)} opportunities identified:**\n\n"
                
                for i, opp in enumerate(opportunities[:5], 1):
                    response_msg += f"**{i}. {opp.title}**\n"
                    response_msg += f"   Priority: {opp.priority_score:.2f} | "
                    response_msg += f"ROI: ${opp.roi_estimate.get('three_year_value', 0):,.0f}\n"
                    response_msg += f"   Risk: {opp.risk_assessment.get('overall_risk', 0):.1%}\n\n"
                
                response_msg += "💡 **Next Steps:**\n"
                response_msg += "• Use `detail <number>` for detailed analysis\n"
                response_msg += "• Use `switch assembly` to build workflows\n"
                response_msg += "• Use `opportunities` to see this list again"
                
                return {
                    "message": response_msg,
                    "data": opportunities
                }
                
            else:
                return {
                    "message": f"I don't understand '{user_input}'. Type `help` for available commands."
                }
                
        except Exception as e:
            logger.error(f"OpportunityMapper error: {e}", exc_info=True)
            return {
                "message": f"❌ Opportunity mapping failed: {str(e)}\n\nPlease try again or type `help` for available commands."
            }
    
    def get_help(self) -> str:
        return self.get_greeting()


class ChatWorkflowAssembler(BaseChatAgent):
    """Conversational wrapper for WorkflowAssembler agent."""
    
    def __init__(self, session: ChatSession, vault_path: str = "automation_vault"):
        super().__init__(session)
        self.assembler = WorkflowAssembler(Path(vault_path))
        
    def get_greeting(self) -> str:
        available_workflows = self.assembler.get_available_workflows()
        workflow_count = len(available_workflows)
        
        return f"""🔧 Hi! I'm the Workflow Assembly Agent.

I take automation opportunities and build them into working n8n workflows using templates from the automation vault.

**What I can help you with:**
• Assemble workflows from vault templates
• Customize workflows for specific opportunities  
• List available workflow templates ({workflow_count} found)
• Generate n8n-compatible workflow JSON

**Commands:**
• `templates` - List available workflow templates
• `assemble <opportunity_number>` - Build workflow for opportunity
• `workflows` - Show assembled workflows
• `help` - Show this message
• `switch` - Switch to another agent
• `quit` - Exit chat

Ready to build some workflows?"""

    def process_input(self, user_input: str) -> Dict[str, Any]:
        """Process user input for workflow assembly."""
        try:
            parts = user_input.strip().split()
            command = parts[0].lower() if parts else ""
            
            if command == "help":
                return {"message": self.get_help()}
                
            elif command == "templates":
                available_workflows = self.assembler.get_available_workflows()
                
                if available_workflows:
                    response_msg = f"📋 **Available Workflow Templates ({len(available_workflows)}):**\n\n"
                    for i, template in enumerate(available_workflows, 1):
                        response_msg += f"{i}. {template}\n"
                    
                    response_msg += "\n💡 These templates can be customized for your opportunities!"
                else:
                    response_msg = "No workflow templates found in automation vault.\n\n"
                    response_msg += "Please ensure the vault directory contains n8n workflow files."
                    
                return {"message": response_msg}
                
            elif command == "workflows":
                assembled_workflows = self.session.get_context("assembled_workflows", [])
                
                if assembled_workflows:
                    response_msg = f"🔧 **Assembled Workflows ({len(assembled_workflows)}):**\n\n"
                    for i, workflow in enumerate(assembled_workflows, 1):
                        response_msg += f"**{i}. {workflow.name}**\n"
                        response_msg += f"   Nodes: {len(workflow.nodes)} | "
                        response_msg += f"Connections: {len(workflow.connections)}\n"
                        response_msg += f"   For: {workflow.description[:50]}...\n\n"
                    
                    response_msg += "💡 Use `switch validation` to validate these workflows!"
                else:
                    response_msg = "No workflows assembled yet.\n\n"
                    response_msg += "Use `assemble <opportunity_number>` to build workflows from opportunities."
                    
                return {"message": response_msg}
                
            elif command == "assemble":
                if len(parts) < 2:
                    return {"message": "Please specify opportunity number: `assemble <opportunity_number>`"}
                    
                try:
                    opp_num = int(parts[1]) - 1
                    opportunities = self.session.get_context("opportunities", [])
                    
                    if not opportunities:
                        return {
                            "message": "No opportunities found. Please map opportunities first!\n\nUse `switch opportunity` to create opportunities."
                        }
                    
                    if 0 <= opp_num < len(opportunities):
                        opportunity = opportunities[opp_num]
                        
                        # Get available workflows
                        available_workflows = self.assembler.get_available_workflows()
                        
                        if not available_workflows:
                            return {
                                "message": "No workflow templates available in vault.\n\nPlease ensure automation_vault contains n8n workflow files."
                            }
                        
                        # Use first available workflow for demo (could be made smarter)
                        selected_templates = available_workflows[:2]  # Use first 2 templates
                        
                        # Assemble workflow
                        assembled_workflow = self.assembler.assemble_workflows(selected_templates, opportunity)
                        
                        # Store in session
                        assembled_workflows = self.session.get_context("assembled_workflows", [])
                        assembled_workflows.append(assembled_workflow)
                        self.session.set_context("assembled_workflows", assembled_workflows)
                        
                        response_msg = f"""✅ **Workflow assembled successfully!**

🔧 **Workflow Details:**
• Name: {assembled_workflow.name}
• Description: {assembled_workflow.description}
• Nodes: {len(assembled_workflow.nodes)}
• Connections: {len(assembled_workflow.connections)}

📋 **Built for Opportunity:**
{opportunity.title}

💡 **Next Steps:**
• Use `switch validation` to validate this workflow
• Use `workflows` to see all assembled workflows
• Use `switch docs` to generate documentation"""
                        
                        return {
                            "message": response_msg,
                            "data": assembled_workflow
                        }
                    else:
                        return {"message": f"Opportunity {parts[1]} not found. Use `switch opportunity` then `opportunities` to see available options."}
                        
                except ValueError:
                    return {"message": "Please provide a valid number: `assemble <opportunity_number>`"}
                    
            else:
                return {
                    "message": f"I don't understand '{user_input}'. Type `help` for available commands."
                }
                
        except Exception as e:
            logger.error(f"WorkflowAssembler error: {e}", exc_info=True)
            return {
                "message": f"❌ Workflow assembly failed: {str(e)}\n\nPlease try again or type `help` for available commands."
            }
    
    def get_help(self) -> str:
        return self.get_greeting()


class ChatWorkflowValidator(BaseChatAgent):
    """Conversational wrapper for WorkflowValidator agent."""
    
    def __init__(self, session: ChatSession):
        super().__init__(session)
        self.validator = WorkflowValidator()
        
    def get_greeting(self) -> str:
        return """✅ Hi! I'm the Workflow Validation Agent.

I validate assembled workflows to ensure they meet quality standards and will work correctly when deployed.

**What I can help you with:**
• Validate workflow structure and connections
• Check for security and performance issues
• Generate detailed validation reports
• Ensure compliance with best practices

**Commands:**
• `validate` - Validate all assembled workflows
• `validate <number>` - Validate specific workflow
• `reports` - Show validation reports
• `help` - Show this message  
• `switch` - Switch to another agent
• `quit` - Exit chat

Ready to validate your workflows?"""

    def process_input(self, user_input: str) -> Dict[str, Any]:
        """Process user input for workflow validation."""
        try:
            parts = user_input.strip().split()
            command = parts[0].lower() if parts else ""
            
            if command == "help":
                return {"message": self.get_help()}
                
            elif command == "reports":
                validation_reports = self.session.get_context("validation_reports", [])
                
                if validation_reports:
                    response_msg = f"📊 **Validation Reports ({len(validation_reports)}):**\n\n"
                    for i, report in enumerate(validation_reports, 1):
                        summary = report['summary']
                        status = "✅ PASS" if summary['overall_status'] == 'PASS' else "❌ FAIL"
                        response_msg += f"**{i}. {report.get('workflow_name', f'Workflow {i}')}** {status}\n"
                        response_msg += f"   Passed: {summary['passed']}/{summary['total_checks']} "
                        response_msg += f"({summary['success_rate']:.1%})\n\n"
                    
                    response_msg += "💡 Use `validate` to run validation again!"
                else:
                    response_msg = "No validation reports available.\n\n"
                    response_msg += "Use `validate` to validate your assembled workflows."
                    
                return {"message": response_msg}
                
            elif command == "validate":
                assembled_workflows = self.session.get_context("assembled_workflows", [])
                
                if not assembled_workflows:
                    return {
                        "message": "No workflows to validate. Please assemble workflows first!\n\nUse `switch assembly` to create workflows."
                    }
                
                # Check if validating specific workflow
                if len(parts) > 1:
                    try:
                        workflow_num = int(parts[1]) - 1
                        if 0 <= workflow_num < len(assembled_workflows):
                            workflow = assembled_workflows[workflow_num]
                            workflows_to_validate = [workflow]
                        else:
                            return {"message": f"Workflow {parts[1]} not found. Use `switch assembly` then `workflows` to see available workflows."}
                    except ValueError:
                        return {"message": "Please provide a valid number: `validate <number>`"}
                else:
                    workflows_to_validate = assembled_workflows
                
                # Validate workflows
                validation_reports = []
                response_msg = f"🔍 **Validating {len(workflows_to_validate)} workflow(s)...**\n\n"
                
                for i, workflow in enumerate(workflows_to_validate, 1):
                    validation_results = self.validator.validate_workflow(workflow)
                    validation_report = self.validator.generate_validation_report(validation_results)
                    validation_report['workflow_name'] = workflow.name
                    validation_reports.append(validation_report)
                    
                    # Format results
                    summary = validation_report['summary']
                    status = "✅ PASS" if summary['overall_status'] == 'PASS' else "❌ FAIL"
                    
                    response_msg += f"**{i}. {workflow.name}** {status}\n"
                    response_msg += f"   Checks: {summary['passed']}/{summary['total_checks']} passed "
                    response_msg += f"({summary['success_rate']:.1%})\n"
                    
                    if summary['overall_status'] == 'FAIL':
                        response_msg += "   Issues found:\n"
                        for level, data in validation_report['by_level'].items():
                            if data['failed'] > 0:
                                response_msg += f"     • {level.title()}: {data['failed']} failures\n"
                    
                    response_msg += "\n"
                
                # Store reports in session
                existing_reports = self.session.get_context("validation_reports", [])
                existing_reports.extend(validation_reports)
                self.session.set_context("validation_reports", existing_reports)
                
                response_msg += "💡 **Next Steps:**\n"
                response_msg += "• Use `reports` to review detailed validation results\n"
                response_msg += "• Use `switch docs` to generate documentation for validated workflows\n" 
                response_msg += "• Fix any validation issues before deployment"
                
                return {
                    "message": response_msg,
                    "data": validation_reports
                }
                
            else:
                return {
                    "message": f"I don't understand '{user_input}'. Type `help` for available commands."
                }
                
        except Exception as e:
            logger.error(f"WorkflowValidator error: {e}", exc_info=True)
            return {
                "message": f"❌ Validation failed: {str(e)}\n\nPlease try again or type `help` for available commands."
            }
    
    def get_help(self) -> str:
        return self.get_greeting()


class ChatDocumentationGenerator(BaseChatAgent):
    """Conversational wrapper for DocumentationGenerator agent."""
    
    def __init__(self, session: ChatSession):
        super().__init__(session)
        self.generator = DocumentationGenerator()
        
    def get_greeting(self) -> str:
        return """📝 Hi! I'm the Documentation Generation Agent.

I create comprehensive documentation for your automation packages including implementation guides, runbooks, and client materials.

**What I can help you with:**
• Generate implementation guides with screenshots
• Create configuration and setup documentation
• Write runbooks for monitoring and troubleshooting
• Produce client-facing one-pagers and materials

**Commands:**
• `generate` - Generate documentation for validated workflows
• `docs` - List generated documentation
• `preview <doc_type>` - Preview specific documentation
• `help` - Show this message
• `switch` - Switch to another agent  
• `quit` - Exit chat

Ready to document your automations?"""

    def process_input(self, user_input: str) -> Dict[str, Any]:
        """Process user input for documentation generation."""
        try:
            parts = user_input.strip().split()
            command = parts[0].lower() if parts else ""
            
            if command == "help":
                return {"message": self.get_help()}
                
            elif command == "docs":
                generated_docs = self.session.get_context("generated_docs", {})
                
                if generated_docs:
                    response_msg = f"📚 **Generated Documentation ({len(generated_docs)} sets):**\n\n"
                    for i, (workflow_name, docs) in enumerate(generated_docs.items(), 1):
                        response_msg += f"**{i}. {workflow_name}**\n"
                        response_msg += f"   Documents: {', '.join(docs.keys())}\n\n"
                    
                    response_msg += "💡 Use `preview <doc_type>` to see document content!"
                else:
                    response_msg = "No documentation generated yet.\n\n"
                    response_msg += "Use `generate` to create documentation for your workflows."
                    
                return {"message": response_msg}
                
            elif command == "preview":
                if len(parts) < 2:
                    return {"message": "Please specify document type: `preview <doc_type>`\n\nAvailable types: implementation, configuration, runbook, sop, loom-outline, client-one-pager"}
                    
                doc_type = parts[1].lower()
                generated_docs = self.session.get_context("generated_docs", {})
                
                if not generated_docs:
                    return {"message": "No documentation available. Use `generate` to create documentation first."}
                
                # Find document across all workflow docs
                found_doc = None
                for workflow_name, docs in generated_docs.items():
                    if doc_type in docs:
                        found_doc = docs[doc_type]
                        break
                
                if found_doc:
                    # Truncate for preview
                    preview = found_doc[:500] + "..." if len(found_doc) > 500 else found_doc
                    response_msg = f"📄 **{doc_type.title()} Documentation Preview:**\n\n```\n{preview}\n```\n\n"
                    response_msg += "💡 Full documentation is stored in session context!"
                    return {"message": response_msg}
                else:
                    return {"message": f"Document type '{doc_type}' not found.\n\nAvailable types: implementation, configuration, runbook, sop, loom-outline, client-one-pager"}
                    
            elif command == "generate":
                assembled_workflows = self.session.get_context("assembled_workflows", [])
                validation_reports = self.session.get_context("validation_reports", [])
                opportunities = self.session.get_context("opportunities", [])
                niche_brief = self.session.get_context("niche_brief")
                
                if not assembled_workflows:
                    return {
                        "message": "No workflows available for documentation.\n\nPlease assemble workflows first using `switch assembly`."
                    }
                
                response_msg = f"📝 **Generating documentation for {len(assembled_workflows)} workflow(s)...**\n\n"
                generated_docs = {}
                
                for i, workflow in enumerate(assembled_workflows):
                    # Find corresponding opportunity and validation report
                    opportunity = opportunities[i] if i < len(opportunities) else None
                    validation_report = validation_reports[i] if i < len(validation_reports) else None
                    
                    if opportunity and niche_brief:
                        # Generate complete documentation
                        docs = self.generator.generate_complete_documentation(
                            opportunity, workflow, validation_report, niche_brief
                        )
                        
                        generated_docs[workflow.name] = docs
                        
                        response_msg += f"✅ **{workflow.name}**\n"
                        response_msg += f"   Generated: {', '.join(docs.keys())}\n\n"
                    else:
                        response_msg += f"⚠️ **{workflow.name}**\n"
                        response_msg += f"   Missing opportunity or niche data for full documentation\n\n"
                
                # Store in session
                self.session.set_context("generated_docs", generated_docs)
                
                response_msg += "💡 **Next Steps:**\n"
                response_msg += "• Use `docs` to see all generated documentation\n"
                response_msg += "• Use `preview <doc_type>` to review specific documents\n"
                response_msg += "• Use `switch package` to create final packages"
                
                return {
                    "message": response_msg,
                    "data": generated_docs
                }
                
            else:
                return {
                    "message": f"I don't understand '{user_input}'. Type `help` for available commands."
                }
                
        except Exception as e:
            logger.error(f"DocumentationGenerator error: {e}", exc_info=True)
            return {
                "message": f"❌ Documentation generation failed: {str(e)}\n\nPlease try again or type `help` for available commands."
            }
    
    def get_help(self) -> str:
        return self.get_greeting()


class ChatPackageGenerator(BaseChatAgent):
    """Conversational wrapper for PackageGenerator agent."""
    
    def __init__(self, session: ChatSession):
        super().__init__(session)
        self.generator = PackageGenerator()
        
    def get_greeting(self) -> str:
        return """📦 Hi! I'm the Package Generation Agent.

I create final automation packages with all metadata, workflows, documentation, and deployment artifacts ready for production use.

**What I can help you with:**
• Generate complete automation packages
• Create metadata.json with all package information
• Bundle workflows, docs, and test fixtures
• Prepare packages for deployment and distribution

**Commands:**
• `generate` - Generate packages from session data
• `packages` - List generated packages  
• `package <number>` - Show detailed package info
• `help` - Show this message
• `switch` - Switch to another agent
• `quit` - Exit chat

Ready to package your automations?"""

    def process_input(self, user_input: str) -> Dict[str, Any]:
        """Process user input for package generation."""
        try:
            parts = user_input.strip().split()
            command = parts[0].lower() if parts else ""
            
            if command == "help":
                return {"message": self.get_help()}
                
            elif command == "packages":
                generated_packages = self.session.get_context("generated_packages", [])
                
                if generated_packages:
                    response_msg = f"📦 **Generated Packages ({len(generated_packages)}):**\n\n"
                    for i, package in enumerate(generated_packages, 1):
                        response_msg += f"**{i}. {package.name}**\n"
                        response_msg += f"   Slug: {package.slug}\n"
                        response_msg += f"   ROI: {package.roi_notes}\n"
                        response_msg += f"   Status: {package.status}\n\n"
                    
                    response_msg += "💡 Use `package <number>` for detailed package information!"
                else:
                    response_msg = "No packages generated yet.\n\n"
                    response_msg += "Use `generate` to create packages from your session data."
                    
                return {"message": response_msg}
                
            elif command == "package":
                if len(parts) < 2:
                    return {"message": "Please specify package number: `package <number>`"}
                    
                try:
                    pkg_num = int(parts[1]) - 1
                    generated_packages = self.session.get_context("generated_packages", [])
                    
                    if 0 <= pkg_num < len(generated_packages):
                        package = generated_packages[pkg_num]
                        
                        response_msg = f"""📦 **Package Details**

**{package.name}**

🏷️ **Metadata:**
• Slug: {package.slug}  
• Status: {package.status}
• Version: {package.version}
• Last Validated: {package.last_validated}

🎯 **Problem & Solution:**
{package.problem_statement}

💰 **ROI Information:**
{package.roi_notes}

📊 **Technical Details:**
• Inputs: {', '.join(package.inputs)}
• Outputs: {', '.join(package.outputs)}
• Dependencies: {', '.join(package.dependencies)}

🔒 **Security:**
{package.security_notes}

🏷️ **Niche Tags:** {', '.join(package.niche_tags)}

✅ **Ready for deployment!**"""
                        
                        return {"message": response_msg, "data": package}
                    else:
                        return {"message": f"Package {parts[1]} not found. Use `packages` to see available packages."}
                        
                except ValueError:
                    return {"message": "Please provide a valid number: `package <number>`"}
                    
            elif command == "generate":
                assembled_workflows = self.session.get_context("assembled_workflows", [])
                opportunities = self.session.get_context("opportunities", [])
                validation_reports = self.session.get_context("validation_reports", [])
                niche_brief = self.session.get_context("niche_brief")
                
                if not assembled_workflows or not opportunities:
                    return {
                        "message": "Missing required data for package generation.\n\nPlease ensure you have:\n• Assembled workflows (`switch assembly`)\n• Mapped opportunities (`switch opportunity`)"
                    }
                
                response_msg = f"📦 **Generating {len(assembled_workflows)} package(s)...**\n\n"
                generated_packages = []
                
                for i, workflow in enumerate(assembled_workflows):
                    opportunity = opportunities[i] if i < len(opportunities) else opportunities[0]
                    validation_report = validation_reports[i] if i < len(validation_reports) else None
                    
                    # Generate package
                    package = self.generator.generate_package(
                        opportunity=opportunity,
                        workflow=workflow,
                        niche_brief=niche_brief,
                        validation_report=validation_report
                    )
                    
                    generated_packages.append(package)
                    
                    response_msg += f"✅ **{package.name}**\n"
                    response_msg += f"   Slug: {package.slug}\n"
                    response_msg += f"   ROI: {package.roi_notes[:60]}...\n"
                    response_msg += f"   Status: {package.status}\n\n"
                
                # Store in session
                self.session.set_context("generated_packages", generated_packages)
                
                response_msg += "🎉 **Package generation completed!**\n\n"
                response_msg += "💡 **Next Steps:**\n"
                response_msg += "• Use `packages` to review all generated packages\n"
                response_msg += "• Use `package <number>` for detailed package information\n"
                response_msg += "• Packages are ready for deployment and distribution!"
                
                return {
                    "message": response_msg,
                    "data": generated_packages
                }
                
            else:
                return {
                    "message": f"I don't understand '{user_input}'. Type `help` for available commands."
                }
                
        except Exception as e:
            logger.error(f"PackageGenerator error: {e}", exc_info=True)
            return {
                "message": f"❌ Package generation failed: {str(e)}\n\nPlease try again or type `help` for available commands."
            }
    
    def get_help(self) -> str:
        return self.get_greeting()


# Agent registry for easy lookup
AGENT_REGISTRY = {
    'niche': ChatNicheResearcher,
    'opportunity': ChatOpportunityMapper,
    'assembly': ChatWorkflowAssembler,
    'validation': ChatWorkflowValidator,  
    'docs': ChatDocumentationGenerator,
    'package': ChatPackageGenerator,
}

AGENT_NAMES = {
    'niche': 'Niche Research Agent',
    'opportunity': 'Opportunity Mapping Agent', 
    'assembly': 'Workflow Assembly Agent',
    'validation': 'Workflow Validation Agent',
    'docs': 'Documentation Generator Agent',
    'package': 'Package Generation Agent',
}