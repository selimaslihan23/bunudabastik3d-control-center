from __future__ import annotations
import json
import shutil
import sqlite3
from pathlib import Path
from datetime import datetime

APP_DIR = Path.home() / '.bunudabastik3d_ecosystem'
APP_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = APP_DIR / 'controlcenter.sqlite3'
BACKUP_DIR = APP_DIR / 'backups'
BACKUP_DIR.mkdir(parents=True, exist_ok=True)

DEFAULT_SETTINGS = {
    'company_name': 'BunuDaBastık3D',
    'printer_model': 'Bambu Lab X2D',
    'operator_name': 'Selim',
    'ui_theme': 'Nebula Mor',
    'background_effect': 'Aurora Pulse',
    'button_style': 'Glow Neon',
    'animation_level': 'Hafif',
    'currency': 'TL',
    'accent_color': '#A855F7',
    'accent_dark': '#241038',
    'window_bg': '#0B0B13',
    'card_bg': '#171423',
    'bridge_url': 'http://127.0.0.1:8787',
    'webhook_secret': '',
    'odoo_url': 'https://bunudabastik3d.odoo.com',
    'odoo_db': '',
    'odoo_username': '',
    'odoo_api_key': '',
    'imap_host': 'imap.gmail.com',
    'imap_port': '993',
    'imap_username': '',
    'imap_password': '',
    'imap_mailbox': 'INBOX',
    'imap_fetch_limit': '25',
    'gmail_oauth_query': 'in:inbox',
    'gmail_oauth_limit': '25',
    'gmail_oauth_configured': '0',
    'pla_cost_kg': '650',
    'petg_cost_kg': '750',
    'abs_cost_kg': '850',
    'asa_cost_kg': '950',
    'tpu_cost_kg': '1100',
    'support_cost_kg': '1400',
    'machine_hour_rate': '70',
    'labor_fee': '60',
    'design_hour_rate': '350',
    'post_process_fee': '40',
    'packaging_fee': '25',
    'failure_rate': '0.12',
    'profit_rate': '0.70',
    'vat_rate': '0.20',
    'commission_rate': '0.00',
    'minimum_price': '250',
}

SCHEMA = [
"""CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT NOT NULL)""",
"""CREATE TABLE IF NOT EXISTS inbox_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source TEXT DEFAULT 'Manual', channel_id TEXT DEFAULT '', external_id TEXT DEFAULT '',
    customer_name TEXT DEFAULT '', phone TEXT DEFAULT '', email TEXT DEFAULT '', instagram TEXT DEFAULT '',
    subject TEXT DEFAULT '', message TEXT DEFAULT '', attachment_urls TEXT DEFAULT '', makerworld_link TEXT DEFAULT '',
    requested_material TEXT DEFAULT 'PLA', requested_color TEXT DEFAULT '', quantity INTEGER DEFAULT 1,
    grams REAL DEFAULT 0, support_grams REAL DEFAULT 0, time_min REAL DEFAULT 0,
    priority TEXT DEFAULT 'Normal', status TEXT DEFAULT 'Yeni', assigned_to TEXT DEFAULT '',
    quote_id INTEGER DEFAULT 0, order_id INTEGER DEFAULT 0, raw_json TEXT DEFAULT '',
    created_at TEXT NOT NULL, updated_at TEXT NOT NULL
)""",
"""CREATE TABLE IF NOT EXISTS email_messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    imap_uid TEXT DEFAULT '', from_addr TEXT DEFAULT '', to_addr TEXT DEFAULT '',
    subject TEXT DEFAULT '', body TEXT DEFAULT '', date_text TEXT DEFAULT '', has_attachments INTEGER DEFAULT 0,
    status TEXT DEFAULT 'Yeni', inbox_id INTEGER DEFAULT 0,
    created_at TEXT NOT NULL, updated_at TEXT NOT NULL
)""",
"""CREATE TABLE IF NOT EXISTS quotes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    inbox_id INTEGER DEFAULT 0, customer_name TEXT DEFAULT '', phone TEXT DEFAULT '', email TEXT DEFAULT '',
    title TEXT DEFAULT '', source TEXT DEFAULT '', material TEXT DEFAULT 'PLA', color TEXT DEFAULT '',
    grams REAL DEFAULT 0, support_grams REAL DEFAULT 0, time_min REAL DEFAULT 0, quantity INTEGER DEFAULT 1,
    design_minutes REAL DEFAULT 0, cost_estimate REAL DEFAULT 0, price REAL DEFAULT 0, margin_amount REAL DEFAULT 0,
    status TEXT DEFAULT 'Ön Teklif', valid_until TEXT DEFAULT '', notes TEXT DEFAULT '',
    odoo_id TEXT DEFAULT '', created_at TEXT NOT NULL, updated_at TEXT NOT NULL
)""",
"""CREATE TABLE IF NOT EXISTS catalog (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    makerworld_link TEXT DEFAULT '', model_id TEXT DEFAULT '', sku TEXT DEFAULT '', title TEXT DEFAULT '', category TEXT DEFAULT 'MakerWorld',
    material TEXT DEFAULT 'PLA', color TEXT DEFAULT '', grams REAL DEFAULT 0, support_grams REAL DEFAULT 0, time_min REAL DEFAULT 0,
    grams_basis TEXT DEFAULT 'Toplam', time_basis TEXT DEFAULT 'Toplam',
    quantity INTEGER DEFAULT 1, estimated_price REAL DEFAULT 0, cost_estimate REAL DEFAULT 0, margin_amount REAL DEFAULT 0,
    status TEXT DEFAULT 'Aktif', odoo_product_id TEXT DEFAULT '', notes TEXT DEFAULT '', created_at TEXT NOT NULL, updated_at TEXT NOT NULL
)""",
"""CREATE TABLE IF NOT EXISTS customers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL, phone TEXT DEFAULT '', email TEXT DEFAULT '', instagram TEXT DEFAULT '', source TEXT DEFAULT '', notes TEXT DEFAULT '',
    created_at TEXT NOT NULL, updated_at TEXT NOT NULL
)""",
"""CREATE TABLE IF NOT EXISTS orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    quote_id INTEGER DEFAULT 0, customer_name TEXT DEFAULT '', phone TEXT DEFAULT '', email TEXT DEFAULT '', source TEXT DEFAULT '',
    item_name TEXT DEFAULT '', makerworld_link TEXT DEFAULT '', material TEXT DEFAULT 'PLA', grams REAL DEFAULT 0, support_grams REAL DEFAULT 0,
    time_min REAL DEFAULT 0, quantity INTEGER DEFAULT 1, price REAL DEFAULT 0, cost_estimate REAL DEFAULT 0,
    status TEXT DEFAULT 'Yeni Talep', payment_status TEXT DEFAULT 'Bekliyor', due_date TEXT DEFAULT '', odoo_lead_id TEXT DEFAULT '', notes TEXT DEFAULT '',
    created_at TEXT NOT NULL, updated_at TEXT NOT NULL
)""",
"""CREATE TABLE IF NOT EXISTS production_jobs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id INTEGER DEFAULT 0, job_name TEXT DEFAULT '', printer TEXT DEFAULT 'Bambu Lab X2D', material TEXT DEFAULT 'PLA',
    grams REAL DEFAULT 0, support_grams REAL DEFAULT 0, time_min REAL DEFAULT 0, status TEXT DEFAULT 'Baskıya Hazır', priority TEXT DEFAULT 'Normal',
    started_at TEXT DEFAULT '', completed_at TEXT DEFAULT '', notes TEXT DEFAULT '', created_at TEXT NOT NULL, updated_at TEXT NOT NULL
)""",
"""CREATE TABLE IF NOT EXISTS inventory (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    item TEXT NOT NULL, category TEXT DEFAULT 'Filament', material TEXT DEFAULT '', color TEXT DEFAULT '', unit TEXT DEFAULT 'g',
    current_qty REAL DEFAULT 0, min_qty REAL DEFAULT 0, unit_cost REAL DEFAULT 0, supplier TEXT DEFAULT '', notes TEXT DEFAULT '',
    created_at TEXT NOT NULL, updated_at TEXT NOT NULL
)""",
"""CREATE TABLE IF NOT EXISTS message_templates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL, channel TEXT DEFAULT 'WhatsApp', body TEXT NOT NULL, created_at TEXT NOT NULL, updated_at TEXT NOT NULL
)""",
"""CREATE TABLE IF NOT EXISTS sync_queue (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    entity_type TEXT NOT NULL, entity_id INTEGER NOT NULL, target TEXT DEFAULT 'Odoo', action TEXT DEFAULT 'upsert',
    status TEXT DEFAULT 'Bekliyor', last_error TEXT DEFAULT '', created_at TEXT NOT NULL, updated_at TEXT NOT NULL
)""",
"""CREATE TABLE IF NOT EXISTS cost_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    setting_key TEXT UNIQUE DEFAULT '', name TEXT NOT NULL, group_name TEXT DEFAULT 'Genel', unit TEXT DEFAULT 'TL',
    value REAL DEFAULT 0, active INTEGER DEFAULT 1, notes TEXT DEFAULT '', created_at TEXT NOT NULL, updated_at TEXT NOT NULL
)""",
"""CREATE TABLE IF NOT EXISTS app_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    level TEXT DEFAULT 'INFO', title TEXT NOT NULL, detail TEXT DEFAULT '', created_at TEXT NOT NULL, updated_at TEXT NOT NULL
)""",
]

DEFAULT_TEMPLATES = [
    ('Talep alındı', 'WhatsApp', 'Merhaba {customer_name}, BunuDaBastık3D’ye ulaştığınız için teşekkürler. Talebiniz kontrol panelimize düştü; model/dosya bilgilerini inceleyip ön teklif paylaşacağız.'),
    ('Ön teklif hazır', 'WhatsApp', 'Merhaba {customer_name}, {title} için ön teklifimiz {price} TL. Malzeme: {material}. Tahmini baskı süresi: {time_min} dk. Onayınızla üretime alabiliriz.'),
    ('Eksik bilgi', 'WhatsApp', 'Merhaba {customer_name}, net fiyat verebilmemiz için model dosyası, ölçü veya kullanım amacı bilgisini paylaşabilir misiniz?'),
    ('Baskı başladı', 'WhatsApp', 'Merhaba {customer_name}, {title} siparişiniz baskıya alındı. Tamamlandığında görsel ve teslimat bilgisini paylaşacağız.'),
    ('Teslime hazır', 'WhatsApp', 'Merhaba {customer_name}, {title} siparişiniz hazır. Teslim/kargo detaylarını netleştirebiliriz.'),
    ('E-posta cevap taslağı', 'Email', 'Merhaba {customer_name},\n\nBunuDaBastık3D’ye ulaştığınız için teşekkür ederiz. Talebinizi aldık ve teknik incelemeye ekledik. Dosya, ölçü ve malzeme bilgileri netleştiğinde fiyat/süre bilgisini paylaşacağız.\n\nSaygılarımızla,\nBunuDaBastık3D'),
]

DEFAULT_INVENTORY = [
    ('PLA Siyah', 'Filament', 'PLA', 'Siyah', 'g', 1000, 200, 0.65, '', 'Başlangıç stoğu'),
    ('PLA Beyaz', 'Filament', 'PLA', 'Beyaz', 'g', 1000, 200, 0.65, '', 'Başlangıç stoğu'),
    ('PETG Siyah', 'Filament', 'PETG', 'Siyah', 'g', 1000, 200, 0.75, '', 'Başlangıç stoğu'),
    ('TPU 95A Siyah', 'Filament', 'TPU', 'Siyah', 'g', 500, 150, 1.10, '', 'Esnek parça'),
    ('Support Filament', 'Filament', 'SUPPORT', 'Natural', 'g', 500, 100, 1.40, '', 'Destek malzemesi'),
    ('Kargo Kutusu', 'Paketleme', '', '', 'adet', 30, 8, 12, '', 'Paketleme'),
]

DEFAULT_COST_ITEMS = [
    ('pla_cost_kg', 'PLA filament kg maliyeti', 'Malzeme', 'TL/kg', 650, 'Fiyatlama motorunda PLA için kullanılır.'),
    ('petg_cost_kg', 'PETG filament kg maliyeti', 'Malzeme', 'TL/kg', 750, 'Fiyatlama motorunda PETG için kullanılır.'),
    ('abs_cost_kg', 'ABS filament kg maliyeti', 'Malzeme', 'TL/kg', 850, 'Fiyatlama motorunda ABS için kullanılır.'),
    ('asa_cost_kg', 'ASA filament kg maliyeti', 'Malzeme', 'TL/kg', 950, 'Fiyatlama motorunda ASA için kullanılır.'),
    ('tpu_cost_kg', 'TPU filament kg maliyeti', 'Malzeme', 'TL/kg', 1100, 'Fiyatlama motorunda TPU için kullanılır.'),
    ('support_cost_kg', 'Support filament kg maliyeti', 'Malzeme', 'TL/kg', 1400, 'Destek malzemesi hesabında kullanılır.'),
    ('machine_hour_rate', 'Makine saat ücreti', 'Operasyon', 'TL/saat', 70, 'Baskı süresine göre makine payı.'),
    ('labor_fee', 'Standart işçilik', 'Operasyon', 'TL/iş', 60, 'Her baskıya eklenen temel işçilik.'),
    ('design_hour_rate', 'Modelleme saat ücreti', 'Tasarım', 'TL/saat', 350, 'Modelleme/düzeltme işlerinde kullanılır.'),
    ('post_process_fee', 'Son işlem ücreti', 'Operasyon', 'TL/iş', 40, 'Destek temizleme/zımpara/minik rötuş.'),
    ('packaging_fee', 'Paketleme ücreti', 'Operasyon', 'TL/iş', 25, 'Kutu/poşet/etiket payı.'),
    ('failure_rate', 'Fire oranı', 'Risk', 'oran', 0.12, 'Başarısız baskı risk payı. Örn 0.12 = %12.'),
    ('profit_rate', 'Kâr oranı', 'Kâr', 'oran', 0.70, 'Maliyet üstüne kâr. Örn 0.70 = %70.'),
    ('vat_rate', 'KDV oranı', 'Vergi', 'oran', 0.20, 'KDV hesabı. Örn 0.20 = %20.'),
    ('commission_rate', 'Komisyon oranı', 'Komisyon', 'oran', 0.00, 'Pazar yeri/ödeme komisyonu.'),
    ('minimum_price', 'Minimum sipariş fiyatı', 'Satış', 'TL', 250, 'Bunun altına teklif düşmez.'),
]


# Global kayıt/sıralama merkezi için yönetilebilir tablolar.
SORTABLE_TABLES = [
    'inbox_items', 'email_messages', 'quotes', 'catalog', 'orders',
    'production_jobs', 'inventory', 'customers', 'message_templates',
    'sync_queue', 'cost_items'
]

RELATED_ID_REFERENCES = {
    'inbox_items': [('quotes', 'inbox_id'), ('email_messages', 'inbox_id')],
    'quotes': [('orders', 'quote_id')],
    'orders': [('production_jobs', 'order_id')],
}



def now():
    return datetime.now().strftime('%Y-%m-%d %H:%M:%S')


def connect(path: str | Path | None = None):
    conn = sqlite3.connect(str(path or DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def _columns(conn, table):
    return {r[1] for r in conn.execute(f'PRAGMA table_info({table})').fetchall()}


def _ensure_columns(conn):
    """Eski MVP / PRO veritabanlarını yeni FINAL_STABLE_CRUD şemasına taşır.
    Önceki sürümlerde tablo varsa CREATE TABLE eksik kolon eklemez; bu yüzden
    burada bütün günlük kullanım kolonlarını güvenli şekilde ekliyoruz.
    """
    migrations = {
        'inbox_items': {
            'source':'TEXT DEFAULT "Manual"', 'channel_id':'TEXT DEFAULT ""', 'external_id':'TEXT DEFAULT ""',
            'customer_name':'TEXT DEFAULT ""', 'phone':'TEXT DEFAULT ""', 'email':'TEXT DEFAULT ""', 'instagram':'TEXT DEFAULT ""',
            'subject':'TEXT DEFAULT ""', 'message':'TEXT DEFAULT ""', 'attachment_urls':'TEXT DEFAULT ""', 'makerworld_link':'TEXT DEFAULT ""',
            'requested_material':'TEXT DEFAULT "PLA"', 'requested_color':'TEXT DEFAULT ""', 'quantity':'INTEGER DEFAULT 1',
            'grams':'REAL DEFAULT 0', 'support_grams':'REAL DEFAULT 0', 'time_min':'REAL DEFAULT 0',
            'priority':'TEXT DEFAULT "Normal"', 'status':'TEXT DEFAULT "Yeni"', 'assigned_to':'TEXT DEFAULT ""',
            'quote_id':'INTEGER DEFAULT 0', 'order_id':'INTEGER DEFAULT 0', 'raw_json':'TEXT DEFAULT ""',
            'created_at':'TEXT DEFAULT ""', 'updated_at':'TEXT DEFAULT ""'
        },
        'email_messages': {
            'imap_uid':'TEXT DEFAULT ""', 'from_addr':'TEXT DEFAULT ""', 'to_addr':'TEXT DEFAULT ""',
            'subject':'TEXT DEFAULT ""', 'body':'TEXT DEFAULT ""', 'date_text':'TEXT DEFAULT ""',
            'has_attachments':'INTEGER DEFAULT 0', 'status':'TEXT DEFAULT "Yeni"', 'inbox_id':'INTEGER DEFAULT 0',
            'created_at':'TEXT DEFAULT ""', 'updated_at':'TEXT DEFAULT ""'
        },
        'quotes': {
            'inbox_id':'INTEGER DEFAULT 0', 'customer_name':'TEXT DEFAULT ""', 'phone':'TEXT DEFAULT ""', 'email':'TEXT DEFAULT ""',
            'title':'TEXT DEFAULT ""', 'source':'TEXT DEFAULT ""', 'material':'TEXT DEFAULT "PLA"', 'color':'TEXT DEFAULT ""',
            'grams':'REAL DEFAULT 0', 'support_grams':'REAL DEFAULT 0', 'time_min':'REAL DEFAULT 0', 'quantity':'INTEGER DEFAULT 1',
            'design_minutes':'REAL DEFAULT 0', 'cost_estimate':'REAL DEFAULT 0', 'price':'REAL DEFAULT 0', 'margin_amount':'REAL DEFAULT 0',
            'status':'TEXT DEFAULT "Ön Teklif"', 'valid_until':'TEXT DEFAULT ""', 'notes':'TEXT DEFAULT ""', 'odoo_id':'TEXT DEFAULT ""',
            'created_at':'TEXT DEFAULT ""', 'updated_at':'TEXT DEFAULT ""'
        },
        'catalog': {
            'makerworld_link':'TEXT DEFAULT ""', 'model_id':'TEXT DEFAULT ""', 'sku':'TEXT DEFAULT ""', 'title':'TEXT DEFAULT ""',
            'category':'TEXT DEFAULT "MakerWorld"', 'material':'TEXT DEFAULT "PLA"', 'color':'TEXT DEFAULT ""',
            'grams':'REAL DEFAULT 0', 'support_grams':'REAL DEFAULT 0', 'time_min':'REAL DEFAULT 0',
            'grams_basis':'TEXT DEFAULT "Toplam"', 'time_basis':'TEXT DEFAULT "Toplam"',
            'quantity':'INTEGER DEFAULT 1', 'estimated_price':'REAL DEFAULT 0', 'cost_estimate':'REAL DEFAULT 0', 'margin_amount':'REAL DEFAULT 0',
            'status':'TEXT DEFAULT "Aktif"', 'odoo_product_id':'TEXT DEFAULT ""', 'notes':'TEXT DEFAULT ""',
            'created_at':'TEXT DEFAULT ""', 'updated_at':'TEXT DEFAULT ""'
        },
        'customers': {
            'name':'TEXT DEFAULT ""', 'phone':'TEXT DEFAULT ""', 'email':'TEXT DEFAULT ""', 'instagram':'TEXT DEFAULT ""',
            'source':'TEXT DEFAULT ""', 'notes':'TEXT DEFAULT ""', 'created_at':'TEXT DEFAULT ""', 'updated_at':'TEXT DEFAULT ""'
        },
        'orders': {
            'quote_id':'INTEGER DEFAULT 0', 'customer_name':'TEXT DEFAULT ""', 'phone':'TEXT DEFAULT ""', 'email':'TEXT DEFAULT ""', 'source':'TEXT DEFAULT ""',
            'item_name':'TEXT DEFAULT ""', 'makerworld_link':'TEXT DEFAULT ""', 'material':'TEXT DEFAULT "PLA"',
            'grams':'REAL DEFAULT 0', 'support_grams':'REAL DEFAULT 0', 'time_min':'REAL DEFAULT 0', 'quantity':'INTEGER DEFAULT 1',
            'price':'REAL DEFAULT 0', 'cost_estimate':'REAL DEFAULT 0', 'status':'TEXT DEFAULT "Yeni Talep"', 'payment_status':'TEXT DEFAULT "Bekliyor"',
            'due_date':'TEXT DEFAULT ""', 'odoo_lead_id':'TEXT DEFAULT ""', 'notes':'TEXT DEFAULT ""',
            'created_at':'TEXT DEFAULT ""', 'updated_at':'TEXT DEFAULT ""'
        },
        'production_jobs': {
            'order_id':'INTEGER DEFAULT 0', 'job_name':'TEXT DEFAULT ""', 'printer':'TEXT DEFAULT "Bambu Lab X2D"',
            'material':'TEXT DEFAULT "PLA"', 'grams':'REAL DEFAULT 0', 'support_grams':'REAL DEFAULT 0', 'time_min':'REAL DEFAULT 0',
            'status':'TEXT DEFAULT "Baskıya Hazır"', 'priority':'TEXT DEFAULT "Normal"', 'started_at':'TEXT DEFAULT ""', 'completed_at':'TEXT DEFAULT ""',
            'notes':'TEXT DEFAULT ""', 'created_at':'TEXT DEFAULT ""', 'updated_at':'TEXT DEFAULT ""'
        },
        'inventory': {
            'item':'TEXT DEFAULT ""', 'category':'TEXT DEFAULT "Filament"', 'material':'TEXT DEFAULT ""', 'color':'TEXT DEFAULT ""', 'unit':'TEXT DEFAULT "g"',
            'current_qty':'REAL DEFAULT 0', 'min_qty':'REAL DEFAULT 0', 'unit_cost':'REAL DEFAULT 0', 'supplier':'TEXT DEFAULT ""', 'notes':'TEXT DEFAULT ""',
            'created_at':'TEXT DEFAULT ""', 'updated_at':'TEXT DEFAULT ""'
        },
        'message_templates': {
            'name':'TEXT DEFAULT ""', 'channel':'TEXT DEFAULT "WhatsApp"', 'body':'TEXT DEFAULT ""', 'created_at':'TEXT DEFAULT ""', 'updated_at':'TEXT DEFAULT ""'
        },
        'sync_queue': {
            'entity_type':'TEXT DEFAULT ""', 'entity_id':'INTEGER DEFAULT 0', 'target':'TEXT DEFAULT "Odoo"', 'action':'TEXT DEFAULT "upsert"',
            'status':'TEXT DEFAULT "Bekliyor"', 'last_error':'TEXT DEFAULT ""', 'created_at':'TEXT DEFAULT ""', 'updated_at':'TEXT DEFAULT ""'
        },
        'cost_items': {
            'setting_key':'TEXT UNIQUE DEFAULT ""', 'name':'TEXT DEFAULT ""', 'group_name':'TEXT DEFAULT "Genel"', 'unit':'TEXT DEFAULT "TL"',
            'value':'REAL DEFAULT 0', 'active':'INTEGER DEFAULT 1', 'notes':'TEXT DEFAULT ""', 'created_at':'TEXT DEFAULT ""', 'updated_at':'TEXT DEFAULT ""'
        },
        'app_events': {
            'level':'TEXT DEFAULT "INFO"', 'title':'TEXT DEFAULT ""', 'detail':'TEXT DEFAULT ""', 'created_at':'TEXT DEFAULT ""',
            'updated_at':'TEXT DEFAULT ""'
        }
    }
    for table in SORTABLE_TABLES:
        migrations.setdefault(table, {})['sort_order'] = 'REAL DEFAULT 0'
    for table, cols in migrations.items():
        try:
            existing = _columns(conn, table)
        except Exception:
            continue
        for col, definition in cols.items():
            if col not in existing:
                try:
                    conn.execute(f'ALTER TABLE {table} ADD COLUMN {col} {definition}')
                except sqlite3.OperationalError:
                    pass
    # Eski MVP katalog kolonlarını yeni adlara taşı.
    try:
        catalog_cols = _columns(conn, 'catalog')
        if 'manual_grams' in catalog_cols and 'grams' in catalog_cols:
            conn.execute('UPDATE catalog SET grams=COALESCE(NULLIF(grams,0), manual_grams)')
        if 'manual_time_min' in catalog_cols and 'time_min' in catalog_cols:
            conn.execute('UPDATE catalog SET time_min=COALESCE(NULLIF(time_min,0), manual_time_min)')
        if 'auto_grams' in catalog_cols and 'grams' in catalog_cols:
            conn.execute('UPDATE catalog SET grams=COALESCE(NULLIF(grams,0), auto_grams)')
        if 'auto_time_min' in catalog_cols and 'time_min' in catalog_cols:
            conn.execute('UPDATE catalog SET time_min=COALESCE(NULLIF(time_min,0), auto_time_min)')
    except Exception:
        pass
    # Sıralama kolonu yeni eklenen eski verilerde 0/null kalmasın.
    for table in SORTABLE_TABLES:
        try:
            cols = _columns(conn, table)
            if 'sort_order' in cols:
                conn.execute(f'UPDATE {table} SET sort_order=id WHERE COALESCE(sort_order, 0)=0')
        except Exception:
            pass


def init_db(path: str | Path | None = None):
    with connect(path) as conn:
        for statement in SCHEMA:
            conn.execute(statement)
        _ensure_columns(conn)
        for k, v in DEFAULT_SETTINGS.items():
            conn.execute('INSERT OR IGNORE INTO settings(key, value) VALUES (?, ?)', (k, str(v)))
        count = conn.execute('SELECT COUNT(*) FROM message_templates').fetchone()[0]
        if count == 0:
            for name, channel, body in DEFAULT_TEMPLATES:
                conn.execute('INSERT INTO message_templates(name, channel, body, created_at, updated_at) VALUES (?, ?, ?, ?, ?)', (name, channel, body, now(), now()))
        inv_count = conn.execute('SELECT COUNT(*) FROM inventory').fetchone()[0]
        if inv_count == 0:
            for row in DEFAULT_INVENTORY:
                conn.execute('''INSERT INTO inventory(item, category, material, color, unit, current_qty, min_qty, unit_cost, supplier, notes, created_at, updated_at)
                              VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''', (*row, now(), now()))
        cost_count = conn.execute('SELECT COUNT(*) FROM cost_items').fetchone()[0]
        if cost_count == 0:
            for setting_key, name, group_name, unit, default_value, notes in DEFAULT_COST_ITEMS:
                value = float(DEFAULT_SETTINGS.get(setting_key, default_value))
                conn.execute('''INSERT OR IGNORE INTO cost_items(setting_key, name, group_name, unit, value, active, notes, created_at, updated_at)
                              VALUES (?, ?, ?, ?, ?, 1, ?, ?, ?)''', (setting_key, name, group_name, unit, value, notes, now(), now()))
        conn.commit()


def get_settings():
    init_db()
    with connect() as conn:
        return {r['key']: r['value'] for r in conn.execute('SELECT key, value FROM settings')}


def save_setting(key, value):
    with connect() as conn:
        conn.execute('INSERT INTO settings(key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value=excluded.value', (key, str(value)))
        conn.commit()


def save_settings(values: dict):
    with connect() as conn:
        for k, v in values.items():
            conn.execute('INSERT INTO settings(key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value=excluded.value', (k, str(v)))
        conn.commit()


def delete_setting(key):
    with connect() as conn:
        conn.execute('DELETE FROM settings WHERE key=?', (key,))
        conn.commit()


def restore_default_cost_items():
    with connect() as conn:
        ts = now()
        for setting_key, name, group_name, unit, default_value, notes in DEFAULT_COST_ITEMS:
            conn.execute('INSERT INTO settings(key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value=excluded.value', (setting_key, str(default_value)))
            conn.execute('''INSERT INTO cost_items(setting_key, name, group_name, unit, value, active, notes, created_at, updated_at)
                         VALUES (?, ?, ?, ?, ?, 1, ?, ?, ?)
                         ON CONFLICT(setting_key) DO UPDATE SET name=excluded.name, group_name=excluded.group_name, unit=excluded.unit, value=excluded.value, active=1, notes=excluded.notes, updated_at=excluded.updated_at''',
                         (setting_key, name, group_name, unit, float(default_value), notes, ts, ts))
        conn.commit()


def insert(table, data: dict):
    data = dict(data)
    ts = now()
    data.setdefault('created_at', ts)
    data.setdefault('updated_at', ts)
    cols = ', '.join(data.keys())
    qs = ', '.join(['?'] * len(data))
    with connect() as conn:
        cur = conn.execute(f'INSERT INTO {table} ({cols}) VALUES ({qs})', list(data.values()))
        row_id = cur.lastrowid
        try:
            if table in SORTABLE_TABLES and 'sort_order' in _columns(conn, table) and 'sort_order' not in data:
                conn.execute(f'UPDATE {table} SET sort_order=? WHERE id=?', (row_id, row_id))
        except Exception:
            pass
        conn.commit()
        return row_id


def update(table, row_id: int, data: dict):
    data = dict(data)
    data['updated_at'] = now()
    assignments = ', '.join([f'{k}=?' for k in data.keys()])
    with connect() as conn:
        conn.execute(f'UPDATE {table} SET {assignments} WHERE id=?', list(data.values()) + [row_id])
        conn.commit()


def get_row(table, row_id: int):
    with connect() as conn:
        return conn.execute(f'SELECT * FROM {table} WHERE id=?', (row_id,)).fetchone()


def list_rows(table, where='', params=(), order='id DESC', limit=None):
    sql = f'SELECT * FROM {table}'
    if where:
        sql += ' WHERE ' + where
    if order:
        # Ana liste ekranlarında elle düzenlenen sıra kullanılsın. sort_order büyük olan üstte görünür.
        try:
            if table in SORTABLE_TABLES and order.strip().lower() == 'id desc':
                with connect() as chk_conn:
                    if 'sort_order' in _columns(chk_conn, table):
                        order = 'sort_order DESC, id DESC'
        except Exception:
            pass
        sql += ' ORDER BY ' + order
    if limit:
        sql += ' LIMIT ' + str(int(limit))
    with connect() as conn:
        return conn.execute(sql, tuple(params)).fetchall()


def delete_row(table, row_id: int):
    with connect() as conn:
        conn.execute(f'DELETE FROM {table} WHERE id=?', (row_id,))
        conn.commit()


def set_record_sort_order(table: str, row_id: int, sort_order: float):
    if table not in SORTABLE_TABLES:
        raise ValueError('Bu tablo sıralama merkezinde yönetilemez.')
    with connect() as conn:
        if 'sort_order' not in _columns(conn, table):
            conn.execute(f'ALTER TABLE {table} ADD COLUMN sort_order REAL DEFAULT 0')
        conn.execute(f'UPDATE {table} SET sort_order=?, updated_at=? WHERE id=?', (float(sort_order), now(), int(row_id)))
        conn.commit()


def move_record(table: str, row_id: int, direction: str):
    if table not in SORTABLE_TABLES:
        raise ValueError('Bu tablo sıralama merkezinde yönetilemez.')
    if direction not in ('up', 'down', 'top', 'bottom'):
        raise ValueError('Geçersiz hareket.')
    with connect() as conn:
        if 'sort_order' not in _columns(conn, table):
            conn.execute(f'ALTER TABLE {table} ADD COLUMN sort_order REAL DEFAULT 0')
            conn.execute(f'UPDATE {table} SET sort_order=id WHERE COALESCE(sort_order,0)=0')
        row = conn.execute(f'SELECT id, sort_order FROM {table} WHERE id=?', (int(row_id),)).fetchone()
        if not row:
            raise ValueError('Kayıt bulunamadı.')
        current = float(row['sort_order'] or row['id'])
        if direction == 'top':
            maxv = conn.execute(f'SELECT COALESCE(MAX(sort_order),0) FROM {table}').fetchone()[0] or 0
            conn.execute(f'UPDATE {table} SET sort_order=?, updated_at=? WHERE id=?', (float(maxv)+1, now(), int(row_id)))
        elif direction == 'bottom':
            minv = conn.execute(f'SELECT COALESCE(MIN(sort_order),0) FROM {table}').fetchone()[0] or 0
            conn.execute(f'UPDATE {table} SET sort_order=?, updated_at=? WHERE id=?', (float(minv)-1, now(), int(row_id)))
        elif direction == 'up':
            other = conn.execute(f'SELECT id, sort_order FROM {table} WHERE sort_order>? ORDER BY sort_order ASC LIMIT 1', (current,)).fetchone()
            if other:
                conn.execute(f'UPDATE {table} SET sort_order=?, updated_at=? WHERE id=?', (other['sort_order'], now(), int(row_id)))
                conn.execute(f'UPDATE {table} SET sort_order=?, updated_at=? WHERE id=?', (current, now(), int(other['id'])))
        elif direction == 'down':
            other = conn.execute(f'SELECT id, sort_order FROM {table} WHERE sort_order<? ORDER BY sort_order DESC LIMIT 1', (current,)).fetchone()
            if other:
                conn.execute(f'UPDATE {table} SET sort_order=?, updated_at=? WHERE id=?', (other['sort_order'], now(), int(row_id)))
                conn.execute(f'UPDATE {table} SET sort_order=?, updated_at=? WHERE id=?', (current, now(), int(other['id'])))
        conn.commit()


def change_record_id(table: str, old_id: int, new_id: int):
    if table not in SORTABLE_TABLES:
        raise ValueError('Bu tablo ID merkezinde yönetilemez.')
    old_id = int(old_id); new_id = int(new_id)
    if new_id <= 0:
        raise ValueError('Yeni ID pozitif tam sayı olmalı.')
    with connect() as conn:
        exists = conn.execute(f'SELECT id FROM {table} WHERE id=?', (new_id,)).fetchone()
        if exists:
            raise ValueError(f'{new_id} ID zaten bu tabloda kullanılıyor.')
        row = conn.execute(f'SELECT id FROM {table} WHERE id=?', (old_id,)).fetchone()
        if not row:
            raise ValueError('Eski kayıt bulunamadı.')
        conn.execute('PRAGMA foreign_keys=OFF')
        conn.execute(f'UPDATE {table} SET id=?, updated_at=? WHERE id=?', (new_id, now(), old_id))
        # Bilinen ilişki kolonlarını da taşı. Böylece sipariş/üretim bağı kopmaz.
        for rel_table, rel_col in RELATED_ID_REFERENCES.get(table, []):
            try:
                if rel_col in _columns(conn, rel_table):
                    conn.execute(f'UPDATE {rel_table} SET {rel_col}=?, updated_at=? WHERE {rel_col}=?', (new_id, now(), old_id))
            except Exception:
                pass
        conn.commit()


def log_event(title, detail='', level='INFO'):
    try:
        insert('app_events', {'level': level, 'title': title, 'detail': detail, 'created_at': now()})
    except Exception:
        pass


def add_sync(entity_type, entity_id, target='Odoo', action='upsert'):
    return insert('sync_queue', {'entity_type': entity_type, 'entity_id': entity_id, 'target': target, 'action': action, 'status': 'Bekliyor'})


def stats():
    with connect() as conn:
        q = lambda sql, p=(): conn.execute(sql, p).fetchone()[0]
        return {
            'inbox_new': q("SELECT COUNT(*) FROM inbox_items WHERE status IN ('Yeni','İncelenecek')"),
            'emails_new': q("SELECT COUNT(*) FROM email_messages WHERE status='Yeni'"),
            'quotes_open': q("SELECT COUNT(*) FROM quotes WHERE status NOT IN ('Onaylandı','Reddedildi','Siparişe Döndü')"),
            'orders_open': q("SELECT COUNT(*) FROM orders WHERE status NOT IN ('Teslim Edildi','İptal')"),
            'jobs_open': q("SELECT COUNT(*) FROM production_jobs WHERE status NOT IN ('Tamamlandı','Başarısız')"),
            'low_stock': q('SELECT COUNT(*) FROM inventory WHERE current_qty <= min_qty'),
            'revenue': q("SELECT COALESCE(SUM(price),0) FROM orders WHERE status != 'İptal'"),
        }


def backup_database():
    init_db()
    dst = BACKUP_DIR / f"controlcenter_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.sqlite3"
    shutil.copy2(DB_PATH, dst)
    return dst


def import_inbox_item(payload: dict, source_default='Bridge'):
    external_id = str(payload.get('external_id') or payload.get('id') or '')
    source = str(payload.get('source') or source_default)
    if external_id:
        existing = list_rows('inbox_items', 'source=? AND external_id=?', (source, external_id), limit=1)
        if existing:
            return existing[0]['id']
    data = {
        'source': source,
        'channel_id': str(payload.get('channel_id') or ''),
        'external_id': external_id,
        'customer_name': str(payload.get('customer_name') or payload.get('name') or ''),
        'phone': str(payload.get('phone') or ''),
        'email': str(payload.get('email') or ''),
        'instagram': str(payload.get('instagram') or ''),
        'subject': str(payload.get('subject') or payload.get('title') or ''),
        'message': str(payload.get('message') or payload.get('body') or ''),
        'attachment_urls': json.dumps(payload.get('attachment_urls') or payload.get('attachments') or [], ensure_ascii=False),
        'makerworld_link': str(payload.get('makerworld_link') or ''),
        'requested_material': str(payload.get('requested_material') or payload.get('material') or 'PLA'),
        'requested_color': str(payload.get('requested_color') or payload.get('color') or ''),
        'quantity': int(float(payload.get('quantity') or 1)),
        'grams': float(payload.get('grams') or 0),
        'support_grams': float(payload.get('support_grams') or 0),
        'time_min': float(payload.get('time_min') or 0),
        'priority': str(payload.get('priority') or 'Normal'),
        'status': str(payload.get('status') or 'Yeni'),
        'raw_json': json.dumps(payload, ensure_ascii=False),
    }
    return insert('inbox_items', data)
