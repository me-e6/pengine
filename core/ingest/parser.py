"""
Data Parser
===========
Parses CSV and Excel files into structured data.
Handles various formats, encodings, and edge cases.
"""

import pandas as pd
from pathlib import Path
from typing import List, Dict, Tuple, Optional, Any
from dataclasses import dataclass
import logging
import re

logger = logging.getLogger(__name__)


@dataclass
class ParsedTable:
    """Result of parsing a single table/sheet"""
    name: str
    columns: List[str]
    data: List[Dict[str, Any]]
    row_count: int
    col_count: int
    numeric_columns: List[str]
    text_columns: List[str]
    date_columns: List[str]
    has_time_dimension: bool
    time_column: Optional[str]
    sample_values: Dict[str, List[Any]]  # First 5 values per column


@dataclass
class ParseResult:
    """Complete result of parsing a file"""
    success: bool
    filename: str
    file_type: str
    tables: List[ParsedTable]
    total_rows: int
    error_message: Optional[str] = None


class DataParser:
    """
    Intelligent data parser for CSV and Excel files.
    
    Features:
    - Auto-detects column types
    - Identifies time dimensions
    - Handles multiple sheets (Excel)
    - Cleans and normalizes data
    """
    
    # Patterns to detect time-related columns
    TIME_PATTERNS = [
        r'year', r'date', r'period', r'month', r'quarter', 
        r'fy', r'fiscal', r'time', r'yr', r'annual'
    ]
    
    def __init__(self):
        self.time_regex = re.compile(
            '|'.join(self.TIME_PATTERNS), 
            re.IGNORECASE
        )
    
    def parse(self, file_path: str) -> ParseResult:
        """
        Main entry point: parse any supported file.
        
        Args:
            file_path: Path to the file
            
        Returns:
            ParseResult with all extracted tables
        """
        path = Path(file_path)
        
        if not path.exists():
            return ParseResult(
                success=False,
                filename=path.name,
                file_type="unknown",
                tables=[],
                total_rows=0,
                error_message=f"File not found: {file_path}"
            )
        
        suffix = path.suffix.lower()
        
        try:
            if suffix == '.csv':
                return self._parse_csv(path)
            elif suffix in ['.xlsx', '.xls']:
                return self._parse_excel(path)
            else:
                return ParseResult(
                    success=False,
                    filename=path.name,
                    file_type=suffix,
                    tables=[],
                    total_rows=0,
                    error_message=f"Unsupported file type: {suffix}"
                )
        except Exception as e:
            logger.error(f"Parse error for {file_path}: {e}", exc_info=True)
            return ParseResult(
                success=False,
                filename=path.name,
                file_type=suffix,
                tables=[],
                total_rows=0,
                error_message=str(e)
            )
    
    def _parse_csv(self, path: Path) -> ParseResult:
        """Parse a CSV file"""
        
        # Try different encodings
        encodings = ['utf-8', 'latin-1', 'cp1252']
        df = None
        
        for encoding in encodings:
            try:
                df = pd.read_csv(path, encoding=encoding)
                break
            except UnicodeDecodeError:
                continue
        
        if df is None:
            return ParseResult(
                success=False,
                filename=path.name,
                file_type="csv",
                tables=[],
                total_rows=0,
                error_message="Could not decode file with any supported encoding"
            )
        
        # Clean the dataframe
        df = self._clean_dataframe(df)
        
        # Analyze and create ParsedTable
        table = self._analyze_dataframe(df, path.stem)
        
        return ParseResult(
            success=True,
            filename=path.name,
            file_type="csv",
            tables=[table],
            total_rows=table.row_count
        )
    
    def _parse_excel(self, path: Path) -> ParseResult:
        """Parse an Excel file (all sheets)"""
        
        try:
            xl = pd.ExcelFile(path)
        except Exception as e:
            return ParseResult(
                success=False,
                filename=path.name,
                file_type="excel",
                tables=[],
                total_rows=0,
                error_message=f"Could not open Excel file: {e}"
            )
        
        tables = []
        total_rows = 0
        
        for sheet_name in xl.sheet_names:
            try:
                df = pd.read_excel(xl, sheet_name=sheet_name)
                
                # Skip empty sheets
                if df.empty or len(df.columns) == 0:
                    continue
                
                # Clean the dataframe
                df = self._clean_dataframe(df)
                
                # Analyze
                table = self._analyze_dataframe(df, sheet_name)
                tables.append(table)
                total_rows += table.row_count
                
            except Exception as e:
                logger.warning(f"Could not parse sheet {sheet_name}: {e}")
                continue
        
        return ParseResult(
            success=len(tables) > 0,
            filename=path.name,
            file_type="excel",
            tables=tables,
            total_rows=total_rows,
            error_message=None if tables else "No valid sheets found"
        )
    
    def _clean_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean and normalize a dataframe"""
        
        # Remove completely empty rows and columns
        df = df.dropna(how='all').dropna(axis=1, how='all')
        
        # Clean column names
        df.columns = [self._clean_column_name(col) for col in df.columns]
        
        # Remove duplicate columns
        df = df.loc[:, ~df.columns.duplicated()]
        
        # Strip whitespace from string columns
        for col in df.select_dtypes(include=['object']).columns:
            df[col] = df[col].astype(str).str.strip()
            # Replace 'nan' strings with actual NaN
            df[col] = df[col].replace('nan', pd.NA)
        
        return df
    
    def _clean_column_name(self, name: Any) -> str:
        """Clean a column name"""
        name = str(name).strip()
        # Replace multiple spaces/underscores with single underscore
        name = re.sub(r'[\s_]+', '_', name)
        # Remove special characters except underscore
        name = re.sub(r'[^\w\s_]', '', name)
        return name
    
    def _analyze_dataframe(self, df: pd.DataFrame, name: str) -> ParsedTable:
        """Analyze a dataframe and create ParsedTable"""
        
        columns = df.columns.tolist()
        
        # Categorize columns
        numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
        date_cols = df.select_dtypes(include=['datetime']).columns.tolist()
        text_cols = [c for c in columns if c not in numeric_cols and c not in date_cols]
        
        # Detect time dimension
        time_col = self._detect_time_column(df, columns)
        has_time = time_col is not None
        
        # If we found a time column, check if it has multiple periods
        if has_time:
            unique_periods = df[time_col].nunique()
            has_time = unique_periods >= 2
        
        # Get sample values
        sample_values = {}
        for col in columns[:10]:  # Limit to first 10 columns
            sample_values[col] = df[col].head(5).tolist()
        
        # Convert to list of dicts (limit to 1000 rows for memory)
        data = df.head(1000).to_dict(orient='records')
        
        return ParsedTable(
            name=name,
            columns=columns,
            data=data,
            row_count=len(df),
            col_count=len(columns),
            numeric_columns=numeric_cols,
            text_columns=text_cols,
            date_columns=date_cols,
            has_time_dimension=has_time,
            time_column=time_col,
            sample_values=sample_values
        )
    
    def _detect_time_column(self, df: pd.DataFrame, columns: List[str]) -> Optional[str]:
        """Detect which column represents time/period"""
        
        for col in columns:
            # Check column name
            if self.time_regex.search(col):
                return col
            
            # Check if column contains year-like values (1900-2100)
            if col in df.columns:
                try:
                    values = df[col].dropna()
                    if len(values) > 0:
                        # Check if numeric and in year range
                        if pd.api.types.is_numeric_dtype(values):
                            min_val = values.min()
                            max_val = values.max()
                            if 1900 <= min_val <= 2100 and 1900 <= max_val <= 2100:
                                return col
                        # Check if string contains year pattern
                        elif pd.api.types.is_string_dtype(values):
                            sample = str(values.iloc[0])
                            if re.search(r'(19|20)\d{2}', sample):
                                return col
                except:
                    continue
        
        return None


# === Convenience function ===
def parse_file(file_path: str) -> ParseResult:
    """Quick parse function"""
    parser = DataParser()
    return parser.parse(file_path)
