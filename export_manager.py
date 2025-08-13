"""
Export Manager for Smart SQL Pipeline Generator
Handles exporting data and results to multiple formats
"""
import pandas as pd
import json
import csv
import io
from datetime import datetime
from typing import Dict, List, Optional, Union
import base64

class ExportManager:
    def __init__(self):
        self.supported_formats = ['csv', 'json', 'excel', 'sql', 'txt']
    
    def export_query_results(self, data: pd.DataFrame, format_type: str, 
                           filename: Optional[str] = None, 
                           query_info: Optional[Dict] = None) -> Dict:
        """Export query results to specified format"""
        
        if format_type not in self.supported_formats:
            return {
                'success': False,
                'error': f"Unsupported format: {format_type}. Supported: {self.supported_formats}"
            }
        
        try:
            if filename is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"query_results_{timestamp}"
            
            # Remove file extension if provided
            filename = filename.replace(f'.{format_type}', '')
            
            if format_type == 'csv':
                return self._export_csv(data, filename, query_info)
            elif format_type == 'json':
                return self._export_json(data, filename, query_info)
            elif format_type == 'excel':
                return self._export_excel(data, filename, query_info)
            elif format_type == 'sql':
                return self._export_sql(data, filename, query_info)
            elif format_type == 'txt':
                return self._export_txt(data, filename, query_info)
                
        except Exception as e:
            return {
                'success': False,
                'error': f"Export failed: {str(e)}"
            }
    
    def _export_csv(self, data: pd.DataFrame, filename: str, query_info: Dict = None) -> Dict:
        """Export to CSV format"""
        
        output = io.StringIO()
        
        # Add header with query info if available
        if query_info:
            output.write(f"# Query Results Export\n")
            output.write(f"# Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            output.write(f"# Requirement: {query_info.get('requirement', 'N/A')}\n")
            output.write(f"# Rows: {len(data)}\n")
            output.write(f"# Columns: {len(data.columns)}\n")
            output.write("#\n")
        
        # Write data
        data.to_csv(output, index=False)
        csv_content = output.getvalue()
        output.close()
        
        return {
            'success': True,
            'filename': f"{filename}.csv",
            'content': csv_content,
            'mime_type': 'text/csv',
            'size': len(csv_content.encode('utf-8'))
        }
    
    def _export_json(self, data: pd.DataFrame, filename: str, query_info: Dict = None) -> Dict:
        """Export to JSON format"""
        
        export_data = {
            'metadata': {
                'generated': datetime.now().isoformat(),
                'row_count': len(data),
                'column_count': len(data.columns),
                'columns': list(data.columns)
            },
            'data': data.to_dict('records')
        }
        
        if query_info:
            export_data['query_info'] = query_info
        
        json_content = json.dumps(export_data, indent=2, default=str)
        
        return {
            'success': True,
            'filename': f"{filename}.json",
            'content': json_content,
            'mime_type': 'application/json',
            'size': len(json_content.encode('utf-8'))
        }
    
    def _export_excel(self, data: pd.DataFrame, filename: str, query_info: Dict = None) -> Dict:
        """Export to Excel format"""
        
        output = io.BytesIO()
        
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            # Write main data
            data.to_excel(writer, sheet_name='Query Results', index=False)
            
            # Add metadata sheet if query info available
            if query_info:
                metadata_df = pd.DataFrame([
                    ['Generated', datetime.now().strftime('%Y-%m-%d %H:%M:%S')],
                    ['Requirement', query_info.get('requirement', 'N/A')],
                    ['Complexity', query_info.get('complexity', 'N/A')],
                    ['Execution Time', f"{query_info.get('execution_time', 0):.3f}s"],
                    ['Row Count', len(data)],
                    ['Column Count', len(data.columns)]
                ], columns=['Property', 'Value'])
                
                metadata_df.to_excel(writer, sheet_name='Metadata', index=False)
                
                # Add column info
                column_info_df = pd.DataFrame([
                    [col, str(data[col].dtype), data[col].isnull().sum()] 
                    for col in data.columns
                ], columns=['Column', 'Data Type', 'Null Count'])
                
                column_info_df.to_excel(writer, sheet_name='Column Info', index=False)
        
        excel_content = output.getvalue()
        output.close()
        
        # Convert to base64 for download
        excel_b64 = base64.b64encode(excel_content).decode()
        
        return {
            'success': True,
            'filename': f"{filename}.xlsx",
            'content': excel_content,
            'content_b64': excel_b64,
            'mime_type': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            'size': len(excel_content)
        }
    
    def _export_sql(self, data: pd.DataFrame, filename: str, query_info: Dict = None) -> Dict:
        """Export as SQL INSERT statements"""
        
        output = io.StringIO()
        
        # Add header
        output.write(f"-- SQL Insert Statements\n")
        output.write(f"-- Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        
        if query_info:
            output.write(f"-- Original Requirement: {query_info.get('requirement', 'N/A')}\n")
            output.write(f"-- Rows: {len(data)}\n")
        
        output.write(f"-- Columns: {', '.join(data.columns)}\n\n")
        
        # Generate table name
        table_name = filename.lower().replace(' ', '_')
        
        # Create table statement
        output.write(f"-- Create table statement\n")
        output.write(f"CREATE TABLE IF NOT EXISTS {table_name} (\n")
        
        column_definitions = []
        for col in data.columns:
            dtype = data[col].dtype
            if dtype == 'object':
                col_type = "TEXT"
            elif dtype in ['int64', 'int32']:
                col_type = "INTEGER"
            elif dtype in ['float64', 'float32']:
                col_type = "REAL"
            else:
                col_type = "TEXT"
            
            column_definitions.append(f"    {col} {col_type}")
        
        output.write(",\n".join(column_definitions))
        output.write(f"\n);\n\n")
        
        # Insert statements
        output.write(f"-- Insert statements\n")
        for _, row in data.iterrows():
            values = []
            for val in row:
                if pd.isna(val):
                    values.append("NULL")
                elif isinstance(val, str):
                    # Escape single quotes
                    escaped_val = val.replace("'", "''")
                    values.append(f"'{escaped_val}'")
                else:
                    values.append(str(val))
            
            values_str = ", ".join(values)
            output.write(f"INSERT INTO {table_name} VALUES ({values_str});\n")
        
        sql_content = output.getvalue()
        output.close()
        
        return {
            'success': True,
            'filename': f"{filename}.sql",
            'content': sql_content,
            'mime_type': 'text/sql',
            'size': len(sql_content.encode('utf-8'))
        }
    
    def _export_txt(self, data: pd.DataFrame, filename: str, query_info: Dict = None) -> Dict:
        """Export as formatted text"""
        
        output = io.StringIO()
        
        # Add header
        output.write("=" * 80 + "\n")
        output.write("QUERY RESULTS REPORT\n")
        output.write("=" * 80 + "\n\n")
        
        output.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        
        if query_info:
            output.write(f"Requirement: {query_info.get('requirement', 'N/A')}\n")
            output.write(f"Complexity: {query_info.get('complexity', 'N/A')}\n")
            output.write(f"Execution Time: {query_info.get('execution_time', 0):.3f} seconds\n")
        
        output.write(f"Total Rows: {len(data):,}\n")
        output.write(f"Total Columns: {len(data.columns)}\n\n")
        
        # Column summary
        output.write("COLUMN SUMMARY\n")
        output.write("-" * 40 + "\n")
        for col in data.columns:
            dtype = data[col].dtype
            null_count = data[col].isnull().sum()
            unique_count = data[col].nunique()
            
            output.write(f"{col}:\n")
            output.write(f"  Type: {dtype}\n")
            output.write(f"  Null values: {null_count}\n")
            output.write(f"  Unique values: {unique_count}\n\n")
        
        # Data preview
        output.write("DATA PREVIEW (First 20 rows)\n")
        output.write("-" * 40 + "\n")
        output.write(data.head(20).to_string(index=False))
        output.write("\n\n")
        
        # Summary statistics for numeric columns
        numeric_cols = data.select_dtypes(include=['number']).columns
        if len(numeric_cols) > 0:
            output.write("NUMERIC COLUMN STATISTICS\n")
            output.write("-" * 40 + "\n")
            output.write(data[numeric_cols].describe().to_string())
            output.write("\n\n")
        
        output.write("=" * 80 + "\n")
        output.write("End of Report\n")
        output.write("=" * 80 + "\n")
        
        txt_content = output.getvalue()
        output.close()
        
        return {
            'success': True,
            'filename': f"{filename}.txt",
            'content': txt_content,
            'mime_type': 'text/plain',
            'size': len(txt_content.encode('utf-8'))
        }
    
    def create_export_summary(self, exports: List[Dict]) -> str:
        """Create a summary of all exports"""
        
        summary = f"""
# 📊 Export Summary Report

**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 📋 Export Details

"""
        
        total_size = 0
        for i, export in enumerate(exports, 1):
            if export['success']:
                size_mb = export['size'] / (1024 * 1024)
                total_size += export['size']
                
                summary += f"""
### {i}. {export['filename']}
- **Format:** {export['mime_type']}
- **Size:** {export['size']:,} bytes ({size_mb:.2f} MB)
- **Status:** ✅ Success
"""
            else:
                summary += f"""
### {i}. Export Failed
- **Error:** {export.get('error', 'Unknown error')}
- **Status:** ❌ Failed
"""
        
        total_size_mb = total_size / (1024 * 1024)
        summary += f"""

## 📈 Summary Statistics
- **Total Exports:** {len(exports)}
- **Successful:** {sum(1 for e in exports if e['success'])}
- **Failed:** {sum(1 for e in exports if not e['success'])}
- **Total Size:** {total_size:,} bytes ({total_size_mb:.2f} MB)
"""
        
        return summary

def test_export_manager():
    """Test the export manager functionality"""
    print("🧪 Testing Export Manager...")
    
    # Create sample data
    sample_data = pd.DataFrame({
        'customer_id': [1, 2, 3, 4, 5],
        'customer_name': ['John Smith', 'Jane Doe', 'Mike Johnson', 'Sarah Wilson', 'David Brown'],
        'total_orders': [5, 3, 8, 12, 2],
        'total_amount': [599.99, 299.50, 899.75, 1299.99, 149.99],
        'registration_date': ['2024-01-15', '2024-02-20', '2024-03-10', '2024-04-05', '2024-05-12']
    })
    
    query_info = {
        'requirement': 'Show customer summary with order totals',
        'complexity': 'medium',
        'execution_time': 0.045
    }
    
    export_manager = ExportManager()
    
    # Test different export formats
    formats_to_test = ['csv', 'json', 'txt']
    exports = []
    
    for format_type in formats_to_test:
        print(f"   Testing {format_type.upper()} export...")
        result = export_manager.export_query_results(
            sample_data, 
            format_type, 
            f"test_export_{format_type}",
            query_info
        )
        exports.append(result)
        
        if result['success']:
            print(f"   ✅ {format_type.upper()} export successful - {result['size']} bytes")
        else:
            print(f"   ❌ {format_type.upper()} export failed: {result['error']}")
    
    # Create summary
    summary = export_manager.create_export_summary(exports)
    print(f"\n📋 Export Summary Created")
    
    return exports

if __name__ == "__main__":
    test_export_manager()