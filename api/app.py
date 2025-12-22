from flask import Flask, render_template, request, jsonify, send_file
import sqlite3
from datetime import datetime
import pandas as pd
from fpdf import FPDF
import io

app = Flask(
    __name__,
    template_folder="../templates",
    static_folder="../static"
)

DB_PATH = "/tmp/inventory.db"

def get_db():
    return sqlite3.connect(DB_PATH)

def init_db():
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS inventory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            barcode TEXT UNIQUE,
            quantity INTEGER,
            updated_time TEXT
        )
    """)

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
    return render_template("index.html", inventory=inventory, logs=logs)

# ---------------- ADD ITEM (NO REFRESH) ---------------- #

@app.route("/add", methods=["POST"])
def add_item():
    data = request.get_json()
    barcode = data.get("barcode")
    qty = int(data.get("quantity", 0))
    time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if not barcode or qty <= 0:
        return jsonify({"status": "error", "message": "Invalid input"}), 400

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

    return jsonify({"status": "success"})

# ---------------- REMOVE ITEM (NO REFRESH) ---------------- #

@app.route("/remove", methods=["POST"])
def remove_item():
    data = request.get_json()
    barcode = data.get("barcode")
    qty = int(data.get("quantity", 0))
    time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if not barcode or qty <= 0:
        return jsonify({"status": "error", "message": "Invalid input"}), 400

    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        "SELECT quantity FROM inventory WHERE barcode = ?",
        (barcode,)
    )
    row = cur.fetchone()

    if not row:
        conn.close()
        return jsonify({"status": "error", "message": "Item not found"}), 404

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

    return jsonify({"status": "success"})

# Required for Vercel
app = app
