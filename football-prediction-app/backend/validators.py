"""
Input validation utilities for the Football Prediction API
"""

import re
from datetime import datetime, timedelta
from typing import Optional, Union, List
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
    valid_statuses = ['scheduled', 'in_play', 'finished', 'postponed', 'cancelled']
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
    
    # Basic format validation - should be alphanumeric with some special chars
    if not re.match(r'^[a-zA-Z0-9_\-]+$', api_key):
        raise ValidationError(f"{service_name} key contains invalid characters")
    
    return api_key

def validate_email(email: str, field_name: str = "email") -> str:
    """
    Validate email address format
    """
    if not email:
        raise ValidationError(f"{field_name} is required", field=field_name)
    
    # Basic email regex pattern
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    
    if not re.match(email_pattern, email):
        raise ValidationError(f"Invalid {field_name} format", field=field_name)
    
    if len(email) > 120:
        raise ValidationError(f"{field_name} is too long (max 120 characters)", field=field_name)
    
    return email.lower().strip()

def validate_password(password: str, field_name: str = "password") -> str:
    """
    Validate password strength
    """
    if not password:
        raise ValidationError(f"{field_name} is required", field=field_name)
    
    if len(password) < 8:
        raise ValidationError(f"{field_name} must be at least 8 characters long", field=field_name)
    
    # Check for at least one uppercase, one lowercase, one digit
    if not re.search(r'[A-Z]', password):
        raise ValidationError(f"{field_name} must contain at least one uppercase letter", field=field_name)
    
    if not re.search(r'[a-z]', password):
        raise ValidationError(f"{field_name} must contain at least one lowercase letter", field=field_name)
    
    if not re.search(r'\d', password):
        raise ValidationError(f"{field_name} must contain at least one number", field=field_name)
    
    return password

def validate_match_id(match_id: Union[str, int], field_name: str = "match_id") -> int:
    """
    Validate match ID parameter
    """
    try:
        match_id_int = int(match_id)
        if match_id_int <= 0:
            raise ValidationError(f"{field_name} must be a positive integer", field=field_name)
        return match_id_int
    except (ValueError, TypeError):
        raise ValidationError(f"{field_name} must be a valid integer", field=field_name)

def validate_float_parameter(value: Union[str, float, None], field_name: str, 
                           min_value: Optional[float] = None, 
                           max_value: Optional[float] = None) -> Optional[float]:
    """
    Validate float parameter with optional bounds
    """
    if value is None:
        return None
    
    try:
        float_value = float(value)
        
        if min_value is not None and float_value < min_value:
            raise ValidationError(f"{field_name} must be at least {min_value}", field=field_name)
        
        if max_value is not None and float_value > max_value:
            raise ValidationError(f"{field_name} must be at most {max_value}", field=field_name)
        
        return float_value
    except (ValueError, TypeError):
        raise ValidationError(f"{field_name} must be a valid number", field=field_name)

def validate_integer_list(values: Union[str, List[int]], field_name: str) -> List[int]:
    """
    Validate a list of integers (comma-separated string or list)
    """
    if isinstance(values, str):
        try:
            int_list = [int(v.strip()) for v in values.split(',') if v.strip()]
        except ValueError:
            raise ValidationError(f"{field_name} must contain valid integers", field=field_name)
    elif isinstance(values, list):
        try:
            int_list = [int(v) for v in values]
        except (ValueError, TypeError):
            raise ValidationError(f"{field_name} must contain valid integers", field=field_name)
    else:
        raise ValidationError(f"{field_name} must be a list or comma-separated string", field=field_name)
    
    if not int_list:
        raise ValidationError(f"{field_name} cannot be empty", field=field_name)
    
    # Check all are positive
    if any(v <= 0 for v in int_list):
        raise ValidationError(f"{field_name} must contain positive integers only", field=field_name)
    
    return int_list