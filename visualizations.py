import matplotlib
matplotlib.use("Agg")  # MUST be first

import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
import io
import base64

DB_PATH = "/tmp/inventory.db"

def generate_charts_base64():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT name, quantity FROM inventory", conn)
    conn.close()

    if df.empty:
        return None, None

    items = df["name"].to_numpy()
    quantity = df["quantity"].to_numpy()

    # -------- Item Popularity --------
    plt.figure(figsize=(8, 4))
    plt.barh(items, quantity)
    plt.xlabel("Quantity")
    plt.title("Item Popularity")

    buf = io.BytesIO()
    plt.savefig(buf, format="png", bbox_inches="tight")
    buf.seek(0)
    popularity_img = base64.b64encode(buf.read()).decode()
    plt.close()

    # -------- Stock Levels --------
    plt.figure(figsize=(8, 4))
    max_qty = max(quantity)
    percent = (quantity / max_qty) * 100
    plt.barh(items, percent)
    plt.xlabel("Stock %")
    plt.title("Stock Levels")

    buf = io.BytesIO()
    plt.savefig(buf, format="png", bbox_inches="tight")
    buf.seek(0)
    stock_img = base64.b64encode(buf.read()).decode()
    plt.close()

    return popularity_img, stock_img
