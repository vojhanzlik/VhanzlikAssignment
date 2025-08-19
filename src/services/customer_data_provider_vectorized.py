import logging
from pathlib import Path
from typing import Generator, List
import pandas as pd

from src.config.validation_config import ValidationConfig
from src.models.customer import Customer
from src.services.customer_data_provider import CustomerDataProvider
from src.utils.validation.customer_validation_vectorized import (
    validate_ages_df,
    validate_banner_ids_df,
    validate_names_df,
    validate_cookies_df
)

logger = logging.getLogger(__name__)


class CustomerDataProviderVectorized(CustomerDataProvider):
    """
    Customer data provider using pandas operations for processing.
    """
    
    def __init__(self, csv_path: str | Path, batch_size: int = 1000, validation_config: ValidationConfig = ValidationConfig()):

        super().__init__(csv_path, batch_size, validation_config)

    def get_next_batch(self) -> Generator[List[Customer], None, None]:
        """
        Generator that yields batches of validated customer records using optimized approach.
        """
        logger.info(f"Starting optimized processing of CSV file: {self.csv_path}")
        logger.info(f"Batch size: {self.batch_size}")
        logger.info(f"Validation config: min_age={self.validation_config.min_age}, "
                    f"max_age={self.validation_config.max_age}")

        total_processed = 0
        total_valid = 0

        try:
            for chunk_num, df_chunk in enumerate(pd.read_csv(self.csv_path, chunksize=self.batch_size)):

                logger.debug(f"Processing chunk {chunk_num + 1}, size: {len(df_chunk)}")

                valid_df = self._validate_batch(df_chunk)

                total_processed += len(df_chunk)
                total_valid += len(valid_df)

                if len(valid_df) > 0:
                    customers = self._create_customers_bulk(valid_df)
                    if customers:
                        yield customers

                logger.debug(f"Chunk {chunk_num + 1}: {len(valid_df)}/{len(df_chunk)} records valid")

        except Exception as e:
            logger.error(f"Error reading CSV file: {str(e)}")
            raise

        finally:
            success_rate = (total_valid / total_processed * 100) if total_processed > 0 else 0
            logger.info(
                f"Processing complete. Total processed: {total_processed}, "
                f"Total valid: {total_valid}, "
                f"Success rate: {success_rate:.2f}%"
            )
    
    def _validate_batch(self, df_batch: pd.DataFrame) -> pd.DataFrame:
        """
        Validate batch using vectorized pandas operations.

        """
        original_count = len(df_batch)

        df_batch = validate_ages_df(
            df_batch,
            min_age=self.validation_config.min_age,
            max_age=self.validation_config.max_age
        )
        df_batch = validate_banner_ids_df(
            df_batch,
            min_banner_id=self.validation_config.min_banner_id,
            max_banner_id=self.validation_config.max_banner_id
        )
        df_batch = validate_names_df(df_batch)
        df_batch = validate_cookies_df(df_batch)

        final_count = len(df_batch)
        logger.debug(f"Batch validation: {original_count} -> {final_count} records ({final_count/original_count*100:.1f}%)")

        return df_batch
    
    def _create_customers_bulk(self, df: pd.DataFrame) -> List[Customer]:
        """
        Create Customer objects from validated DataFrame.
        """
        customers = []
        validation_context = self.validation_config.to_context()
        
        records = df.to_dict('records')
        
        for record in records:
            try:
                customer = Customer.model_validate(record, context=validation_context)
                customers.append(customer)
            except Exception as e:
                # this should never happen as validation was done with pandas
                logger.error(f"Unexpected error creating customer from validated data: {record}, Error: {e}")
                continue
        
        return customers
    
