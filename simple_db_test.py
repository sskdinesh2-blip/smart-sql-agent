import sqlite3
import os

print("🧪 Testing simple database creation...")

# Create data directory
os.makedirs("../data", exist_ok=True)

# Create database
conn = sqlite3.connect("../data/test.db")
cursor = conn.cursor()

# Create simple table
cursor.execute("""
CREATE TABLE IF NOT EXISTS test_table (
    id INTEGER PRIMARY KEY,
    name TEXT
)
""")

# Insert test data
cursor.execute("INSERT OR REPLACE INTO test_table (id, name) VALUES (1, 'Test Data')")
conn.commit()

# Test query
cursor.execute("SELECT * FROM test_table")
result = cursor.fetchall()

print(f"✅ Database test successful! Found: {result}")

conn.close()
print("✅ Simple database working!")