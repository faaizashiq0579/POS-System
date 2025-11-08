import sqlite3

conn = sqlite3.connect("shop.db")
cursor = conn.cursor()

# Add barcode column if it doesn't exist
try:
    cursor.execute("ALTER TABLE products ADD COLUMN barcode TEXT UNIQUE")
    print("✅ Column 'barcode' added successfully!")
except sqlite3.OperationalError:
    print("⚠️ Column 'barcode' already exists.")

conn.commit()
conn.close()
