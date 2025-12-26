from flask import Flask, render_template, request, redirect
import sqlite3

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
            name TEXT,
            quantity INTEGER
        )
    """)
    conn.commit()
    conn.close()

# Init DB immediately (Vercel-safe)
init_db()

@app.route("/", methods=["GET", "POST"])
def index():
    conn = get_db()
    cur = conn.cursor()

    if request.method == "POST":
        barcode = request.form["barcode"]
        name = request.form["name"]
        quantity = int(request.form["quantity"])
        action = request.form["action"]  # add / remove

        cur.execute("SELECT id, quantity FROM inventory WHERE barcode = ?", (barcode,))
        row = cur.fetchone()

        # ➕ ADD LOGIC
        if action == "add":
            if row:
                new_qty = row[1] + quantity
                cur.execute(
                    "UPDATE inventory SET quantity = ? WHERE barcode = ?",
                    (new_qty, barcode)
                )
            else:
                cur.execute(
                    "INSERT INTO inventory (barcode, name, quantity) VALUES (?, ?, ?)",
                    (barcode, name, quantity)
                )

        # ➖ REMOVE LOGIC
        elif action == "remove":
            if not row:
                # Barcode not found → do nothing
                conn.close()
                return redirect("/")

            current_qty = row[1]

            if quantity >= current_qty:
                # Remove completely if quantity reaches 0 or below
                cur.execute(
                    "DELETE FROM inventory WHERE barcode = ?",
                    (barcode,)
                )
            else:
                # Reduce quantity
                new_qty = current_qty - quantity
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

    return render_template("index.html", items=items)

@app.route("/delete/<int:item_id>")
def delete(item_id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("DELETE FROM inventory WHERE id = ?", (item_id,))
    conn.commit()
    conn.close()
    return redirect("/")
