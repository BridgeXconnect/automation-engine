"""Notion API integration client with database operations support."""

import os
import time
import logging
from typing import Any, Dict, List, Optional
from notion_client import Client, APIErrorCode, APIResponseError
from notion_client.helpers import collect_paginated_api

from ..models.notion import NotionDatabase, NotionBusinessOS
from ..models.package import AutomationPackage

logger = logging.getLogger(__name__)


class NotionClientError(Exception):
    """Custom exception for Notion client operations."""
    pass


class NotionClient:
    """Notion API client wrapper with enhanced functionality.
    
    Provides database operations, error handling, retry logic, and 
    Business OS integration following patterns from ramnes/notion-sdk-py.
    """
    
    def __init__(self, auth_token: Optional[str] = None, max_retries: int = 3, retry_delay: float = 1.0):
        """Initialize Notion client.
        
        Args:
            auth_token: Notion API token (defaults to NOTION_TOKEN env var)
            max_retries: Maximum number of retry attempts
            retry_delay: Base delay between retries in seconds
        """
        token = auth_token or os.environ.get("NOTION_TOKEN")
        if not token:
            raise NotionClientError("NOTION_TOKEN environment variable is required")
        
        self.client = Client(auth=token)
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self._workspace_id: Optional[str] = None
    
    def _retry_with_backoff(self, operation, *args, **kwargs):
        """Execute operation with exponential backoff retry logic."""
        last_error = None
        
        for attempt in range(self.max_retries + 1):
            try:
                return operation(*args, **kwargs)
            except APIResponseError as e:
                last_error = e
                
                # Don't retry certain error types
                if e.code in [APIErrorCode.ObjectNotFound, APIErrorCode.Unauthorized]:
                    raise e
                
                if attempt < self.max_retries:
                    # Exponential backoff with jitter
                    delay = self.retry_delay * (2 ** attempt) * (0.5 + 0.5 * time.time() % 1)
                    logger.warning(f"Notion API error on attempt {attempt + 1}: {e}. Retrying in {delay:.2f}s")
                    time.sleep(delay)
                else:
                    logger.error(f"Max retries ({self.max_retries}) exceeded for Notion operation")
                    raise e
            except Exception as e:
                logger.error(f"Unexpected error in Notion operation: {e}")
                raise NotionClientError(f"Notion operation failed: {e}")
        
        if last_error:
            raise last_error
    
    def get_workspace_id(self) -> str:
        """Get the workspace ID for the authenticated user."""
        if self._workspace_id is None:
            try:
                self._retry_with_backoff(self.client.users.list)
                # The workspace ID is typically part of the user info or can be inferred
                self._workspace_id = "workspace"  # Placeholder - would need actual logic
            except Exception as e:
                logger.error(f"Failed to get workspace ID: {e}")
                self._workspace_id = "unknown"
        
        return self._workspace_id
    
    def create_database(self, parent_page_id: str, database_schema: NotionDatabase) -> str:
        """Create a new database in Notion.
        
        Args:
            parent_page_id: ID of the parent Notion page
            database_schema: Database schema configuration
            
        Returns:
            Created database ID
        """
        try:
            schema = database_schema.to_notion_schema()
            create_payload = {
                "parent": {"type": "page_id", "page_id": parent_page_id},
                **schema
            }
            
            response = self._retry_with_backoff(
                self.client.databases.create,
                **create_payload
            )
            
            database_id = response["id"]
            logger.info(f"Created Notion database: {database_schema.title} (ID: {database_id})")
            
            return database_id
            
        except APIResponseError as e:
            if e.code == APIErrorCode.ObjectNotFound:
                raise NotionClientError(f"Parent page {parent_page_id} not found")
            else:
                raise NotionClientError(f"Failed to create database: {e}")
    
    def query_database(self, database_id: str, filter_criteria: Optional[Dict[str, Any]] = None,
                      sorts: Optional[List[Dict[str, Any]]] = None, 
                      page_size: int = 100) -> List[Dict[str, Any]]:
        """Query database with optional filtering and sorting.
        
        Args:
            database_id: Target database ID
            filter_criteria: Notion API filter object
            sorts: List of sort objects
            page_size: Number of results per page
            
        Returns:
            List of database records
        """
        try:
            query_params: Dict[str, Any] = {"database_id": database_id}
            
            if filter_criteria:
                query_params["filter"] = filter_criteria
            if sorts:
                query_params["sorts"] = sorts
            
            # Use pagination helper to get all results
            all_results = collect_paginated_api(
                self.client.databases.query,
                **query_params
            )
            
            logger.info(f"Retrieved {len(all_results)} records from database {database_id}")
            return all_results
            
        except APIResponseError as e:
            if e.code == APIErrorCode.ObjectNotFound:
                raise NotionClientError(f"Database {database_id} not found")
            else:
                raise NotionClientError(f"Failed to query database: {e}")
    
    def create_page(self, database_id: str, properties: Dict[str, Any], 
                   content_blocks: Optional[List[Dict[str, Any]]] = None) -> str:
        """Create a new page in a database.
        
        Args:
            database_id: Target database ID
            properties: Page properties matching database schema
            content_blocks: Optional page content blocks
            
        Returns:
            Created page ID
        """
        try:
            create_payload: Dict[str, Any] = {
                "parent": {"type": "database_id", "database_id": database_id},
                "properties": properties
            }
            
            if content_blocks:
                create_payload["children"] = content_blocks
            
            response = self._retry_with_backoff(
                self.client.pages.create,
                **create_payload
            )
            
            page_id = response["id"]
            logger.info(f"Created page in database {database_id} (ID: {page_id})")
            
            return page_id
            
        except APIResponseError as e:
            if e.code == APIErrorCode.ObjectNotFound:
                raise NotionClientError(f"Database {database_id} not found")
            else:
                raise NotionClientError(f"Failed to create page: {e}")
    
    def update_page(self, page_id: str, properties: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing page's properties.
        
        Args:
            page_id: Target page ID
            properties: Updated properties
            
        Returns:
            Updated page object
        """
        try:
            response = self._retry_with_backoff(
                self.client.pages.update,
                page_id=page_id,
                properties=properties
            )
            
            logger.info(f"Updated page {page_id}")
            return response
            
        except APIResponseError as e:
            if e.code == APIErrorCode.ObjectNotFound:
                raise NotionClientError(f"Page {page_id} not found")
            else:
                raise NotionClientError(f"Failed to update page: {e}")
    
    def search_databases(self, query: str) -> List[Dict[str, Any]]:
        """Search for databases by name.
        
        Args:
            query: Search query string
            
        Returns:
            List of matching databases
        """
        try:
            response = self._retry_with_backoff(
                self.client.search,
                query=query,
                filter={"value": "database", "property": "object"}
            )
            
            return response.get("results", [])
            
        except APIResponseError as e:
            raise NotionClientError(f"Failed to search databases: {e}")
    
    def get_database_schema(self, database_id: str) -> Dict[str, Any]:
        """Get database schema information.
        
        Args:
            database_id: Target database ID
            
        Returns:
            Database schema object
        """
        try:
            response = self._retry_with_backoff(
                self.client.databases.retrieve,
                database_id=database_id
            )
            
            return response
            
        except APIResponseError as e:
            if e.code == APIErrorCode.ObjectNotFound:
                raise NotionClientError(f"Database {database_id} not found")
            else:
                raise NotionClientError(f"Failed to get database schema: {e}")
    
    def create_business_os(self, parent_page_id: str) -> Dict[str, str]:
        """Create complete Notion Business OS with all databases.
        
        Args:
            parent_page_id: Parent page to create databases under
            
        Returns:
            Dictionary mapping database names to IDs
        """
        logger.info("Creating Notion Business OS databases...")
        
        business_os = NotionBusinessOS.create_default_schema()
        database_ids = {}
        
        try:
            # Create databases that don't depend on relations first
            for name, database in [
                ("library", business_os.library),
                ("components", business_os.components),
                ("clients", business_os.clients)
            ]:
                db_id = self.create_database(parent_page_id, database)
                database_ids[name] = db_id
                database.database_id = db_id
            
            # Update relation IDs and create dependent databases
            business_os.update_relation_ids(database_ids)
            
            # Create automations database (depends on library, clients, deployments)
            automations_id = self.create_database(parent_page_id, business_os.automations)
            database_ids["automations"] = automations_id
            business_os.automations.database_id = automations_id
            
            # Update deployments relation and create
            business_os.update_relation_ids({"automations": automations_id})
            deployments_id = self.create_database(parent_page_id, business_os.deployments)
            database_ids["deployments"] = deployments_id
            business_os.deployments.database_id = deployments_id
            
            logger.info(f"Successfully created Business OS with databases: {list(database_ids.keys())}")
            return database_ids
            
        except Exception as e:
            logger.error(f"Failed to create Business OS: {e}")
            raise NotionClientError(f"Business OS creation failed: {e}")
    
    def create_library_record(self, package: AutomationPackage) -> str:
        """Create a Library database record for an automation package.
        
        Args:
            package: AutomationPackage to create record for
            
        Returns:
            Created page ID
        """
        # Find Library database
        databases = self.search_databases("Library")
        if not databases:
            raise NotionClientError("Library database not found. Create Business OS first.")
        
        library_db_id = databases[0]["id"]
        
        # Convert package to Notion properties format
        properties = {
            "Name": {
                "title": [{"text": {"content": package.name}}]
            },
            "Slug": {
                "rich_text": [{"text": {"content": package.slug}}]
            },
            "Problem Statement": {
                "rich_text": [{"text": {"content": package.problem_statement}}]
            },
            "ROI Notes": {
                "rich_text": [{"text": {"content": package.roi_notes}}]
            },
            "Status": {
                "select": {"name": package.status.value.title()}
            },
            "Version": {
                "rich_text": [{"text": {"content": package.version}}]
            },
            "Last Validated": {
                "date": {"start": package.last_validated.isoformat()}
            }
        }
        
        # Add multi-select properties
        if package.niche_tags:
            properties["Niche Tags"] = {
                "multi_select": [{"name": tag} for tag in package.niche_tags]
            }
        
        if package.dependencies:
            properties["Dependencies"] = {
                "multi_select": [{"name": dep} for dep in package.dependencies]
            }
        
        return self.create_page(library_db_id, properties)
    
    def get_library_record(self, record_id: str) -> Dict[str, Any]:
        """Get a Library database record by ID.
        
        Args:
            record_id: Library record page ID
            
        Returns:
            Page object with properties
        """
        try:
            response = self._retry_with_backoff(
                self.client.pages.retrieve,
                page_id=record_id
            )
            
            return response
            
        except APIResponseError as e:
            if e.code == APIErrorCode.ObjectNotFound:
                raise NotionClientError(f"Library record {record_id} not found")
            else:
                raise NotionClientError(f"Failed to get library record: {e}")
    
    def verify_database_schema(self) -> bool:
        """Verify that all required Business OS databases exist and are properly configured.
        
        Returns:
            True if schema is valid, raises exception otherwise
        """
        required_databases = ["Library", "Automations", "Components", "Clients", "Deployments"]
        
        try:
            for db_name in required_databases:
                results = self.search_databases(db_name)
                if not results:
                    raise NotionClientError(f"Required database '{db_name}' not found")
            
            logger.info("Business OS schema verification successful")
            return True
            
        except Exception as e:
            logger.error(f"Schema verification failed: {e}")
            raise