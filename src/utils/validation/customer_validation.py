"""Validation functions for customer data fields."""

import re
import uuid

from pydantic_core.core_schema import ValidationInfo

from src.config.validation_config import MIN_AGE_PARAM, MAX_AGE_PARAM, MAX_BANNER_ID_PARAM, MIN_BANNER_ID_PARAM


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


def validate_banner_id(v: int, info: ValidationInfo) -> int:
    """Validate that banner_id is between bounds."""
    if not info.context or MIN_BANNER_ID_PARAM not in info.context or MAX_BANNER_ID_PARAM not in info.context:
        raise ValueError('Insufficient context information')

    min_banner_id = info.context.get(MIN_BANNER_ID_PARAM)
    max_banner_id = info.context.get(MAX_BANNER_ID_PARAM)

    if not (min_banner_id <= v <= max_banner_id):
        raise ValueError('Banner_id must be between 0 and 99')
    return v


def validate_age(v: int, info: ValidationInfo) -> int:
    """Validate age with configurable minimum age."""
    if not info.context or MIN_AGE_PARAM not in info.context or MAX_AGE_PARAM not in info.context:
        raise ValueError('Insufficient context information')

    min_age = info.context.get(MIN_AGE_PARAM)
    max_age = info.context.get(MAX_AGE_PARAM)

    if v < min_age:
        raise ValueError(f'Age must be at least {min_age}')
    if v > max_age:
        raise ValueError(f'Age must not exceed {max_age}')
    return v
