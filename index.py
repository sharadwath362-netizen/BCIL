from flask import Flask, render_template, request, redirect
import sqlite3
import os

# Charts are OPTIONAL – app will still work if they fail
try:
    import visualizations
except Exception:
    visualizations = None

app = Flask(
    __name__,
    template_folder="templates",
    static_folder="static"
)

DB_PATH = "/tmp/inventory.db"

# ------------------ DB INIT ------------------
def init_db():
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

# ------------------ ROUTES ------------------
@app.route("/", methods=["GET", "POST"])
def index():
    init_db()

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    if request.method == "POST":
        barcode = request.form["barcode"]
        name = request.form["name"]
        quantity = int(request.form["quantity"])
        action = request.form["action"]

        cur.execute(
            "SELECT quantity FROM inventory WHERE barcode = ?",
            (barcode,)
        )
        row = cur.fetchone()

        if action == "add":
            if row:
                cur.execute(
                    "UPDATE inventory SET quantity = ? WHERE barcode = ?",
                    (row[0] + quantity, barcode)
                )
            else:
                cur.execute(
                    "INSERT INTO inventory (barcode, name, quantity) VALUES (?, ?, ?)",
                    (barcode, name, quantity)
                )

        elif action == "remove" and row:
            new_qty = row[0] - quantity
            if new_qty <= 0:
                cur.execute(
                    "DELETE FROM inventory WHERE barcode = ?",
                    (barcode,)
                )
            else:
                cur.execute(
                    "UPDATE inventory SET quantity = ? WHERE barcode = ?",
                    (new_qty, barcode)
                )

        conn.commit()
        conn.close()
        return redirect("/")

    cur.execute("SELECT * FROM inventory")
    items = cur.fetchall()
    conn.close()

    # Charts (safe)
    popularity_img = None
    stock_img = None
    if visualizations:
        try:
            popularity_img, stock_img = visualizations.generate_charts_base64()
        except Exception:
            pass

    return render_template(
        "index.html",
        items=items,
        popularity_img=popularity_img,
        stock_img=stock_img
    )

@app.route("/delete/<int:item_id>")
def delete(item_id):
    init_db()
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("DELETE FROM inventory WHERE id = ?", (item_id,))
    conn.commit()
    conn.close()
    return redirect("/")
