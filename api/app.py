
    
from flask import Flask, render_template, request, redirect
import sqlite3
from datetime import datetime

# Flask app paths for Vercel
app = Flask(
    __name__,
    template_folder="../templates",
    static_folder="../static"
)

DB_PATH = "/tmp/inventory.db"

def get_db():
    return sqlite3.connect(DB_PATH)

# Initialize database
def init_db():
    conn = get_db()
    cur = conn.cursor()

    # Inventory with quantity
    cur.execute("""
        CREATE TABLE IF NOT EXISTS inventory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            barcode TEXT UNIQUE,
            quantity INTEGER,
            updated_time TEXT
        )
    """)

    # Logs with quantity change
    cur.execute("""
        CREATE TABLE IF NOT EXISTS logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            barcode TEXT,
            action TEXT,
            quantity INTEGER,
            time TEXT
        )
    """)

    conn.commit()
    conn.close()

init_db()

@app.route("/")
def index():
    conn = get_db()
    cur = conn.cursor()

    inventory = cur.execute(
        "SELECT * FROM inventory ORDER BY id DESC"
    ).fetchall()

    logs = cur.execute(
        "SELECT * FROM logs ORDER BY id DESC"
    ).fetchall()

    conn.close()
    return render_template(
        "index.html",
        inventory=inventory,
        logs=logs
    )

@app.route("/add", methods=["POST"])
def add_item():
    barcode = request.form.get("barcode")
    qty = int(request.form.get("quantity", 0))
    time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if barcode and qty > 0:
        conn = get_db()
        cur = conn.cursor()

        cur.execute(
            "SELECT quantity FROM inventory WHERE barcode = ?",
            (barcode,)
        )
        row = cur.fetchone()

        if row:
            new_qty = row[0] + qty
            cur.execute(
                "UPDATE inventory SET quantity = ?, updated_time = ? WHERE barcode = ?",
                (new_qty, time, barcode)
            )
        else:
            cur.execute(
                "INSERT INTO inventory (barcode, quantity, updated_time) VALUES (?, ?, ?)",
                (barcode, qty, time)
            )

        cur.execute(
            "INSERT INTO logs (barcode, action, quantity, time) VALUES (?, ?, ?, ?)",
            (barcode, "Added", qty, time)
        )

        conn.commit()
        conn.close()

    return redirect("/")

@app.route("/remove", methods=["POST"])
def remove_item():
    barcode = request.form.get("barcode")
    qty = int(request.form.get("quantity", 0))
    time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if barcode and qty > 0:
        conn = get_db()
        cur = conn.cursor()

        cur.execute(
            "SELECT quantity FROM inventory WHERE barcode = ?",
            (barcode,)
        )
        row = cur.fetchone()

        if row:
            remaining = row[0] - qty

            if remaining > 0:
                cur.execute(
                    "UPDATE inventory SET quantity = ?, updated_time = ? WHERE barcode = ?",
                    (remaining, time, barcode)
                )
            else:
                cur.execute(
                    "DELETE FROM inventory WHERE barcode = ?",
                    (barcode,)
                )

            cur.execute(
                "INSERT INTO logs (barcode, action, quantity, time) VALUES (?, ?, ?, ?)",
                (barcode, "Removed", qty, time)
            )

            conn.commit()

        conn.close()

    return redirect("/")

# Required export for Vercel
app = app
