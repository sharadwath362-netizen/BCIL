from flask import Flask, render_template, request, redirect, send_file
import sqlite3
from datetime import datetime
import pandas as pd
from fpdf import FPDF
import io

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
    conn = get_db()
    cur = conn.cursor()
    logs = cur.execute("SELECT * FROM logs ORDER BY id DESC").fetchall()
    conn.close()

    pdf = FPDF()
    pdf.add_page()

    # ---------- LOGO WATERMARK ----------
    pdf.image(
        "static/college_logo.png",
        x=35,        # horizontal position
        y=60,        # vertical position
        w=140        # width (large = watermark feel)
    )
    # -----------------------------------

    # Move cursor down so table prints OVER the watermark
    pdf.set_y(20)

    # Title
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, "Inventory Time Log", ln=True, align="C")
    pdf.ln(5)

    # Table Header
    pdf.set_font("Arial", "B", 11)
    headers = ["ID", "Barcode", "Action", "Qty", "Time"]
    widths = [10, 40, 25, 15, 60]

    for i in range(len(headers)):
        pdf.cell(widths[i], 10, headers[i], 1)
    pdf.ln()

    # Table Rows
    pdf.set_font("Arial", "", 10)
    for row in logs:
        pdf.cell(widths[0], 8, str(row[0]), 1)
        pdf.cell(widths[1], 8, str(row[1]), 1)
        pdf.cell(widths[2], 8, str(row[2]), 1)
        pdf.cell(widths[3], 8, str(row[3]), 1)
        pdf.cell(widths[4], 8, str(row[4]), 1)
        pdf.ln()

    output = io.BytesIO()
    pdf.output(output)
    output.seek(0)

    filename = f"inventory_logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    return send_file(
        output,
        as_attachment=True,
        download_name=filename,
        mimetype="application/pdf"
    )



# Required export for Vercel
app = app
