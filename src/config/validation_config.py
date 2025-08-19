import json
import logging
from pathlib import Path
from typing import Annotated

import pydantic_core
from pydantic import BaseModel, Field, field_validator

logger = logging.getLogger(__name__)

class ValidationConfig(BaseModel):
    """Configuration for customer validation parameters with robust JSON parsing."""
    
    min_age: Annotated[int, Field(ge=0, le=150)] = 18
    max_age: Annotated[int, Field(ge=0, le=150)] = 1
    min_banner_id: Annotated[int, Field(ge=0)] = 0
    max_banner_id: Annotated[int, Field(ge=0)] = 99

    @field_validator('max_age')
    @classmethod
    def age_max_greater_than_min(cls, v, info):
        if 'min_age' in info.data and v <= info.data['min_age']:
            raise ValueError('max_age must be greater than min_age')
        return v


    @field_validator('max_banner_id')
    @classmethod
    def banner_max_greater_than_min(cls, v, info):
        if 'min_banner_id' in info.data and v <= info.data['min_banner_id']:
            raise ValueError('max_banner_id must be greater than min_banner_id')
        return v
