import sqlite3
import json
import os
import sys
import logging
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

# CONFIGURAZIONE PERCORSI
app_data_dir = os.getenv('APPDATA')
market_data_dir = os.path.join(app_data_dir, 'MarketOS')
if not os.path.exists(market_data_dir):
    try: os.makedirs(market_data_dir)
    except: market_data_dir = '.'

DB_FILE = os.path.join(market_data_dir, 'market.db')
LOG_FILE = os.path.join(market_data_dir, 'server_error.log')

logging.basicConfig(filename=LOG_FILE, level=logging.ERROR, format='%(asctime)s %(levelname)s: %(message)s')

if getattr(sys, 'frozen', False):
    template_folder = os.path.join(sys._MEIPASS)
    static_folder = os.path.join(sys._MEIPASS)
else:
    base_dir = os.path.dirname(os.path.abspath(__file__))
    template_folder = base_dir
    static_folder = base_dir

try:
    app = Flask(__name__, static_folder=static_folder, static_url_path='')
    CORS(app)

    def init_db():
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        
        # Tabelle Prodotti e Log
        c.execute('''CREATE TABLE IF NOT EXISTS products (code TEXT PRIMARY KEY, name TEXT, price REAL, cost REAL, stock INTEGER, originalPrice REAL, isWeighable INTEGER DEFAULT 0, category TEXT)''')
        c.execute('''CREATE TABLE IF NOT EXISTS logs (id INTEGER PRIMARY KEY AUTOINCREMENT, date TEXT, type TEXT, total REAL, items_json TEXT)''')
        
        # Tabella Categorie
        c.execute('''CREATE TABLE IF NOT EXISTS categories (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT UNIQUE)''')

        # Popola Default se vuota
        c.execute("SELECT count(*) FROM categories")
        if c.fetchone()[0] == 0:
            default_cats = ["Generale", "Frutta", "Verdura", "Panetteria", "Macelleria", "Scatolame", "Bevande"]
            c.executemany("INSERT OR IGNORE INTO categories (name) VALUES (?)", [(cat,) for cat in default_cats])

        conn.commit()
        conn.close()

    @app.route('/')
    def serve_ui():
        return send_from_directory(static_folder, 'market_os.html')

    # --- API PRODOTTI ---
    @app.route('/api/products', methods=['GET'])
    def get_products():
        try:
            conn = sqlite3.connect(DB_FILE)
            conn.row_factory = sqlite3.Row
            c = conn.cursor()
            c.execute("SELECT * FROM products")
            rows = c.fetchall()
            products = []
            for row in rows:
                p = dict(row)
                p['isWeighable'] = bool(p['isWeighable'])
                if 'category' not in p or p['category'] is None: p['category'] = ""
                products.append(p)
            conn.close()
            return jsonify(products)
        except Exception as e:
            logging.error(f"DB Error: {e}")
            return jsonify([]), 500

    @app.route('/api/products', methods=['POST'])
    def upsert_product():
        try:
            data = request.json
            conn = sqlite3.connect(DB_FILE)
            c = conn.cursor()
            is_weighable = 1 if data.get('isWeighable') else 0
            category = data.get('category', "")
            c.execute('''INSERT INTO products (code, name, price, cost, stock, originalPrice, isWeighable, category) 
                         VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                         ON CONFLICT(code) DO UPDATE SET 
                         name=excluded.name, price=excluded.price, cost=excluded.cost, stock=excluded.stock, 
                         originalPrice=excluded.originalPrice, isWeighable=excluded.isWeighable, category=excluded.category''', 
                      (data['code'], data['name'], data['price'], data['cost'], data['stock'], data.get('originalPrice'), is_weighable, category))
            conn.commit()
            conn.close()
            return jsonify({"success": True})
        except Exception as e:
            logging.error(f"DB Error: {e}")
            return jsonify({"error": str(e)}), 500

    @app.route('/api/products/<code_id>', methods=['DELETE'])
    def delete_product(code_id):
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("DELETE FROM products WHERE code = ?", (code_id,))
        conn.commit()
        conn.close()
        return jsonify({"success": True})

    # --- API CATEGORIE ---
    @app.route('/api/categories', methods=['GET'])
    def get_categories():
        conn = sqlite3.connect(DB_FILE)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute("SELECT * FROM categories ORDER BY name")
        rows = c.fetchall()
        conn.close()
        return jsonify([dict(row) for row in rows])

    @app.route('/api/categories', methods=['POST'])
    def add_category():
        data = request.json
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        try:
            c.execute("INSERT INTO categories (name) VALUES (?)", (data['name'],))
            conn.commit()
            conn.close()
            return jsonify({"success": True})
        except sqlite3.IntegrityError:
            conn.close()
            return jsonify({"error": "Categoria esistente"}), 400

    @app.route('/api/categories/<cat_id>', methods=['DELETE'])
    def delete_category(cat_id):
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("DELETE FROM categories WHERE id = ?", (cat_id,))
        conn.commit()
        conn.close()
        return jsonify({"success": True})

    # --- API LOGS ---
    @app.route('/api/logs', methods=['POST'])
    def add_log():
        data = request.json
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("INSERT INTO logs (date, type, total, items_json) VALUES (?, ?, ?, ?)", (data['date'], data['type'], data['total'], json.dumps(data.get('items', []))))
        conn.commit()
        conn.close()
        return jsonify({"success": True})

    def start_server_thread():
        if not os.path.exists(market_data_dir): os.makedirs(market_data_dir)
        init_db()
        app.run(host='127.0.0.1', port=5500, debug=False, use_reloader=False)

    if __name__ == '__main__':
        start_server_thread()

except Exception as e:
    with open(os.path.join(os.getenv('TEMP'), 'MARKETOS_FATAL.txt'), "w") as f: f.write(str(e))