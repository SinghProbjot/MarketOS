import sqlite3
import json
import os
import sys
import logging
import platform
import threading
import time
from datetime import datetime, timedelta
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

# ... (Configurazione percorsi e seriale invariata) ...
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

# ... (Classe ScaleManager invariata) ...
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
            with serial.Serial(self.port, self.baudrate, timeout=1) as ser:
                ser.reset_input_buffer()
                line = ser.readline().decode('utf-8', errors='ignore').strip()
                if not line: return {"error": "Nessun dato dalla bilancia"}
                import re
                match = re.search(r"(\d+\.\d+)", line)
                if match: return {"weight": float(match.group(1)), "raw": line}
                match_int = re.search(r"(\d+)", line)
                if match_int: return {"weight": float(match_int.group(1)) / 1000, "raw": line}
                return {"error": f"Formato non riconosciuto: {line}"}
        except serial.SerialException as e: return {"error": f"Errore connessione: {str(e)}"}
        except Exception as e: return {"error": f"Errore generico: {str(e)}"}

scale_manager = ScaleManager()

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    # Tabelle Esistenti
    c.execute('''CREATE TABLE IF NOT EXISTS products (code TEXT PRIMARY KEY, name TEXT, price REAL, cost REAL, stock INTEGER, originalPrice REAL, isWeighable INTEGER DEFAULT 0, category TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS logs (id INTEGER PRIMARY KEY AUTOINCREMENT, date TEXT, type TEXT, total REAL, items_json TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS categories (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT UNIQUE)''')
    
    # NUOVA TABELLA: BATCHES (Lotti con scadenza)
    # entry_date serve per il FIFO se non c'è expiry_date
    c.execute('''CREATE TABLE IF NOT EXISTS batches (
        id INTEGER PRIMARY KEY AUTOINCREMENT, 
        product_code TEXT, 
        quantity REAL, 
        expiry_date TEXT, 
        entry_date TEXT,
        FOREIGN KEY(product_code) REFERENCES products(code)
    )''')

    # Popola categorie default
    c.execute("SELECT count(*) FROM categories")
    if c.fetchone()[0] == 0:
        default_cats = ["Generale", "Frutta", "Verdura", "Panetteria", "Macelleria", "Scatolame", "Bevande"]
        c.executemany("INSERT OR IGNORE INTO categories (name) VALUES (?)", [(cat,) for cat in default_cats])

    conn.commit()
    conn.close()

# --- HELPER FIFO ---
def consume_stock_fifo(cursor, code, quantity_sold):
    """Scala la quantità dai lotti più vecchi (che scadono prima)"""
    # Seleziona lotti con quantità > 0, ordinati per scadenza (i vuoti/nulli per ultimi) poi per data inserimento
    cursor.execute("""
        SELECT id, quantity, expiry_date 
        FROM batches 
        WHERE product_code = ? AND quantity > 0 
        ORDER BY 
            CASE WHEN expiry_date IS NULL OR expiry_date = '' THEN 1 ELSE 0 END, 
            expiry_date ASC, 
            entry_date ASC
    """, (code,))
    
    batches = cursor.fetchall()
    remaining_to_sell = quantity_sold

    for batch in batches:
        b_id, b_qty, b_exp = batch
        
        if remaining_to_sell <= 0:
            break
            
        if b_qty >= remaining_to_sell:
            # Questo lotto copre tutta la vendita
            cursor.execute("UPDATE batches SET quantity = quantity - ? WHERE id = ?", (remaining_to_sell, b_id))
            remaining_to_sell = 0
        else:
            # Questo lotto non basta, lo svuotiamo e passiamo al prossimo
            cursor.execute("UPDATE batches SET quantity = 0 WHERE id = ?", (b_id,))
            remaining_to_sell -= b_qty
    
    # Aggiorna anche lo stock totale nella tabella products per velocità di lettura
    cursor.execute("UPDATE products SET stock = stock - ? WHERE code = ?", (quantity_sold, code))

# --- API ROUTES ---
@app.route('/')
def serve_ui():
    return send_from_directory(static_folder, 'market_os.html')

# API BILANCIA (Invariate)
@app.route('/api/scale/read', methods=['GET'])
def get_scale_weight(): return jsonify(scale_manager.read_weight())
@app.route('/api/scale/config', methods=['POST'])
def set_scale_config():
    data = request.json
    scale_manager.save_config(data.get('port'), data.get('baudrate', 9600))
    return jsonify({"success": True})
@app.route('/api/scale/config', methods=['GET'])
def get_scale_config(): return jsonify({'port': scale_manager.port, 'baudrate': scale_manager.baudrate})

# API PRODOTTI
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
        # Aggiungiamo informazione sulla scadenza più prossima per la visualizzazione
        c.execute("SELECT min(expiry_date) FROM batches WHERE product_code = ? AND quantity > 0 AND expiry_date != ''", (p['code'],))
        next_expiry = c.fetchone()[0]
        p['nextExpiry'] = next_expiry
        products.append(p)
    conn.close()
    return jsonify(products)

@app.route('/api/products', methods=['POST'])
def upsert_product():
    try:
        data = request.json
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        
        is_weighable = 1 if data.get('isWeighable') else 0
        category = data.get('category', "")
        
        # 1. Aggiorna o Crea il Prodotto (Anagrafica)
        c.execute('''INSERT INTO products (code, name, price, cost, stock, originalPrice, isWeighable, category) 
                     VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                     ON CONFLICT(code) DO UPDATE SET 
                     name=excluded.name, price=excluded.price, cost=excluded.cost, 
                     originalPrice=excluded.originalPrice, isWeighable=excluded.isWeighable, category=excluded.category''', 
                  (data['code'], data['name'], data['price'], data['cost'], 0, data.get('originalPrice'), is_weighable, category))
        
        # 2. Gestione Stock: Se è un nuovo carico (addStock > 0), crea un lotto
        # Se stiamo solo modificando il prezzo, non tocchiamo i lotti
        added_stock = float(data.get('addedStock', 0)) # Nuova quantità da aggiungere
        expiry_date = data.get('expiryDate', "")      # Data scadenza di questo carico

        if added_stock > 0:
            entry_date = datetime.now().strftime("%Y-%m-%d")
            c.execute("INSERT INTO batches (product_code, quantity, expiry_date, entry_date) VALUES (?, ?, ?, ?)",
                      (data['code'], added_stock, expiry_date, entry_date))
        
        # 3. Ricalcola stock totale dai lotti per coerenza
        c.execute("SELECT sum(quantity) FROM batches WHERE product_code = ?", (data['code'],))
        total_stock = c.fetchone()[0] or 0
        
        # Se l'utente ha forzato un valore stock manuale (es. inventario), 
        # e non combacia con la somma dei lotti, creiamo un lotto di "aggiustamento" o resettiamo
        if 'forceStock' in data and data['forceStock']:
             # Caso semplificato: Resetta tutto e crea un unico lotto (Inventario Rapido)
             forced_qty = float(data['stock'])
             c.execute("DELETE FROM batches WHERE product_code = ?", (data['code'],))
             c.execute("INSERT INTO batches (product_code, quantity, expiry_date, entry_date) VALUES (?, ?, ?, ?)",
                      (data['code'], forced_qty, "", datetime.now().strftime("%Y-%m-%d")))
             total_stock = forced_qty

        c.execute("UPDATE products SET stock = ? WHERE code = ?", (total_stock, data['code']))

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
    c.execute("DELETE FROM batches WHERE product_code = ?", (code_id,)) # Cancella anche i lotti
    c.execute("DELETE FROM products WHERE code = ?", (code_id,))
    conn.commit()
    conn.close()
    return jsonify({"success": True})

# --- API REPORT SCADENZE ---
@app.route('/api/expiry-report', methods=['GET'])
def get_expiry_report():
    months = int(request.args.get('months', 1)) # Default 1 mese avanti
    target_date = (datetime.now() + timedelta(days=30 * months)).strftime("%Y-%m-%d")
    today = datetime.now().strftime("%Y-%m-%d")

    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    # Trova lotti che scadono entro target_date e hanno quantità > 0
    # Unisce con nome prodotto
    c.execute("""
        SELECT p.name, p.code, b.quantity, b.expiry_date 
        FROM batches b
        JOIN products p ON b.product_code = p.code
        WHERE b.quantity > 0 
          AND b.expiry_date != '' 
          AND b.expiry_date <= ?
        ORDER BY b.expiry_date ASC
    """, (target_date,))
    
    rows = c.fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])

@app.route('/api/logs', methods=['GET', 'POST'])
def handle_logs():
    conn = sqlite3.connect(DB_FILE)
    if request.method == 'GET':
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute("SELECT * FROM logs ORDER BY date DESC LIMIT 5000")
        rows = c.fetchall()
        logs = [dict(r) for r in rows]
        for l in logs:
            if l['items_json']: l['items'] = json.loads(l['items_json'])
        conn.close()
        return jsonify(logs)
    else:
        # POST: Nuova vendita
        data = request.json
        c = conn.cursor()
        try:
            # Registra Log
            c.execute("INSERT INTO logs (date, type, total, items_json) VALUES (?, ?, ?, ?)", 
                     (data['date'], data['type'], data['total'], json.dumps(data.get('items', []))))
            
            # Scala Stock FIFO
            for item in data.get('items', []):
                consume_stock_fifo(c, item['code'], item['qty'])
            
            conn.commit()
            conn.close()
            return jsonify({"success": True})
        except Exception as e:
            return jsonify({"error": str(e)}), 500

# API Categorie (Invariate)
@app.route('/api/categories', methods=['GET', 'POST'])
def handle_categories():
    conn = sqlite3.connect(DB_FILE)
    if request.method == 'GET':
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute("SELECT * FROM categories ORDER BY name")
        rows = [dict(r) for r in c.fetchall()]
        conn.close()
        return jsonify(rows)
    else:
        data = request.json
        c = conn.cursor()
        try:
            c.execute("INSERT INTO categories (name) VALUES (?)", (data['name'],))
            conn.commit()
            conn.close()
            return jsonify({"success": True})
        except: return jsonify({"error": "Esistente"}), 400

@app.route('/api/categories/<id>', methods=['DELETE'])
def del_category(id):
    conn = sqlite3.connect(DB_FILE)
    conn.execute("DELETE FROM categories WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    return jsonify({"success": True})

def start_server_thread():
    if not os.path.exists(market_data_dir): os.makedirs(market_data_dir)
    init_db()
    app.run(host='127.0.0.1', port=5500, debug=False, use_reloader=False)

if __name__ == '__main__':
    start_server_thread()