import logging

from typing import Annotated, Any
from typing_extensions import Self
from pydantic import BaseModel, Field, field_validator, ValidationInfo, model_validator, ValidationError
from pydantic.functional_validators import ModelWrapValidatorHandler

from src.utils.validation.customer_validation import validate_name, validate_cookie, validate_banner_id, \
    validate_age


class Customer(BaseModel):
    """Customer model with validation"""

    Name: Annotated[str, Field(min_length=1)]
    Age: int
    Cookie: Annotated[str, Field(min_length=1)]
    Banner_id: int

    @model_validator(mode='wrap')
    @classmethod
    def log_failed_validation(cls, data: Any, handler: ModelWrapValidatorHandler[Self]) -> Self:
        """ inspired by https://docs.pydantic.dev/latest/concepts/validators/#model-validators :)"""
        try:
            return handler(data)
        except ValidationError:
            logging.error('Model %s failed to validate with data %s', cls, data)
            raise

    @field_validator('Name', mode='after')
    @classmethod
    def validate_name_format(cls, v: str) -> str:
        return validate_name(v)

    @field_validator('Cookie', mode='after')
    @classmethod
    def validate_cookie_format(cls, v: str) -> str:
        return validate_cookie(v)

    @field_validator('Banner_id', mode='after')
    @classmethod
    def validate_banner_id_range(cls, v: int, info: ValidationInfo) -> int:
        return validate_banner_id(v, info)

    @field_validator('Age', mode='after')
    @classmethod
    def validate_age_limits(cls, v: int, info: ValidationInfo) -> int:
        return validate_age(v, info)

