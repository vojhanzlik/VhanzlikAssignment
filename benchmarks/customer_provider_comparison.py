"""
Timing comparison between CustomerDataProvider and CustomerDataProviderVectorized.

"""
import tempfile
import csv
import time
from pathlib import Path

from src.services.customer_data_provider import CustomerDataProvider
from src.services.customer_data_provider_vectorized import CustomerDataProviderVectorized
from src.config.validation_config import ValidationConfig


def create_test_csv(size: int, valid_ratio: float = 0.8) -> str:
    """Create a temporary CSV file with test data."""
    temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv')
    writer = csv.writer(temp_file)
    
    writer.writerow(["Name", "Age", "Cookie", "Banner_id"])
    
    valid_count = int(size * valid_ratio)
    invalid_count = size - valid_count
    
    for i in range(valid_count):
        writer.writerow([
            "Customer",
            "10",
            "26555324-53df-4eb1-8835-e6c0078bb2c0",
            "10"
        ])
    
    for i in range(invalid_count):
        writer.writerow([
            f"Invalid{i}",
            "10",
            "26555324-53df-4eb1-8835-e6c0078bb2c0",
            "10"
        ])
    
    temp_file.close()
    return temp_file.name


def timer(
        provider_class: CustomerDataProviderVectorized | CustomerDataProvider,
        csv_path: str,
        batch_size: int = 1000
) -> float:
    """
    Time a data provider and return execution time.
    """
    config = ValidationConfig()
    provider = provider_class(config, csv_path, batch_size=batch_size)
    
    start_time = time.perf_counter()
    
    for batch in provider.get_next_batch():
        continue

    end_time = time.perf_counter()
    execution_time = end_time - start_time
    
    return execution_time


def run_comparison(dataset_size: int, valid_ratio: float = 0.8):
    """Run comparison for a specific dataset size."""
    print(f"\n* ({dataset_size:,} records, {valid_ratio:.0%} valid)")

    csv_path = create_test_csv(dataset_size, valid_ratio)
    
    try:
        print("Testing Standard Provider...")
        std_time = timer(CustomerDataProvider, csv_path)
        
        print("Testing Vectorized Provider...")
        vec_time = timer(CustomerDataProviderVectorized, csv_path)
        
        print(f"\n Results:")
        print(f"Standard Provider: {std_time:.4f}s")
        print(f"Vectorized Provider: {vec_time:.4f}s")

        if vec_time < std_time:
            speedup = std_time / vec_time
            print(f"Vectorized is {speedup:.2f}x faster")
        else:
            slowdown = vec_time / std_time
            print(f"Vectorized is {slowdown:.2f}x slower")
        
    finally:
        Path(csv_path).unlink()
