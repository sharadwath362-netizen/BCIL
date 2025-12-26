from flask import Flask, render_template, request, redirect
import sqlite3
import os
import visualizations  # Import the visualizations file

app = Flask(
    __name__,
    template_folder="../templates",
    static_folder="../static"
)

DB_PATH = "/tmp/inventory.db"

# ------------------------------
# Database helper functions
# ------------------------------
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

# Initialize DB immediately
init_db()

# ------------------------------
# Routes
# ------------------------------
@app.route("/", methods=["GET", "POST"])
def index():
    conn = get_db()
    cur = conn.cursor()

    if request.method == "POST":
        barcode = request.form["barcode"]
        name = request.form["name"]
        quantity = int(request.form["quantity"])
        action = request.form["action"]  # "add" or "remove"

        # Check if the item already exists
        cur.execute("SELECT id, quantity FROM inventory WHERE barcode = ?", (barcode,))
        row = cur.fetchone()

        # ➕ Add stock
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

        # ➖ Remove stock
        elif action == "remove":
            if row:
                current_qty = row[1]
                if quantity >= current_qty:
                    # Remove completely if quantity is zero or below
                    cur.execute("DELETE FROM inventory WHERE barcode = ?", (barcode,))
                else:
                    new_qty = current_qty - quantity
                    cur.execute(
                        "UPDATE inventory SET quantity = ? WHERE barcode = ?",
                        (new_qty, barcode)
                    )
            # If item doesn't exist, do nothing

        conn.commit()
        conn.close()
        return redirect("/")

    # GET request: fetch all items for display
    cur.execute("SELECT * FROM inventory")
    items = cur.fetchall()
    conn.close()

    # Generate charts based on current inventory
    visualizations.generate_charts()

    return render_template("index.html", items=items)

@app.route("/delete/<int:item_id>")
def delete(item_id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("DELETE FROM inventory WHERE id = ?", (item_id,))
    conn.commit()
    conn.close()
    return redirect("/")

if __name__ == "__main__":
    app.run(debug=True)

