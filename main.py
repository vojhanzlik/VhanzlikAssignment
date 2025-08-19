import logging
import os

from src.config.main_config import MainConfig
from src.config.validation_config import ValidationConfig

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_config() -> MainConfig:
    """
    Loads validation config from a path specified by env variable
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


def main():

    config = load_config()
    logger.info(f"Loaded config: {config}")


if __name__ == "__main__":
    main()