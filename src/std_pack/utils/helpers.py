"""General helper functions"""
import hashlib
import secrets
import string
from typing import Any, Dict, List, Optional
import json


def generate_random_string(length: int = 32) -> str:
    """Generate random string"""
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))


def generate_random_code(length: int = 6, digits_only: bool = True) -> str:
    """Generate random code"""
    alphabet = string.digits if digits_only else string.ascii_uppercase + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))


def generate_hash(data: str, algorithm: str = "sha256") -> str:
    """Generate hash from string"""
    hash_func = getattr(hashlib, algorithm)
    return hash_func(data.encode()).hexdigest()


def truncate_string(text: str, max_length: int, suffix: str = "...") -> str:
    """Truncate string to max length"""
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix


def slugify(text: str) -> str:
    """Convert string to slug"""
    # Lowercase
    text = text.lower()
    
    # Replace spaces and special chars with hyphen
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[\s_]+', '-', text)
    text = re.sub(r'^-+|-+$', '', text)
    
    return text


def deep_merge(dict1: Dict, dict2: Dict) -> Dict:
    """Deep merge two dictionaries"""
    result = dict1.copy()
    
    for key, value in dict2.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = value
    
    return result


def flatten_dict(data: Dict, parent_key: str = '', separator: str = '.') -> Dict:
    """Flatten nested dictionary"""
    items = []
    
    for key, value in data.items():
        new_key = f"{parent_key}{separator}{key}" if parent_key else key
        
        if isinstance(value, dict):
            items.extend(flatten_dict(value, new_key, separator).items())
        else:
            items.append((new_key, value))
    
    return dict(items)


def chunk_list(lst: List[Any], chunk_size: int) -> List[List[Any]]:
    """Split list into chunks"""
    return [lst[i:i + chunk_size] for i in range(0, len(lst), chunk_size)]


def remove_none_values(data: Dict) -> Dict:
    """Remove None values from dictionary"""
    return {k: v for k, v in data.items() if v is not None}


def safe_json_loads(data: str, default: Any = None) -> Any:
    """Safe JSON loads with default value"""
    try:
        return json.loads(data)
    except (json.JSONDecodeError, TypeError):
        return default


def safe_json_dumps(data: Any, default: str = "{}") -> str:
    """Safe JSON dumps with default value"""
    try:
        return json.dumps(data)
    except (TypeError, ValueError):
        return default


def get_nested_value(data: Dict, path: str, default: Any = None, separator: str = '.') -> Any:
    """Get nested dictionary value by path"""
    keys = path.split(separator)
    value = data
    
    try:
        for key in keys:
            value = value[key]
        return value
    except (KeyError, TypeError):
        return default


def set_nested_value(data: Dict, path: str, value: Any, separator: str = '.') -> Dict:
    """Set nested dictionary value by path"""
    keys = path.split(separator)
    current = data
    
    for key in keys[:-1]:
        if key not in current or not isinstance(current[key], dict):
            current[key] = {}
        current = current[key]
    
    current[keys[-1]] = value
    return data


import re  # Add this import at the top