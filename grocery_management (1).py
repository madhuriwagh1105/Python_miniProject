"""
============================================================
       ABC GROCERY STORE - MANAGEMENT SYSTEM
============================================================
Author  : Grocery Management System
Version : 1.0
Database: SQLite
============================================================
"""

import sqlite3
import hashlib
import json
import os
import sys
from datetime import datetime

# ─────────────────────────────────────────
#  CONFIG
# ─────────────────────────────────────────
DB_FILE        = "grocery_store.db"
CART_FILE      = "carts.json"
STORE_NAME     = "ABC Grocery Store"
STORE_ADDRESS  = "123, MG Road, Nagpur, Maharashtra - 440001"
STORE_MOBILE   = "+91-9876543210"
STORE_GST      = "27ABCDE1234F1Z5"
GST_RATE       = 0.05          # 5 %
DISCOUNT_RATE  = 0.10          # 10 % (applied when total > ₹500)
DISCOUNT_LIMIT = 500           # minimum subtotal to earn discount

# ─────────────────────────────────────────
#  HELPERS
# ─────────────────────────────────────────

def clear():
    os.system("cls" if os.name == "nt" else "clear")

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def separator(char="─", width=54):
    print(char * width)

def header(title: str):
    separator("═")
    print(f"  {title.center(50)}")
    separator("═")

def pause():
    input("\n  Press Enter to continue...")

def fmt_inr(amount: float) -> str:
    return f"₹{amount:,.2f}"

# ─────────────────────────────────────────
#  DATABASE INITIALISATION
# ─────────────────────────────────────────

def get_conn():
    return sqlite3.connect(DB_FILE)

def init_db():
    conn = get_conn()
    cur  = conn.cursor()

    cur.executescript("""
        PRAGMA foreign_keys = ON;

        CREATE TABLE IF NOT EXISTS users (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            username      TEXT    NOT NULL UNIQUE,
            password_hash TEXT    NOT NULL,
            role          TEXT    NOT NULL DEFAULT 'user',
            created_at    TEXT    NOT NULL DEFAULT (datetime('now','localtime'))
        );

        CREATE TABLE IF NOT EXISTS products (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            name       TEXT    NOT NULL UNIQUE,
            price      REAL    NOT NULL CHECK(price >= 0),
            quantity   INTEGER NOT NULL CHECK(quantity >= 0),
            created_at TEXT    NOT NULL DEFAULT (datetime('now','localtime'))
        );

        CREATE TABLE IF NOT EXISTS orders (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            username    TEXT    NOT NULL,
            subtotal    REAL    NOT NULL,
            gst_amount  REAL    NOT NULL,
            discount    REAL    NOT NULL DEFAULT 0,
            total       REAL    NOT NULL,
            bill_file   TEXT,
            ordered_at  TEXT    NOT NULL DEFAULT (datetime('now','localtime'))
        );

        CREATE TABLE IF NOT EXISTS order_items (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id    INTEGER NOT NULL REFERENCES orders(id),
            product_id  INTEGER NOT NULL REFERENCES products(id),
            product_name TEXT   NOT NULL,
            quantity    INTEGER NOT NULL,
            unit_price  REAL    NOT NULL,
            total_price REAL    NOT NULL
        );
    """)

    # seed default admin if not present
    cur.execute("SELECT id FROM users WHERE username='admin'")
    if not cur.fetchone():
        cur.execute(
            "INSERT INTO users (username, password_hash, role) VALUES (?,?,?)",
            ("admin", hash_password("admin123"), "admin")
        )
        print("  [INFO] Default admin created  →  username: admin | password: admin123")

    conn.commit()
    conn.close()

# ─────────────────────────────────────────
#  CART (JSON persistence per user)
# ─────────────────────────────────────────

def load_carts() -> dict:
    if os.path.exists(CART_FILE):
        try:
            with open(CART_FILE) as f:
                return json.load(f)
        except Exception:
            pass
    return {}

def save_carts(carts: dict):
    with open(CART_FILE, "w") as f:
        json.dump(carts, f, indent=2)

def get_cart(username: str) -> dict:
    return load_carts().get(username, {})

def set_cart(username: str, cart: dict):
    carts = load_carts()
    carts[username] = cart
    save_carts(carts)

def clear_cart(username: str):
    set_cart(username, {})

# ─────────────────────────────────────────
#  PRODUCT HELPERS
# ─────────────────────────────────────────

def get_product_by_id(pid: int):
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("SELECT id, name, price, quantity FROM products WHERE id=?", (pid,))
        return cur.fetchone()

def get_product_by_name(name: str):
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("SELECT id, name, price, quantity FROM products WHERE LOWER(name)=LOWER(?)", (name,))
        return cur.fetchone()

def get_all_products():
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("SELECT id, name, price, quantity FROM products ORDER BY name")
        return cur.fetchall()

# ─────────────────────────────────────────
#  AUTH
# ─────────────────────────────────────────

def authenticate(username: str, password: str):
    """Returns (role) or None."""
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT role FROM users WHERE username=? AND password_hash=?",
            (username, hash_password(password))
        )
        row = cur.fetchone()
        return row[0] if row else None

def register_user(username: str, password: str) -> bool:
    try:
        with get_conn() as conn:
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO users (username, password_hash, role) VALUES (?,?,?)",
                (username, hash_password(password), "user")
            )
            conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False

# ─────────────────────────────────────────
#  BILL GENERATION
# ─────────────────────────────────────────

def generate_bill(username: str, cart_snapshot: list, subtotal: float,
                  gst_amount: float, discount: float, total: float) -> str:
    now      = datetime.now()
    dt_str   = now.strftime("%Y-%m-%d %H:%M:%S")
    file_tag = now.strftime("%Y%m%d_%H%M%S")
    filename = f"bill_{username}_{file_tag}.txt"

    lines = []
    W = 54

    def ln(text="", align="left", fill=" "):
        if align == "center":
            lines.append(text.center(W))
        elif align == "right":
            lines.append(text.rjust(W))
        else:
            lines.append(text)

    def sep(c="─"):
        lines.append(c * W)

    sep("═")
    ln("ABC GROCERY STORE", "center")
    ln("CASH / TAX INVOICE", "center")
    sep("═")
    ln(f"Store : {STORE_NAME}")
    ln(f"Addr  : {STORE_ADDRESS}")
    ln(f"Mobile: {STORE_MOBILE}")
    ln(f"GSTIN : {STORE_GST}")
    sep()
    ln(f"Customer : {username}")
    ln(f"Date/Time: {dt_str}")
    sep()
    ln(f"{'#':<3} {'Product':<20} {'Qty':>4} {'Rate':>8} {'Amount':>10}")
    sep()

    for i, (name, qty, unit_price, total_price) in enumerate(cart_snapshot, 1):
        ln(f"{i:<3} {name:<20} {qty:>4} {fmt_inr(unit_price):>8} {fmt_inr(total_price):>10}")

    sep()
    ln(f"{'Subtotal':>43} {fmt_inr(subtotal):>10}")
    ln(f"{'GST (5%)':>43} {fmt_inr(gst_amount):>10}")
    if discount > 0:
        ln(f"{'Discount (10%)':>43} -{fmt_inr(discount):>9}")
    sep("═")
    ln(f"{'FINAL TOTAL':>43} {fmt_inr(total):>10}")
    sep("═")
    ln("Thank you for shopping with us!", "center")
    ln("Visit again  ❤", "center")
    sep("═")

    content = "\n".join(lines)
    with open(filename, "w", encoding="utf-8") as f:
        f.write(content)

    return filename

# ─────────────────────────────────────────
#  ██████  ADMIN PANEL  ██████
# ─────────────────────────────────────────

def admin_add_product():
    header("ADD NEW PRODUCT")
    name = input("  Product name : ").strip()
    if not name:
        print("  [!] Name cannot be empty.")
        return

    if get_product_by_name(name):
        print(f"  [!] Product '{name}' already exists. Use 'Update Stock' instead.")
        return

    try:
        price    = float(input("  Price (₹)    : "))
        quantity = int(input("  Quantity     : "))
        if price < 0 or quantity < 0:
            raise ValueError
    except ValueError:
        print("  [!] Invalid price or quantity.")
        return

    with get_conn() as conn:
        conn.execute(
            "INSERT INTO products (name, price, quantity) VALUES (?,?,?)",
            (name, price, quantity)
        )
        conn.commit()

    print(f"\n  ✔ Product '{name}' added successfully.")
    pause()

def admin_update_stock():
    header("UPDATE PRODUCT STOCK")
    products = get_all_products()
    if not products:
        print("  No products found.")
        pause()
        return

    print(f"\n  {'ID':<5} {'Name':<25} {'Price':>10} {'Stock':>8}")
    separator()
    for pid, name, price, qty in products:
        print(f"  {pid:<5} {name:<25} {fmt_inr(price):>10} {qty:>8}")
    separator()

    try:
        pid = int(input("\n  Enter Product ID to update: "))
        row = get_product_by_id(pid)
        if not row:
            print("  [!] Product not found.")
            pause()
            return

        print(f"\n  Current stock of '{row[1]}': {row[3]}")
        new_qty = int(input("  New stock quantity      : "))
        if new_qty < 0:
            raise ValueError
    except ValueError:
        print("  [!] Invalid input.")
        pause()
        return

    with get_conn() as conn:
        conn.execute("UPDATE products SET quantity=? WHERE id=?", (new_qty, pid))
        conn.commit()

    print(f"\n  ✔ Stock updated to {new_qty} for '{row[1]}'.")
    pause()

def admin_view_products():
    header("ALL PRODUCTS")
    products = get_all_products()
    if not products:
        print("  No products in database.")
        pause()
        return

    print(f"\n  {'ID':<5} {'Name':<25} {'Price':>10} {'Stock':>8}")
    separator()
    for pid, name, price, qty in products:
        low = " ⚠ LOW" if qty < 5 else ""
        print(f"  {pid:<5} {name:<25} {fmt_inr(price):>10} {qty:>8}{low}")
    separator()
    pause()

def admin_view_all_orders():
    header("ALL CUSTOMER ORDERS")
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT o.id, o.username, o.subtotal, o.gst_amount, o.discount,
                   o.total, o.bill_file, o.ordered_at
            FROM orders o
            ORDER BY o.ordered_at DESC
        """)
        orders = cur.fetchall()

    if not orders:
        print("  No orders placed yet.")
        pause()
        return

    for order in orders:
        oid, uname, sub, gst, disc, total, bill_f, oat = order
        print(f"\n  Order #{oid}  |  Customer: {uname}  |  {oat}")
        separator()

        with get_conn() as conn:
            cur = conn.cursor()
            cur.execute("""
                SELECT product_name, quantity, unit_price, total_price
                FROM order_items WHERE order_id=?
            """, (oid,))
            items = cur.fetchall()

        print(f"  {'Product':<22} {'Qty':>5} {'Rate':>10} {'Total':>10}")
        separator("·")
        for name, qty, rate, tot in items:
            print(f"  {name:<22} {qty:>5} {fmt_inr(rate):>10} {fmt_inr(tot):>10}")
        separator("·")
        print(f"  {'Subtotal':>38} {fmt_inr(sub):>10}")
        print(f"  {'GST (5%)':>38} {fmt_inr(gst):>10}")
        if disc > 0:
            print(f"  {'Discount':>38} -{fmt_inr(disc):>9}")
        print(f"  {'TOTAL':>38} {fmt_inr(total):>10}")
        if bill_f:
            print(f"  Bill File : {bill_f}")
        separator()

    pause()

def admin_panel(username: str):
    while True:
        clear()
        header(f"ADMIN PANEL  [ {username} ]")
        print("""
  1. Add New Product
  2. Update Product Stock
  3. View All Products
  4. View All Orders
  0. Logout
        """)
        separator()
        choice = input("  Select option: ").strip()

        if   choice == "1": admin_add_product()
        elif choice == "2": admin_update_stock()
        elif choice == "3": admin_view_products()
        elif choice == "4": admin_view_all_orders()
        elif choice == "0":
            print("\n  Logged out. Goodbye, Admin!\n")
            break
        else:
            print("  [!] Invalid option.")
            pause()

# ─────────────────────────────────────────
#  ██████  USER PANEL  ██████
# ─────────────────────────────────────────

def user_view_products():
    header("AVAILABLE PRODUCTS")
    products = get_all_products()
    if not products:
        print("  No products available yet.")
        pause()
        return

    print(f"\n  {'ID':<5} {'Name':<25} {'Price':>10} {'Stock':>8}")
    separator()
    for pid, name, price, qty in products:
        avail = qty if qty > 0 else "Out of Stock"
        print(f"  {pid:<5} {name:<25} {fmt_inr(price):>10} {str(avail):>8}")
    separator()
    pause()

def user_view_cart(username: str, silent=False) -> dict:
    cart = get_cart(username)
    if not silent:
        header("YOUR CART")
    if not cart:
        if not silent:
            print("  Cart is empty.")
            pause()
        return cart

    total = 0.0
    if not silent:
        print(f"\n  {'Product':<25} {'Qty':>5} {'Rate':>10} {'Total':>10}")
        separator()

    for pid_str, item in cart.items():
        line_total = item["qty"] * item["price"]
        total += line_total
        if not silent:
            print(f"  {item['name']:<25} {item['qty']:>5} {fmt_inr(item['price']):>10} {fmt_inr(line_total):>10}")

    if not silent:
        separator()
        print(f"  {'Cart Total':>41} {fmt_inr(total):>10}")
        separator()
        pause()

    return cart

def user_add_to_cart(username: str):
    header("ADD PRODUCT TO CART")
    products = get_all_products()
    if not products:
        print("  No products available.")
        pause()
        return

    print(f"\n  {'ID':<5} {'Name':<25} {'Price':>10} {'Stock':>8}")
    separator()
    for pid, name, price, qty in products:
        avail = qty if qty > 0 else "—"
        print(f"  {pid:<5} {name:<25} {fmt_inr(price):>10} {str(avail):>8}")
    separator()

    try:
        pid = int(input("\n  Enter Product ID: "))
        row = get_product_by_id(pid)
        if not row:
            print("  [!] Product not found.")
            pause()
            return

        _, name, price, stock = row
        if stock == 0:
            print(f"  [!] '{name}' is out of stock.")
            pause()
            return

        qty = int(input(f"  Quantity (available: {stock}): "))
        if qty <= 0:
            raise ValueError

        # check stock including already-carted quantity
        cart = get_cart(username)
        already_in_cart = cart.get(str(pid), {}).get("qty", 0)
        if already_in_cart + qty > stock:
            print(f"  [!] Only {stock - already_in_cart} more unit(s) can be added (stock: {stock}, in cart: {already_in_cart}).")
            pause()
            return

    except ValueError:
        print("  [!] Invalid input.")
        pause()
        return

    cart = get_cart(username)
    if str(pid) in cart:
        cart[str(pid)]["qty"] += qty
    else:
        cart[str(pid)] = {"name": name, "price": price, "qty": qty}
    set_cart(username, cart)

    print(f"\n  ✔ {qty}× '{name}' added to cart.")
    pause()

def user_update_cart(username: str):
    header("UPDATE CART QUANTITY")
    cart = get_cart(username)
    if not cart:
        print("  Cart is empty.")
        pause()
        return

    print(f"\n  {'PID':<6} {'Product':<25} {'In Cart':>8} {'Stock':>8}")
    separator()
    for pid_str, item in cart.items():
        row = get_product_by_id(int(pid_str))
        stock = row[3] if row else "N/A"
        print(f"  {pid_str:<6} {item['name']:<25} {item['qty']:>8} {str(stock):>8}")
    separator()

    try:
        pid_str = input("\n  Enter Product ID to update (or 0 to cancel): ").strip()
        if pid_str == "0":
            return
        if pid_str not in cart:
            print("  [!] Product not in cart.")
            pause()
            return

        new_qty = int(input(f"  New quantity for '{cart[pid_str]['name']}' (0 to remove): "))
        if new_qty < 0:
            raise ValueError
    except ValueError:
        print("  [!] Invalid input.")
        pause()
        return

    if new_qty == 0:
        del cart[pid_str]
        set_cart(username, cart)
        print("  ✔ Item removed from cart.")
    else:
        row = get_product_by_id(int(pid_str))
        if not row:
            print("  [!] Product no longer exists.")
            pause()
            return
        stock = row[3]
        if new_qty > stock:
            print(f"  [!] Only {stock} unit(s) in stock.")
            pause()
            return
        cart[pid_str]["qty"] = new_qty
        set_cart(username, cart)
        print(f"  ✔ Quantity updated to {new_qty}.")

    pause()

def user_remove_from_cart(username: str):
    header("REMOVE ITEM FROM CART")
    cart = get_cart(username)
    if not cart:
        print("  Cart is empty.")
        pause()
        return

    print(f"\n  {'PID':<6} {'Product':<25} {'Qty':>6}")
    separator()
    for pid_str, item in cart.items():
        print(f"  {pid_str:<6} {item['name']:<25} {item['qty']:>6}")
    separator()

    pid_str = input("\n  Enter Product ID to remove (or 0 to cancel): ").strip()
    if pid_str == "0":
        return
    if pid_str not in cart:
        print("  [!] Product not in cart.")
        pause()
        return

    name = cart[pid_str]["name"]
    del cart[pid_str]
    set_cart(username, cart)
    print(f"\n  ✔ '{name}' removed from cart.")
    pause()

def user_checkout(username: str):
    header("CHECKOUT")
    cart = get_cart(username)
    if not cart:
        print("  Cart is empty. Nothing to checkout.")
        pause()
        return

    # ── validate stock one more time ──
    print("\n  Validating stock availability...")
    issues = []
    for pid_str, item in cart.items():
        row = get_product_by_id(int(pid_str))
        if not row:
            issues.append(f"  '{item['name']}' no longer exists.")
        elif row[3] < item["qty"]:
            issues.append(f"  '{item['name']}': only {row[3]} left (you need {item['qty']}).")

    if issues:
        print("\n  [!] Cannot proceed — stock issues found:")
        for msg in issues:
            print(msg)
        print("  Please update your cart.")
        pause()
        return

    # ── calculate bill ──
    cart_snapshot = []
    subtotal = 0.0
    for pid_str, item in cart.items():
        line = item["qty"] * item["price"]
        subtotal += line
        cart_snapshot.append((item["name"], item["qty"], item["price"], line))

    gst_amount = round(subtotal * GST_RATE, 2)
    discount   = round(subtotal * DISCOUNT_RATE, 2) if subtotal > DISCOUNT_LIMIT else 0.0
    total      = round(subtotal + gst_amount - discount, 2)

    # ── show summary ──
    print(f"\n  {'Product':<22} {'Qty':>4} {'Rate':>10} {'Amount':>10}")
    separator()
    for name, qty, price, line in cart_snapshot:
        print(f"  {name:<22} {qty:>4} {fmt_inr(price):>10} {fmt_inr(line):>10}")
    separator()
    print(f"  {'Subtotal':>37} {fmt_inr(subtotal):>10}")
    print(f"  {'GST (5%)':>37} {fmt_inr(gst_amount):>10}")
    if discount > 0:
        print(f"  {'Discount (10%)':>37} -{fmt_inr(discount):>9}")
    separator("═")
    print(f"  {'FINAL TOTAL':>37} {fmt_inr(total):>10}")
    separator("═")

    confirm = input("\n  Confirm order? (yes/no): ").strip().lower()
    if confirm not in ("yes", "y"):
        print("  Order cancelled.")
        pause()
        return

    # ── deduct stock & save order ──
    conn = get_conn()
    try:
        cur = conn.cursor()

        # deduct stock
        for pid_str, item in cart.items():
            cur.execute(
                "UPDATE products SET quantity = quantity - ? WHERE id=?",
                (item["qty"], int(pid_str))
            )

        # insert order
        cur.execute("""
            INSERT INTO orders (username, subtotal, gst_amount, discount, total)
            VALUES (?,?,?,?,?)
        """, (username, subtotal, gst_amount, discount, total))
        order_id = cur.lastrowid

        # insert order items
        for pid_str, item in cart.items():
            line = item["qty"] * item["price"]
            cur.execute("""
                INSERT INTO order_items (order_id, product_id, product_name, quantity, unit_price, total_price)
                VALUES (?,?,?,?,?,?)
            """, (order_id, int(pid_str), item["name"], item["qty"], item["price"], line))

        # generate bill
        bill_file = generate_bill(username, cart_snapshot, subtotal, gst_amount, discount, total)

        # store bill filename
        cur.execute("UPDATE orders SET bill_file=? WHERE id=?", (bill_file, order_id))

        conn.commit()
    except Exception as e:
        conn.rollback()
        print(f"\n  [!] Error placing order: {e}")
        pause()
        return
    finally:
        conn.close()

    # ── clear cart ──
    clear_cart(username)

    print(f"\n  ✔ Order placed successfully! (Order #{order_id})")
    print(f"  📄 Bill saved as: {bill_file}")
    pause()

def user_order_history(username: str):
    header("MY ORDER HISTORY")
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT id, subtotal, gst_amount, discount, total, bill_file, ordered_at
            FROM orders WHERE username=?
            ORDER BY ordered_at DESC
        """, (username,))
        orders = cur.fetchall()

    if not orders:
        print("  No orders placed yet.")
        pause()
        return

    for oid, sub, gst, disc, total, bill_f, oat in orders:
        print(f"\n  Order #{oid}  |  {oat}")
        separator("·")
        with get_conn() as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT product_name, quantity, unit_price, total_price FROM order_items WHERE order_id=?",
                (oid,)
            )
            items = cur.fetchall()

        for name, qty, rate, tot in items:
            print(f"  {name:<22} {qty:>4} × {fmt_inr(rate):>10} = {fmt_inr(tot):>10}")
        separator("·")
        print(f"  {'Subtotal':>38} {fmt_inr(sub):>10}")
        print(f"  {'GST':>38} {fmt_inr(gst):>10}")
        if disc > 0:
            print(f"  {'Discount':>38} -{fmt_inr(disc):>9}")
        print(f"  {'TOTAL':>38} {fmt_inr(total):>10}")
        if bill_f:
            print(f"  Bill: {bill_f}")
        separator()

    pause()

def user_panel(username: str):
    while True:
        clear()
        header(f"USER PANEL  [ {username} ]")
        cart = get_cart(username)
        items_count = sum(v["qty"] for v in cart.values()) if cart else 0
        print(f"\n  🛒 Cart items: {items_count}\n")
        print("""  1. View Products
  2. Add Product to Cart
  3. View Cart
  4. Update Cart Quantity
  5. Remove Item from Cart
  6. Checkout / Place Order
  7. My Order History
  0. Logout
        """)
        separator()
        choice = input("  Select option: ").strip()

        if   choice == "1": user_view_products()
        elif choice == "2": user_add_to_cart(username)
        elif choice == "3": user_view_cart(username)
        elif choice == "4": user_update_cart(username)
        elif choice == "5": user_remove_from_cart(username)
        elif choice == "6": user_checkout(username)
        elif choice == "7": user_order_history(username)
        elif choice == "0":
            print(f"\n  Logged out. Goodbye, {username}!\n")
            break
        else:
            print("  [!] Invalid option.")
            pause()

# ─────────────────────────────────────────
#  LOGIN / REGISTER
# ─────────────────────────────────────────

def login():
    header("LOGIN")
    username = input("  Username: ").strip()
    password = input("  Password: ").strip()

    if not username or not password:
        print("  [!] Username and password are required.")
        pause()
        return

    role = authenticate(username, password)
    if role is None:
        print("  [!] Invalid credentials.")
        pause()
        return

    clear()
    print(f"\n  ✔ Welcome, {username}!  (Role: {role})\n")

    if role == "admin":
        admin_panel(username)
    else:
        user_panel(username)

def register():
    header("NEW USER REGISTRATION")
    username = input("  Choose username: ").strip()
    if not username:
        print("  [!] Username cannot be empty.")
        pause()
        return

    password = input("  Choose password: ").strip()
    if len(password) < 4:
        print("  [!] Password must be at least 4 characters.")
        pause()
        return

    confirm = input("  Confirm password: ").strip()
    if password != confirm:
        print("  [!] Passwords do not match.")
        pause()
        return

    if register_user(username, password):
        print(f"\n  ✔ Account created for '{username}'. You can now log in.")
    else:
        print(f"  [!] Username '{username}' is already taken.")
    pause()

# ─────────────────────────────────────────
#  MAIN MENU
# ─────────────────────────────────────────

def main():
    init_db()
    while True:
        clear()
        header("ABC GROCERY STORE")
        print(f"""
  {STORE_ADDRESS}
  {STORE_MOBILE}
        """)
        separator()
        print("""
  1. Login
  2. Register (New User)
  0. Exit
        """)
        separator()
        choice = input("  Select option: ").strip()

        if   choice == "1": login()
        elif choice == "2": register()
        elif choice == "0":
            print("\n  Thank you for visiting ABC Grocery Store! Goodbye.\n")
            sys.exit(0)
        else:
            print("  [!] Invalid option.")
            pause()

# ─────────────────────────────────────────

if __name__ == "__main__":
    main()
