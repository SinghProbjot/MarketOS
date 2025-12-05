import sqlite3
import json
import os
import sys
import logging
import platform
import threading
import time
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

# Modulo seriale opzionale (non crasha se manca, ma serve per la bilancia)
try:
    import serial
    SERIAL_AVAILABLE = True
except ImportError:
    SERIAL_AVAILABLE = False

# --- CONFIGURAZIONE PERCORSI CROSS-PLATFORM ---
system_os = platform.system()
base_dir = ''

if system_os == 'Windows':
    base_dir = os.getenv('APPDATA')
elif system_os == 'Darwin': 
    base_dir = os.path.expanduser('~/Library/Application Support')
else: 
    base_dir = os.path.expanduser('~/.local/share')

market_data_dir = os.path.join(base_dir, 'MarketOS')

if not os.path.exists(market_data_dir):
    try: os.makedirs(market_data_dir)
    except: market_data_dir = '.'

DB_FILE = os.path.join(market_data_dir, 'market.db')
LOG_FILE = os.path.join(market_data_dir, 'server_error.log')
CONFIG_FILE = os.path.join(market_data_dir, 'scale_config.json') # File config bilancia separato

logging.basicConfig(filename=LOG_FILE, level=logging.ERROR, format='%(asctime)s %(levelname)s: %(message)s')

if getattr(sys, 'frozen', False):
    template_folder = os.path.join(sys._MEIPASS)
    static_folder = os.path.join(sys._MEIPASS)
else:
    current_dir = os.path.dirname(os.path.abspath(__file__))
    template_folder = current_dir
    static_folder = current_dir

app = Flask(__name__, static_folder=static_folder, static_url_path='')
CORS(app)

# --- GESTIONE BILANCIA ---
class ScaleManager:
    def __init__(self):
        self.port = None
        self.baudrate = 9600
        self.load_config()

    def load_config(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r') as f:
                    data = json.load(f)
                    self.port = data.get('port')
                    self.baudrate = data.get('baudrate', 9600)
            except: pass

    def save_config(self, port, baudrate=9600):
        self.port = port
        self.baudrate = baudrate
        with open(CONFIG_FILE, 'w') as f:
            json.dump({'port': port, 'baudrate': baudrate}, f)

    def read_weight(self):
        if not SERIAL_AVAILABLE:
            return {"error": "Libreria pyserial non installata"}
        if not self.port:
            return {"error": "Porta COM non configurata"}
        
        try:
            # Tenta di aprire la connessione, leggere e chiudere (stateless)
            # Protocollo standard bilance (es. Dibal/Mettler): inviano stringhe continue tipo "W:  1.235kg"
            # Questo è un parser generico che cerca numeri float nella stringa
            with serial.Serial(self.port, self.baudrate, timeout=1) as ser:
                # Pulisci buffer
                ser.reset_input_buffer()
                # Leggi una riga
                line = ser.readline().decode('utf-8', errors='ignore').strip()
                
                if not line:
                    return {"error": "Nessun dato dalla bilancia"}

                # Cerca di estrarre un numero dalla stringa (rimuovi lettere tipo 'kg', 'N', ecc)
                import re
                match = re.search(r"(\d+\.\d+)", line)
                if match:
                    return {"weight": float(match.group(1)), "raw": line}
                
                # Fallback per numeri interi o formati diversi
                match_int = re.search(r"(\d+)", line)
                if match_int:
                    # Spesso le bilance mandano il peso in grammi se è intero
                    return {"weight": float(match_int.group(1)) / 1000, "raw": line}
                
                return {"error": f"Formato non riconosciuto: {line}"}

        except serial.SerialException as e:
            return {"error": f"Errore connessione: {str(e)}"}
        except Exception as e:
            return {"error": f"Errore generico: {str(e)}"}

scale_manager = ScaleManager()

# --- DB FUNCTIONS ---
def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS products (code TEXT PRIMARY KEY, name TEXT, price REAL, cost REAL, stock INTEGER, originalPrice REAL, isWeighable INTEGER DEFAULT 0, category TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS logs (id INTEGER PRIMARY KEY AUTOINCREMENT, date TEXT, type TEXT, total REAL, items_json TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS categories (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT UNIQUE)''')
    
    c.execute("SELECT count(*) FROM categories")
    if c.fetchone()[0] == 0:
        default_cats = ["Generale", "Frutta", "Verdura", "Panetteria", "Macelleria", "Scatolame", "Bevande"]
        c.executemany("INSERT OR IGNORE INTO categories (name) VALUES (?)", [(cat,) for cat in default_cats])

    conn.commit()
    conn.close()

# --- ROUTES ---
@app.route('/')
def serve_ui():
    return send_from_directory(static_folder, 'market_os.html')

# API BILANCIA
@app.route('/api/scale/read', methods=['GET'])
def get_scale_weight():
    return jsonify(scale_manager.read_weight())

@app.route('/api/scale/config', methods=['POST'])
def set_scale_config():
    data = request.json
    scale_manager.save_config(data.get('port'), data.get('baudrate', 9600))
    return jsonify({"success": True})

@app.route('/api/scale/config', methods=['GET'])
def get_scale_config():
    return jsonify({'port': scale_manager.port, 'baudrate': scale_manager.baudrate})

# API PRODOTTI & LOGS (Invariate)
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
    except Exception as e: return jsonify([]), 500

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
    except Exception as e: return jsonify({"error": str(e)}), 500

@app.route('/api/products/<code_id>', methods=['DELETE'])
def delete_product(code_id):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("DELETE FROM products WHERE code = ?", (code_id,))
    conn.commit()
    conn.close()
    return jsonify({"success": True})

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

@app.route('/api/logs', methods=['GET'])
def get_logs():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM logs ORDER BY date DESC LIMIT 5000")
    rows = c.fetchall()
    logs = []
    for row in rows:
        r = dict(row)
        if r['items_json']: r['items'] = json.loads(r['items_json'])
        logs.append(r)
    conn.close()
    return jsonify(logs)

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