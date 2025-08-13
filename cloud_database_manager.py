"""
Cloud Database Manager for Smart SQL Pipeline Generator
Supports multiple database types with cloud integration
"""
import os
import asyncio
import logging
from typing import Dict, List, Optional, Union, Any
from dataclasses import dataclass
from enum import Enum
import pandas as pd
import sqlite3
import psycopg2
from sqlalchemy import create_engine, text
from sqlalchemy.pool import QueuePool
from sqlalchemy.exc import SQLAlchemyError
import time
from datetime import datetime
import json

class DatabaseType(Enum):
    SQLITE = "sqlite"
    POSTGRESQL = "postgresql"
    MYSQL = "mysql"

@dataclass
class DatabaseConfig:
    db_type: DatabaseType
    host: Optional[str] = None
    port: Optional[int] = None
    database: str = "smart_sql_agent"
    username: Optional[str] = None
    password: Optional[str] = None
    ssl_mode: str = "prefer"
    pool_size: int = 5
    max_overflow: int = 10
    pool_timeout: int = 30

@dataclass
class QueryResult:
    success: bool
    data: Optional[pd.DataFrame] = None
    row_count: int = 0
    execution_time: float = 0.0
    columns: List[str] = None
    error: Optional[str] = None
    database_type: Optional[str] = None

class CloudDatabaseManager:
    def __init__(self, config: DatabaseConfig = None):
        self.logger = self._setup_logging()
        self.config = config or self._get_default_config()
        self.engine = None
        self.connection_pool = None
        self._connection_status = {"connected": False, "last_check": None, "error": None}
        
        # Initialize connection
        self._initialize_connection()
    
    def _setup_logging(self) -> logging.Logger:
        """Setup logging for database operations"""
        logger = logging.getLogger('CloudDatabaseManager')
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    def _get_default_config(self) -> DatabaseConfig:
        """Get default database configuration from environment"""
        
        # Check for cloud database configuration
        if os.getenv('DATABASE_URL'):
            # Parse DATABASE_URL (common in cloud deployments)
            db_url = os.getenv('DATABASE_URL')
            if db_url.startswith('postgres'):
                return self._parse_postgres_url(db_url)
        
        # Check for specific PostgreSQL config
        if all([os.getenv('DB_HOST'), os.getenv('DB_USER'), os.getenv('DB_PASSWORD')]):
            return DatabaseConfig(
                db_type=DatabaseType.POSTGRESQL,
                host=os.getenv('DB_HOST'),
                port=int(os.getenv('DB_PORT', 5432)),
                database=os.getenv('DB_NAME', 'smart_sql_agent'),
                username=os.getenv('DB_USER'),
                password=os.getenv('DB_PASSWORD'),
                ssl_mode=os.getenv('DB_SSL_MODE', 'require')
            )
        
        # Default to SQLite for local development
        return DatabaseConfig(
            db_type=DatabaseType.SQLITE,
            database="data/sample_database.db"
        )
    
    def _parse_postgres_url(self, url: str) -> DatabaseConfig:
        """Parse PostgreSQL URL format"""
        # Example: postgresql://user:password@host:port/database
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            
            return DatabaseConfig(
                db_type=DatabaseType.POSTGRESQL,
                host=parsed.hostname,
                port=parsed.port or 5432,
                database=parsed.path.lstrip('/'),
                username=parsed.username,
                password=parsed.password,
                ssl_mode='require'
            )
        except Exception as e:
            self.logger.error(f"Failed to parse database URL: {e}")
            return self._get_default_config()
    
    def _initialize_connection(self):
        """Initialize database connection with connection pooling"""
        try:
            connection_string = self._build_connection_string()
            
            if self.config.db_type == DatabaseType.SQLITE:
                self.engine = create_engine(
                    connection_string,
                    pool_pre_ping=True,
                    echo=False
                )
            else:
                # PostgreSQL/MySQL with connection pooling
                self.engine = create_engine(
                    connection_string,
                    poolclass=QueuePool,
                    pool_size=self.config.pool_size,
                    max_overflow=self.config.max_overflow,
                    pool_timeout=self.config.pool_timeout,
                    pool_pre_ping=True,
                    echo=False
                )
            
            # Test connection
            self._test_connection()
            
            self.logger.info(f"Successfully connected to {self.config.db_type.value} database")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize database connection: {e}")
            self._connection_status = {
                "connected": False, 
                "last_check": datetime.now().isoformat(),
                "error": str(e)
            }
    
    def _build_connection_string(self) -> str:
        """Build database connection string"""
        
        if self.config.db_type == DatabaseType.SQLITE:
            db_path = self.config.database
            # Ensure directory exists
            os.makedirs(os.path.dirname(db_path), exist_ok=True)
            return f"sqlite:///{db_path}"
        
        elif self.config.db_type == DatabaseType.POSTGRESQL:
            return (
                f"postgresql://{self.config.username}:{self.config.password}"
                f"@{self.config.host}:{self.config.port}/{self.config.database}"
                f"?sslmode={self.config.ssl_mode}"
            )
        
        elif self.config.db_type == DatabaseType.MYSQL:
            return (
                f"mysql+pymysql://{self.config.username}:{self.config.password}"
                f"@{self.config.host}:{self.config.port}/{self.config.database}"
            )
        
        else:
            raise ValueError(f"Unsupported database type: {self.config.db_type}")
    
    def _test_connection(self):
        """Test database connection"""
        try:
            with self.engine.connect() as conn:
                if self.config.db_type == DatabaseType.SQLITE:
                    conn.execute(text("SELECT 1"))
                else:
                    conn.execute(text("SELECT 1 as test"))
                
                self._connection_status = {
                    "connected": True,
                    "last_check": datetime.now().isoformat(),
                    "error": None
                }
                
        except Exception as e:
            self._connection_status = {
                "connected": False,
                "last_check": datetime.now().isoformat(),
                "error": str(e)
            }
            raise
    
    def execute_query(self, query: str, params: Dict = None) -> QueryResult:
        """Execute SQL query with comprehensive error handling"""
        
        start_time = time.time()
        
        try:
            # Validate query safety
            if not self._is_query_safe(query):
                return QueryResult(
                    success=False,
                    error="Query contains potentially unsafe operations",
                    database_type=self.config.db_type.value
                )
            
            with self.engine.connect() as conn:
                # Execute query
                result = conn.execute(text(query), params or {})
                
                # Handle different result types
                if result.returns_rows:
                    # SELECT query
                    df = pd.DataFrame(result.fetchall(), columns=result.keys())
                    row_count = len(df)
                    columns = list(df.columns)
                else:
                    # INSERT/UPDATE/DELETE
                    df = pd.DataFrame()
                    row_count = result.rowcount
                    columns = []
                
                execution_time = time.time() - start_time
                
                self.logger.info(
                    f"Query executed successfully: {row_count} rows, "
                    f"{execution_time:.3f}s, DB: {self.config.db_type.value}"
                )
                
                return QueryResult(
                    success=True,
                    data=df,
                    row_count=row_count,
                    execution_time=execution_time,
                    columns=columns,
                    database_type=self.config.db_type.value
                )
                
        except SQLAlchemyError as e:
            execution_time = time.time() - start_time
            error_msg = f"Database error: {str(e)}"
            self.logger.error(f"Query failed: {error_msg}")
            
            return QueryResult(
                success=False,
                error=error_msg,
                execution_time=execution_time,
                database_type=self.config.db_type.value
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            error_msg = f"Unexpected error: {str(e)}"
            self.logger.error(f"Query failed: {error_msg}")
            
            return QueryResult(
                success=False,
                error=error_msg,
                execution_time=execution_time,
                database_type=self.config.db_type.value
            )
    
    def _is_query_safe(self, query: str) -> bool:
        """Basic query safety validation"""
        query_upper = query.upper().strip()
        
        # Allow SELECT, WITH (CTEs)
        safe_statements = ['SELECT', 'WITH']
        
        # Check if query starts with safe statement
        for statement in safe_statements:
            if query_upper.startswith(statement):
                return True
        
        # Disallow potentially dangerous operations
        dangerous_operations = [
            'DROP', 'DELETE', 'INSERT', 'UPDATE', 'ALTER', 'CREATE',
            'TRUNCATE', 'GRANT', 'REVOKE', 'EXEC', 'EXECUTE'
        ]
        
        for operation in dangerous_operations:
            if operation in query_upper:
                return False
        
        return True
    
    def get_connection_status(self) -> Dict[str, Any]:
        """Get current connection status"""
        # Refresh connection status
        try:
            self._test_connection()
        except:
            pass  # Status already updated in _test_connection
        
        return {
            **self._connection_status,
            "database_type": self.config.db_type.value,
            "host": self.config.host or "local",
            "database": self.config.database,
            "pool_info": self._get_pool_info() if self.engine else None
        }
    
    def _get_pool_info(self) -> Dict[str, Any]:
        """Get connection pool information"""
        if hasattr(self.engine.pool, 'size'):
            return {
                "pool_size": self.engine.pool.size(),
                "checked_in": self.engine.pool.checkedin(),
                "checked_out": self.engine.pool.checkedout(),
                "overflow": self.engine.pool.overflow(),
                "total_connections": self.engine.pool.size() + self.engine.pool.overflow()
            }
        return {"pool_type": "simple"}
    
    def get_schema_info(self) -> Dict[str, Any]:
        """Get database schema information"""
        try:
            schema_info = {}
            
            if self.config.db_type == DatabaseType.SQLITE:
                # SQLite schema query
                tables_query = "SELECT name FROM sqlite_master WHERE type='table'"
            else:
                # PostgreSQL schema query
                tables_query = """
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                """
            
            # Get tables
            tables_result = self.execute_query(tables_query)
            
            if not tables_result.success:
                return {"error": tables_result.error}
            
            tables = tables_result.data.iloc[:, 0].tolist() if len(tables_result.data) > 0 else []
            
            # Get schema for each table
            for table in tables:
                if self.config.db_type == DatabaseType.SQLITE:
                    columns_query = f"PRAGMA table_info({table})"
                    count_query = f"SELECT COUNT(*) FROM {table}"
                else:
                    columns_query = f"""
                    SELECT column_name, data_type, is_nullable
                    FROM information_schema.columns 
                    WHERE table_name = '{table}'
                    ORDER BY ordinal_position
                    """
                    count_query = f"SELECT COUNT(*) FROM {table}"
                
                # Get columns
                columns_result = self.execute_query(columns_query)
                count_result = self.execute_query(count_query)
                
                if columns_result.success and count_result.success:
                    if self.config.db_type == DatabaseType.SQLITE:
                        columns = columns_result.data['name'].tolist()
                    else:
                        columns = columns_result.data['column_name'].tolist()
                    
                    row_count = count_result.data.iloc[0, 0]
                    
                    schema_info[table] = {
                        "columns": columns,
                        "row_count": int(row_count),
                        "column_details": columns_result.data.to_dict('records') if len(columns_result.data) > 0 else []
                    }
            
            return schema_info
            
        except Exception as e:
            self.logger.error(f"Failed to get schema info: {e}")
            return {"error": str(e)}
    
    def create_sample_tables(self) -> bool:
        """Create sample tables for demonstration (PostgreSQL compatible)"""
        try:
            # Only create if we have write permissions and it's safe
            if self.config.db_type != DatabaseType.SQLITE:
                self.logger.info("Sample table creation skipped for cloud databases")
                return True
            
            # For SQLite, create sample tables
            sample_tables = {
                "customers": """
                CREATE TABLE IF NOT EXISTS customers (
                    customer_id INTEGER PRIMARY KEY,
                    name TEXT NOT NULL,
                    email TEXT UNIQUE,
                    city TEXT,
                    registration_date DATE,
                    lifetime_value DECIMAL(10,2) DEFAULT 0
                )
                """,
                "orders": """
                CREATE TABLE IF NOT EXISTS orders (
                    order_id INTEGER PRIMARY KEY,
                    customer_id INTEGER,
                    order_date DATE,
                    total_amount DECIMAL(10,2),
                    status TEXT DEFAULT 'completed',
                    FOREIGN KEY (customer_id) REFERENCES customers (customer_id)
                )
                """,
                "products": """
                CREATE TABLE IF NOT EXISTS products (
                    product_id INTEGER PRIMARY KEY,
                    product_name TEXT,
                    category TEXT,
                    price DECIMAL(10,2)
                )
                """
            }
            
            for table_name, create_sql in sample_tables.items():
                result = self.execute_query(create_sql)
                if not result.success:
                    self.logger.error(f"Failed to create table {table_name}: {result.error}")
                    return False
            
            self.logger.info("Sample tables created successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to create sample tables: {e}")
            return False
    
    def close_connection(self):
        """Close database connection and cleanup"""
        try:
            if self.engine:
                self.engine.dispose()
                self.logger.info("Database connection closed")
        except Exception as e:
            self.logger.error(f"Error closing connection: {e}")

# Cloud provider specific configurations
class CloudProviderConfigs:
    
    @staticmethod
    def aws_rds_postgres(host: str, database: str, username: str, password: str) -> DatabaseConfig:
        """AWS RDS PostgreSQL configuration"""
        return DatabaseConfig(
            db_type=DatabaseType.POSTGRESQL,
            host=host,
            port=5432,
            database=database,
            username=username,
            password=password,
            ssl_mode='require',
            pool_size=10,
            max_overflow=20
        )
    
    @staticmethod
    def digitalocean_postgres(host: str, database: str, username: str, password: str, port: int = 25060) -> DatabaseConfig:
        """DigitalOcean Managed PostgreSQL configuration"""
        return DatabaseConfig(
            db_type=DatabaseType.POSTGRESQL,
            host=host,
            port=port,
            database=database,
            username=username,
            password=password,
            ssl_mode='require',
            pool_size=8,
            max_overflow=15
        )
    
    @staticmethod
    def local_postgres(database: str = "smart_sql_agent", username: str = "postgres", password: str = "password") -> DatabaseConfig:
        """Local PostgreSQL configuration"""
        return DatabaseConfig(
            db_type=DatabaseType.POSTGRESQL,
            host='localhost',
            port=5432,
            database=database,
            username=username,
            password=password,
            ssl_mode='disable',
            pool_size=5,
            max_overflow=10
        )

def test_cloud_database():
    """Test cloud database functionality"""
    print("🧪 Testing Cloud Database Manager...")
    
    try:
        # Test with default config (SQLite)
        db_manager = CloudDatabaseManager()
        
        # Test connection status
        status = db_manager.get_connection_status()
        print(f"✅ Connection Status: {status['connected']}")
        print(f"   Database Type: {status['database_type']}")
        print(f"   Host: {status['host']}")
        
        # Test schema info
        schema = db_manager.get_schema_info()
        if "error" not in schema:
            print(f"✅ Schema Info: Found {len(schema)} tables")
            for table, info in schema.items():
                print(f"   - {table}: {info['row_count']} rows, {len(info['columns'])} columns")
        else:
            print(f"❌ Schema Error: {schema['error']}")
        
        # Test query execution
        test_query = "SELECT 1 as test_column"
        result = db_manager.execute_query(test_query)
        
        if result.success:
            print(f"✅ Query Test: Success - {result.execution_time:.3f}s")
        else:
            print(f"❌ Query Test: Failed - {result.error}")
        
        # Test pool info
        pool_info = status.get('pool_info')
        if pool_info:
            print(f"✅ Connection Pool: {pool_info}")
        
        print("✅ Cloud Database Manager test completed successfully!")
        
        return db_manager
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    test_cloud_database()