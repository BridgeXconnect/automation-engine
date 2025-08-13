"""Helper functions and utilities for the Automation Package Generator."""

import logging
import re
import sys
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

def generate_slug(text: str, max_length: int = 50) -> str:
    """Generate URL-friendly slug from text.
    
    Args:
        text: Input text to convert
        max_length: Maximum length of slug
        
    Returns:
        URL-friendly slug string
    """
    if not text:
        return "untitled"
    
    # Convert to lowercase and replace spaces/special chars with hyphens
    slug = text.lower()
    slug = re.sub(r'[^\w\s-]', '', slug)  # Remove special characters
    slug = re.sub(r'[-\s]+', '-', slug)   # Replace spaces and multiple hyphens
    slug = slug.strip('-')                # Remove leading/trailing hyphens
    
    # Truncate if too long
    if len(slug) > max_length:
        slug = slug[:max_length].rstrip('-')
    
    # Ensure not empty
    if not slug:
        slug = "untitled"
    
    return slug

def format_timestamp(dt: datetime, format_type: str = 'iso') -> str:
    """Format datetime timestamp.
    
    Args:
        dt: Datetime object to format
        format_type: Format type ('iso', 'readable', 'filename')
        
    Returns:
        Formatted timestamp string
    """
    if format_type == 'iso':
        return dt.isoformat()
    elif format_type == 'readable':
        return dt.strftime('%Y-%m-%d %H:%M:%S')
    elif format_type == 'filename':
        return dt.strftime('%Y%m%d_%H%M%S')
    else:
        return dt.isoformat()

def setup_logging(level: int = logging.INFO, 
                 log_file: Optional[Path] = None,
                 console_output: bool = True) -> None:
    """Setup logging configuration.
    
    Args:
        level: Logging level
        log_file: Optional file path for logging
        console_output: Whether to log to console
    """
    # Create formatter
    formatter = logging.Formatter(
        fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    
    # Clear existing handlers
    root_logger.handlers.clear()
    
    # Console handler
    if console_output:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)
    
    # File handler
    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
    
    logger.info(f"Logging configured - Level: {logging.getLevelName(level)}")

def safe_filename(filename: str, max_length: int = 255) -> str:
    """Create safe filename by removing/replacing invalid characters.
    
    Args:
        filename: Original filename
        max_length: Maximum filename length
        
    Returns:
        Safe filename string
    """
    if not filename:
        return "untitled"
    
    # Replace invalid characters for cross-platform compatibility
    safe_chars = re.sub(r'[<>:"/\\|?*]', '_', filename)
    safe_chars = re.sub(r'[^\w\s.-]', '', safe_chars)
    safe_chars = safe_chars.strip()
    
    # Truncate if too long
    if len(safe_chars) > max_length:
        safe_chars = safe_chars[:max_length].rstrip('.')
    
    # Ensure not empty
    if not safe_chars:
        safe_chars = "untitled"
    
    return safe_chars

def calculate_file_hash(file_path: Path, algorithm: str = 'sha256') -> str:
    """Calculate hash of file content.
    
    Args:
        file_path: Path to file
        algorithm: Hash algorithm ('md5', 'sha1', 'sha256')
        
    Returns:
        Hex string of file hash
    """
    hash_algo = hashlib.new(algorithm)
    
    try:
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_algo.update(chunk)
        
        return hash_algo.hexdigest()
        
    except Exception as e:
        logger.error(f"Failed to calculate hash for {file_path}: {e}")
        return ""

def format_bytes(bytes_value: int) -> str:
    """Format bytes value to human readable string.
    
    Args:
        bytes_value: Number of bytes
        
    Returns:
        Human readable string (e.g., '1.5 MB')
    """
    if bytes_value == 0:
        return "0 B"
    
    units = ['B', 'KB', 'MB', 'GB', 'TB']
    bytes_float = float(bytes_value)
    
    for unit in units:
        if bytes_float < 1024.0:
            return f"{bytes_float:.1f} {unit}"
        bytes_float /= 1024.0
    
    return f"{bytes_float:.1f} {units[-1]}"

def format_duration(seconds: float) -> str:
    """Format duration in seconds to human readable string.
    
    Args:
        seconds: Duration in seconds
        
    Returns:
        Human readable duration (e.g., '2m 30s')
    """
    if seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        mins = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{mins}m {secs}s"
    else:
        hours = int(seconds // 3600)
        mins = int((seconds % 3600) // 60)
        return f"{hours}h {mins}m"

def validate_url(url: str) -> bool:
    """Validate if string is a valid URL.
    
    Args:
        url: URL string to validate
        
    Returns:
        True if valid URL, False otherwise
    """
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except Exception:
        return False

def extract_domain_from_url(url: str) -> Optional[str]:
    """Extract domain from URL.
    
    Args:
        url: URL string
        
    Returns:
        Domain string or None if invalid URL
    """
    try:
        parsed = urlparse(url)
        return parsed.netloc
    except Exception:
        return None

def clean_text(text: str, max_length: Optional[int] = None) -> str:
    """Clean and normalize text content.
    
    Args:
        text: Input text to clean
        max_length: Optional maximum length
        
    Returns:
        Cleaned text string
    """
    if not text:
        return ""
    
    # Normalize whitespace
    cleaned = re.sub(r'\s+', ' ', text.strip())
    
    # Remove non-printable characters
    cleaned = ''.join(char for char in cleaned if char.isprintable() or char.isspace())
    
    # Truncate if needed
    if max_length and len(cleaned) > max_length:
        cleaned = cleaned[:max_length].rstrip()
    
    return cleaned

def merge_dicts(*dicts: Dict[str, Any], deep: bool = True) -> Dict[str, Any]:
    """Merge multiple dictionaries.
    
    Args:
        *dicts: Dictionaries to merge
        deep: Whether to do deep merge for nested dicts
        
    Returns:
        Merged dictionary
    """
    result: Dict[str, Any] = {}
    
    for d in dicts:
        if not isinstance(d, dict):
            continue
            
        for key, value in d.items():
            if deep and key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = merge_dicts(result[key], value, deep=True)
            else:
                result[key] = value
    
    return result

def get_nested_value(data: Dict[str, Any], key_path: str, default: Any = None) -> Any:
    """Get nested value from dictionary using dot notation.
    
    Args:
        data: Dictionary to search
        key_path: Dot-separated key path (e.g., 'user.profile.name')
        default: Default value if key not found
        
    Returns:
        Value at key path or default
    """
    keys = key_path.split('.')
    current = data
    
    try:
        for key in keys:
            current = current[key]
        return current
    except (KeyError, TypeError):
        return default

def set_nested_value(data: Dict[str, Any], key_path: str, value: Any) -> None:
    """Set nested value in dictionary using dot notation.
    
    Args:
        data: Dictionary to modify
        key_path: Dot-separated key path
        value: Value to set
    """
    keys = key_path.split('.')
    current = data
    
    for key in keys[:-1]:
        if key not in current:
            current[key] = {}
        current = current[key]
    
    current[keys[-1]] = value

def flatten_dict(data: Dict[str, Any], parent_key: str = '', separator: str = '.') -> Dict[str, Any]:
    """Flatten nested dictionary.
    
    Args:
        data: Dictionary to flatten
        parent_key: Parent key prefix
        separator: Key separator
        
    Returns:
        Flattened dictionary
    """
    items: List[Tuple[str, Any]] = []
    
    for key, value in data.items():
        new_key = f"{parent_key}{separator}{key}" if parent_key else key
        
        if isinstance(value, dict):
            items.extend(flatten_dict(value, new_key, separator).items())
        else:
            items.append((new_key, value))
    
    return dict(items)

def validate_json_schema(data: Dict[str, Any], required_fields: List[str]) -> List[str]:
    """Validate dictionary against required fields schema.
    
    Args:
        data: Data to validate
        required_fields: List of required field names (supports dot notation)
        
    Returns:
        List of missing field error messages
    """
    errors = []
    
    for field in required_fields:
        value = get_nested_value(data, field)
        if value is None or value == "":
            errors.append(f"Missing required field: {field}")
    
    return errors

def create_progress_bar(current: int, total: int, width: int = 50) -> str:
    """Create ASCII progress bar.
    
    Args:
        current: Current progress value
        total: Total progress value  
        width: Width of progress bar in characters
        
    Returns:
        Progress bar string
    """
    if total == 0:
        percentage = 100.0
    else:
        percentage = min(100.0, (current / total) * 100)
    
    filled_width = int(width * percentage / 100)
    bar = '█' * filled_width + '░' * (width - filled_width)
    
    return f"[{bar}] {percentage:.1f}% ({current}/{total})"

def truncate_string(text: str, max_length: int, suffix: str = "...") -> str:
    """Truncate string to maximum length with suffix.
    
    Args:
        text: Text to truncate
        max_length: Maximum length including suffix
        suffix: Suffix to add when truncated
        
    Returns:
        Truncated string
    """
    if len(text) <= max_length:
        return text
    
    truncate_length = max_length - len(suffix)
    if truncate_length <= 0:
        return suffix[:max_length]
    
    return text[:truncate_length] + suffix

def retry_on_exception(func, max_retries: int = 3, delay: float = 1.0, 
                      exceptions: tuple = (Exception,)):
    """Retry function on exception with exponential backoff.
    
    Args:
        func: Function to retry
        max_retries: Maximum number of retries
        delay: Initial delay in seconds
        exceptions: Tuple of exceptions to catch
        
    Returns:
        Function result or raises last exception
    """
    import time
    
    for attempt in range(max_retries + 1):
        try:
            return func()
        except exceptions as e:
            if attempt == max_retries:
                raise e
            
            wait_time = delay * (2 ** attempt)  # Exponential backoff
            logger.warning(f"Attempt {attempt + 1} failed: {e}. Retrying in {wait_time}s...")
            time.sleep(wait_time)

def generate_unique_id(prefix: str = "", length: int = 8) -> str:
    """Generate unique identifier.
    
    Args:
        prefix: Optional prefix for ID
        length: Length of random part
        
    Returns:
        Unique identifier string
    """
    import random
    import string
    
    random_part = ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))
    
    if prefix:
        return f"{prefix}_{random_part}"
    else:
        return random_part

def normalize_line_endings(text: str, ending: str = '\n') -> str:
    """Normalize line endings in text.
    
    Args:
        text: Input text
        ending: Target line ending
        
    Returns:
        Text with normalized line endings
    """
    # Replace Windows and Mac line endings with Unix
    text = text.replace('\r\n', '\n').replace('\r', '\n')
    
    if ending != '\n':
        text = text.replace('\n', ending)
    
    return text

def extract_keywords(text: str, min_length: int = 3, max_count: int = 10) -> List[str]:
    """Extract keywords from text.
    
    Args:
        text: Input text
        min_length: Minimum keyword length
        max_count: Maximum number of keywords
        
    Returns:
        List of extracted keywords
    """
    # Simple keyword extraction (in real implementation, might use NLP libraries)
    words = re.findall(r'\b[a-zA-Z]+\b', text.lower())
    
    # Filter by length and common stop words
    stop_words = {'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'}
    keywords = [word for word in words if len(word) >= min_length and word not in stop_words]
    
    # Count frequency and return most common
    from collections import Counter
    word_counts = Counter(keywords)
    
    return [word for word, count in word_counts.most_common(max_count)]