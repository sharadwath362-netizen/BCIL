from flask import Flask, render_template, request, redirect, send_file
import sqlite3
from datetime import datetime
import pandas as pd
from fpdf import FPDF
import io
import os

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

# ---------------- Export Routes ---------------- #

@app.route("/export/excel")
def export_excel():
    conn = get_db()
    df = pd.read_sql_query("SELECT * FROM logs ORDER BY id DESC", conn)
    conn.close()

    output = io.BytesIO()
    df.to_excel(output, index=False, engine="openpyxl")
    output.seek(0)

    filename = f"inventory_logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    return send_file(
        output,
        as_attachment=True,
        download_name=filename,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

@app.route("/export/pdf")
def export_pdf():
    from fpdf import FPDF
    import os, io

    conn = get_db()
    cur = conn.cursor()
    logs = cur.execute("SELECT * FROM logs ORDER BY id DESC").fetchall()
    conn.close()

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    # -------- PATH SETUP (VERCEL SAFE) --------
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    logo_path = os.path.join(BASE_DIR, "..", "static", "college_logo.png")

    # -------- HEADER LOGO --------
    try:
        if os.path.exists(logo_path):
            pdf.image(logo_path, x=10, y=8, w=25)
    except Exception:
        pass  # NEVER crash PDF

    # Header text
    pdf.set_xy(40, 10)
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 8, "Barcode Based Inventory System", ln=True)

    pdf.set_x(40)
    pdf.set_font("Arial", "", 10)
    pdf.cell(0, 6, "Inventory Time Log Report", ln=True)

    pdf.ln(12)

    # -------- WATERMARK (CENTER LOGO) --------
    try:
        if os.path.exists(logo_path):
            pdf.image(logo_path, x=30, y=70, w=150)
    except Exception:
        pass  # watermark must NEVER crash

    # -------- TABLE --------
    pdf.set_font("Arial", "B", 11)
    headers = ["ID", "Barcode", "Action", "Qty", "Time"]
    widths = [10, 40, 25, 15, 60]

    for i in range(len(headers)):
        pdf.cell(widths[i], 8, headers[i], 1)
    pdf.ln()

    pdf.set_font("Arial", "", 10)
    for row in logs:
        pdf.cell(widths[0], 8, str(row[0]), 1)
        pdf.cell(widths[1], 8, str(row[1]), 1)
        pdf.cell(widths[2], 8, str(row[2]), 1)
        pdf.cell(widths[3], 8, str(row[3]), 1)
        pdf.cell(widths[4], 8, str(row[4]), 1)
        pdf.ln()

    # -------- OUTPUT --------
    buffer = io.BytesIO()
    pdf.output(buffer)
    buffer.seek(0)

    return send_file(
        buffer,
        as_attachment=True,
        download_name="inventory_logs.pdf",
        mimetype="application/pdf"
    )


    
# Required export for Vercel
app = app
