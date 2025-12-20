from flask import Flask, render_template, request, redirect
import sqlite3
from datetime import datetime
import os

# Create Flask app with correct paths for Vercel
app = Flask(
    __name__,
    template_folder="../templates",
    static_folder="../static"
)

# Database path (Vercel allows /tmp only)
DB_PATH = "/tmp/inventory.db"

def connect_db():
    return sqlite3.connect(DB_PATH)

# Initialize database
def init_db():
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS inventory (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        barcode TEXT UNIQUE,
        added_time TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        barcode TEXT,
        action TEXT,
        time TEXT
    )
    """)

    conn.commit()
    conn.close()

# Initialize DB once
init_db()

@app.route("/")
def index():
    conn = connect_db()
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
    time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if barcode:
        conn = connect_db()
        cur = conn.cursor()

        try:
            cur.execute(
                "INSERT INTO inventory (barcode, added_time) VALUES (?, ?)",
                (barcode, time)
            )
            cur.execute(
                "INSERT INTO logs (barcode, action, time) VALUES (?, ?, ?)",
                (barcode, "Added", time)
            )
            conn.commit()
        except sqlite3.IntegrityError:
            pass  # Ignore duplicate barcode
        finally:
            conn.close()

    return redirect("/")

@app.route("/remove", methods=["POST"])
def remove_item():
    barcode = request.form.get("barcode")
    time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if barcode:
        conn = connect_db()
        cur = conn.cursor()

        cur.execute(
            "DELETE FROM inventory WHERE barcode = ?",
            (barcode,)
        )

        cur.execute(
            "INSERT INTO logs (barcode, action, time) VALUES (?, ?, ?)",
            (barcode, "Removed", time)
        )

        conn.commit()
        conn.close()

    return redirect("/")

# IMPORTANT: expose app to Vercel
app = app
