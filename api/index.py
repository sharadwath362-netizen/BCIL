from flask import Flask, render_template, request, redirect
import sqlite3
import os

app = Flask(__name__, template_folder="../templates", static_folder="../static")

DB_PATH = "/tmp/inventory.db"

# ------------------ Initialize DB ------------------
def init_db():
    if not os.path.exists(DB_PATH):
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS inventory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                barcode TEXT UNIQUE,
                name TEXT,
                quantity INTEGER
            )
        """)
        conn.commit()
        conn.close()

# ------------------ Routes ------------------
@app.route("/", methods=["GET", "POST"])
def index():
    init_db()  # Ensure DB exists

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

        conn.commit()
        conn.close()
        return redirect("/")

    # GET request: fetch all items
    cur.execute("SELECT * FROM inventory")
    items = cur.fetchall()
    conn.close()

    return render_template("index.html", items=items)

@app.route("/delete/<int:item_id>")
def delete(item_id):
    init_db()
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("DELETE FROM inventory WHERE id = ?", (item_id,))
    conn.commit()
    conn.close()
    return redirect("/")

