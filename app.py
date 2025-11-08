import sys
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget,
    QLabel, QLineEdit, QTableWidget, QTableWidgetItem, QHBoxLayout,
    QMessageBox, QSpinBox, QHeaderView, QFrame, QInputDialog, QTextEdit,
    QCompleter
)
from PyQt5.QtGui import QTextDocument
from datetime import datetime
from PyQt5.QtPrintSupport import QPrinter, QPrintDialog
from PyQt5.QtCore import Qt, QSizeF
from PyQt5.QtGui import QFont
from database import Inventory, SaleManager, ConcreteProduct

class POS(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("🛒 Shop POS System")
        self.setGeometry(100, 50, 1200, 650)

        # Database
        self.inv = Inventory()
        self.sales = SaleManager(self.inv.conn)

        # --- Main Layout ---
        main_layout = QHBoxLayout()

        # --- Side Menu ---
        side_menu = QVBoxLayout()
        side_menu.setAlignment(Qt.AlignTop)

        menu_label = QLabel("Inventory")
        menu_label.setFont(QFont("Segoe UI", 16, QFont.Bold))
        side_menu.addWidget(menu_label)

        btn_add_product = QPushButton("➕ Add Product")
        btn_add_product.clicked.connect(self.add_product_dialog)
        side_menu.addWidget(btn_add_product)

        btn_update_stock = QPushButton("📦 Update Stock")
        btn_update_stock.clicked.connect(self.update_stock_dialog)
        side_menu.addWidget(btn_update_stock)

        btn_update_price = QPushButton("💰 Update Price")
        btn_update_price.clicked.connect(self.update_price_dialog)
        side_menu.addWidget(btn_update_price)

        btn_all_products = QPushButton("📃 All Products")
        btn_all_products.clicked.connect(self.get_all_products)
        side_menu.addWidget(btn_all_products)

        btn_delete_product = QPushButton("🗑️ Delete Product")
        btn_delete_product.clicked.connect(self.delete_product_dialog)
        side_menu.addWidget(btn_delete_product)

        btn_sales_history = QPushButton("📑 Sales History")
        btn_sales_history.clicked.connect(self.get_all_sales)
        side_menu.addWidget(btn_sales_history)

        side_menu_widget = QFrame()
        side_menu_widget.setLayout(side_menu)
        side_menu_widget.setFixedWidth(200)
        main_layout.addWidget(side_menu_widget)

        # --- POS Main Area ---
        pos_layout = QVBoxLayout()

        # Title
        title = QLabel("K&B MART")
        title.setFont(QFont("Segoe UI", 24, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        pos_layout.addWidget(title)

        # Input Controls
        controls_layout = QHBoxLayout()
        self.product_input = QLineEdit()
        self.product_input.setPlaceholderText("🔎 Enter Name or Scan Barcode")
        self.product_input.setFont(QFont("Segoe UI", 14))
        self.product_input.returnPressed.connect(self.add_to_bill)

        self.qty_input = QSpinBox()
        self.qty_input.setRange(1, 1000)
        self.qty_input.setFont(QFont("Segoe UI", 14))

        add_btn = QPushButton("➕ Add to Bill")
        add_btn.setFont(QFont("Segoe UI", 12, QFont.Bold))
        add_btn.clicked.connect(self.add_to_bill)

        controls_layout.addWidget(self.product_input)
        controls_layout.addWidget(self.qty_input)
        controls_layout.addWidget(add_btn)
        pos_layout.addLayout(controls_layout)

        # Bill Table
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["Product", "Qty", "Price", "Total", "Barcode","Delete"])
        self.table.setFont(QFont("Segoe UI", 12))
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.cellChanged.connect(self.edit_quantity)
        pos_layout.addWidget(self.table)

        # Total Label
        self.total_label = QLabel("Grand Total: Rs.0")
        self.total_label.setFont(QFont("Segoe UI", 20, QFont.Bold))
        pos_layout.addWidget(self.total_label)

        # Complete Sale
        self.finalize_btn = QPushButton("✅ Complete Sale")
        self.finalize_btn.setFont(QFont("Segoe UI", 14, QFont.Bold))
        self.finalize_btn.clicked.connect(self.complete_sale)
        pos_layout.addWidget(self.finalize_btn)

        # Add POS layout to main layout
        main_layout.addLayout(pos_layout)

        # Set central widget
        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)

        # --- Initialize autocomplete ---
        self.update_completer()

    # -------------------------------
    # Autocomplete for product input
    # -------------------------------
    def update_completer(self):
        rows = self.inv.get_all_products()
        product_names = [row[0] for row in rows]
        completer = QCompleter(product_names)
        completer.setCaseSensitivity(Qt.CaseInsensitive)
        completer.setFilterMode(Qt.MatchContains)
        self.product_input.setCompleter(completer)

    # -------------------------------
    # Add product dialog
    # -------------------------------
    def add_product_dialog(self):
        barcode, ok0 = QInputDialog.getText(self, "Add Product", "Scan or Enter Barcode (Optional):")
        if not ok0:
            barcode = ""
        name, ok1 = QInputDialog.getText(self, "Add Product", "Enter Product Name:")
        if not ok1 or not name:
            return
        price, ok2 = QInputDialog.getDouble(self, "Add Product", "Enter Price:")
        if not ok2:
            return
        stock, ok3 = QInputDialog.getInt(self, "Add Product", "Enter Stock:")
        if not ok3:
            return
        result = self.inv.add_product(ConcreteProduct(name, price, stock, barcode))
        self.update_completer()
        QMessageBox.information(self, "Info", result)

    def update_stock_dialog(self):
        name, ok1 = QInputDialog.getText(self, "Update Stock", "Enter Product Name:")
        if not ok1 or not name:
            return
        stock, ok2 = QInputDialog.getInt(self, "Update Stock", "Enter New Stock:")
        if not ok2:
            return
        result = self.inv.update_stock(name, stock)
        self.update_completer()
        QMessageBox.information(self, "Info", result)

    def update_price_dialog(self):
        name, ok1 = QInputDialog.getText(self, "Update Price", "Enter Product Name:")
        if not ok1 or not name:
            return
        price, ok2 = QInputDialog.getDouble(self, "Update Price", "Enter New Price:")
        if not ok2:
            return
        result = self.inv.update_price(name, price)
        self.update_completer()
        QMessageBox.information(self, "Info", result)

    def delete_product_dialog(self):
        name, ok = QInputDialog.getText(self, "Delete Product", "Enter Product Name to Delete:")
        if not ok or not name:
            return
        result = self.inv.delete_product(name)
        self.update_completer()
        QMessageBox.information(self, "Info", result)

    # -------------------------------
    # Show products
    # -------------------------------
    def get_all_products(self):
        rows = self.inv.get_all_products()
        if not rows:
            QMessageBox.information(self, "Info", "No products found!")
            return

        html = "<html><head><style>table {border-collapse: collapse; width: 100%;} th, td {border: 1px solid #444; padding: 8px; text-align: left;} th {background-color: #28a745; color: white;} tr:nth-child(even) {background-color: #f2f2f2;}</style></head><body><h2>All Products Report</h2><table><tr><th>Name</th><th>Price (Rs.)</th><th>Stock</th><th>Barcode</th></tr>"
        for row in rows:
            html += f"<tr><td>{row[0]}</td><td>{row[1]}</td><td>{row[2]}</td><td>{row[3]}</td></tr>"
        html += "</table></body></html>"

        self.products_window = QTextEdit()
        self.products_window.setReadOnly(True)
        self.products_window.setHtml(html)
        self.products_window.setWindowTitle("All Products")
        self.products_window.resize(700, 500)
        self.products_window.show()

    # -------------------------------
    # Show sales history
    # -------------------------------
    def get_all_sales(self):
        rows = self.sales.get_all_sales()
        if not rows:
            QMessageBox.information(self, "Info", "No sales found!")
            return

        html = "<html><head><style>table {border-collapse: collapse; width: 100%;} th, td {border: 1px solid #444; padding: 8px; text-align: left;} th {background-color: #007bff; color: white;} tr:nth-child(even) {background-color: #f2f2f2;}</style></head><body><h2>Sales History</h2><table><tr><th>Date</th><th>Product</th><th>Qty</th><th>Total (Rs.)</th></tr>"
        for row in rows:
            html += f"<tr><td>{row[0]}</td><td>{row[1]}</td><td>{row[2]}</td><td>{row[3]}</td></tr>"
        html += "</table></body></html>"

        self.sales_window = QTextEdit()
        self.sales_window.setReadOnly(True)
        self.sales_window.setHtml(html)
        self.sales_window.setWindowTitle("Sales History")
        self.sales_window.resize(700, 500)
        self.sales_window.show()

    # -------------------------------
    # Add product to bill
    # -------------------------------
    def add_to_bill(self):
        code_or_name = self.product_input.text().strip()
        if not code_or_name:
            QMessageBox.warning(self, "Error", "Enter product name or scan barcode!")
            return

        qty = self.qty_input.value()

        self.inv.cursor.execute(
            "SELECT name, price, stock, barcode FROM products WHERE name=?",
            (code_or_name,)
        )
        row = self.inv.cursor.fetchone()

        if not row:
            self.inv.cursor.execute(
                "SELECT name, price, stock, barcode FROM products WHERE barcode=?",
                (code_or_name,)
            )
            row = self.inv.cursor.fetchone()

        if not row:
            QMessageBox.warning(self, "Error", "Product not found!")
            self.product_input.clear()
            return

        prod_name, price, stock, barcode = row

        if qty > stock:
            QMessageBox.warning(self, "Error", f"Not enough stock! Available: {stock}")
            self.product_input.clear()
            return

        for r in range(self.table.rowCount()):
            if self.table.item(r, 0).text() == prod_name:
                old_qty = int(self.table.item(r, 1).text())
                new_qty = old_qty + qty
                self.table.item(r, 1).setText(str(new_qty))
                self.table.item(r, 3).setText(str(new_qty * price))
                self.update_total()
                self.product_input.clear()
                return

        row_position = self.table.rowCount()
        self.table.insertRow(row_position)
        self.table.setItem(row_position, 0, QTableWidgetItem(prod_name))
        self.table.setItem(row_position, 1, QTableWidgetItem(str(qty)))
        self.table.setItem(row_position, 2, QTableWidgetItem(str(price)))
        self.table.setItem(row_position, 3, QTableWidgetItem(str(price * qty)))
        self.table.setItem(row_position, 4, QTableWidgetItem(str(barcode)))

        delete_btn = QPushButton("🗑️")
        delete_btn.clicked.connect(lambda _, btn=delete_btn: self.delete_from_bill_widget(btn))
        self.table.setCellWidget(row_position, 5, delete_btn)
        self.update_total()
        self.product_input.clear()

    def delete_from_bill_widget(self, btn):
        for r in range(self.table.rowCount()):
            if self.table.cellWidget(r, 5) == btn:
                self.table.removeRow(r)
                self.update_total()
                break

    # -------------------------------
    # Edit quantity directly
    # -------------------------------
    def edit_quantity(self, row, col):
        if col == 1:
            try:
                qty = int(self.table.item(row, col).text())
                price = float(self.table.item(row, 2).text())
                self.table.item(row, 3).setText(str(qty * price))
                self.update_total()
            except:
                pass

    # -------------------------------
    # Update total
    # -------------------------------
    def update_total(self):
        total = 0
        for r in range(self.table.rowCount()):
            total += float(self.table.item(r, 3).text())
        self.total_label.setText(f"Grand Total: Rs.{total}")

    # -------------------------------
    # Complete sale and print
    # -------------------------------
    def complete_sale(self):
        if self.table.rowCount() == 0:
            QMessageBox.warning(self, "Error", "No items in bill!")
            return

        self.finalize_btn.setEnabled(False)

        try:
            shop_name = "🛒 My Shop"
            user_name = "Admin"
            date_time = datetime.now().strftime("%d/%m/%Y %H:%M")

            # Optimized for thermal printer: 32 characters width (fits 80mm paper at 10pt monospaced)
            receipt_width = 32
            separator = "=" * receipt_width

            receipt = f"{separator}\n"
            # Center shop name (truncate if too long)
            shop_name_short = (shop_name[:receipt_width//2 * 2]).center(receipt_width)
            receipt += f"{shop_name_short}\n"
            receipt += f"{separator}\n"
            receipt += f"Date: {date_time}\n"
            receipt += f"Cashier: {user_name}\n"
            receipt += f"{separator}\n"

            # Compact items header (fits 32 chars: Name=16, Qty=3, Price=6, Total=7)
            receipt += f"{'Item':<16} {'Qty':>2} {'@':>1} {'Price':>5} {'Total':>7}\n"
            receipt += f"{separator}\n"

            total_amount = 0
            for r in range(self.table.rowCount()):
                name = self.table.item(r, 0).text()[:16]  # Truncate to 16 chars
                qty = int(self.table.item(r, 1).text())
                price = float(self.table.item(r, 2).text())
                item_total = float(self.table.item(r, 3).text())
                total_amount += item_total
                
                name_padded = name.ljust(16)
                # Compact line: Name (16) + Qty (2) + @ (1) + Price (5) + Total (7) = 31 chars
                receipt += f"{name_padded}{qty:>2} @ {price:>5.2f} {item_total:>7.2f}\n"
                
                barcode = self.table.item(r, 4).text()
                self.sales.make_sale(name=name, barcode=barcode, quantity=qty)

            receipt += f"{separator}\n"
            # Total line (fits width)
            total_padded = "TOTAL AMOUNT".ljust(22)
            receipt += f"{total_padded}{total_amount:>7.2f}\n"
            receipt += f"{separator}\n"
            receipt += "Thank you!\n"
            receipt += "Visit again.\n"  # Short footer for small paper
            receipt += f"{separator}\n"
            receipt += "\n"  # Extra line for clean cut

            # Direct print setup for thermal printer (small paper, no popups)
            doc = QTextDocument()
            doc.setPlainText(receipt)
            # Monospaced font optimized for thermal (small size, fixed width)
            font = QFont("Courier New", 8)  # Smaller font (8pt) for compact receipt
            doc.setDefaultFont(font)
            
            printer = QPrinter(QPrinter.HighResolution)
            printer.setOutputFormat(QPrinter.NativeFormat)  # Only physical printing
            printer.setPageSize(QPrinter.Custom)
            # Thermal paper: 80mm width, 150mm height (enough for typical receipt; auto-feeds if longer)
            printer.setPaperSize(QSizeF(80, 150), QPrinter.Millimeter)
            printer.setFullPage(True)
            printer.setPageMargins(0, 0, 0, 0, QPrinter.Millimeter)  # Zero margins for edge-to-edge
            printer.setOrientation(QPrinter.Portrait)
            printer.setColorMode(QPrinter.Monochrome)  # Black & white for thermal

            # Attempt direct print to default printer (no dialog for POS speed)
            success = doc.print_(printer)
            if success:
                self.table.setRowCount(0)
                self.update_total()
                QMessageBox.information(self, "Success", "Sale Completed and Receipt Printed ✅")
            else:
                # Fallback: Manual print dialog (only if direct fails, e.g., no default printer)
                dialog = QPrintDialog(printer, self)
                dialog.setWindowTitle("Print Receipt (Manual)")
                if dialog.exec_() == QPrintDialog.Accepted:
                    doc.print_(printer)
                    self.table.setRowCount(0)
                    self.update_total()
                    QMessageBox.information(self, "Success", "Sale Completed and Receipt Printed ✅")
                else:
                    self.table.setRowCount(0)
                    self.update_total()
                    QMessageBox.information(self, "Info", "Sale Completed. Printing Cancelled.")
        except Exception as e:
            # Robust error handling: Always complete sale, log error
            print(f"Error in complete_sale: {e}")
            self.table.setRowCount(0)
            self.update_total()
            QMessageBox.warning(self, "Warning", f"Sale Completed, but printing failed: {str(e)}\nCheck printer connection.")
        finally:
            self.finalize_btn.setEnabled(True)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = POS()
    window.show()
    sys.exit(app.exec_())
