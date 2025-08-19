import re
import uuid

from pydantic_core.core_schema import ValidationInfo


def validate_name(v: str) -> str:
    """Validate that name contains only letters and spaces."""
    if not re.match(r'^[A-Za-z\s]+$', v.strip()):
        raise ValueError('Name must contain only letters and spaces')
    return v.strip()


def validate_cookie(v: str) -> str:
    """Validate that cookie is a valid UUID format."""
    try:
        uuid.UUID(v)
        return v
    except ValueError:
        raise ValueError('Cookie must be a valid UUID format')


def validate_banner_id(v: int) -> int:
    """Validate that banner_id is between bounds."""
    if not (0 <= v <= 99):
        raise ValueError('Banner_id must be between 0 and 99')
    return v


def validate_age_with_config(v: int, info: ValidationInfo) -> int:
    """Validate age with configurable minimum age."""
    min_age = info.context.get('min_age', 18) if info.context else 18
    max_age = info.context.get('max_age', 100) if info.context else 100

    if v < min_age:
        raise ValueError(f'Age must be at least {min_age}')
    if v > max_age:
        raise ValueError(f'Age must not exceed {max_age}')
    return v
