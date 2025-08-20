
## Comparison of two implentation of the csv parsing and validation

After implementing the [customer_data_provider.py](../src/services/customer_data_provider.py) I immediately realized
this would not be a very efficient approach, so I [re-implemented](../src/services/customer_data_provider_vectorized.py) the same interface using pandas and wanted to see just 
how much faster it would be, and it turns out to be even faster than I had thought. So even though I find the pydantic 
way of validation much more readable and understandable then dropping rows in pandas, the difference in efficiency seems well worth it:)

### Performance Results

| Dataset Size      | Valid Ratio | Standard Provider | Vectorized Provider | Speedup |
|-------------------|-------------|-------------------|---------------------|---------|
| 1,000,000 records | 50%         | 214.1577s | 3.8710s | **55.32x faster** |

## Running the benchmark
From the root dir:
```bash
python run_data_provider_benchmark.py
```
