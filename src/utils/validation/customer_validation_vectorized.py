"""
Vectorized versions of validation functions pandas DataFrame processing.
"""
import logging
import re
import uuid
import pandas as pd

logger = logging.getLogger(__name__)

# TODO: hard coded column names are probably not ideal

def validate_ages_df(df: pd.DataFrame, min_age: int = 18, max_age: int = 100) -> pd.DataFrame:
    """Validate age column and filter invalid records with logging."""
    age_mask = (df['Age'] >= min_age) & (df['Age'] <= max_age)
    invalid_count = len(df[~age_mask])
    if invalid_count > 0:
        logger.warning(f"Filtered {invalid_count} records with invalid age")
    return df[age_mask]


def validate_banner_ids_df(df: pd.DataFrame, min_banner_id: int = 0, max_banner_id: int = 99) -> pd.DataFrame:
    """Validate banner_id column and filter invalid records with logging."""
    banner_mask = (df['Banner_id'] >= min_banner_id) & (df['Banner_id'] <= max_banner_id)
    invalid_count = len(df[~banner_mask])
    if invalid_count > 0:
        logger.warning(f"Filtered {invalid_count} records with invalid banner_id")
    return df[banner_mask]


def validate_names_df(df: pd.DataFrame) -> pd.DataFrame:
    """Validate name column and filter invalid records with logging."""
    cleaned_names = df['Name'].str.strip()
    name_pattern = re.compile(r'^[A-Za-z\s]+$')
    name_mask = cleaned_names.str.match(name_pattern, na=False)
    
    invalid_count = len(df[~name_mask])
    if invalid_count > 0:
        logger.warning(f"Filtered {invalid_count} records with invalid names")
    
    validated_df = df[name_mask].copy()
    validated_df['Name'] = cleaned_names[name_mask]
    return validated_df


def validate_cookies_df(df: pd.DataFrame) -> pd.DataFrame:
    """Validate cookie column and filter invalid records with logging."""
    def is_valid_uuid(uuid_str):
        try:
            uuid.UUID(str(uuid_str))
            return True
        except (ValueError, TypeError):
            return False
    
    uuid_mask = df['Cookie'].apply(is_valid_uuid)
    invalid_count = len(df[~uuid_mask])
    if invalid_count > 0:
        logger.warning(f"Filtered {invalid_count} records with invalid UUIDs")
    return df[uuid_mask]