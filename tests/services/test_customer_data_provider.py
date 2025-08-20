import pytest
import tempfile
import csv
from pathlib import Path
from unittest.mock import patch, Mock

from src.services.customer_data_provider import CustomerDataProvider
from src.config.validation_config import ValidationConfig
from src.models.customer import Customer


class TestCustomerDataProvider:
    """Test cases for CustomerDataProvider class."""
    
    @pytest.fixture
    def config(self):
        """Provide test configuration."""
        return ValidationConfig(min_age=18, max_age=100, min_banner_id=0, max_banner_id=99)
    
    @pytest.fixture
    def valid_csv_data(self) -> list:
        """Provide valid CSV test data."""
        return [
            ["Name", "Age", "Cookie", "Banner_id"],
            ["John Doe", "35", "26555324-53df-4eb1-8835-e6c0078bb2c0", "35"],
            ["Jane Smith", "28", "87654321-1234-5678-9abc-def012345678", "42"]
        ]
    
    @pytest.fixture
    def mixed_csv_data(self) -> list:
        """Provide CSV data with valid and invalid records."""
        return [
            ["Name", "Age", "Cookie", "Banner_id"],
            ["John Doe", "35", "26555324-53df-4eb1-8835-e6c0078bb2c0", "35"],  # Valid
            ["Jane Smith", "28", "87654321-1234-5678-9abc-def012345678", "42"],  # Valid
            ["Bob Wilson", "-5", "11111111-2222-3333-4444-555555555555", "15"],  # Invalid age
            ["Invalid Name123", "40", "98765432-1098-7654-3210-fedcba987654", "30"],  # Invalid name
            ["Mike Davis", "25", "99999999-8888-7777-6666-555555555555", "150"]  # Invalid banner_id
        ]
    
    def create_temp_csv(self, data: list):
        """Create a temporary CSV file with given data."""
        temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv')
        writer = csv.writer(temp_file)
        for row in data:
            writer.writerow(row)
        temp_file.close()
        return temp_file.name
    
    def test_initialization_valid_path(self, config: ValidationConfig, valid_csv_data: list):
        """Test initialization with valid CSV path."""
        csv_path = self.create_temp_csv(valid_csv_data)
        try:
            provider = CustomerDataProvider(config, csv_path, batch_size=100)
            assert provider.csv_path == Path(csv_path)
            assert provider.batch_size == 100
            assert provider.validation_config == config
        finally:
            Path(csv_path).unlink()
    
    def test_initialization_invalid_path(self, config: ValidationConfig):
        """Test initialization with invalid CSV path."""
        with pytest.raises(FileNotFoundError):
            CustomerDataProvider(config, "non_existent_file.csv")

    
    def test_get_next_batch_all_valid(self, config: ValidationConfig, valid_csv_data: list):
        """Test processing CSV with all valid records."""
        csv_path = self.create_temp_csv(valid_csv_data)
        try:
            provider = CustomerDataProvider(config, csv_path, batch_size=1)
            
            batches = list(provider.get_next_batch())
            
            # Should have 2 batches
            assert len(batches) == 2
            
            # First batch should have 1 customer
            assert len(batches[0]) == 1
            assert all(isinstance(customer, Customer) for customer in batches[0])
            
            # Second batch should have 1 customer
            assert len(batches[1]) == 1
            assert isinstance(batches[1][0], Customer)

            first_customer = batches[0][0]
            assert first_customer.Name == "John Doe"
            assert first_customer.Age == 35
            assert first_customer.Banner_id == 35
            
        finally:
            Path(csv_path).unlink()
    
    def test_get_next_batch_mixed_validity(self, config: ValidationConfig, mixed_csv_data: list):
        """Test processing CSV with mixed valid/invalid records."""
        csv_path = self.create_temp_csv(mixed_csv_data)
        try:
            provider = CustomerDataProvider(config, csv_path, batch_size=10)
            
            batches = list(provider.get_next_batch())
            
            # Should have 1 batch
            assert len(batches) == 1
            
            # Should only have 2 valid customers
            valid_customers = batches[0]
            assert len(valid_customers) == 2
            
            names = [customer.Name for customer in valid_customers]
            assert "John Doe" in names
            assert "Jane Smith" in names
            
        finally:
            Path(csv_path).unlink()
    
    def test_empty_batch(self, config: ValidationConfig):
        """Test that empty batches are not yielded."""
        # only invalid records
        invalid_data = [
            ["Name", "Age", "Cookie", "Banner_id"],
            ["Invalid123", "0", "invalid-uuid", "150"]
        ]
        
        csv_path = self.create_temp_csv(invalid_data)
        try:
            provider = CustomerDataProvider(config, csv_path)
            
            batches = list(provider.get_next_batch())
            
            assert len(batches) == 0
            
        finally:
            Path(csv_path).unlink()
    
    def test_correct_batch_sizes(self, config: ValidationConfig):
        """Test that batch size is respected."""
        valid_data = [["Name", "Age", "Cookie", "Banner_id"]]
        for i in range(25):
            valid_data.append([
                f"Customer",
                "25",
                "26555324-53df-4eb1-8835-e6c0078bb2c0",
                "35"
            ])
        
        csv_path = self.create_temp_csv(valid_data)
        try:
            provider = CustomerDataProvider(config, csv_path, batch_size=10)
            
            batches = list(provider.get_next_batch())
            
            assert len(batches) == 3
            assert len(batches[0]) == 10
            assert len(batches[1]) == 10
            assert len(batches[2]) == 5
            
        finally:
            Path(csv_path).unlink()
