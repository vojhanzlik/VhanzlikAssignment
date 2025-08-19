import json
import logging
from pathlib import Path

import pydantic_core
from pydantic import BaseModel

from src.config.validation_config import ValidationConfig

logger = logging.getLogger(__name__)


class MainConfig(BaseModel):
    """Configuration for customer validation parameters with robust JSON parsing."""

    customer_data_path: str = "data/customer_data.json"
    validation_config: ValidationConfig = ValidationConfig()

    @classmethod
    def from_json(cls, path_to_json: str | Path) -> 'MainConfig':
        try:
            with open(path_to_json, 'r') as f:
                return cls.model_validate(
                    pydantic_core.from_json(json.load(f))
                )
        except FileNotFoundError:
            raise FileNotFoundError(f"File not found: {path_to_json}")
        except Exception:
            raise RuntimeError(f"Unhandled exception parsing {path_to_json}")

