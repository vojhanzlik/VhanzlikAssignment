"""Main entry point for the data connector"""

import asyncio
import logging
from pathlib import Path

from src.config.main_config import MainConfig

from src.services.customer_data_provider_vectorized import CustomerDataProviderVectorized
from src.services.showads_api_service import ShowAdsApiService

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

CUSTOMER_DATA_PATH = Path(__file__).parent / 'data' / 'data.csv'
CONFIG_PATH = Path(__file__).parent / 'config' / 'config.json'

def load_config() -> MainConfig:
    """
    Loads config from a path specified by env variable
    falls back to default config.
    """
    try:
        config = MainConfig.from_json(CONFIG_PATH)
        logger.info(f"Loaded config from {CONFIG_PATH}")
    except Exception as e:
        logger.error(f"Error loading config from {CONFIG_PATH}: {e}")
        logger.info("Falling back to default config")
        config = MainConfig()
    return config


async def main():
    config = load_config()
    logger.info(f"Loaded config: {config}")

    customer_provider = CustomerDataProviderVectorized(
        config.validation_config,
        CUSTOMER_DATA_PATH,
        batch_size=10000
    )

    async with ShowAdsApiService("project_key") as service:
        try:
            for batch in customer_provider.get_next_batch():
                await service.send_customers(batch)
        except Exception as e:
            logger.error(f"Failed to send customers: {e}")

if __name__ == "__main__":
    asyncio.run(main())