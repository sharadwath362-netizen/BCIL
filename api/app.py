from flask import Flask, render_template, request, jsonify
from datetime import datetime
import firebase_admin
from firebase_admin import credentials, firestore

app = Flask(
    __name__,
    template_folder="../templates",
    static_folder="../static"
)

# ---------------- FIREBASE INITIALIZATION ---------------- #
cred = credentials.Certificate("firebase_key.json")  # Path to your Firebase service account JSON
firebase_admin.initialize_app(cred)
db = firestore.client()

# ---------------- HOME PAGE ---------------- #
@app.route("/")
def index():
    items_ref = db.collection("inventory")
    docs = items_ref.order_by("updated_time", direction=firestore.Query.DESCENDING).stream()
    inventory = [doc.to_dict() for doc in docs]

    logs_ref = db.collection("logs")
    logs_docs = logs_ref.order_by("time", direction=firestore.Query.DESCENDING).stream()
    logs = [doc.to_dict() for doc in logs_docs]

    return render_template("index.html", inventory=inventory, logs=logs)

# ---------------- ADD ITEM ---------------- #
@app.route("/add", methods=["POST"])
def add_item():
    data = request.get_json()
    barcode = data.get("barcode")
    qty = int(data.get("quantity", 0))
    time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if not barcode or qty <= 0:
        return jsonify({"status": "error", "message": "Invalid input"}), 400

    item_ref = db.collection("inventory").document(barcode)
    item = item_ref.get()
    if item.exists:
        new_qty = item.to_dict().get("quantity", 0) + qty
        item_ref.update({"quantity": new_qty, "updated_time": time})
    else:
        item_ref.set({"barcode": barcode, "quantity": qty, "updated_time": time})

    # Add log
    db.collection("logs").add({"barcode": barcode, "action": "Added", "quantity": qty, "time": time})

    return jsonify({"status": "success"})

# ---------------- REMOVE ITEM ---------------- #
@app.route("/remove", methods=["POST"])
def remove_item():
    data = request.get_json()
    barcode = data.get("barcode")
    qty = int(data.get("quantity", 0))
    time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if not barcode or qty <= 0:
        return jsonify({"status": "error", "message": "Invalid input"}), 400

    item_ref = db.collection("inventory").document(barcode)
    item = item_ref.get()
    if not item.exists:
        return jsonify({"status": "error", "message": "Item not found"}), 404

    remaining = item.to_dict().get("quantity", 0) - qty
    if remaining > 0:
        item_ref.update({"quantity": remaining, "updated_time": time})
    else:
        item_ref.delete()

    # Add log
    db.collection("logs").add({"barcode": barcode, "action": "Removed", "quantity": qty, "time": time})

    return jsonify({"status": "success"})

# ---------------- RESET INVENTORY ---------------- #
@app.route("/reset", methods=["POST"])
def reset_inventory():
    # Delete all items
    items = db.collection("inventory").stream()
    for item in items:
        db.collection("inventory").document(item.id).delete()

    # Delete all logs
    logs = db.collection("logs").stream()
    for log in logs:
        db.collection("logs").document(log.id).delete()

    return jsonify({"status": "inventory_cleared"})

# ---------------- INVENTORY DATA FOR CHART.JS ---------------- #
@app.route("/inventory-data")
def inventory_data():
    items_ref = db.collection("inventory")
    docs = items_ref.stream()
    data = [{"item": doc.to_dict()["barcode"], "quantity": doc.to_dict()["quantity"]} for doc in docs]
    return jsonify(data)

# Required for Vercel
app = app

