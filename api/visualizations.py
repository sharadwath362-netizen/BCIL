import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os

# Path to SQLite database
DB_PATH = "/tmp/inventory.db"

# Path to store charts (matches your Flask static folder)
CHARTS_DIR = "../static/charts"

# Ensure charts folder exists
os.makedirs(CHARTS_DIR, exist_ok=True)

def generate_charts():
    # Fetch inventory data
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT name, quantity FROM inventory", conn)
    conn.close()

    if df.empty:
        return  # Nothing to plot

    items = df['name'].to_numpy()
    quantity = df['quantity'].to_numpy()

    # ---------------------------
    # 1️⃣ Item Popularity (Horizontal Bar)
    # ---------------------------
    sns.set_style("whitegrid")
    plt.figure(figsize=(10,6))
    colors = sns.color_palette("viridis", len(items))
    sns.barplot(x=quantity, y=items, palette=colors)
    plt.title("Item Popularity", fontsize=16, weight='bold')
    plt.xlabel("Quantity")
    for index, value in enumerate(quantity):
        plt.text(value + 0.5, index, str(value), va='center')
    plt.tight_layout()
    plt.savefig(f"{CHARTS_DIR}/item_popularity.png")
    plt.close()

    # ---------------------------
    # 2️⃣ Stock Levels (Gauge-style)
    # ---------------------------
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
    plt.tight_layout()
    plt.savefig(f"{CHARTS_DIR}/stock_levels.png")
    plt.close()
