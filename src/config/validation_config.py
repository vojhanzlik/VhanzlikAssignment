"""Validation configuration for customer data processing rules."""

import logging
from typing import Annotated

from pydantic import BaseModel, Field, field_validator

logger = logging.getLogger(__name__)

"""
These need to match with the ValidationConfig fields below.
They are later passed to validation functions as arguments using the to_context() method below.  
"""
MIN_AGE_PARAM = 'min_age'
MAX_AGE_PARAM = 'max_age'
MIN_BANNER_ID_PARAM = 'min_banner_id'
MAX_BANNER_ID_PARAM = 'max_banner_id'

class ValidationConfig(BaseModel):
    """Configuration for customer validation parameters with JSON parsing."""
    
    min_age: Annotated[int, Field(ge=0, validate_default=True)] = 18
    max_age: Annotated[int, Field(ge=0, validate_default=True)] = 100
    min_banner_id: Annotated[int, Field(ge=0, validate_default=True)] = 0
    max_banner_id: Annotated[int, Field(ge=0, validate_default=True)] = 99

    @field_validator('max_age')
    @classmethod
    def age_max_greater_than_min(cls, v, info):
        if MIN_AGE_PARAM in info.data and v < info.data[MIN_AGE_PARAM]:
            raise ValueError('max_age must be greater than min_age')
        return v


    @field_validator('max_banner_id')
    @classmethod
    def banner_max_greater_than_min(cls, v, info):
        if MIN_BANNER_ID_PARAM in info.data and v < info.data[MIN_BANNER_ID_PARAM]:
            raise ValueError('max_banner_id must be greater than min_banner_id')
        return v


    def to_context(self) -> dict:
        """
        Context is passed to validators, does not look pretty, but it is the only
        way to pass arguments to validator functions that I found.
        """
        return {
            MIN_AGE_PARAM: self.min_age,
            MAX_AGE_PARAM: self.max_age,
            MIN_BANNER_ID_PARAM: self.min_banner_id,
            MAX_BANNER_ID_PARAM: self.max_banner_id
        }