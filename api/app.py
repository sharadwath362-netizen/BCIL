from flask import Flask, render_template, request, redirect, send_file
import sqlite3
from datetime import datetime
import pandas as pd
from fpdf import FPDF
import os

app = Flask(
    __name__,
    template_folder="../templates",
    static_folder="../static"
)

DB_PATH = "/tmp/inventory.db"
LOGO_PATH = os.path.join(app.static_folder, "college_logo.png")


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

    inventory = cur.execute("SELECT * FROM inventory ORDER BY id DESC").fetchall()
    logs = cur.execute("SELECT * FROM logs ORDER BY id DESC").fetchall()

    conn.close()
    return render_template("index.html", inventory=inventory, logs=logs)


@app.route("/add", methods=["POST"])
def add_item():
    barcode = request.form["barcode"]
    qty = int(request.form["quantity"])
    time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    conn = get_db()
    cur = conn.cursor()

    cur.execute("SELECT quantity FROM inventory WHERE barcode=?", (barcode,))
    row = cur.fetchone()

    if row:
        cur.execute(
            "UPDATE inventory SET quantity=?, updated_time=? WHERE barcode=?",
            (row[0] + qty, time, barcode)
        )
    else:
        cur.execute(
            "INSERT INTO inventory (barcode, quantity, updated_time) VALUES (?, ?, ?)",
            (barcode, qty, time)
        )

    cur.execute(
        "INSERT INTO logs (barcode, action, quantity, time) VALUES (?, 'Added', ?, ?)",
        (barcode, qty, time)
    )

    conn.commit()
    conn.close()
    return redirect("/")


@app.route("/remove", methods=["POST"])
def remove_item():
    barcode = request.form["barcode"]
    qty = int(request.form["quantity"])
    time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    conn = get_db()
    cur = conn.cursor()

    cur.execute("SELECT quantity FROM inventory WHERE barcode=?", (barcode,))
    row = cur.fetchone()

    if row:
        remaining = row[0] - qty
        if remaining > 0:
            cur.execute(
                "UPDATE inventory SET quantity=?, updated_time=? WHERE barcode=?",
                (remaining, time, barcode)
            )
        else:
            cur.execute("DELETE FROM inventory WHERE barcode=?", (barcode,))

        cur.execute(
            "INSERT INTO logs (barcode, action, quantity, time) VALUES (?, 'Removed', ?, ?)",
            (barcode, qty, time)
        )

    conn.commit()
    conn.close()
    return redirect("/")


# ---------- EXPORT EXCEL ----------
@app.route("/export/excel")
def export_excel():
    conn = get_db()
    df = pd.read_sql_query("SELECT * FROM logs ORDER BY id DESC", conn)
    conn.close()

    file_path = "/tmp/inventory_logs.xlsx"
    df.to_excel(file_path, index=False)

    return send_file(file_path, as_attachment=True)


# ---------- EXPORT PDF ----------
@app.route("/export/pdf")
def export_pdf():
    conn = get_db()
    logs = conn.execute("SELECT * FROM logs ORDER BY id DESC").fetchall()
    conn.close()

    pdf = FPDF()
    pdf.add_page()

    # Header Logo
    if os.path.exists(LOGO_PATH):
        pdf.image(LOGO_PATH, x=10, y=8, w=18)

    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, "Barcode Based Inventory Log", ln=True, align="C")
    pdf.ln(6)

    # Watermark
    if os.path.exists(LOGO_PATH):
        pdf.set_alpha(0.08)
        pdf.image(LOGO_PATH, x=35, y=70, w=140)
        pdf.set_alpha(1)

    pdf.set_font("Arial", size=10)

    for log in logs:
        pdf.cell(0, 8, f"{log[1]} | {log[2]} | Qty: {log[3]} | {log[4]}", ln=True)

    file_path = "/tmp/inventory_logs.pdf"
    pdf.output(file_path)

    return send_file(file_path, as_attachment=True)


# Vercel entry point
app = app
