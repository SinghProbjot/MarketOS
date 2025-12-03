import sqlite3
import json
import os
import sys
import logging
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

# --- CONFIGURAZIONE PERCORSI WINDOWS ---
# Usiamo Roaming per i dati (standard Windows per i DB)
app_data_dir = os.getenv('APPDATA') # Solitamente C:\Users\Nome\AppData\Roaming
market_data_dir = os.path.join(app_data_dir, 'MarketOS')

# Assicura che la cartella esista
if not os.path.exists(market_data_dir):
    try:
        os.makedirs(market_data_dir)
    except OSError as e:
        # Fallback critico
        market_data_dir = '.'

DB_FILE = os.path.join(market_data_dir, 'market.db')
LOG_FILE = os.path.join(market_data_dir, 'server_error.log')

# Scrive un file di testo nella cartella del programma per dirti dove sta il DB
try:
    with open("DOVE_SONO_I_DATI.txt", "w") as f:
        f.write(f"Il database si trova qui:\n{DB_FILE}")
except: pass

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
        c.execute('''CREATE TABLE IF NOT EXISTS products (code TEXT PRIMARY KEY, name TEXT, price REAL, cost REAL, stock INTEGER, originalPrice REAL, isWeighable INTEGER DEFAULT 0)''')
        c.execute('''CREATE TABLE IF NOT EXISTS logs (id INTEGER PRIMARY KEY AUTOINCREMENT, date TEXT, type TEXT, total REAL, items_json TEXT)''')
        conn.commit()
        conn.close()

    @app.route('/')
    def serve_ui():
        return send_from_directory(static_folder, 'market_os.html')

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
                products.append(p)
            conn.close()
            return jsonify(products)
        except Exception as e:
            logging.error(f"DB Error: {e}")
            return jsonify({"error": str(e)}), 500

    @app.route('/api/products', methods=['POST'])
    def upsert_product():
        try:
            data = request.json
            conn = sqlite3.connect(DB_FILE)
            c = conn.cursor()
            is_weighable = 1 if data.get('isWeighable') else 0
            c.execute('''INSERT INTO products (code, name, price, cost, stock, originalPrice, isWeighable) VALUES (?, ?, ?, ?, ?, ?, ?)
                         ON CONFLICT(code) DO UPDATE SET name=excluded.name, price=excluded.price, cost=excluded.cost, stock=excluded.stock, originalPrice=excluded.originalPrice, isWeighable=excluded.isWeighable''', 
                      (data['code'], data['name'], data['price'], data['cost'], data['stock'], data.get('originalPrice'), is_weighable))
            conn.commit()
            conn.close()
            return jsonify({"success": True})
        except Exception as e:
            logging.error(f"DB Error: {e}")
            return jsonify({"error": str(e)}), 500

    @app.route('/api/products/<code_id>', methods=['DELETE'])
    def delete_product(code_id):
        try:
            conn = sqlite3.connect(DB_FILE)
            c = conn.cursor()
            c.execute("DELETE FROM products WHERE code = ?", (code_id,))
            conn.commit()
            conn.close()
            return jsonify({"success": True})
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route('/api/logs', methods=['POST'])
    def add_log():
        try:
            data = request.json
            conn = sqlite3.connect(DB_FILE)
            c = conn.cursor()
            c.execute("INSERT INTO logs (date, type, total, items_json) VALUES (?, ?, ?, ?)", (data['date'], data['type'], data['total'], json.dumps(data.get('items', []))))
            conn.commit()
            conn.close()
            return jsonify({"success": True})
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    def start_server_thread():
        if not os.path.exists(market_data_dir): os.makedirs(market_data_dir)
        init_db()
        app.run(host='127.0.0.1', port=5500, debug=False, use_reloader=False)

    if __name__ == '__main__':
        start_server_thread()

except Exception as e:
    with open("FATAL_ERROR.txt", "w") as f: f.write(str(e))