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

# Initialize DB immediately (important for Vercel)
init_db()

@app.route("/", methods=["GET", "POST"])
def index():
    conn = get_db()
    cur = conn.cursor()

    if request.method == "POST":
        barcode = request.form["barcode"]
        name = request.form["name"]
        quantity = int(request.form["quantity"])

        # 🔥 SAFE UPSERT LOGIC
        cur.execute("SELECT quantity FROM inventory WHERE barcode = ?", (barcode,))
        row = cur.fetchone()

        if row:
            new_qty = row[0] + quantity
            cur.execute(
                "UPDATE inventory SET quantity = ? WHERE barcode = ?",
                (new_qty, barcode)
            )
        else:
            cur.execute(
                "INSERT INTO inventory (barcode, name, quantity) VALUES (?, ?, ?)",
                (barcode, name, quantity)
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

