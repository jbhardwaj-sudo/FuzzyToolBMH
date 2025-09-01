import pandas as pd
from typing import List, Dict, Any, Union
import os

class FileHandler:
    """
    Handles file operations for the fuzzy matching tool.
    """
    
    SUPPORTED_FORMATS = ['.xlsx', '.xls', '.csv']
    
    @staticmethod
    def read_file(file_path: str) -> pd.DataFrame:
        """
        Read data from file into DataFrame.
        
        Args:
            file_path: Path to input file
            
        Returns:
            DataFrame containing file data
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        file_ext = os.path.splitext(file_path)[1].lower()
        if file_ext not in FileHandler.SUPPORTED_FORMATS:
            raise ValueError(f"Unsupported file format: {file_ext}")
        
        try:
            if file_ext in ['.xlsx', '.xls']:
                return pd.read_excel(file_path)
            elif file_ext == '.csv':
                return pd.read_csv(file_path)
        except Exception as e:
            raise IOError(f"Error reading file: {str(e)}")
    
    @staticmethod
    def save_results(df: pd.DataFrame, 
                    output_path: str,
                    include_scores: bool = True) -> None:
        """
        Save matching results to file.
        
        Args:
            df: DataFrame containing results
            output_path: Path to save output file
            include_scores: Whether to include score columns
        """
        try:
            file_ext = os.path.splitext(output_path)[1].lower()
            
            if file_ext == '.csv':
                df.to_csv(output_path, index=False)
            elif file_ext in ['.xlsx', '.xls']:
                df.to_excel(output_path, index=False)
            else:
                raise ValueError(f"Unsupported output format: {file_ext}")
                
        except Exception as e:
            raise IOError(f"Error saving results: {str(e)}")
    
    @staticmethod
    def validate_file(file_path: str, required_columns: List[str] = None) -> bool:
        """
        Validate input file format and content.
        
        Args:
            file_path: Path to file to validate
            required_columns: List of required column names
            
        Returns:
            True if valid, raises appropriate exception if not
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        file_ext = os.path.splitext(file_path)[1].lower()
        if file_ext not in FileHandler.SUPPORTED_FORMATS:
            raise ValueError(f"Unsupported file format: {file_ext}")
        
        if required_columns:
            df = FileHandler.read_file(file_path)
            missing_cols = [col for col in required_columns if col not in df.columns]
            if missing_cols:
                raise ValueError(f"Missing required columns: {missing_cols}")
        
        return True
    
    @staticmethod
    def get_column_names(file_path: str) -> List[str]:
        """
        Get list of column names from file.
        
        Args:
            file_path: Path to input file
            
        Returns:
            List of column names
        """
        df = FileHandler.read_file(file_path)
        return df.columns.tolist()
    
    @staticmethod
    def read_lists(file_path: str, 
                   list1_col: str, 
                   list2_col: str) -> tuple[List[str], List[str]]:
        """
        Read two lists from specified columns in a file.
        
        Args:
            file_path: Path to input file
            list1_col: Column name for first list
            list2_col: Column name for second list
            
        Returns:
            Tuple of (list1, list2)
        """
        df = FileHandler.read_file(file_path)
        
        if list1_col not in df.columns or list2_col not in df.columns:
            raise ValueError(f"Missing required columns: {list1_col} and/or {list2_col}")
        
        return df[list1_col].tolist(), df[list2_col].tolist()
