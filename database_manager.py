"""
Simple Database Manager for Smart SQL Pipeline Generator
"""
import sqlite3
import pandas as pd
import os
from datetime import datetime

class DatabaseManager:
    def __init__(self, db_path: str = "../data/sample_database.db"):
        self.db_path = db_path
        self.ensure_data_directory()
        self.connection = None
        self.create_sample_database()
    
    def ensure_data_directory(self):
        """Create data directory if it doesn't exist"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
    
    def get_connection(self):
        """Get database connection"""
        if self.connection is None:
            self.connection = sqlite3.connect(self.db_path)
        return self.connection
    
    def create_sample_database(self):
        """Create sample database with basic tables"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Create customers table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS customers (
            customer_id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            email TEXT,
            city TEXT,
            registration_date DATE
        )
        """)
        
        # Create orders table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            order_id INTEGER PRIMARY KEY,
            customer_id INTEGER,
            order_date DATE,
            total_amount DECIMAL(10,2),
            status TEXT,
            FOREIGN KEY (customer_id) REFERENCES customers (customer_id)
        )
        """)
        
        # Create products table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS products (
            product_id INTEGER PRIMARY KEY,
            product_name TEXT,
            category TEXT,
            price DECIMAL(10,2)
        )
        """)
        
        # Check if data exists
        cursor.execute("SELECT COUNT(*) FROM customers")
        if cursor.fetchone()[0] == 0:
            self.insert_sample_data(cursor)
            conn.commit()
            print("✅ Sample database created with test data")
        else:
            print("✅ Database already exists")
    
    def insert_sample_data(self, cursor):
        """Insert sample data"""
        
        # Sample customers
        customers = [
            (1, 'John Smith', 'john@email.com', 'New York', '2024-01-15'),
            (2, 'Jane Doe', 'jane@email.com', 'Los Angeles', '2024-02-20'),
            (3, 'Mike Johnson', 'mike@email.com', 'Chicago', '2024-03-10'),
            (4, 'Sarah Wilson', 'sarah@email.com', 'Houston', '2024-04-05'),
            (5, 'David Brown', 'david@email.com', 'Phoenix', '2024-05-12')
        ]
        
        cursor.executemany("""
        INSERT INTO customers VALUES (?, ?, ?, ?, ?)
        """, customers)
        
        # Sample products
        products = [
            (1, 'Laptop', 'Electronics', 999.99),
            (2, 'Phone', 'Electronics', 699.99),
            (3, 'T-Shirt', 'Clothing', 29.99),
            (4, 'Jeans', 'Clothing', 79.99),
            (5, 'Book', 'Books', 19.99)
        ]
        
        cursor.executemany("""
        INSERT INTO products VALUES (?, ?, ?, ?)
        """, products)
        
        # Sample orders
        orders = [
            (1, 1, '2024-06-01', 999.99, 'completed'),
            (2, 2, '2024-06-02', 699.99, 'completed'),
            (3, 3, '2024-06-03', 109.98, 'completed'),
            (4, 4, '2024-06-04', 79.99, 'pending'),
            (5, 5, '2024-06-05', 19.99, 'completed'),
            (6, 1, '2024-06-06', 29.99, 'completed'),
            (7, 2, '2024-06-07', 79.99, 'shipped')
        ]
        
        cursor.executemany("""
        INSERT INTO orders VALUES (?, ?, ?, ?, ?)
        """, orders)
    
    def execute_query(self, query: str):
        """Execute SQL query safely"""
        try:
            # Only allow SELECT queries for safety
            if not query.strip().upper().startswith('SELECT'):
                return {
                    'success': False,
                    'error': 'Only SELECT queries are allowed',
                    'data': None
                }
            
            conn = self.get_connection()
            df = pd.read_sql_query(query, conn)
            
            return {
                'success': True,
                'data': df,
                'row_count': len(df),
                'columns': list(df.columns)
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'data': None
            }
    
    def get_schema_info(self):
        """Get database schema information"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            
            schema_info = {}
            for table in tables:
                cursor.execute(f"PRAGMA table_info({table})")
                columns = cursor.fetchall()
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                row_count = cursor.fetchone()[0]
                
                schema_info[table] = {
                    'columns': [col[1] for col in columns],
                    'row_count': row_count
                }
            
            return schema_info
        except Exception as e:
            return {'error': str(e)}
    
    def get_sample_queries(self):
        """Get sample queries for testing"""
        return [
            {
                'name': 'Daily Sales Report',
                'query': """
                SELECT 
                    order_date,
                    COUNT(*) as order_count,
                    SUM(total_amount) as total_revenue
                FROM orders 
                WHERE status = 'completed'
                GROUP BY order_date
                ORDER BY order_date DESC
                """
            },
            {
                'name': 'Customer Orders',
                'query': """
                SELECT 
                    c.name,
                    c.city,
                    COUNT(o.order_id) as order_count,
                    SUM(o.total_amount) as total_spent
                FROM customers c
                LEFT JOIN orders o ON c.customer_id = o.customer_id
                GROUP BY c.customer_id, c.name, c.city
                ORDER BY total_spent DESC
                """
            },
            {
                'name': 'Product Sales',
                'query': """
                SELECT 
                    p.product_name,
                    p.category,
                    p.price,
                    COUNT(o.order_id) as times_ordered
                FROM products p
                LEFT JOIN orders o ON p.price = o.total_amount
                GROUP BY p.product_id
                ORDER BY times_ordered DESC
                """
            }
        ]

def test_database():
    """Test the database functionality"""
    print("🧪 Testing Database Manager...")
    
    try:
        db = DatabaseManager()
        
        # Test schema
        schema = db.get_schema_info()
        print(f"✅ Found {len(schema)} tables:")
        for table, info in schema.items():
            print(f"  - {table}: {info['row_count']} rows")
        
        # Test sample query
        queries = db.get_sample_queries()
        result = db.execute_query(queries[0]['query'])
        
        if result['success']:
            print(f"✅ Sample query successful: {result['row_count']} rows returned")
            print("✅ Database is working perfectly!")
        else:
            print(f"❌ Query failed: {result['error']}")
            
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_database()