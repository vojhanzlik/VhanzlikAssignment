"""
Vectorized versions of validation functions pandas DataFrame processing.
"""
import re
import uuid
import logging
import pandas as pd

logger = logging.getLogger(__name__)

# TODO: hard coded column names are probably not ideal

def validate_ages_df(df: pd.DataFrame, min_age: int = 18, max_age: int = 100) -> pd.DataFrame:
    """Validate age column and filter invalid records with logging."""
    age_mask = (df['Age'] >= min_age) & (df['Age'] <= max_age)
    invalid_rows = df[~age_mask]
    if not invalid_rows.empty:
        logger.warning(f"Filtered {len(invalid_rows)} records with invalid age:\n{invalid_rows}")
    return df[age_mask]


def validate_banner_ids_df(df: pd.DataFrame, min_banner_id: int = 0, max_banner_id: int = 99) -> pd.DataFrame:
    """Validate banner_id column and filter invalid records with logging."""
    banner_mask = (df['Banner_id'] >= min_banner_id) & (df['Banner_id'] <= max_banner_id)
    invalid_rows = df[~banner_mask]
    if not invalid_rows.empty:
        logger.warning(f"Filtered {len(invalid_rows)} records with invalid banner_id:\n{invalid_rows}")
    return df[banner_mask]


def validate_names_df(df: pd.DataFrame) -> pd.DataFrame:
    """Validate name column and filter invalid records with logging."""
    cleaned_names = df['Name'].str.strip()
    name_pattern = re.compile(r'^[A-Za-z\s]+$')
    name_mask = cleaned_names.str.match(name_pattern, na=False)

    invalid_rows = df[~name_mask]
    if not invalid_rows.empty:
        logger.warning(f"Filtered {len(invalid_rows)} records with invalid names:\n{invalid_rows}")

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
    invalid_rows = df[~uuid_mask]
    if not invalid_rows.empty:
        logger.warning(f"Filtered {len(invalid_rows)} records with invalid UUIDs:\n{invalid_rows}")
    return df[uuid_mask]
