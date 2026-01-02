"""
Smart Chunker
=============
Intelligently breaks parsed data into meaningful chunks
for storage in the knowledge base.

Chunking Strategy:
- Each table becomes at least one chunk
- Large tables are split by logical groupings
- Time series data preserves temporal continuity
- Summary chunks are created for quick retrieval
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import json
import hashlib

from .parser import ParsedTable, ParseResult


@dataclass
class DataChunkRaw:
    """
    Raw chunk before domain tagging and embedding.
    Will be converted to full DataChunk after AI processing.
    """
    chunk_id: str
    content: str                    # Human-readable text representation
    content_type: str               # "summary", "table", "time_series", "statistics"
    
    # Source tracking
    source_table: str
    source_file: str
    
    # Structured data
    columns: List[str]
    data_rows: List[Dict]
    row_count: int
    
    # Time info (if applicable)
    has_time_dimension: bool
    time_column: Optional[str]
    time_range: Optional[tuple]     # (start, end)
    
    # For retrieval
    key_entities: List[str]         # Important values found
    numeric_highlights: Dict[str, Any]  # min, max, avg of numeric cols
    
    # Metadata
    chunk_index: int                # Position in sequence
    total_chunks: int               # Total chunks from same table


class SmartChunker:
    """
    Intelligent chunking system that creates meaningful,
    retrievable units from parsed data.
    
    Creates multiple chunk types:
    1. Summary chunk - High-level overview
    2. Table chunk - Full or partial table data
    3. Time slice chunks - Data grouped by time period
    4. Statistics chunk - Numeric summaries
    """
    
    def __init__(self, max_rows_per_chunk: int = 50):
        self.max_rows = max_rows_per_chunk
    
    def chunk(self, parse_result: ParseResult, source_name: str) -> List[DataChunkRaw]:
        """
        Main entry: chunk all tables from a parse result.
        
        Args:
            parse_result: Output from DataParser
            source_name: Name of the data source (e.g., "Census 2021")
            
        Returns:
            List of DataChunkRaw ready for tagging
        """
        if not parse_result.success:
            return []
        
        all_chunks = []
        
        for table in parse_result.tables:
            chunks = self._chunk_table(table, parse_result.filename, source_name)
            all_chunks.extend(chunks)
        
        return all_chunks
    
    def _chunk_table(
        self, 
        table: ParsedTable, 
        filename: str,
        source_name: str
    ) -> List[DataChunkRaw]:
        """Chunk a single parsed table"""
        
        chunks = []
        
        # 1. Always create a summary chunk
        summary_chunk = self._create_summary_chunk(table, filename, source_name)
        chunks.append(summary_chunk)
        
        # 2. Create statistics chunk if numeric data exists
        if table.numeric_columns:
            stats_chunk = self._create_statistics_chunk(table, filename, source_name)
            chunks.append(stats_chunk)
        
        # 3. Create data chunks
        if table.has_time_dimension and table.time_column:
            # Time-aware chunking
            time_chunks = self._create_time_chunks(table, filename, source_name)
            chunks.extend(time_chunks)
        elif table.row_count <= self.max_rows:
            # Small table - single chunk
            data_chunk = self._create_full_table_chunk(table, filename, source_name)
            chunks.append(data_chunk)
        else:
            # Large table - split into parts
            split_chunks = self._create_split_chunks(table, filename, source_name)
            chunks.extend(split_chunks)
        
        # Update total_chunks count
        total = len(chunks)
        for i, chunk in enumerate(chunks):
            chunk.chunk_index = i
            chunk.total_chunks = total
        
        return chunks
    
    def _create_summary_chunk(
        self, 
        table: ParsedTable, 
        filename: str,
        source_name: str
    ) -> DataChunkRaw:
        """Create a high-level summary chunk"""
        
        # Build human-readable summary
        content_parts = [
            f"Data Summary: {table.name}",
            f"Source: {source_name}",
            f"",
            f"Structure:",
            f"- Total rows: {table.row_count}",
            f"- Total columns: {table.col_count}",
            f"",
            f"Columns: {', '.join(table.columns[:15])}",  # Limit columns shown
        ]
        
        if table.numeric_columns:
            content_parts.append(f"Numeric fields: {', '.join(table.numeric_columns[:10])}")
        
        if table.has_time_dimension:
            content_parts.append(f"Time dimension: {table.time_column}")
            time_range = self._get_time_range(table)
            if time_range:
                content_parts.append(f"Period: {time_range[0]} to {time_range[1]}")
        
        # Add sample data description
        if table.sample_values:
            content_parts.append("")
            content_parts.append("Sample values:")
            for col, values in list(table.sample_values.items())[:5]:
                sample = [str(v)[:30] for v in values[:3]]
                content_parts.append(f"  {col}: {', '.join(sample)}")
        
        content = "\n".join(content_parts)
        
        # Extract key entities (unique values from text columns)
        key_entities = self._extract_key_entities(table)
        
        return DataChunkRaw(
            chunk_id=self._generate_id(filename, table.name, "summary"),
            content=content,
            content_type="summary",
            source_table=table.name,
            source_file=filename,
            columns=table.columns,
            data_rows=[],  # Summary doesn't include raw data
            row_count=table.row_count,
            has_time_dimension=table.has_time_dimension,
            time_column=table.time_column,
            time_range=self._get_time_range(table),
            key_entities=key_entities,
            numeric_highlights=self._get_numeric_highlights(table),
            chunk_index=0,
            total_chunks=1
        )
    
    def _create_statistics_chunk(
        self, 
        table: ParsedTable, 
        filename: str,
        source_name: str
    ) -> DataChunkRaw:
        """Create a statistics summary chunk"""
        
        import pandas as pd
        df = pd.DataFrame(table.data)
        
        content_parts = [
            f"Statistical Summary: {table.name}",
            f"Source: {source_name}",
            f""
        ]
        
        for col in table.numeric_columns[:10]:
            if col in df.columns:
                try:
                    series = pd.to_numeric(df[col], errors='coerce')
                    stats = {
                        'min': series.min(),
                        'max': series.max(),
                        'mean': series.mean(),
                        'median': series.median()
                    }
                    content_parts.append(
                        f"{col}: min={stats['min']:.2f}, max={stats['max']:.2f}, "
                        f"avg={stats['mean']:.2f}, median={stats['median']:.2f}"
                    )
                except:
                    continue
        
        return DataChunkRaw(
            chunk_id=self._generate_id(filename, table.name, "statistics"),
            content="\n".join(content_parts),
            content_type="statistics",
            source_table=table.name,
            source_file=filename,
            columns=table.numeric_columns,
            data_rows=[],
            row_count=table.row_count,
            has_time_dimension=table.has_time_dimension,
            time_column=table.time_column,
            time_range=self._get_time_range(table),
            key_entities=[],
            numeric_highlights=self._get_numeric_highlights(table),
            chunk_index=0,
            total_chunks=1
        )
    
    def _create_time_chunks(
        self, 
        table: ParsedTable, 
        filename: str,
        source_name: str
    ) -> List[DataChunkRaw]:
        """Create chunks grouped by time periods"""
        
        import pandas as pd
        df = pd.DataFrame(table.data)
        
        if table.time_column not in df.columns:
            return [self._create_full_table_chunk(table, filename, source_name)]
        
        chunks = []
        time_col = table.time_column
        
        # Get unique time periods
        unique_periods = df[time_col].unique()
        
        # If too many periods, group them
        if len(unique_periods) > 10:
            # Create single time series chunk
            chunk = self._create_time_series_chunk(table, filename, source_name)
            chunks.append(chunk)
        else:
            # Create chunk per period or group of periods
            for period in unique_periods:
                period_data = df[df[time_col] == period].to_dict(orient='records')
                
                content = self._data_to_text(
                    period_data, 
                    table.columns,
                    f"{table.name} - {time_col}: {period}",
                    source_name
                )
                
                chunk = DataChunkRaw(
                    chunk_id=self._generate_id(filename, table.name, f"period_{period}"),
                    content=content,
                    content_type="time_slice",
                    source_table=table.name,
                    source_file=filename,
                    columns=table.columns,
                    data_rows=period_data[:self.max_rows],
                    row_count=len(period_data),
                    has_time_dimension=True,
                    time_column=time_col,
                    time_range=(period, period),
                    key_entities=self._extract_entities_from_data(period_data, table.text_columns),
                    numeric_highlights={},
                    chunk_index=0,
                    total_chunks=1
                )
                chunks.append(chunk)
        
        return chunks
    
    def _create_time_series_chunk(
        self, 
        table: ParsedTable, 
        filename: str,
        source_name: str
    ) -> DataChunkRaw:
        """Create a chunk representing time series data"""
        
        content = self._data_to_text(
            table.data,
            table.columns,
            f"{table.name} (Time Series: {table.time_column})",
            source_name
        )
        
        return DataChunkRaw(
            chunk_id=self._generate_id(filename, table.name, "time_series"),
            content=content,
            content_type="time_series",
            source_table=table.name,
            source_file=filename,
            columns=table.columns,
            data_rows=table.data[:self.max_rows],
            row_count=table.row_count,
            has_time_dimension=True,
            time_column=table.time_column,
            time_range=self._get_time_range(table),
            key_entities=self._extract_key_entities(table),
            numeric_highlights=self._get_numeric_highlights(table),
            chunk_index=0,
            total_chunks=1
        )
    
    def _create_full_table_chunk(
        self, 
        table: ParsedTable, 
        filename: str,
        source_name: str
    ) -> DataChunkRaw:
        """Create a single chunk for small tables"""
        
        content = self._data_to_text(
            table.data,
            table.columns,
            table.name,
            source_name
        )
        
        return DataChunkRaw(
            chunk_id=self._generate_id(filename, table.name, "full"),
            content=content,
            content_type="table",
            source_table=table.name,
            source_file=filename,
            columns=table.columns,
            data_rows=table.data,
            row_count=table.row_count,
            has_time_dimension=table.has_time_dimension,
            time_column=table.time_column,
            time_range=self._get_time_range(table),
            key_entities=self._extract_key_entities(table),
            numeric_highlights=self._get_numeric_highlights(table),
            chunk_index=0,
            total_chunks=1
        )
    
    def _create_split_chunks(
        self, 
        table: ParsedTable, 
        filename: str,
        source_name: str
    ) -> List[DataChunkRaw]:
        """Split large tables into multiple chunks"""
        
        chunks = []
        total_parts = (table.row_count + self.max_rows - 1) // self.max_rows
        
        for i in range(total_parts):
            start = i * self.max_rows
            end = min(start + self.max_rows, table.row_count)
            part_data = table.data[start:end]
            
            content = self._data_to_text(
                part_data,
                table.columns,
                f"{table.name} (Part {i+1}/{total_parts})",
                source_name
            )
            
            chunk = DataChunkRaw(
                chunk_id=self._generate_id(filename, table.name, f"part_{i+1}"),
                content=content,
                content_type="table",
                source_table=table.name,
                source_file=filename,
                columns=table.columns,
                data_rows=part_data,
                row_count=len(part_data),
                has_time_dimension=table.has_time_dimension,
                time_column=table.time_column,
                time_range=self._get_time_range(table),
                key_entities=self._extract_entities_from_data(part_data, table.text_columns),
                numeric_highlights={},
                chunk_index=i,
                total_chunks=total_parts
            )
            chunks.append(chunk)
        
        return chunks
    
    def _data_to_text(
        self, 
        data: List[Dict], 
        columns: List[str],
        title: str,
        source: str
    ) -> str:
        """Convert data rows to human-readable text"""
        
        lines = [
            f"Data: {title}",
            f"Source: {source}",
            f"Columns: {', '.join(columns[:15])}",
            f"Rows: {len(data)}",
            ""
        ]
        
        # Add sample rows as text
        for i, row in enumerate(data[:10]):
            row_text = " | ".join(f"{k}: {v}" for k, v in list(row.items())[:8])
            lines.append(f"Row {i+1}: {row_text}")
        
        if len(data) > 10:
            lines.append(f"... and {len(data) - 10} more rows")
        
        return "\n".join(lines)
    
    def _extract_key_entities(self, table: ParsedTable) -> List[str]:
        """Extract important entity names from table"""
        entities = set()
        
        for col in table.text_columns[:5]:
            if col in table.sample_values:
                for val in table.sample_values[col]:
                    if val and str(val) not in ['nan', 'None', '']:
                        entities.add(str(val)[:50])
        
        return list(entities)[:20]
    
    def _extract_entities_from_data(
        self, 
        data: List[Dict], 
        text_columns: List[str]
    ) -> List[str]:
        """Extract entities from data rows"""
        entities = set()
        
        for row in data[:20]:
            for col in text_columns[:5]:
                if col in row and row[col]:
                    val = str(row[col])
                    if val not in ['nan', 'None', '']:
                        entities.add(val[:50])
        
        return list(entities)[:20]
    
    def _get_time_range(self, table: ParsedTable) -> Optional[tuple]:
        """Get the time range from table data"""
        if not table.has_time_dimension or not table.time_column:
            return None
        
        try:
            time_values = [
                row.get(table.time_column) 
                for row in table.data 
                if row.get(table.time_column) is not None
            ]
            if time_values:
                return (min(time_values), max(time_values))
        except:
            pass
        
        return None
    
    def _get_numeric_highlights(self, table: ParsedTable) -> Dict[str, Any]:
        """Get min/max/avg for numeric columns"""
        import pandas as pd
        
        highlights = {}
        df = pd.DataFrame(table.data)
        
        for col in table.numeric_columns[:5]:
            if col in df.columns:
                try:
                    series = pd.to_numeric(df[col], errors='coerce')
                    highlights[col] = {
                        'min': float(series.min()) if not pd.isna(series.min()) else None,
                        'max': float(series.max()) if not pd.isna(series.max()) else None,
                        'avg': float(series.mean()) if not pd.isna(series.mean()) else None
                    }
                except:
                    continue
        
        return highlights
    
    def _generate_id(self, filename: str, table_name: str, suffix: str) -> str:
        """Generate a unique chunk ID"""
        content = f"{filename}_{table_name}_{suffix}"
        return hashlib.md5(content.encode()).hexdigest()[:16]


# === Convenience function ===
def chunk_parsed_data(parse_result: ParseResult, source_name: str) -> List[DataChunkRaw]:
    """Quick chunk function"""
    chunker = SmartChunker()
    return chunker.chunk(parse_result, source_name)
