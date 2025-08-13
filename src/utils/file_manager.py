"""File management utilities for package creation and organization."""

import json
import logging
import shutil
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class FileManagerError(Exception):
    """Custom exception for file management operations."""
    pass

class PackageFileManager:
    """PackageFileManager following CLAUDE.md directory structure.
    
    Handles directory creation, cross-platform paths, cleanup/backup,
    and enforces the standard package structure:
    
    /packages/<slug>/
      workflows/     → n8n JSON exports
      docs/          → implementation.md, configuration.md, runbook.md, etc.
      tests/         → fixtures, happy-path script, failure cases  
      metadata.json  → tags, niche, ROI notes, inputs, outputs, dependencies
    """
    
    def __init__(self, base_output_dir: Path):
        """Initialize file manager with base output directory.
        
        Args:
            base_output_dir: Base directory for all packages
        """
        self.base_dir = Path(base_output_dir).resolve()
        self.base_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Initialized PackageFileManager at {self.base_dir}")
    
    def create_package_directory(self, package_slug: str) -> Path:
        """Create standard package directory structure.
        
        Args:
            package_slug: Unique package identifier
            
        Returns:
            Path to created package directory
        """
        package_dir = self.base_dir / package_slug
        
        try:
            # Create main package directory
            package_dir.mkdir(exist_ok=True)
            logger.info(f"Created package directory: {package_dir}")
            
            # Create standard subdirectories per CLAUDE.md
            subdirs = ['workflows', 'docs', 'tests']
            for subdir in subdirs:
                (package_dir / subdir).mkdir(exist_ok=True)
                logger.debug(f"Created subdirectory: {package_dir / subdir}")
            
            # Create placeholder files to maintain directory structure
            self._create_placeholder_files(package_dir)
            
            return package_dir
            
        except Exception as e:
            raise FileManagerError(f"Failed to create package directory '{package_slug}': {e}")
    
    def _create_placeholder_files(self, package_dir: Path) -> None:
        """Create placeholder files to maintain directory structure."""
        placeholders = {
            'docs/README.md': '# Documentation\n\nDocumentation files will be generated here.',
            'tests/README.md': '# Tests\n\nTest fixtures and scripts will be placed here.',
            'workflows/README.md': '# Workflows\n\nn8n workflow exports will be saved here.'
        }
        
        for rel_path, content in placeholders.items():
            file_path = package_dir / rel_path
            if not file_path.exists():
                file_path.write_text(content, encoding='utf-8')
    
    def save_json(self, data: Dict[str, Any], file_path: Path) -> None:
        """Save data as formatted JSON file.
        
        Args:
            data: Data to save
            file_path: Target file path
        """
        try:
            # Ensure parent directory exists
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write JSON with proper formatting
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False, default=str)
            
            logger.info(f"Saved JSON file: {file_path}")
            
        except Exception as e:
            raise FileManagerError(f"Failed to save JSON to '{file_path}': {e}")
    
    def save_text(self, content: str, file_path: Path) -> None:
        """Save text content to file.
        
        Args:
            content: Text content to save
            file_path: Target file path
        """
        try:
            # Ensure parent directory exists
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write text content
            file_path.write_text(content, encoding='utf-8')
            logger.info(f"Saved text file: {file_path}")
            
        except Exception as e:
            raise FileManagerError(f"Failed to save text to '{file_path}': {e}")
    
    def load_json(self, file_path: Path) -> Dict[str, Any]:
        """Load JSON data from file.
        
        Args:
            file_path: Source file path
            
        Returns:
            Loaded JSON data
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            logger.debug(f"Loaded JSON file: {file_path}")
            return data
            
        except Exception as e:
            raise FileManagerError(f"Failed to load JSON from '{file_path}': {e}")
    
    def load_text(self, file_path: Path) -> str:
        """Load text content from file.
        
        Args:
            file_path: Source file path
            
        Returns:
            File text content
        """
        try:
            content = file_path.read_text(encoding='utf-8')
            logger.debug(f"Loaded text file: {file_path}")
            return content
            
        except Exception as e:
            raise FileManagerError(f"Failed to load text from '{file_path}': {e}")
    
    def list_packages(self) -> List[Dict[str, Any]]:
        """List all packages in the base directory.
        
        Returns:
            List of package information dictionaries
        """
        packages = []
        
        try:
            for package_dir in self.base_dir.iterdir():
                if package_dir.is_dir() and not package_dir.name.startswith('.'):
                    package_info = self._get_package_info(package_dir)
                    if package_info:
                        packages.append(package_info)
            
            logger.info(f"Found {len(packages)} packages")
            return packages
            
        except Exception as e:
            logger.error(f"Failed to list packages: {e}")
            return []
    
    def _get_package_info(self, package_dir: Path) -> Optional[Dict[str, Any]]:
        """Get package information from directory.
        
        Args:
            package_dir: Package directory path
            
        Returns:
            Package information dictionary or None if invalid
        """
        try:
            metadata_file = package_dir / 'metadata.json'
            
            if metadata_file.exists():
                metadata = self.load_json(metadata_file)
                return {
                    'slug': package_dir.name,
                    'path': str(package_dir),
                    'metadata': metadata,
                    'has_workflows': (package_dir / 'workflows').exists(),
                    'has_docs': (package_dir / 'docs').exists(),
                    'has_tests': (package_dir / 'tests').exists(),
                    'created_at': datetime.fromtimestamp(package_dir.stat().st_ctime),
                    'modified_at': datetime.fromtimestamp(package_dir.stat().st_mtime)
                }
            else:
                return {
                    'slug': package_dir.name,
                    'path': str(package_dir),
                    'metadata': {},
                    'has_workflows': False,
                    'has_docs': False,
                    'has_tests': False,
                    'created_at': datetime.fromtimestamp(package_dir.stat().st_ctime),
                    'modified_at': datetime.fromtimestamp(package_dir.stat().st_mtime)
                }
                
        except Exception as e:
            logger.warning(f"Failed to get info for package '{package_dir.name}': {e}")
            return None
    
    def backup_package(self, package_slug: str, backup_suffix: Optional[str] = None) -> Path:
        """Create backup of package directory.
        
        Args:
            package_slug: Package identifier
            backup_suffix: Optional suffix for backup directory name
            
        Returns:
            Path to backup directory
        """
        package_dir = self.base_dir / package_slug
        
        if not package_dir.exists():
            raise FileManagerError(f"Package '{package_slug}' does not exist")
        
        # Generate backup name
        if backup_suffix is None:
            backup_suffix = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        backup_dir = self.base_dir / f"{package_slug}_backup_{backup_suffix}"
        
        try:
            # Copy entire package directory
            shutil.copytree(package_dir, backup_dir)
            logger.info(f"Created backup: {backup_dir}")
            return backup_dir
            
        except Exception as e:
            raise FileManagerError(f"Failed to backup package '{package_slug}': {e}")
    
    def cleanup_package(self, package_slug: str, keep_backup: bool = True) -> None:
        """Clean up package directory with optional backup.
        
        Args:
            package_slug: Package identifier
            keep_backup: Whether to create backup before cleanup
        """
        package_dir = self.base_dir / package_slug
        
        if not package_dir.exists():
            logger.warning(f"Package '{package_slug}' does not exist")
            return
        
        try:
            # Create backup if requested
            if keep_backup:
                backup_dir = self.backup_package(package_slug, "cleanup")
                logger.info(f"Backup created before cleanup: {backup_dir}")
            
            # Remove package directory
            shutil.rmtree(package_dir)
            logger.info(f"Cleaned up package: {package_slug}")
            
        except Exception as e:
            raise FileManagerError(f"Failed to cleanup package '{package_slug}': {e}")
    
    def validate_package_structure(self, package_slug: str) -> List[str]:
        """Validate package directory structure against CLAUDE.md standards.
        
        Args:
            package_slug: Package identifier
            
        Returns:
            List of validation error messages (empty if valid)
        """
        package_dir = self.base_dir / package_slug
        errors = []
        
        if not package_dir.exists():
            errors.append(f"Package directory does not exist: {package_dir}")
            return errors
        
        # Check required directories
        required_dirs = ['workflows', 'docs', 'tests']
        for req_dir in required_dirs:
            dir_path = package_dir / req_dir
            if not dir_path.exists():
                errors.append(f"Missing required directory: {req_dir}")
            elif not dir_path.is_dir():
                errors.append(f"Path exists but is not a directory: {req_dir}")
        
        # Check metadata.json
        metadata_file = package_dir / 'metadata.json'
        if not metadata_file.exists():
            errors.append("Missing metadata.json file")
        else:
            try:
                metadata = self.load_json(metadata_file)
                # Validate required metadata fields per CLAUDE.md
                required_fields = ['name', 'slug', 'problem_statement', 'roi_notes']
                for field in required_fields:
                    if field not in metadata or not metadata[field]:
                        errors.append(f"Missing or empty required metadata field: {field}")
            except Exception as e:
                errors.append(f"Invalid metadata.json: {e}")
        
        # Check for at least one workflow file
        workflows_dir = package_dir / 'workflows'
        if workflows_dir.exists():
            workflow_files = list(workflows_dir.glob('*.json'))
            if not workflow_files:
                errors.append("No workflow JSON files found in workflows/ directory")
        
        return errors
    
    def get_package_stats(self) -> Dict[str, Any]:
        """Get statistics about all packages.
        
        Returns:
            Dictionary with package statistics
        """
        packages = self.list_packages()
        
        stats = {
            'total_packages': len(packages),
            'packages_with_workflows': 0,
            'packages_with_docs': 0,
            'packages_with_tests': 0,
            'total_size_bytes': 0,
            'oldest_package': None,
            'newest_package': None
        }
        
        if packages:
            # Calculate statistics
            for pkg in packages:
                if pkg['has_workflows']:
                    stats['packages_with_workflows'] = (stats['packages_with_workflows'] or 0) + 1
                if pkg['has_docs']:
                    stats['packages_with_docs'] = (stats['packages_with_docs'] or 0) + 1
                if pkg['has_tests']:
                    stats['packages_with_tests'] = (stats['packages_with_tests'] or 0) + 1
                
                # Calculate directory size
                pkg_path = Path(pkg['path'])
                if pkg_path.exists():
                    stats['total_size_bytes'] = (stats['total_size_bytes'] or 0) + self._get_directory_size(pkg_path)
            
            # Find oldest and newest packages
            packages_by_date = sorted(packages, key=lambda p: p['created_at'])
            stats['oldest_package'] = packages_by_date[0]['slug']
            stats['newest_package'] = packages_by_date[-1]['slug']
        
        return stats
    
    def _get_directory_size(self, directory: Path) -> int:
        """Calculate total size of directory in bytes."""
        total_size = 0
        try:
            for file_path in directory.rglob('*'):
                if file_path.is_file():
                    total_size += file_path.stat().st_size
        except Exception as e:
            logger.warning(f"Failed to calculate size for {directory}: {e}")
        return total_size
    
    def export_package(self, package_slug: str, export_path: Path, 
                      format: str = 'zip') -> Path:
        """Export package as archive.
        
        Args:
            package_slug: Package identifier
            export_path: Target export path (without extension)
            format: Archive format ('zip' or 'tar')
            
        Returns:
            Path to created archive
        """
        package_dir = self.base_dir / package_slug
        
        if not package_dir.exists():
            raise FileManagerError(f"Package '{package_slug}' does not exist")
        
        try:
            if format == 'zip':
                archive_path = export_path.with_suffix('.zip')
                shutil.make_archive(str(export_path), 'zip', package_dir)
            elif format == 'tar':
                archive_path = export_path.with_suffix('.tar.gz')
                shutil.make_archive(str(export_path), 'gztar', package_dir)
            else:
                raise FileManagerError(f"Unsupported archive format: {format}")
            
            logger.info(f"Exported package '{package_slug}' to {archive_path}")
            return archive_path
            
        except Exception as e:
            raise FileManagerError(f"Failed to export package '{package_slug}': {e}")
    
    def get_cross_platform_path(self, *path_parts: str) -> Path:
        """Create cross-platform path from parts.
        
        Args:
            *path_parts: Path components
            
        Returns:
            Cross-platform Path object
        """
        return Path(*path_parts)
    
    def ensure_directory_exists(self, directory: Path) -> None:
        """Ensure directory exists, creating if necessary.
        
        Args:
            directory: Directory path to ensure
        """
        try:
            directory.mkdir(parents=True, exist_ok=True)
            logger.debug(f"Ensured directory exists: {directory}")
        except Exception as e:
            raise FileManagerError(f"Failed to ensure directory exists '{directory}': {e}")