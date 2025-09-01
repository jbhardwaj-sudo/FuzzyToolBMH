import pandas as pd
from typing import List, Dict
import re

class DataPreprocessor:
    """
    Handles data preprocessing and cleaning operations for fuzzy matching.
    """
    
    @staticmethod
    def clean_text(text: str) -> str:
        """
        Clean and standardize text data.
        
        Args:
            text: Input text to clean
            
        Returns:
            Cleaned text string
        """
        if not isinstance(text, str):
            text = str(text)
            
        # Convert to lowercase
        text = text.lower()
        
        # Remove special characters and extra whitespace
        text = re.sub(r'[^\w\s]', ' ', text)
        text = re.sub(r'\s+', ' ', text)
        
        # Strip leading/trailing whitespace
        return text.strip()
    
    @staticmethod
    def prepare_dataframe(df: pd.DataFrame, columns: List[str]) -> pd.DataFrame:
        """
        Prepare DataFrame for matching by cleaning specified columns.
        
        Args:
            df: Input DataFrame
            columns: List of column names to clean
            
        Returns:
            Processed DataFrame
        """
        df_clean = df.copy()
        
        for col in columns:
            if col in df_clean.columns:
                df_clean[col] = df_clean[col].apply(DataPreprocessor.clean_text)
        
        return df_clean
    
    @staticmethod
    def validate_input_data(df: pd.DataFrame, required_columns: List[str]) -> bool:
        """
        Validate that input DataFrame has required columns.
        
        Args:
            df: Input DataFrame
            required_columns: List of required column names
            
        Returns:
            True if valid, raises ValueError if not
        """
        missing_cols = [col for col in required_columns if col not in df.columns]
        if missing_cols:
            raise ValueError(f"Missing required columns: {missing_cols}")
        return True
    
    @staticmethod
    def handle_missing_values(df: pd.DataFrame, columns: List[str], 
                            strategy: str = 'fill_empty') -> pd.DataFrame:
        """
        Handle missing values in specified columns.
        
        Args:
            df: Input DataFrame
            columns: List of columns to process
            strategy: Strategy to handle missing values ('fill_empty' or 'drop')
            
        Returns:
            Processed DataFrame
        """
        df_processed = df.copy()
        
        if strategy == 'fill_empty':
            for col in columns:
                if col in df_processed.columns:
                    df_processed[col] = df_processed[col].fillna('')
        elif strategy == 'drop':
            df_processed = df_processed.dropna(subset=columns)
        else:
            raise ValueError(f"Invalid strategy: {strategy}")
        
        return df_processed
    
    @staticmethod
    def standardize_format(df: pd.DataFrame, format_rules: Dict[str, str]) -> pd.DataFrame:
        """
        Standardize format of specified columns according to rules.
        
        Args:
            df: Input DataFrame
            format_rules: Dictionary mapping column names to format rules
            
        Returns:
            Processed DataFrame with standardized formats
        """
        df_standardized = df.copy()
        
        for column, rule in format_rules.items():
            if column not in df_standardized.columns:
                continue
                
            if rule == 'date':
                df_standardized[column] = pd.to_datetime(
                    df_standardized[column], 
                    errors='coerce'
                ).dt.strftime('%Y-%m-%d')
            elif rule == 'phone':
                df_standardized[column] = df_standardized[column].apply(
                    lambda x: re.sub(r'\D', '', str(x)) if pd.notnull(x) else x
                )
            elif rule == 'numeric':
                df_standardized[column] = pd.to_numeric(
                    df_standardized[column], 
                    errors='coerce'
                )
                
        return df_standardized
