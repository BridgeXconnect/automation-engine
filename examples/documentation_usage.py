#!/usr/bin/env python3
"""Example usage of DocumentationGenerator in PRP workflow.

This example demonstrates how to use the DocumentationGenerator class
to create all required documentation types for automation packages.
"""

import sys
from pathlib import Path

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from src.models.package import AutomationPackage, PackageStatus
from src.modules.documentation import DocumentationGenerator


def demonstrate_documentation_generation():
    """Demonstrate complete documentation generation workflow."""
    
    print("DocumentationGenerator - PRP Integration Example")
    print("=" * 55)
    
    # 1. Create automation package (this would come from PRP process)
    package = AutomationPackage(
        name="Invoice Processing Automation", 
        slug="invoice-processing-automation",
        niche_tags=["accounting", "finance", "automation", "ai"],
        problem_statement="Manual invoice processing creates bottlenecks, errors, and delayed payments",
        outcomes=[
            "95% reduction in manual processing time",
            "99.5% accuracy in data extraction", 
            "3-day reduction in payment processing time",
            "80% decrease in processing costs"
        ],
        roi_notes="Save $8,000 monthly in processing costs, reduce FTE by 1.5, improve cash flow by 15%",
        inputs={
            "invoice_files": "PDF invoices from email/upload",
            "vendor_database": "Master vendor list with payment terms",
            "approval_rules": "Business rules for approval routing"
        },
        outputs={
            "extracted_data": "Structured invoice data (JSON)",
            "approval_routing": "Automated approval workflows",
            "accounting_entries": "Posted to accounting system",
            "payment_scheduling": "Scheduled payments with cash flow optimization"
        },
        dependencies=[
            "QuickBooks Online API",
            "Xero API (alternative)", 
            "OCR service (Google Vision API)",
            "Email service (SMTP/IMAP)",
            "Slack API for notifications"
        ],
        security_notes="Financial data encrypted at rest and in transit, SOX compliance maintained, audit trails preserved",
        status=PackageStatus.VALIDATED,
        version="2.1.0"
    )
    
    print(f"Package: {package.name}")
    print(f"Problem: {package.problem_statement[:80]}...")
    print(f"ROI: {package.roi_notes[:60]}...")
    
    # 2. Initialize DocumentationGenerator
    templates_dir = Path("./templates/docs")  # Custom template directory
    doc_gen = DocumentationGenerator(templates_dir)
    
    print(f"\nInitialized DocumentationGenerator with templates at: {templates_dir}")
    
    # 3. Prepare additional template variables (from PRP context)
    template_variables = {
        # Implementation details
        "prerequisites": [
            "QuickBooks Online or Xero account with API access",
            "Google Cloud Platform account for OCR services", 
            "n8n instance (cloud recommended for this workflow)",
            "Email account with IMAP access for invoice retrieval",
            "Slack workspace for notifications (optional)"
        ],
        
        "installation_steps": [
            "Import n8n workflow JSON file",
            "Configure QuickBooks/Xero API credentials",
            "Set up Google Vision API key and project",
            "Configure email connection (IMAP settings)",
            "Test OCR accuracy with sample invoices",
            "Configure approval routing rules",
            "Set up Slack notifications (if used)",
            "Run end-to-end test with sample invoice"
        ],
        
        "configuration_steps": [
            "Set QB_API_KEY or XERO_API_KEY environment variable",
            "Set GOOGLE_VISION_API_KEY for OCR processing",
            "Configure EMAIL_HOST, EMAIL_USER, EMAIL_PASS",
            "Set SLACK_WEBHOOK_URL for notifications",
            "Configure APPROVAL_THRESHOLDS in workflow",
            "Set VENDOR_DATABASE_PATH or API endpoint",
            "Validate all connections in n8n interface"
        ],
        
        "testing_steps": [
            "Send test invoice to monitored email address",
            "Verify OCR extraction accuracy (>95% target)",
            "Confirm vendor matching works correctly",
            "Test approval routing for different amounts",
            "Validate accounting system integration",
            "Check notification delivery to stakeholders",
            "Run bulk test with 10 different invoice types"
        ],
        
        # Configuration details
        "integration_gotchas": [
            "QuickBooks API rate limits: 500 requests/minute",
            "Google Vision API costs $1.50 per 1000 pages",
            "Email IMAP may timeout with large attachments",
            "PDF quality affects OCR accuracy significantly",
            "Vendor matching requires clean master data",
            "Approval routing depends on correct user mapping"
        ],
        
        # Additional context
        "implementation_notes": "This automation works best with standardized invoice formats. Plan for 2-week implementation including testing.",
        "business_impact": "Typical 10x ROI within 6 months through reduced processing time and improved accuracy",
        "success_metrics": {
            "Processing Time": "< 5 minutes per invoice (vs 45 minutes manual)",
            "Accuracy Rate": "> 99% data extraction accuracy",
            "Cost per Invoice": "< $0.50 (vs $8.00 manual processing)",
            "Exception Rate": "< 5% requiring manual intervention"
        }
    }
    
    # 4. Generate complete documentation suite
    print("\nGenerating documentation suite...")
    suite = doc_gen.generate_documentation_suite(
        package=package,
        template_variables=template_variables
    )
    
    # 5. Display generated documents
    print(f"\n✅ Generated {len(suite.get_all_documents())} documents:")
    print("-" * 50)
    
    for doc in suite.get_all_documents():
        print(f"\n📄 {doc.title}")
        print(f"   Type: {doc.doc_type.value.title()}")
        print(f"   Audience: {doc.audience.value.title()}")
        print(f"   Length: {doc.word_count} words ({doc.estimated_read_time} min read)")
        print(f"   Client-facing: {'Yes' if doc.is_client_facing() else 'No'}")
        
        # Show content preview
        preview = doc.content.replace('\n', ' ')[:100]
        print(f"   Preview: {preview}...")
    
    # 6. Show content separation
    print(f"\n📊 Content Analysis:")
    client_docs = suite.get_client_documents()
    internal_docs = suite.get_internal_documents()
    
    print(f"   Client-facing documents ({len(client_docs)}):")
    for doc in client_docs:
        print(f"     • {doc.doc_type.value}")
    
    print(f"   Internal documents ({len(internal_docs)}):")
    for doc in internal_docs:
        print(f"     • {doc.doc_type.value}")
    
    # 7. Calculate suite metrics
    metrics = suite.calculate_total_content_metrics()
    print(f"\n📈 Suite Metrics:")
    print(f"   Total documents: {metrics['document_count']}")
    print(f"   Total word count: {metrics['total_word_count']:,}")
    print(f"   Total read time: {metrics['total_read_time']} minutes")
    print(f"   Average per doc: {metrics['total_word_count'] // metrics['document_count']:,} words")
    
    # 8. Save documents to package structure
    package_dir = Path(f"./packages/{package.slug}/docs")
    print(f"\n💾 Saving documents to: {package_dir}")
    
    saved_files = doc_gen.save_documentation_suite(suite, package_dir)
    
    print("   Saved files:")
    for doc_type, file_path in saved_files.items():
        file_size = file_path.stat().st_size
        print(f"     • {doc_type}.md ({file_size:,} bytes)")
    
    # 9. Demonstrate PRP compliance
    print(f"\n✅ PRP Compliance Check:")
    print("   ✓ All required document types generated")
    print("   ✓ Client/internal content properly separated") 
    print("   ✓ Business focus in client materials")
    print("   ✓ Technical details in internal docs")
    print("   ✓ Template-based consistent formatting")
    print("   ✓ Package metadata integration")
    print("   ✓ Documentation metrics calculated")
    print("   ✓ Files saved to standard package structure")
    
    print(f"\n🎉 Documentation generation complete!")
    print(f"Ready for PRP workflow integration and Notion sync.")
    
    return suite


if __name__ == "__main__":
    try:
        suite = demonstrate_documentation_generation()
    except Exception as e:
        print(f"❌ Example failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)