import asyncio
import logging
import os

from src.config.main_config import MainConfig
from src.models.customer import Customer

from src.services.customer_data_provider_vectorized import CustomerDataProviderVectorized
from src.services.showads_api_service import ShowAdsApiService

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_config() -> MainConfig:
    """
    Loads config from a path specified by env variable
    falls back to default config.
    """
    config_path = os.getenv('CONFIG_PATH')

    if not config_path:
        logger.info("No CONFIG_PATH environment variable set, using default config")
        return MainConfig()

    try:
        config = MainConfig.from_json(config_path)
        logger.info(f"Loaded config from {config_path}")
    except Exception as e:
        logger.error(f"Error loading config from {config_path}: {e}")
        logger.info("Falling back to default config")
        config = MainConfig()
    return config


async def main():

    config = load_config()
    logger.info(f"Loaded config: {config}")

    customer_provider = CustomerDataProviderVectorized(
        config.validation_config,
        config.customer_data_path
    )

    async with ShowAdsApiService("project_key") as service:
        try:
            for batch in customer_provider.get_next_batch():
                await service.send_customers(batch)
                logger.info(f"Successfully sent {len(batch)} customers to ShowAds API")
        except Exception as e:
            logger.error(f"Failed to send customers: {e}")

if __name__ == "__main__":
    asyncio.run(main())