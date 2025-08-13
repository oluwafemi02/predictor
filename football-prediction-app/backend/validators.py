"""
Input validation utilities for the Football Prediction API
"""

import re
from datetime import datetime, timedelta
from typing import Optional, Union
from exceptions import ValidationError

def validate_date_string(date_str: str, field_name: str = "date") -> datetime:
    """
    Validate and parse a date string in YYYY-MM-DD format
    """
    if not date_str:
        raise ValidationError(f"{field_name} is required", field=field_name)
    
    try:
        date_obj = datetime.strptime(date_str, '%Y-%m-%d')
        # Check for reasonable date range (not too far in past/future)
        now = datetime.now()
        if date_obj < now - timedelta(days=3650):  # 10 years ago
            raise ValidationError(f"{field_name} cannot be more than 10 years in the past", field=field_name)
        if date_obj > now + timedelta(days=1095):  # 3 years in future
            raise ValidationError(f"{field_name} cannot be more than 3 years in the future", field=field_name)
        return date_obj
    except ValueError:
        raise ValidationError(f"{field_name} must be in YYYY-MM-DD format", field=field_name)

def validate_team_id(team_id: Union[str, int], field_name: str = "team_id") -> int:
    """
    Validate team ID parameter
    """
    try:
        team_id_int = int(team_id)
        if team_id_int <= 0:
            raise ValidationError(f"{field_name} must be a positive integer", field=field_name)
        return team_id_int
    except (ValueError, TypeError):
        raise ValidationError(f"{field_name} must be a valid integer", field=field_name)

def validate_pagination(page: Union[str, int, None], per_page: Union[str, int, None]) -> tuple[int, int]:
    """
    Validate pagination parameters
    """
    try:
        page_int = max(1, int(page) if page else 1)
    except (ValueError, TypeError):
        raise ValidationError("page must be a positive integer", field="page")
    
    try:
        per_page_int = int(per_page) if per_page else 20
        per_page_int = max(1, min(per_page_int, 100))  # Limit to 100 items per page
    except (ValueError, TypeError):
        raise ValidationError("per_page must be a positive integer", field="per_page")
    
    return page_int, per_page_int

def validate_status(status: Optional[str]) -> Optional[str]:
    """
    Validate match status parameter
    """
    valid_statuses = ['scheduled', 'in_play', 'finished', 'postponed']
    if status and status not in valid_statuses:
        raise ValidationError(f"status must be one of: {', '.join(valid_statuses)}", field="status")
    return status

def validate_competition_name(competition: Optional[str]) -> Optional[str]:
    """
    Validate competition name parameter
    """
    if not competition:
        return None
    
    # Basic validation - alphanumeric, spaces, hyphens, underscores only
    if not re.match(r'^[a-zA-Z0-9\s\-_]+$', competition):
        raise ValidationError("competition name contains invalid characters", field="competition")
    
    if len(competition) > 100:
        raise ValidationError("competition name is too long (max 100 characters)", field="competition")
    
    return competition.strip()

def sanitize_text_input(text: Optional[str], max_length: int = 255) -> Optional[str]:
    """
    Sanitize text input by removing potentially dangerous characters
    """
    if not text:
        return None
    
    # Remove potentially dangerous characters
    sanitized = re.sub(r'[<>&"\'%]', '', text)
    
    # Limit length
    if len(sanitized) > max_length:
        sanitized = sanitized[:max_length]
    
    return sanitized.strip() if sanitized else None

def validate_api_key(api_key: Optional[str], service_name: str = "API") -> str:
    """
    Validate API key format
    """
    if not api_key:
        raise ValidationError(f"{service_name} key is required")
    
    if len(api_key) < 10:
        raise ValidationError(f"{service_name} key appears to be invalid (too short)")
    
    # Basic format validation - should be alphanumeric
    if not re.match(r'^[a-zA-Z0-9]+$', api_key):
        raise ValidationError(f"{service_name} key contains invalid characters")
    
    return api_key