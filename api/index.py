from flask import Flask, render_template, request, redirect, send_file
import sqlite3
import os
from datetime import datetime
import pandas as pd
import io

app = Flask(__name__, template_folder="../templates", static_folder="../static")

DB_PATH = "inventory.db"

# ------------------ Initialize DB ------------------
def init_db():
    if not os.path.exists(DB_PATH):
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        # Inventory table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS inventory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                barcode TEXT UNIQUE,
                name TEXT,
                quantity INTEGER
            )
        """)
        # Activity logs table with timestamp
        cur.execute("""
            CREATE TABLE IF NOT EXISTS activity_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                barcode TEXT,
                action TEXT,
                quantity INTEGER
            )
        """)
        conn.commit()
        conn.close()

# ------------------ Main Inventory Page ------------------
@app.route("/", methods=["GET", "POST"])
def index():
    init_db()
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    if request.method == "POST":
        barcode = request.form.get("barcode")
        name = request.form.get("name")
        quantity = int(request.form.get("quantity"))
        action = request.form.get("action")

        cur.execute("SELECT id, quantity FROM inventory WHERE barcode = ?", (barcode,))
        row = cur.fetchone()

        if action == "add":
            if row:
                cur.execute("UPDATE inventory SET quantity = ? WHERE barcode = ?", (row[1]+quantity, barcode))
            else:
                cur.execute("INSERT INTO inventory (barcode, name, quantity) VALUES (?, ?, ?)", (barcode, name, quantity))
        elif action == "remove" and row:
            new_qty = max(row[1] - quantity, 0)
            if new_qty == 0:
                cur.execute("DELETE FROM inventory WHERE barcode = ?", (barcode,))
            else:
                cur.execute("UPDATE inventory SET quantity = ? WHERE barcode = ?", (new_qty, barcode))

        # Log every action with timestamp
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cur.execute("INSERT INTO activity_logs (timestamp, barcode, action, quantity) VALUES (?, ?, ?, ?)",
                    (now, barcode, action, quantity))

        conn.commit()
        conn.close()
        return redirect("/")

    # GET request: fetch inventory
    cur.execute("SELECT * FROM inventory")
    items = cur.fetchall()

    # Prepare Daily Activity data
    cur.execute("""
        SELECT DATE(timestamp) as day, SUM(quantity)
        FROM activity_logs
        GROUP BY day
        ORDER BY day
    """)
    activity_data = cur.fetchall()
    conn.close()

    dates = [row[0] for row in activity_data]
    daily_counts = [row[1] for row in activity_data]

    return render_template("index.html", items=items, dates=dates, daily_counts=daily_counts)

# ------------------ Delete Item ------------------
@app.route("/delete/<int:item_id>")
def delete(item_id):
    init_db()
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("DELETE FROM inventory WHERE id = ?", (item_id,))
    conn.commit()
    conn.close()
    return redirect("/")

# ------------------ History Page ------------------
@app.route("/history")
def history():
    init_db()
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT timestamp, barcode, action, quantity FROM activity_logs ORDER BY timestamp DESC")
    logs = cur.fetchall()
    conn.close()
    return render_template("history.html", logs=logs)

# ------------------ Export History to Excel ------------------
@app.route("/export")
def export():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT timestamp, barcode, action, quantity FROM activity_logs ORDER BY timestamp DESC", conn)
    conn.close()

    output = io.BytesIO()
    df.to_excel(output, index=False)
    output.seek(0)

    return send_file(
        output,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        as_attachment=True,
        download_name="activity_log.xlsx"
    )
