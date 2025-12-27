import matplotlib
matplotlib.use('Agg')  # Serverless-safe backend

import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import io
import base64

DB_PATH = "/tmp/inventory.db"

def generate_charts_base64():
    """
    Returns two base64 strings for Item Popularity and Stock Levels charts.
    """
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT name, quantity FROM inventory", conn)
    conn.close()

    if df.empty:
        return None, None

    items = df['name'].to_numpy()
    quantity = df['quantity'].to_numpy()

    # -------- Item Popularity --------
    plt.figure(figsize=(10,6))
    sns.set_style("whitegrid")
    colors = sns.color_palette("viridis", len(items))
    sns.barplot(x=quantity, y=items, palette=colors)
    plt.title("Item Popularity", fontsize=16, weight='bold')
    plt.xlabel("Quantity")
    for idx, val in enumerate(quantity):
        plt.text(val + 0.5, idx, str(val), va='center')

    buf = io.BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight')
    buf.seek(0)
    popularity_img = base64.b64encode(buf.getvalue()).decode('utf-8')
    buf.close()
    plt.close()

    # -------- Stock Levels --------
    plt.figure(figsize=(10,6))
    max_qty = max(quantity) if len(quantity) > 0 else 1
    stock_percent = quantity / max_qty * 100
    colors = [plt.cm.RdYlGn(p/100) for p in stock_percent]
    bars = plt.barh(items, stock_percent, color=colors)
    plt.xlim(0, 120)
    plt.xlabel("Stock Level (%)")
    plt.title("Stock Levels", fontsize=16, weight='bold')
    for bar, q in zip(bars, quantity):
        plt.text(bar.get_width() + 1, bar.get_y() + bar.get_height()/2, str(q), va='center')

    buf = io.BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight')
    buf.seek(0)
    stock_img = base64.b64encode(buf.getvalue()).decode('utf-8')
    buf.close()
    plt.close()

    return popularity_img, stock_img
