"""Tests for main configuration loading and validation."""

import pytest
import tempfile
import json
from pathlib import Path

from src.config.main_config import MainConfig
from src.config.validation_config import ValidationConfig


class TestMainConfig:
    """Test cases for MainConfig class."""
    
    def test_from_json_valid_file(self):
        """Test loading from a valid JSON file."""
        valid_data = {
            "customer_data_path": "/test/path/customers.csv",
            "validation_config": {
                "min_age": 21,
                "max_age": 65,
                "min_banner_id": 5,
                "max_banner_id": 85
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(valid_data, f)
            temp_path = f.name
        
        try:
            config = MainConfig.from_json(temp_path)
            assert config.customer_data_path == "/test/path/customers.csv"
            assert config.validation_config.min_age == 21
            assert config.validation_config.max_age == 65
            assert config.validation_config.min_banner_id == 5
            assert config.validation_config.max_banner_id == 85
        finally:
            Path(temp_path).unlink()
    
    def test_from_json_partial_data_uses_defaults(self):
        """Loading partial JSON config fills the rest with defaults."""
        partial_data = {
            "customer_data_path": "/custom/data.csv"
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(partial_data, f)
            temp_path = f.name
        
        try:
            config = MainConfig.from_json(temp_path)
            assert config.customer_data_path == "/custom/data.csv"

            default_validation_conf = ValidationConfig()
            assert config.validation_config.min_age == default_validation_conf.min_age
            assert config.validation_config.max_age == default_validation_conf.max_age
            assert config.validation_config.min_banner_id == default_validation_conf.min_banner_id
            assert config.validation_config.max_banner_id == default_validation_conf.max_banner_id
        finally:
            Path(temp_path).unlink()
    
    def test_from_json_partially_filled_subconfig_uses_defaults(self):
        """Loading partial JSON subconfig fills the rest with defaults - including rest of subconfig."""
        validation_partial_config = {
            "validation_config": {
                "min_age": 25,
                "max_age": 70
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(validation_partial_config, f)
            temp_path = f.name
        
        try:
            config = MainConfig.from_json(temp_path)

            default_main_conf = MainConfig()
            assert config.customer_data_path == default_main_conf.customer_data_path
            assert config.validation_config.min_age == 25
            assert config.validation_config.max_age == 70
            assert config.validation_config.min_banner_id == default_main_conf.validation_config.min_banner_id
            assert config.validation_config.max_banner_id == default_main_conf.validation_config.max_banner_id

        finally:
            Path(temp_path).unlink()
    
    def test_from_json_file_not_found(self):
        """Test handling of non-existent file."""
        with pytest.raises(FileNotFoundError):
            MainConfig.from_json("non_existent_file.json")
    
    def test_from_json_invalid_json(self):
        """Test handling of invalid JSON."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write("{ invalid json }")
            temp_path = f.name
        
        try:
            with pytest.raises(RuntimeError):
                MainConfig.from_json(temp_path)
        finally:
            Path(temp_path).unlink()
    
    def test_from_json_invalid_validation_config_min_gt_max(self):
        """Test handling of invalid validation configuration where min age > max age."""
        invalid_data = {
            "customer_data_path": "/test/data.csv",
            "validation_config": {
                "min_age": 50,
                "max_age": 30
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(invalid_data, f)
            temp_path = f.name
        
        try:
            with pytest.raises(ValueError):
                MainConfig.from_json(temp_path)
        finally:
            Path(temp_path).unlink()
