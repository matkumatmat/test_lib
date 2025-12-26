"""Custom validators"""
import re
from typing import Any, Optional
from pydantic import field_validator


def validate_phone_number(phone: str) -> str:
    """Validate phone number format"""
    # Remove spaces and special chars
    cleaned = re.sub(r'[^\d+]', '', phone)
    
    # Check if valid format
    if not re.match(r'^\+?[\d]{10,15}$', cleaned):
        raise ValueError("Invalid phone number format")
    
    return cleaned


def validate_url(url: str) -> str:
    """Validate URL format"""
    url_pattern = re.compile(
        r'^https?://'  # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain
        r'localhost|'  # localhost
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # or IP
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE
    )
    
    if not url_pattern.match(url):
        raise ValueError("Invalid URL format")
    
    return url


def validate_slug(slug: str) -> str:
    """Validate slug format (lowercase, hyphen separated)"""
    if not re.match(r'^[a-z0-9]+(?:-[a-z0-9]+)*$', slug):
        raise ValueError("Invalid slug format. Use lowercase letters, numbers, and hyphens only")
    
    return slug


def validate_positive(value: int | float) -> int | float:
    """Validate positive number"""
    if value <= 0:
        raise ValueError("Value must be positive")
    return value


def validate_non_negative(value: int | float) -> int | float:
    """Validate non-negative number"""
    if value < 0:
        raise ValueError("Value must be non-negative")
    return value


def validate_min_length(value: str, min_length: int) -> str:
    """Validate minimum string length"""
    if len(value) < min_length:
        raise ValueError(f"Minimum length is {min_length} characters")
    return value


def validate_max_length(value: str, max_length: int) -> str:
    """Validate maximum string length"""
    if len(value) > max_length:
        raise ValueError(f"Maximum length is {max_length} characters")
    return value


def validate_alpha_numeric(value: str) -> str:
    """Validate alphanumeric string"""
    if not value.isalnum():
        raise ValueError("Value must contain only letters and numbers")
    return value


def validate_no_whitespace(value: str) -> str:
    """Validate no whitespace in string"""
    if ' ' in value or '\t' in value or '\n' in value:
        raise ValueError("Value must not contain whitespace")
    return value


class PhoneNumberValidator:
    """Pydantic validator for phone numbers"""
    
    @classmethod
    def __get_validators__(cls):
        yield cls.validate
    
    @classmethod
    def validate(cls, v: str) -> str:
        return validate_phone_number(v)


class URLValidator:
    """Pydantic validator for URLs"""
    
    @classmethod
    def __get_validators__(cls):
        yield cls.validate
    
    @classmethod
    def validate(cls, v: str) -> str:
        return validate_url(v)