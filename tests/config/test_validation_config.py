import pytest
import tempfile
import json
from pathlib import Path
from pydantic import ValidationError

from src.config.validation_config import ValidationConfig, MIN_AGE_PARAM, MAX_AGE_PARAM, MIN_BANNER_ID_PARAM, MAX_BANNER_ID_PARAM


class TestValidationConfig:
    """Test cases for ValidationConfig class."""


    @pytest.mark.parametrize("min_age,max_age", [
        (1, 0),
        (30, 20)
    ])
    def test_age_validation_max_greater_than_min(self, min_age, max_age):
        """Test that max_age must be greater than min_age."""
        with pytest.raises(ValidationError) as exc_info:
            ValidationConfig(min_age=min_age, max_age=max_age)
        assert "max_age must be greater than min_age" in str(exc_info.value)

    @pytest.mark.parametrize("min_banner_id,max_banner_id", [
        (1, 0),
        (30, 20)
    ])
    def test_banner_id_validation_max_greater_than_min(self, min_banner_id, max_banner_id):
        """Test that max_banner_id must be greater than min_banner_id."""
        with pytest.raises(ValidationError) as exc_info:
            ValidationConfig(min_banner_id=min_banner_id, max_banner_id=max_banner_id)
        assert "max_banner_id must be greater than min_banner_id" in str(exc_info.value)
    
    def test_negative_values_rejected(self):
        """Test that negative values are rejected."""
        with pytest.raises(ValidationError):
            ValidationConfig(min_age=-5)
        
        with pytest.raises(ValidationError):
            ValidationConfig(min_banner_id=-10)

    def test_zero_values(self):
        """Test that all zero values are accepted."""
        assert ValidationConfig(min_age=0, max_age=0, min_banner_id=0, max_banner_id=0)
