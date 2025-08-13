#!/usr/bin/env python3
"""
Test creating an actual package record in Notion
"""

import sys
import os
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
sys.path.append('src')

from src.integrations.notion_client import NotionClient
from src.models.package import AutomationPackage

def test_package_to_notion():
    """Test creating a package record from our generated package"""
    
    try:
        # Load the generated package
        package_path = "/Users/roymkhabela/context-engineering-intro/packages/automate-manual-lead-intake-and-qualification-proc/metadata.json"
        
        with open(package_path, 'r') as f:
            package_data = json.load(f)
        
        print(f'✅ Loaded package: {package_data["name"]}')
        
        # Create AutomationPackage object
        package = AutomationPackage(**package_data)
        print(f'✅ Created AutomationPackage object')
        
        # Initialize Notion client
        client = NotionClient()
        print('✅ Notion client initialized')
        
        # For demo purposes, let's see what databases exist
        search_results = client.client.search()
        databases = [r for r in search_results['results'] if r['object'] == 'database']
        
        print(f'✅ Found {len(databases)} existing databases in workspace')
        for db in databases[:3]:  # Show first 3
            title = db.get('title', [{}])[0].get('plain_text', 'Untitled')
            print(f'  📊 Database: {title} (ID: {db["id"][:8]}...)')
        
        print('✅ Notion integration test successful!')
        print('📋 Next step: Create Business OS databases or use existing ones')
        
        return True
        
    except Exception as e:
        print(f'❌ Package to Notion test failed: {e}')
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_package_to_notion()
    sys.exit(0 if success else 1)