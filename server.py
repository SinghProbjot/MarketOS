import sqlite3
import json
import os
import sys
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

if getattr(sys, 'frozen', False):
    template_folder = os.path.join(sys._MEIPASS)
    static_folder = os.path.join(sys._MEIPASS)
else:
    template_folder = '.'
    static_folder = '.'

app = Flask(__name__, static_folder=static_folder, static_url_path='')
CORS(app)
DB_FILE = 'market.db'

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS products (code TEXT PRIMARY KEY, name TEXT NOT NULL, price REAL, cost REAL, stock INTEGER, originalPrice REAL, isWeighable INTEGER DEFAULT 0)''')
    c.execute('''CREATE TABLE IF NOT EXISTS logs (id INTEGER PRIMARY KEY AUTOINCREMENT, date TEXT, type TEXT, total REAL, items_json TEXT)''')
    conn.commit()
    conn.close()

@app.route('/')
def serve_ui():
    return send_from_directory('.', 'market_os.html')

@app.route('/api/products', methods=['GET'])
def get_products():
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

@app.route('/api/products', methods=['POST'])
def upsert_product():
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

@app.route('/api/products/<code_id>', methods=['DELETE'])
def delete_product(code_id):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("DELETE FROM products WHERE code = ?", (code_id,))
    conn.commit()
    conn.close()
    return jsonify({"success": True})

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
    init_db()
    app.run(host='127.0.0.1', port=5000, debug=False, use_reloader=False)

if __name__ == '__main__':
    start_server_thread()