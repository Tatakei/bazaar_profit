import os
import sys
import requests
import time
from flask import Flask, render_template, request

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

app = Flask(__name__, 
            template_folder=resource_path("templates"),
            static_folder=resource_path("static"))

BAZAAR_API = "https://api.hypixel.net/v2/skyblock/bazaar"
ITEMS_API = "https://api.hypixel.net/v2/resources/skyblock/items"

cache = {"data": [], "last_updated": 0, "stats": {}}

def get_data():
    now = time.time()
    if cache["data"] and (now - cache["last_updated"] < 30):
        return cache["data"], cache["last_updated"], cache["stats"]

    try:
        bazaar_products = requests.get(BAZAAR_API, timeout=5).json().get("products", {})
        items_data = requests.get(ITEMS_API, timeout=5).json().get("items", [])
        npc_prices = {i["id"]: i.get("npc_sell_price", 0) for i in items_data}
        
        processed_items = []
        stats = {"1m+": 0, "500k-1m": 0, "250k-500k": 0, "100k-250k": 0, "50k-100k": 0, "0-50k": 0}

        for key, val in bazaar_products.items():
            quick = val.get("quick_status", {})
            npc_price = npc_prices.get(key, 0)
            if npc_price == 0 or (quick.get("buyOrders") == 0 and quick.get("sellOrders") == 0):
                continue

            profit = npc_price - quick.get("sellPrice", 0)
            if profit <= 5000: continue

            if profit >= 1_000_000: stats["1m+"] += 1
            elif profit >= 500_000: stats["500k-1m"] += 1
            elif profit >= 250_000: stats["250k-500k"] += 1
            elif profit >= 100_000: stats["100k-250k"] += 1
            elif profit >= 50_000: stats["50k-100k"] += 1
            else: stats["0-50k"] += 1

            processed_items.append({
                "id": key,
                "quick_summary": quick,
                "npc_price": npc_price,
                "profit": profit
            })
            
        cache.update({"data": processed_items, "last_updated": now, "stats": stats})
        return processed_items, now, stats
    except:
        return cache["data"], cache["last_updated"], cache["stats"]

@app.route("/")
def index():
    sort_order = request.args.get("sort", "desc")
    items, last_updated, stats = get_data()
    items.sort(key=lambda x: x["profit"], reverse=(sort_order == "desc"))
    return render_template("index.html", items=items, sort_order=sort_order, last_updated=last_updated, stats=stats)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8080)