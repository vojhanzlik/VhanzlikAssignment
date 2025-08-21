"""Tests for Customer model validation and data integrity."""

import pytest
from pydantic import ValidationError

from src.models.customer import Customer
from src.config.validation_config import ValidationConfig


class TestCustomer:
    """Test cases for Customer model."""
    
    def test_valid_customer_creation(self):
        """Test creating a valid customer."""
        config = ValidationConfig()
        context = config.to_context()
        
        customer_data = {
            "Name": "John Doe",
            "Age": 35,
            "Cookie": "26555324-53df-4eb1-8835-e6c0078bb2c0",
            "Banner_id": 35
        }
        
        customer = Customer.model_validate(customer_data, context=context)
        assert customer.Name == "John Doe"
        assert customer.Age == 35
        assert customer.Cookie == "26555324-53df-4eb1-8835-e6c0078bb2c0"
        assert customer.Banner_id == 35
    
    def test_name_validation_valid_names(self):
        """Test valid name formats."""
        config = ValidationConfig()
        context = config.to_context()
        
        valid_names = [
            "John Doe",
            "A",
            "A B C D E F"
        ]
        
        for name in valid_names:
            customer_data = {
                "Name": name,
                "Age": 25,
                "Cookie": "26555324-53df-4eb1-8835-e6c0078bb2c0",
                "Banner_id": 42
            }
            customer = Customer.model_validate(customer_data, context=context)
            assert customer.Name == name.strip()
    
    def test_name_validation_invalid_names(self):
        """Test invalid name formats."""
        config = ValidationConfig()
        context = config.to_context()
        
        invalid_names = [
            "John123",
            "Mary@Email",
            "User-Name",
            "Name_With_Underscore",
            "123",
            "John.Doe",
            "",
            "   "
        ]
        
        for name in invalid_names:
            customer_data = {
                "Name": name,
                "Age": 25,
                "Cookie": "26555324-53df-4eb1-8835-e6c0078bb2c0",
                "Banner_id": 42
            }
            with pytest.raises(ValidationError):
                Customer.model_validate(customer_data, context=context)
    
    def test_age_validation_valid_ages(self):
        """Test valid age values."""
        config = ValidationConfig(min_age=18, max_age=100)
        context = config.to_context()
        
        valid_ages = [18, 50, 100]
        
        for age in valid_ages:
            customer_data = {
                "Name": "John Doe",
                "Age": age,
                "Cookie": "26555324-53df-4eb1-8835-e6c0078bb2c0",
                "Banner_id": 42
            }
            customer = Customer.model_validate(customer_data, context=context)
            assert customer.Age == age
    
    def test_age_validation_invalid_ages(self):
        """Test invalid age values."""
        config = ValidationConfig(min_age=18, max_age=100)
        context = config.to_context()
        
        invalid_ages = [17, -5, 101]
        
        for age in invalid_ages:
            customer_data = {
                "Name": "John Doe",
                "Age": age,
                "Cookie": "26555324-53df-4eb1-8835-e6c0078bb2c0",
                "Banner_id": 42
            }
            with pytest.raises(ValidationError):
                Customer.model_validate(customer_data, context=context)
    
    def test_cookie_validation_valid_uuids(self):
        """Test valid UUID formats."""
        config = ValidationConfig()
        context = config.to_context()
        
        valid_uuids = [
            "26555324-53df-4eb1-8835-e6c0078bb2c0",
            "00000000-0000-0000-0000-000000000000",
            "ffffffff-ffff-ffff-ffff-ffffffffffff"
        ]
        
        for uuid_str in valid_uuids:
            customer_data = {
                "Name": "John Doe",
                "Age": 25,
                "Cookie": uuid_str,
                "Banner_id": 42
            }
            customer = Customer.model_validate(customer_data, context=context)
            assert customer.Cookie == uuid_str
    
    def test_cookie_validation_invalid_uuids(self):
        """Test invalid UUID formats."""
        config = ValidationConfig()
        context = config.to_context()
        
        invalid_uuids = [
            "invalid-uuid-format",
            "12345",
            "not-a-uuid",
            "",
            "26555324-53df-4eb1-8835-e6c0078bb2c0-invalid",
        ]
        
        for uuid_str in invalid_uuids:
            customer_data = {
                "Name": "John Doe",
                "Age": 25,
                "Cookie": uuid_str,
                "Banner_id": 42
            }
            with pytest.raises(ValidationError):
                Customer.model_validate(customer_data, context=context)
    
    def test_banner_id_validation_valid_ids(self):
        """Test valid banner ID values."""
        config = ValidationConfig(min_banner_id=0, max_banner_id=99)
        context = config.to_context()
        
        valid_ids = [0, 1, 99]
        
        for banner_id in valid_ids:
            customer_data = {
                "Name": "John Doe",
                "Age": 25,
                "Cookie": "26555324-53df-4eb1-8835-e6c0078bb2c0",
                "Banner_id": banner_id
            }
            customer = Customer.model_validate(customer_data, context=context)
            assert customer.Banner_id == banner_id
    
    def test_banner_id_validation_invalid_ids(self):
        """Test invalid banner ID values."""
        config = ValidationConfig(min_banner_id=0, max_banner_id=99)
        context = config.to_context()
        
        invalid_ids = [-1, 100,]
        
        for banner_id in invalid_ids:
            customer_data = {
                "Name": "John Doe",
                "Age": 25,
                "Cookie": "26555324-53df-4eb1-8835-e6c0078bb2c0",
                "Banner_id": banner_id
            }
            with pytest.raises(ValidationError):
                Customer.model_validate(customer_data, context=context)
    
    def test_missing_context(self):
        """Test validation without proper context."""
        customer_data = {
            "Name": "John Doe",
            "Age": 25,
            "Cookie": "26555324-53df-4eb1-8835-e6c0078bb2c0",
            "Banner_id": 42
        }
        
        # should fail without context
        with pytest.raises(ValidationError):
            Customer.model_validate(customer_data)
    
    def test_whitespace_trimming(self):
        """Test that name whitespace is trimmed."""
        config = ValidationConfig()
        context = config.to_context()
        
        customer_data = {
            "Name": "  John Doe  ",
            "Age": 25,
            "Cookie": "26555324-53df-4eb1-8835-e6c0078bb2c0",
            "Banner_id": 42
        }
        
        customer = Customer.model_validate(customer_data, context=context)
        assert customer.Name == "John Doe"
