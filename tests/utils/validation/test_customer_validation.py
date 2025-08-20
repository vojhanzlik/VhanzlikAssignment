import pytest
from unittest.mock import Mock
from pydantic_core.core_schema import ValidationInfo

from src.utils.validation.customer_validation import (
    validate_name, validate_cookie, validate_banner_id, validate_age
)
from src.config.validation_config import MIN_AGE_PARAM, MAX_AGE_PARAM, MIN_BANNER_ID_PARAM, MAX_BANNER_ID_PARAM


class TestValidateName:
    """Test cases for validate_name function."""
    
    def test_valid_names(self):
        """Test valid name formats."""
        valid_names = [
            "John Doe",
            "Mary Jane Watson", 
            "José María",
            "Anne Marie",
            "J",
            "A B C D E F"
        ]
        
        for name in valid_names:
            result = validate_name(name)
            assert result == name.strip()
    
    def test_whitespace_trimming(self):
        """Test that whitespace is properly trimmed."""
        names_with_whitespace = [
            "  John Doe  ",
            "\tMary Jane\t",
            "\n Alice Bob \n",
            "   Single   "
        ]
        
        expected = ["John Doe", "Mary Jane", "Alice Bob", "Single"]
        
        for name, expected_result in zip(names_with_whitespace, expected):
            result = validate_name(name)
            assert result == expected_result
    
    def test_invalid_names(self):
        """Test invalid name formats."""
        invalid_names = [
            "John123",
            "Mary@Email", 
            "User-Name",
            "Name_With_Underscore",
            "123456",
            "John.Doe",
            "",
            "   ",
            "Name123Invalid",
            "Special!Character"
        ]
        
        for name in invalid_names:
            with pytest.raises(ValueError) as exc_info:
                validate_name(name)
            assert "Name must contain only letters and spaces" in str(exc_info.value)


class TestValidateCookie:
    """Test cases for validate_cookie function."""
    
    def test_valid_uuids(self):
        """Test valid UUID formats."""
        valid_uuids = [
            "26555324-53df-4eb1-8835-e6c0078bb2c0",
            "87654321-1234-5678-9abc-def012345678", 
            "00000000-0000-0000-0000-000000000000",
            "ffffffff-ffff-ffff-ffff-ffffffffffff",
            "AAAAAAAA-BBBB-CCCC-DDDD-EEEEEEEEEEEE"
        ]
        
        for uuid_str in valid_uuids:
            result = validate_cookie(uuid_str)
            assert result == uuid_str
    
    def test_invalid_uuids(self):
        """Test invalid UUID formats."""
        invalid_uuids = [
            "invalid-uuid-format",
            "12345",
            "not-a-uuid",
            "",
            "26555324-53df-4eb1-8835-e6c0078bb2c0-extra",
            "26555324-53df-4eb1-8835",
            "26555324-53df-4eb1-8835-e6c0078bb2c0-",
            "too-short-uuid",
            "zzzzzzzz-zzzz-zzzz-zzzz-zzzzzzzzzzzz"
        ]
        
        for uuid_str in invalid_uuids:
            with pytest.raises(ValueError) as exc_info:
                validate_cookie(uuid_str)
            assert "Cookie must be a valid UUID format" in str(exc_info.value)


class TestValidateBannerId:
    """Test cases for validate_banner_id function."""
    
    def test_valid_banner_ids_default_range(self):
        """Test valid banner IDs with default range (0-99)."""
        info = Mock(spec=ValidationInfo)
        info.context = {
            MIN_BANNER_ID_PARAM: 0,
            MAX_BANNER_ID_PARAM: 99
        }
        
        valid_ids = [0, 1, 25, 50, 75, 99]
        
        for banner_id in valid_ids:
            result = validate_banner_id(banner_id, info)
            assert result == banner_id
    
    def test_valid_banner_ids_custom_range(self):
        """Test valid banner IDs with custom range."""
        info = Mock(spec=ValidationInfo)
        info.context = {
            MIN_BANNER_ID_PARAM: 10,
            MAX_BANNER_ID_PARAM: 50
        }
        
        valid_ids = [10, 15, 25, 35, 45, 50]
        
        for banner_id in valid_ids:
            result = validate_banner_id(banner_id, info)
            assert result == banner_id
    
    def test_invalid_banner_ids_default_range(self):
        """Test invalid banner IDs with default range."""
        info = Mock(spec=ValidationInfo)
        info.context = {
            MIN_BANNER_ID_PARAM: 0,
            MAX_BANNER_ID_PARAM: 99
        }
        
        invalid_ids = [-1, -10, 100, 150, 1000]
        
        for banner_id in invalid_ids:
            with pytest.raises(ValueError):
                validate_banner_id(banner_id, info)
    
    def test_invalid_banner_ids_custom_range(self):
        """Test invalid banner IDs with custom range."""
        info = Mock(spec=ValidationInfo)
        info.context = {
            MIN_BANNER_ID_PARAM: 10,
            MAX_BANNER_ID_PARAM: 50
        }
        
        invalid_ids = [5, 9, 51, 75, 100]
        
        for banner_id in invalid_ids:
            with pytest.raises(ValueError):
                validate_banner_id(banner_id, info)
    
    def test_missing_context(self):
        """Test validation without proper context."""
        info = Mock(spec=ValidationInfo)
        info.context = None
        
        with pytest.raises(ValueError) as exc_info:
            validate_banner_id(50, info)
        assert "Insufficient context information" in str(exc_info.value)
    
    def test_incomplete_context(self):
        """Test validation with incomplete context."""
        info = Mock(spec=ValidationInfo)
        info.context = {MIN_BANNER_ID_PARAM: 0}  # Missing MAX_BANNER_ID_PARAM
        
        with pytest.raises(ValueError) as exc_info:
            validate_banner_id(50, info)
        assert "Insufficient context information" in str(exc_info.value)


class TestValidateAge:
    """Test cases for validate_age function."""
    
    def test_valid_ages_default_range(self):
        """Test valid ages with default range (18-100)."""
        info = Mock(spec=ValidationInfo)
        info.context = {
            MIN_AGE_PARAM: 18,
            MAX_AGE_PARAM: 100
        }
        
        valid_ages = [18, 25, 50, 75, 100]
        
        for age in valid_ages:
            result = validate_age(age, info)
            assert result == age
    
    def test_valid_ages_custom_range(self):
        """Test valid ages with custom range."""
        info = Mock(spec=ValidationInfo)
        info.context = {
            MIN_AGE_PARAM: 21,
            MAX_AGE_PARAM: 65
        }
        
        valid_ages = [21, 30, 45, 60, 65]
        
        for age in valid_ages:
            result = validate_age(age, info)
            assert result == age
    
    def test_invalid_ages_below_minimum(self):
        """Test ages below minimum."""
        info = Mock(spec=ValidationInfo)
        info.context = {
            MIN_AGE_PARAM: 18,
            MAX_AGE_PARAM: 100
        }
        
        invalid_ages = [0, 5, 10, 17]
        
        for age in invalid_ages:
            with pytest.raises(ValueError) as exc_info:
                validate_age(age, info)
            assert f"Age must be at least 18" in str(exc_info.value)
    
    def test_invalid_ages_above_maximum(self):
        """Test ages above maximum."""
        info = Mock(spec=ValidationInfo)
        info.context = {
            MIN_AGE_PARAM: 18,
            MAX_AGE_PARAM: 100
        }
        
        invalid_ages = [101, 120, 150, 200]
        
        for age in invalid_ages:
            with pytest.raises(ValueError) as exc_info:
                validate_age(age, info)
            assert f"Age must not exceed 100" in str(exc_info.value)
    
    def test_custom_age_limits_validation(self):
        """Test validation with custom age limits."""
        info = Mock(spec=ValidationInfo)
        info.context = {
            MIN_AGE_PARAM: 25,
            MAX_AGE_PARAM: 60
        }
        
        # Valid age
        result = validate_age(40, info)
        assert result == 40
        
        # Below minimum
        with pytest.raises(ValueError) as exc_info:
            validate_age(20, info)
        assert "Age must be at least 25" in str(exc_info.value)
        
        # Above maximum
        with pytest.raises(ValueError) as exc_info:
            validate_age(70, info)
        assert "Age must not exceed 60" in str(exc_info.value)
    
    def test_missing_context(self):
        """Test validation without proper context."""
        info = Mock(spec=ValidationInfo)
        info.context = None
        
        with pytest.raises(ValueError) as exc_info:
            validate_age(25, info)
        assert "Insufficient context information" in str(exc_info.value)
    
    def test_incomplete_context(self):
        """Test validation with incomplete context."""
        info = Mock(spec=ValidationInfo)
        info.context = {MIN_AGE_PARAM: 18}  # Missing MAX_AGE_PARAM
        
        with pytest.raises(ValueError) as exc_info:
            validate_age(25, info)
        assert "Insufficient context information" in str(exc_info.value)
    
    @pytest.mark.parametrize("min_age,max_age,test_age", [
        (16, 80, 40),
        (21, 65, 35),
        (25, 70, 50),
        (18, 100, 60),
    ])
    def test_various_age_configurations(self, min_age, max_age, test_age):
        """Test various age configuration combinations."""
        info = Mock(spec=ValidationInfo)
        info.context = {
            MIN_AGE_PARAM: min_age,
            MAX_AGE_PARAM: max_age
        }
        
        result = validate_age(test_age, info)
        assert result == test_age