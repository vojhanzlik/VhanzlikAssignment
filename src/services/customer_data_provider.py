import logging
from pathlib import Path
from typing import Generator, List
import pandas as pd
from pydantic import ValidationError

from src.config.validation_config import ValidationConfig
from src.models.customer import Customer

logger = logging.getLogger(__name__)


class CustomerDataProvider:
    """
    Acts as a generator of customer data by yielding batches of customer records from csv files.
    Returns only validated records.
    """
    
    def __init__(
        self, 
        csv_path: str | Path, 
        batch_size: int = 1000,
        validation_config: ValidationConfig = ValidationConfig()
    ):

        self.csv_path = Path(csv_path)
        self.batch_size = batch_size
        self.validation_config = validation_config
        
        if not self.csv_path.exists():
            raise FileNotFoundError(f"CSV file not found: {self.csv_path}")

    def get_next_batch(self) -> Generator[List[Customer], None, None]:
        """
        Generator that yields batches of validated customer records.
        """
        logger.info(f"Starting to process CSV file: {self.csv_path}")
        logger.info(f"Batch size: {self.batch_size}")
        logger.info(f"Validation config: min_age={self.validation_config.min_age}, "
                    f"max_age={self.validation_config.max_age}")

        total_processed = 0
        total_valid = 0

        try:
            for chunk_num, df_chunk in enumerate(
                    pd.read_csv(self.csv_path, chunksize=self.batch_size)
            ):
                logger.debug(f"Processing chunk {chunk_num + 1}, size: {len(df_chunk)}")

                valid_batch = self._validate_batch(df_chunk)

                total_processed += len(df_chunk)
                total_valid += len(valid_batch)

                if valid_batch:
                    yield valid_batch

                logger.debug(
                    f"Chunk {chunk_num + 1}: {len(valid_batch)}/{len(df_chunk)} "
                    f"records valid"
                )

        except Exception as e:
            logger.error(f"Error reading CSV file: {str(e)}")
            raise

        finally:
            logger.info(
                f"Processing complete. Total processed: {total_processed}, "
                f"Total valid: {total_valid}, "
                f"Success rate: {(total_valid / total_processed * 100):.2f}%"
            )

    def _validate_batch(self, df_batch: pd.DataFrame) -> List[Customer]:
        """
        Validate a batch of customer records.
        """
        valid_customers = []
        validation_context = self.validation_config.to_context()
        
        for index, row in df_batch.iterrows():
            try:
                customer_data = row.to_dict()
                customer = Customer.model_validate(
                    customer_data, 
                    context=validation_context
                )
                valid_customers.append(customer)
                
            except ValidationError as e:
                logger.error(
                    f"Validation failed for row {index}: {customer_data}. "
                    f"Errors: {e.errors()}"
                )
                continue
            except Exception as e:
                logger.error(
                    f"Unexpected error processing row {index}: {customer_data}. "
                    f"Error: {str(e)}"
                )
                continue
        
        return valid_customers
    

    
    def get_total_record_count(self) -> int:
        """
        Get the total number of records in the CSV file.

        """
        try:
            # Count lines efficiently without loading into memory
            with open(self.csv_path, 'r') as f:
                return sum(1 for _ in f) - 1  # Subtract header row
        except Exception as e:
            logger.error(f"Error counting records: {str(e)}")
            return 0