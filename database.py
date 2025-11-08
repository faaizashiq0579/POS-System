import sqlite3
from abc import ABC, abstractmethod
import os
from datetime import datetime

class Product(ABC):
    @abstractmethod
    def __init__(self, name, price, stock, barcode=None):
        self.name = name
        self.price = price
        self.stock = stock
        self.barcode = barcode


class ConcreteProduct(Product):
    def __init__(self, name, price, stock, barcode=None):
        super().__init__(name, price, stock, barcode)


class Inventory:
    def __init__(self, db_name="shop.db"):
        self.conn = sqlite3.connect(db_name)
        self.cursor = self.conn.cursor()

        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS products(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE,
            price REAL,
            stock INTEGER,
            barcode TEXT UNIQUE
        )
        """)

        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS sales(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_name TEXT,
            quantity INTEGER,
            price REAL,
            total REAL,
            sale_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        

        self.conn.commit()

    def add_product(self, product: Product):
        try:
            self.cursor.execute(
                "INSERT INTO products (name, price, stock, barcode) VALUES (?, ?, ?, ?)",
                (product.name, product.price, product.stock, product.barcode)
            )
            self.conn.commit()
            return f" Product '{product.name}' added successfully!"
        except Exception as e:
            return f" Error adding product: {e}"

    def search_product(self, name=None, barcode=None):
        if barcode:
            self.cursor.execute("SELECT name, price, stock, barcode FROM products WHERE barcode=?", (barcode,))
        elif name:
            self.cursor.execute("SELECT name, price, stock, barcode FROM products WHERE name LIKE ?", (f"%{name}%",))
        else:
            return " Must provide name or barcode!"

        rows = self.cursor.fetchall()
        if not rows:
            return " Product not found!"
        report = "===== SEARCH RESULTS =====\n"
        for row in rows:
            report += f"{row[0]:<15} | Price: Rs.{row[1]:<5} | Stock: {row[2]} | Barcode: {row[3]}\n"
        return report
    def get_all_products(self):
     self.cursor.execute("SELECT name, price, stock, COALESCE(barcode, '') FROM products")
     return self.cursor.fetchall()


    def update_price(self, name, new_price):
        self.cursor.execute("UPDATE products SET price = ? WHERE name = ?", (new_price, name))
        if self.cursor.rowcount == 0:
            return f" Product '{name}' not found!"
        self.conn.commit()
        return f" Price of {name} updated to Rs.{new_price}"

    def update_stock(self, name, new_stock):
        self.cursor.execute("UPDATE products SET stock = ? WHERE name = ?", (new_stock, name))
        if self.cursor.rowcount == 0:
            return f" Product '{name}' not found!"
        self.conn.commit()
        return f" Stock of {name} updated to {new_stock}"

    def delete_product(self, name):
        self.cursor.execute("DELETE FROM products WHERE name=?", (name,))
        if self.cursor.rowcount == 0:
            return f" Product '{name}' not found!"
        self.conn.commit()
        return f" Product '{name}' deleted successfully!"
   

    def close(self):
        self.conn.close()


class SaleManager:
    def __init__(self, conn):
        self.conn = conn
        self.cursor = self.conn.cursor()

    def make_sale(self, name=None, barcode=None, quantity=1):
        if barcode:
            self.cursor.execute("SELECT name, stock, price FROM products WHERE barcode=?", (barcode,))
        elif name:
            self.cursor.execute("SELECT name, stock, price FROM products WHERE name=?", (name,))
        else:
            return " Must provide product name or barcode!"

        row = self.cursor.fetchone()
        if not row:
            return " Product not found!"

        prod_name, stock, price = row
        if quantity > stock:
            return f" Not enough stock for {prod_name}! Available: {stock}"

        new_stock = stock - quantity
        self.cursor.execute("UPDATE products SET stock=? WHERE name=?", (new_stock, prod_name))

        total = price * quantity
        self.cursor.execute(
            "INSERT INTO sales (product_name, quantity, price, total) VALUES (?, ?, ?, ?)",
            (prod_name, quantity, price, total)
        )
        self.conn.commit()

        self.print_receipt(prod_name, quantity, price, total, new_stock)

        return f" Sold {quantity} x {prod_name} = Rs.{total}\nRemaining stock: {new_stock}"
    
    def get_all_sales(self):
     self.cursor.execute("SELECT sale_time, product_name, quantity, total FROM sales ORDER BY sale_time DESC")
     return self.cursor.fetchall()
    
    def print_receipt(self, product_name, quantity, price, total, remaining_stock):
        receipt = f"=== K&B MART ===\n"
        receipt+= f"User:Admin\n"
        receipt += f"{datetime.now()}\n"
        receipt += f"Item         Qty          Price    Total: \n"
        receipt += f"{product_name}  {quantity}  {price}   {total}\n"

        receipt += "Thank you for shopping!\n"

        filename = "receipt.txt"
        with open(filename, "w") as f:
            f.write(receipt)
        os.startfile(filename, "print") 

