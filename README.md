# ShowAds Data Processor

Processes customer CSV data and sends it to the ShowAds API in bulk batches with retry logic.

## How it works

The script loads customer data from CSV in batches, validates it, chunks each batch into max 1000-record batches, and sends them to the ShowAds API. It retries on failures (429, 500, 401).

Designed to run once and exit. The assignment didn't specify whether it should be a web server, triggered externally, or periodically run itself, etc - so it runs as a simple script.

## Configuration

Mount your own files to customize:
- **Config**: `/app/config/config.json` - validation rules
- **Data**: `/app/data/data.csv` - customer CSV input file

If the file is not mounted, the default one is used.


## Docker Run
From the root dir:
```bash
# Build
docker build -t showads-data-connector .

# Run with default files
docker run --rm showads-data-connector

# Run with custom config and data
docker run --rm -v custom/path/to/config/config.json:/app/config/config.json -v custom/path/to/data/data.csv:/app/data/data.csv showads-data-connector
```

## Local Run

```bash
python main.py
```

## Performance Implementations

There are two customer data provider implementations available.
I initially chose Pydantic validation because to me it seems more clear, but I immediately realized it would not be very efficient. 

- **Standard (Unused)** (`CustomerDataProvider`): Uses Pydantic validation for readability
- **Vectorized** (`CustomerDataProviderVectorized`): Uses pandas operations

The vectorized version is significantly faster for large CSV files (see [benchmarks folder](benchmarks/README.md) for more info).
