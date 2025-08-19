import logging

from typing import Annotated, Any
from typing_extensions import Self
from pydantic import BaseModel, Field, field_validator, ValidationInfo, model_validator, ValidationError
from pydantic.functional_validators import ModelWrapValidatorHandler

from src.utils.validation.customer_validation import validate_name, validate_cookie, validate_banner_id, \
    validate_age_with_config


class Customer(BaseModel):
    """Customer model with validation for ShowAds API."""

    name: Annotated[str, Field(min_length=1, max_length=100)]
    age: Annotated[int, Field(ge=0, le=150)]
    cookie: Annotated[str, Field(min_length=1)]
    banner_id: Annotated[int, Field(ge=0, le=99)]

    @model_validator(mode='wrap')
    @classmethod
    def log_failed_validation(cls, data: Any, handler: ModelWrapValidatorHandler[Self]) -> Self:
        try:
            return handler(data)
        except ValidationError:
            logging.error('Model %s failed to validate with data %s', cls, data)
            raise

    @field_validator('name', mode='after')
    @classmethod
    def validate_name_format(cls, v: str) -> str:
        return validate_name(v)

    @field_validator('cookie', mode='after')
    @classmethod
    def validate_cookie_format(cls, v: str) -> str:
        return validate_cookie(v)

    @field_validator('banner_id', mode='after')
    @classmethod
    def validate_banner_id_range(cls, v: int) -> int:
        return validate_banner_id(v)

    @field_validator('age', mode='after')
    @classmethod
    def validate_age_limits(cls, v: int, info: ValidationInfo) -> int:
        return validate_age_with_config(v, info)

