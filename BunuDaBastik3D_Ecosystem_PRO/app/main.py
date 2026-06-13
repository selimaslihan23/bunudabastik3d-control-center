from __future__ import annotations
import json
import os
import sys
import subprocess
import threading
import time
import math
import webbrowser
import logging
import traceback
from pathlib import Path
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext

# PyInstaller onefile/onedir uyumluluğu.
# Paketli EXE içinde app klasörü veri olarak eklenir ve yerel modüller buradan yüklenir.
if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
    BASE_DIR = Path(sys._MEIPASS)
    CURRENT_DIR = BASE_DIR / 'app'
else:
    CURRENT_DIR = Path(__file__).resolve().parent
    BASE_DIR = CURRENT_DIR.parent
ASSETS_DIR = BASE_DIR / 'assets'
LOG_DIR = Path(os.environ.get('BDB_LOG_DIR', str(BASE_DIR / 'logs')))
try:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        filename=str(LOG_DIR / 'app_debug.log'),
        level=logging.DEBUG,
        format='%(asctime)s | %(levelname)s | %(message)s'
    )
except Exception:
    logging.basicConfig(level=logging.DEBUG)

def _global_excepthook(exc_type, exc, tb):
    try:
        logging.critical('Unhandled exception', exc_info=(exc_type, exc, tb))
    finally:
        sys.__excepthook__(exc_type, exc, tb)

sys.excepthook = _global_excepthook

for _path in (CURRENT_DIR, BASE_DIR):
    if str(_path) not in sys.path:
        sys.path.insert(0, str(_path))

import db
import email_client
import google_oauth_client
from makerworld import extract_model_id, title_from_link
from pricing import calculate_price, format_breakdown, fmt_money, fnum, inum
from odoo_client import OdooClient, OdooConfig
import exporters

APP_TITLE = 'BunuDaBastık3D Control Center PRO'
MATERIALS = ['PLA', 'PETG', 'ABS', 'ASA', 'TPU', 'SUPPORT']
SOURCES = ['WhatsApp', 'Google Forms', 'Email', 'Web', 'Instagram', 'Telefon', 'Yerel', 'Manual', 'Bridge']
PRIORITIES = ['Düşük', 'Normal', 'Yüksek', 'Acil']
INBOX_STATUSES = ['Yeni', 'İncelenecek', 'Teklif Oluşturuldu', 'Siparişe Döndü', 'Arşiv']
QUOTE_STATUSES = ['Ön Teklif', 'Gönderildi', 'Onaylandı', 'Reddedildi', 'Siparişe Döndü']
ORDER_STATUSES = ['Yeni Talep', 'Teklif Hazırlanıyor', 'Onay Bekliyor', 'Baskıya Hazır', 'Baskıda', 'Son İşlem', 'Paketlendi', 'Teslim Edildi', 'İptal']
JOB_STATUSES = ['Baskıya Hazır', 'Baskıda', 'Durakladı', 'Başarısız', 'Son İşlem', 'Tamamlandı']
PAYMENT_STATUSES = ['Bekliyor', 'Kapora Alındı', 'Ödendi', 'İade', 'İptal']

OPERATORS = ['Selim', 'Kemal']
THEME_PRESETS = {
    'Nebula Mor': {
        'accent': '#A855F7', 'accent2': '#D946EF', 'accent_dark': '#241038',
        'sidebar': '#10071C', 'sidebar2': '#26123F', 'bg': '#0A0712', 'card': '#171222',
        'card_alt': '#231636', 'soft': '#4C1D95', 'ink': '#FBF7FF', 'muted': '#D8B4FE', 'line': '#5B21B6',
        'success': '#34D399', 'danger': '#FB7185', 'warning': '#FBBF24'
    },
    'Cyber Gold': {
        'accent': '#F59E0B', 'accent2': '#F97316', 'accent_dark': '#2A1602',
        'sidebar': '#120B02', 'sidebar2': '#2A1602', 'bg': '#0E0A05', 'card': '#1D160B',
        'card_alt': '#2A1F0F', 'soft': '#5A3805', 'ink': '#FFF7ED', 'muted': '#FCD34D', 'line': '#92400E',
        'success': '#22C55E', 'danger': '#EF4444', 'warning': '#FACC15'
    },
    'Matrix Yeşil': {
        'accent': '#22C55E', 'accent2': '#06B6D4', 'accent_dark': '#052E16',
        'sidebar': '#03140A', 'sidebar2': '#052E16', 'bg': '#020A05', 'card': '#07140B',
        'card_alt': '#0C1F12', 'soft': '#14532D', 'ink': '#ECFDF5', 'muted': '#86EFAC', 'line': '#166534',
        'success': '#4ADE80', 'danger': '#FB7185', 'warning': '#FBBF24'
    },
    'Buz Mavisi': {
        'accent': '#38BDF8', 'accent2': '#818CF8', 'accent_dark': '#082F49',
        'sidebar': '#06111F', 'sidebar2': '#0B2340', 'bg': '#07111F', 'card': '#0D1B2E',
        'card_alt': '#13243A', 'soft': '#1E3A8A', 'ink': '#F0F9FF', 'muted': '#BAE6FD', 'line': '#1D4ED8',
        'success': '#34D399', 'danger': '#FB7185', 'warning': '#FBBF24'
    },
    'Sade Pro': {
        'accent': '#8B5CF6', 'accent2': '#A78BFA', 'accent_dark': '#312E81',
        'sidebar': '#111827', 'sidebar2': '#1F2937', 'bg': '#F4F1FF', 'card': '#FFFFFF',
        'card_alt': '#F8FAFC', 'soft': '#DDD6FE', 'ink': '#111827', 'muted': '#6B7280', 'line': '#C4B5FD',
        'success': '#059669', 'danger': '#DC2626', 'warning': '#D97706'
    },
}
BACKGROUND_EFFECTS = ['Statik', 'Aurora Pulse', 'Neon Grid', 'Yıldız Tozu', 'Enerji Çizgileri']
BUTTON_STYLES = ['Glow Neon', 'Solid Pro', 'Neon Çerçeve', 'Minimal']
ANIMATION_LEVELS = ['Kapalı', 'Hafif', 'Canlı']

GLOBAL_RECORD_TABLES = {
    'Gelen Kutusu': {'table': 'inbox_items', 'key': 'inbox', 'title': 'subject', 'detail': 'customer_name', 'status': 'status', 'refresh': 'refresh_inbox'},
    'E-Posta': {'table': 'email_messages', 'key': 'email', 'title': 'subject', 'detail': 'from_addr', 'status': 'status', 'refresh': 'refresh_email'},
    'Teklifler': {'table': 'quotes', 'key': 'quote', 'title': 'title', 'detail': 'customer_name', 'status': 'status', 'refresh': 'refresh_quotes'},
    'Katalog': {'table': 'catalog', 'key': 'catalog', 'title': 'title', 'detail': 'model_id', 'status': 'status', 'refresh': 'refresh_catalog'},
    'Siparişler': {'table': 'orders', 'key': 'order', 'title': 'item_name', 'detail': 'customer_name', 'status': 'status', 'refresh': 'refresh_orders'},
    'Üretim': {'table': 'production_jobs', 'key': 'job', 'title': 'job_name', 'detail': 'printer', 'status': 'status', 'refresh': 'refresh_jobs'},
    'Stok': {'table': 'inventory', 'key': 'inventory', 'title': 'item', 'detail': 'material', 'status': 'category', 'refresh': 'refresh_inventory'},
    'Müşteriler': {'table': 'customers', 'key': 'customer', 'title': 'name', 'detail': 'phone', 'status': 'source', 'refresh': 'refresh_customers'},
    'Mesajlar': {'table': 'message_templates', 'key': 'template', 'title': 'name', 'detail': 'channel', 'status': 'channel', 'refresh': 'refresh_templates'},
    'Senkron': {'table': 'sync_queue', 'key': 'sync', 'title': 'entity_type', 'detail': 'entity_id', 'status': 'status', 'refresh': 'refresh_sync'},
    'Maliyet Kalemleri': {'table': 'cost_items', 'key': 'cost', 'title': 'name', 'detail': 'setting_key', 'status': 'group_name', 'refresh': 'refresh_cost_items'},
}


def safe_json(value, default):
    try:
        return json.loads(value or '')
    except Exception:
        return default


class App(tk.Tk):
    def __init__(self):
        logging.info('App startup begins')
        super().__init__()
        self.safe_mode = (os.environ.get('BDB_SAFE_MODE') == '1') or ('--safe' in sys.argv)
        self.debug_mode = (os.environ.get('BDB_DEBUG') == '1') or ('--debug' in sys.argv)
        logging.info('Safe mode=%s Debug mode=%s Frozen=%s BASE_DIR=%s CURRENT_DIR=%s', self.safe_mode, self.debug_mode, getattr(sys, 'frozen', False), BASE_DIR, CURRENT_DIR)
        db.init_db()
        self.settings = db.get_settings()
        self.ui_theme = self.settings.get('ui_theme', 'Nebula Mor')
        self.background_effect = self.settings.get('background_effect', 'Aurora Pulse')
        self.button_style = self.settings.get('button_style', 'Glow Neon')
        self.animation_level = self.settings.get('animation_level', 'Hafif')
        self.colors = self._build_colors()
        self.title(APP_TITLE)
        # Pencere artık ekrandan taşmayacak şekilde çalışma alanına göre açılır.
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        win_w = min(1500, max(1050, sw - 70))
        win_h = min(920, max(650, sh - 110))
        self.geometry(f'{win_w}x{win_h}+20+20')
        self.minsize(1050, 650)
        self.selected = {}
        self.vars = {}
        self.page_frames = {}
        self.nav_buttons = {}
        self.brand_logo = None
        self.brand_logo_small = None
        self.brand_icon = None
        self.fx_canvas = None
        self.fx_tick = 0
        self.bridge_process = None
        self.integration_status_vars = {}
        self.operator_name = self.settings.get('operator_name', 'Selim') if self.settings.get('operator_name', 'Selim') in OPERATORS else 'Selim'
        self.operator_var = tk.StringVar(value=self.operator_name)
        if not self.safe_mode:
            self.withdraw()
        self._load_brand_assets()
        if not self.safe_mode:
            self._show_splash()
            if not self._show_login():
                logging.info('Login cancelled')
                self.destroy()
                return
        else:
            self.operator_name = self.settings.get('operator_name', 'Selim') if self.settings.get('operator_name', 'Selim') in OPERATORS else 'Selim'
            self.operator_var.set(self.operator_name)
        self._style()
        self._shell()
        self._pages()
        self.deiconify()
        self.after(200, self._fit_window_to_screen)
        self._bind_shortcuts()
        self.show_page('Dashboard')
        self.refresh_all()
        self.after(150, self._bring_to_front)
        logging.info('App UI loaded')

    def _bring_to_front(self):
        try:
            self.lift()
            self.attributes('-topmost', True)
            self.after(600, lambda: self.attributes('-topmost', False))
            self.focus_force()
            logging.info('Window brought to front')
        except Exception:
            logging.exception('Could not bring window to front')

    def _fit_window_to_screen(self):
        # Windows'ta görev çubuğu yüzünden pencere dışına taşmayı azaltır.
        try:
            if sys.platform.startswith('win'):
                self.state('zoomed')
            else:
                sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
                self.geometry(f'{max(1050, sw-70)}x{max(650, sh-110)}+20+20')
        except Exception:
            logging.exception('Window fit failed')

    def _load_brand_assets(self):
        """Load brand logo assets for sidebar and window icon."""
        try:
            logo_path = ASSETS_DIR / 'bdb_brand_logo.png'
            if logo_path.exists():
                raw = tk.PhotoImage(file=str(logo_path))
                self.brand_logo = raw
                if self.brand_logo.width() > 218:
                    factor = max(1, round(self.brand_logo.width() / 218))
                    self.brand_logo = self.brand_logo.subsample(factor, factor)
                self.brand_logo_small = raw
                if self.brand_logo_small.width() > 118:
                    factor = max(1, round(self.brand_logo_small.width() / 118))
                    self.brand_logo_small = self.brand_logo_small.subsample(factor, factor)
        except Exception:
            self.brand_logo = None
            self.brand_logo_small = None
        try:
            icon_path = ASSETS_DIR / 'bdb_brand_icon.png'
            if icon_path.exists():
                self.brand_icon = tk.PhotoImage(file=str(icon_path))
                self.iconphoto(True, self.brand_icon)
        except Exception:
            self.brand_icon = None

    def _build_colors(self):
        # Eski sürümlerden kalan window_bg/card_bg ayarları kontrastı bozabiliyor.
        # Bu yüzden renkleri seçilen tema presetinden alıyoruz.
        return THEME_PRESETS.get(self.ui_theme, THEME_PRESETS['Nebula Mor']).copy()

    def _center_window(self, win, width, height):
        self.update_idletasks()
        sw = self.winfo_screenwidth(); sh = self.winfo_screenheight()
        x = max(0, int((sw - width) / 2)); y = max(0, int((sh - height) / 2))
        win.geometry(f'{width}x{height}+{x}+{y}')

    def _show_splash(self):
        logging.info('Showing splash screen')
        splash = tk.Toplevel(self)
        splash.overrideredirect(True)
        splash.configure(bg='#0B0B13')
        self._center_window(splash, 620, 430)
        wrap = tk.Frame(splash, bg='#0B0B13', highlightbackground='#A855F7', highlightthickness=1)
        wrap.pack(fill='both', expand=True, padx=2, pady=2)
        top_glow = tk.Frame(wrap, bg='#241038', height=8)
        top_glow.pack(fill='x')
        if self.brand_logo is not None:
            tk.Label(wrap, image=self.brand_logo, bg='#0B0B13', bd=0).pack(pady=(30, 8))
        tk.Label(wrap, text='BunuDaBastık3D', bg='#0B0B13', fg='white', font=('Segoe UI', 28, 'bold')).pack()
        tk.Label(wrap, text='Control Center PRO', bg='#0B0B13', fg='#D8B4FE', font=('Segoe UI', 14, 'bold')).pack(pady=(3, 0))
        tk.Label(wrap, text='Yoksa üretiriz.', bg='#0B0B13', fg='#C4B5FD', font=('Segoe UI', 11)).pack(pady=(4, 24))
        bar_frame = tk.Frame(wrap, bg='#0B0B13')
        bar_frame.pack(fill='x', padx=90)
        progress = ttk.Progressbar(bar_frame, mode='determinate', maximum=100, length=420)
        progress.pack(fill='x')
        status = tk.Label(wrap, text='Sistem modülleri hazırlanıyor...', bg='#0B0B13', fg='#B7A8D9', font=('Segoe UI', 9))
        status.pack(pady=14)
        steps = [('Gelen kutusu bağlanıyor', 25), ('Katalog fiyatlayıcı yükleniyor', 52), ('Odoo senkron kuyruğu hazırlanıyor', 78), ('Panel açılıyor', 100)]
        for label, value in steps:
            status.configure(text=label)
            progress['value'] = value
            splash.update()
            time.sleep(0.22)
        splash.destroy()
        logging.info('Splash screen closed')

    def _show_login(self):
        logging.info('Showing login screen')
        result = {'ok': False}
        login = tk.Toplevel(self)
        login.title('BunuDaBastık3D Giriş')
        login.configure(bg='#0B0B13')
        login.resizable(False, False)
        self._center_window(login, 720, 460)
        try:
            if self.brand_icon is not None:
                login.iconphoto(True, self.brand_icon)
        except Exception:
            pass
        outer = tk.Frame(login, bg='#0B0B13')
        outer.pack(fill='both', expand=True)
        hero = tk.Frame(outer, bg='#12081F', width=260)
        hero.pack(side='left', fill='both')
        hero.pack_propagate(False)
        if self.brand_logo is not None:
            tk.Label(hero, image=self.brand_logo, bg='#12081F', bd=0).pack(pady=(44, 12))
        tk.Label(hero, text='Üretim kokpiti', bg='#12081F', fg='white', font=('Segoe UI', 17, 'bold')).pack(anchor='w', padx=24)
        tk.Label(hero, text='Teklif, üretim, stok, e-posta\nve Odoo tek ekranda.', bg='#12081F', fg='#C4B5FD', justify='left', font=('Segoe UI', 10)).pack(anchor='w', padx=24, pady=(8, 0))
        form = tk.Frame(outer, bg='#0B0B13')
        form.pack(side='left', fill='both', expand=True, padx=34, pady=34)
        tk.Label(form, text='Kontrol Merkezine Giriş', bg='#0B0B13', fg='white', font=('Segoe UI', 22, 'bold')).pack(anchor='w')
        tk.Label(form, text='Bu giriş yerel operatör ekranıdır. API anahtarları yalnızca Ayarlar sekmesinde saklanır.', bg='#0B0B13', fg='#B7A8D9', wraplength=370, justify='left', font=('Segoe UI', 9)).pack(anchor='w', pady=(5, 22))
        operator = tk.StringVar(value=self.settings.get('operator_name', 'Selim'))
        pin = tk.StringVar(value='')
        for label, var, show in [('Operatör adı', operator, ''), ('PIN / Not', pin, '*')]:
            tk.Label(form, text=label, bg='#0B0B13', fg='#D8B4FE', font=('Segoe UI', 10, 'bold')).pack(anchor='w')
            e = tk.Entry(form, textvariable=var, show=show, bg='#171423', fg='white', insertbackground='white', relief='flat', font=('Segoe UI', 12), highlightbackground='#3B2A58', highlightcolor='#A855F7', highlightthickness=1)
            e.pack(fill='x', ipady=9, pady=(4, 14))
        remember = tk.BooleanVar(value=True)
        tk.Checkbutton(form, text='Operatör adını hatırla', variable=remember, bg='#0B0B13', fg='#C4B5FD', activebackground='#0B0B13', activeforeground='white', selectcolor='#241038').pack(anchor='w')
        def enter():
            self.operator_name = operator.get().strip() or 'Operatör'
            if remember.get():
                db.set_setting('operator_name', self.operator_name)
                self.settings['operator_name'] = self.operator_name
            result['ok'] = True
            logging.info('Login accepted for operator=%s', self.operator_name)
            login.destroy()
        btn = tk.Button(form, text='Kontrol Merkezine Gir', command=enter, bg='#A855F7', fg='white', activebackground='#D946EF', activeforeground='white', bd=0, padx=16, pady=12, font=('Segoe UI', 11, 'bold'))
        btn.pack(fill='x', pady=(18, 8))
        tk.Button(form, text='Çıkış', command=login.destroy, bg='#171423', fg='#B7A8D9', activebackground='#241038', activeforeground='white', bd=0, padx=16, pady=10, font=('Segoe UI', 10)).pack(fill='x')
        login.bind('<Return>', lambda _e: enter())
        login.protocol('WM_DELETE_WINDOW', login.destroy)
        login.transient(self)
        login.grab_set()
        login.wait_window()
        logging.info('Login screen closed ok=%s', result['ok'])
        return result['ok']

    # ---------- UI core ----------
    def _bind_shortcuts(self):
        self.bind('<F5>', lambda _e: self.refresh_all())
        self.bind('<Control-n>', lambda _e: self.show_page('Gelen Kutusu'))
        self.bind('<Control-e>', lambda _e: self.fetch_emails_thread())
        self.bind('<Control-b>', lambda _e: self.bridge_health())
        self.bind('<Control-k>', lambda _e: self.show_page('Katalog'))

    def _style(self):
        style = ttk.Style(self)
        try:
            style.theme_use('clam')
        except Exception:
            pass
        style.configure('TFrame', background=self.colors['bg'])
        style.configure('Panel.TFrame', background=self.colors['card'])
        style.configure('TLabel', background=self.colors['bg'], foreground=self.colors['ink'], font=('Segoe UI', 10))
        style.configure('Panel.TLabel', background=self.colors['card'], foreground=self.colors['ink'], font=('Segoe UI', 10))
        style.configure('Title.TLabel', background=self.colors['bg'], foreground=self.colors['ink'], font=('Segoe UI', 22, 'bold'))
        style.configure('Sub.TLabel', background=self.colors['bg'], foreground=self.colors['muted'], font=('Segoe UI', 9))
        style.configure('CardTitle.TLabel', background=self.colors['card'], foreground=self.colors['muted'], font=('Segoe UI', 9, 'bold'))
        style.configure('CardValue.TLabel', background=self.colors['card'], foreground=self.colors['ink'], font=('Segoe UI', 20, 'bold'))
        style.configure('TButton', font=('Segoe UI', 10), padding=8, background=self.colors['card_alt'], foreground=self.colors['ink'])
        style.map('TButton', background=[('active', self.colors['soft'])], foreground=[('active', 'white')])
        style.configure('Accent.TButton', font=('Segoe UI', 10, 'bold'), foreground='white', background=self.colors['accent'])
        style.map('Accent.TButton', background=[('active', self.colors['accent2'])])
        style.configure('Treeview', rowheight=30, font=('Segoe UI', 9), background='#12111D', fieldbackground='#12111D', foreground='#F8FAFC', bordercolor=self.colors['line'])
        style.map('Treeview', background=[('selected', self.colors['accent'])], foreground=[('selected', 'white')])
        style.configure('Treeview.Heading', font=('Segoe UI', 9, 'bold'), background=self.colors['card_alt'], foreground='#F8FAFC')
        style.configure('TLabelframe', background=self.colors['card'], bordercolor=self.colors['line'], relief='solid')
        style.configure('TLabelframe.Label', background=self.colors['card'], foreground='#D8B4FE', font=('Segoe UI', 10, 'bold'))
        style.configure('Horizontal.TProgressbar', troughcolor='#171423', background=self.colors['accent'])

    def _shell(self):
        self.configure(bg=self.colors['bg'])
        self.sidebar = tk.Frame(self, bg=self.colors['sidebar'], width=270, highlightbackground='#3B2A58', highlightthickness=1)
        self.sidebar.pack(side='left', fill='y')
        self.sidebar.pack_propagate(False)
        logo = tk.Frame(self.sidebar, bg=self.colors['sidebar'])
        logo.pack(fill='x', padx=16, pady=(16, 12))
        if self.brand_logo is not None:
            tk.Label(logo, image=self.brand_logo, bg=self.colors['sidebar'], bd=0).pack(anchor='center', pady=(0, 8))
        tk.Label(logo, text='BunuDaBastık3D', bg=self.colors['sidebar'], fg='white', font=('Segoe UI', 15, 'bold')).pack(anchor='w')
        tk.Label(logo, text='Yoksa üretiriz.', bg=self.colors['sidebar'], fg='#DDD6FE', font=('Segoe UI', 10, 'bold')).pack(anchor='w', pady=(1, 0))
        self.operator_label = tk.Label(logo, text=f'Operatör: {self.operator_name}', bg=self.colors['sidebar'], fg=self.colors['muted'], font=('Segoe UI', 9, 'bold'))
        self.operator_label.pack(anchor='w')
        op_frame = tk.Frame(logo, bg=self.colors['sidebar'])
        op_frame.pack(fill='x', pady=(5, 2))
        tk.Label(op_frame, text='Aktif operatör', bg=self.colors['sidebar'], fg='#8B7BB4', font=('Segoe UI', 8)).pack(anchor='w')
        self.operator_combo = ttk.Combobox(op_frame, textvariable=self.operator_var, values=OPERATORS, state='readonly', width=18)
        self.operator_combo.pack(fill='x', pady=(2, 0))
        self.operator_combo.bind('<<ComboboxSelected>>', self.change_operator)
        tk.Label(logo, text='Tek panel, çok kanal', bg=self.colors['sidebar'], fg='#8B7BB4', font=('Segoe UI', 8)).pack(anchor='w', pady=(3, 0))
        items = [
            ('Dashboard', '🏠'), ('Gelen Kutusu', '📥'), ('E-Posta', '✉️'), ('Teklifler', '💸'),
            ('Katalog', '🧩'), ('Siparişler', '🧾'), ('Üretim', '🖨️'), ('Stok', '📦'),
            ('Hammadde Fiyat Merkezi', '🧪'), ('Kayıt Sıralama', '🔢'), ('Müşteriler', '👥'), ('Mesajlar', '💬'),
            ('Entegrasyonlar', '🔌'), ('API Ayarları', '🧬'), ('Senkron', '🌐'), ('Ayarlar', '⚙️')]
        nav_wrap = tk.Frame(self.sidebar, bg=self.colors['sidebar'])
        nav_wrap.pack(fill='both', expand=True, padx=0, pady=(0, 6))
        self.sidebar_canvas = tk.Canvas(nav_wrap, bg=self.colors['sidebar'], bd=0, highlightthickness=0)
        nav_scroll = ttk.Scrollbar(nav_wrap, orient='vertical', command=self.sidebar_canvas.yview)
        self.sidebar_canvas.configure(yscrollcommand=nav_scroll.set)
        self.sidebar_canvas.pack(side='left', fill='both', expand=True)
        nav_scroll.pack(side='right', fill='y')
        self.sidebar_menu = tk.Frame(self.sidebar_canvas, bg=self.colors['sidebar'])
        sidebar_window = self.sidebar_canvas.create_window((0, 0), window=self.sidebar_menu, anchor='nw')
        self.sidebar_menu.bind('<Configure>', lambda e: self.sidebar_canvas.configure(scrollregion=self.sidebar_canvas.bbox('all')))
        self.sidebar_canvas.bind('<Configure>', lambda e: self.sidebar_canvas.itemconfigure(sidebar_window, width=e.width))
        self.sidebar_canvas.bind_all('<Control-MouseWheel>', lambda e: self.sidebar_canvas.yview_scroll(int(-1*(e.delta/120)), 'units'))
        for name, icon in items:
            b = tk.Button(self.sidebar_menu, text=f'{icon}  {name}', anchor='w', bd=0, padx=18, pady=8,
                          font=('Segoe UI', 10, 'bold'), bg=self.colors['sidebar'], fg='#EDE9FE',
                          activebackground=self.colors['accent'], activeforeground='white', command=lambda n=name: self.show_page(n))
            b.pack(fill='x', padx=10, pady=1)
            self.nav_buttons[name] = b
        tk.Label(self.sidebar_menu, text='v3.2 GLOBAL ID • Responsive', bg=self.colors['sidebar'], fg='#C4B5FD', font=('Segoe UI', 8)).pack(anchor='w', padx=18, pady=12)
        self.main_area = tk.Frame(self, bg=self.colors['bg'])
        self.main_area.pack(side='left', fill='both', expand=True)
        self.topbar = tk.Frame(self.main_area, bg=self.colors['bg'])
        self.topbar.pack(fill='x', padx=20, pady=(14, 6))
        title_wrap = tk.Frame(self.topbar, bg=self.colors['bg'])
        title_wrap.pack(side='left')
        self.page_title = ttk.Label(title_wrap, text='', style='Title.TLabel')
        self.page_title.pack(anchor='w')
        tk.Label(title_wrap, text='Hızlı kontrol: talep al, fiyatla, üretime gönder, senkronla.', bg=self.colors['bg'], fg=self.colors['muted'], font=('Segoe UI', 9)).pack(anchor='w')
        quick = tk.Frame(self.topbar, bg=self.colors['bg'])
        quick.pack(side='right')
        def qbtn(text, command, accent=False):
            style = self.button_style
            bg = self.colors['accent'] if accent else self.colors['card_alt']
            bd = 0
            relief = 'flat'
            highlight = 0
            if style == 'Neon Çerçeve':
                bg = self.colors['card']
                bd = 1
                relief = 'solid'
                highlight = 1
            elif style == 'Minimal':
                bg = self.colors['sidebar']
            elif style == 'Solid Pro':
                bg = self.colors['accent_dark'] if not accent else self.colors['accent']
            else:  # Glow Neon
                bg = self.colors['accent'] if accent else self.colors['card_alt']
            return tk.Button(quick, text=text, command=command, bg=bg, fg='white', activebackground=self.colors['accent2'], activeforeground='white', bd=bd, relief=relief, highlightthickness=highlight, highlightbackground=self.colors['accent'], padx=12, pady=8, font=('Segoe UI', 9, 'bold'))
        qbtn('＋ Yeni Talep', lambda: self.show_page('Gelen Kutusu'), True).pack(side='left', padx=3)
        qbtn('✉ Mail Çek', self.fetch_emails_thread).pack(side='left', padx=3)
        qbtn('🌐 Bridge', self.bridge_health).pack(side='left', padx=3)
        qbtn('↻ Yenile', self.refresh_all).pack(side='left', padx=3)
        self.status = tk.StringVar(value='Hazır')
        tk.Label(quick, textvariable=self.status, bg=self.colors['bg'], fg=self.colors['muted'], font=('Segoe UI', 9)).pack(side='left', padx=(10, 0))
        self.fx_canvas = tk.Canvas(self.main_area, height=58, bg=self.colors['bg'], highlightthickness=0, bd=0)
        self.fx_canvas.pack(fill='x', padx=18, pady=(0, 8))
        self._setup_ambient_fx()
        self.content = tk.Frame(self.main_area, bg=self.colors['bg'])
        self.content.pack(fill='both', expand=True, padx=18, pady=(4, 18))

    def change_operator(self, _event=None):
        name = self.operator_var.get() if hasattr(self, 'operator_var') else self.operator_name
        if name not in OPERATORS:
            name = 'Selim'
        self.operator_name = name
        try:
            db.save_setting('operator_name', name)
            self.settings['operator_name'] = name
        except Exception:
            logging.exception('Operator could not be saved')
        if hasattr(self, 'operator_label'):
            self.operator_label.configure(text=f'Operatör: {name}')
        self.set_status(f'Aktif operatör: {name}')
        try:
            db.log_event('Operatör değişti', f'Aktif operatör: {name}')
        except Exception:
            pass

    def _setup_ambient_fx(self):
        if self.fx_canvas is None:
            return
        try:
            self.fx_canvas.configure(bg=self.colors['bg'])
            self._draw_fx_frame()
            if self.animation_level != 'Kapalı':
                delay = 280 if self.animation_level == 'Canlı' else 720
                self.after(delay, self._animate_fx)
        except Exception:
            logging.exception('Ambient FX setup failed')

    def _animate_fx(self):
        try:
            if self.fx_canvas is None or self.animation_level == 'Kapalı':
                return
            self.fx_tick += 1
            self._draw_fx_frame()
            delay = 260 if self.animation_level == 'Canlı' else 780
            self.after(delay, self._animate_fx)
        except Exception:
            logging.exception('Ambient FX animation failed')

    def _draw_fx_frame(self):
        c = self.fx_canvas
        if c is None:
            return
        c.delete('all')
        w = max(c.winfo_width(), 900)
        h = max(c.winfo_height(), 58)
        bg = self.colors['bg']; accent = self.colors['accent']; accent2 = self.colors['accent2']; line = self.colors['line']
        c.create_rectangle(0, 0, w, h, fill=bg, outline='')
        effect = self.background_effect
        tick = self.fx_tick
        # Her efekti okunabilirlik için ince bir ambiyans şeridinde tutuyoruz.
        if effect == 'Statik':
            c.create_rectangle(0, h-3, w, h, fill=accent, outline='')
            c.create_text(18, h/2, anchor='w', text='BunuDaBastık3D Operasyon Hattı', fill=self.colors['muted'], font=('Segoe UI', 9, 'bold'))
            return
        if effect == 'Neon Grid':
            step = 42
            offset = (tick * 7) % step
            for x in range(-step, int(w)+step, step):
                c.create_line(x+offset, 0, x+offset-28, h, fill=line, width=1)
            for y in range(8, int(h), 16):
                c.create_line(0, y, w, y, fill='#1B1230', width=1)
            c.create_rectangle(0, h-4, w, h, fill=accent, outline='')
        elif effect == 'Yıldız Tozu':
            for i in range(34):
                x = (i * 113 + tick * (5 + i % 3)) % int(w)
                y = 8 + ((i * 29 + tick * 3) % max(12, int(h-16)))
                r = 1 + (i % 3)
                fill = accent if i % 2 == 0 else accent2
                c.create_oval(x-r, y-r, x+r, y+r, fill=fill, outline='')
            c.create_line(0, h-3, w, h-3, fill=accent2, width=2)
        elif effect == 'Enerji Çizgileri':
            for i in range(7):
                y = 10 + i * 7
                x1 = (tick * (10+i) + i*83) % int(w)
                c.create_line(x1-180, y, x1+120, y+8, fill=accent if i % 2 else accent2, width=2)
                c.create_line(x1+150, y+10, x1+360, y+2, fill=line, width=1)
            c.create_rectangle(0, h-4, w, h, fill=accent, outline='')
        else:  # Aurora Pulse
            for i in range(10):
                x = int((i * w / 9) + math.sin((tick+i)/2.0) * 24)
                color = accent if i % 2 == 0 else accent2
                c.create_oval(x-130, -80, x+160, h+70, outline=color, width=1)
            pulse = 4 + int((math.sin(tick/2) + 1) * 2)
            c.create_rectangle(0, h-pulse, w, h, fill=accent, outline='')
        c.create_text(18, h/2, anchor='w', text=f'{self.background_effect}  •  {self.button_style}  •  Animasyon: {self.animation_level}', fill=self.colors['muted'], font=('Segoe UI', 9, 'bold'))
        c.create_text(w-18, h/2, anchor='e', text='Yoksa üretiriz.', fill=self.colors['ink'], font=('Segoe UI', 10, 'bold'))

    def _pages(self):
        self._dashboard_page(); self._inbox_page(); self._email_page(); self._quotes_page(); self._catalog_page()
        self._orders_page(); self._production_page(); self._inventory_page(); self._raw_material_price_page(); self._record_manager_page(); self._customers_page()
        self._messages_page(); self._integrations_page(); self._api_settings_page(); self._sync_page(); self._settings_page()

    def page(self, name):
        # Her sayfa kendi dikey kaydırmasına sahip. Böylece küçük ekranlarda buton/tablo dışarı taşmaz.
        outer = tk.Frame(self.content, bg=self.colors['bg'])
        outer.place(relx=0, rely=0, relwidth=1, relheight=1)
        canvas = tk.Canvas(outer, bg=self.colors['bg'], bd=0, highlightthickness=0)
        vs = ttk.Scrollbar(outer, orient='vertical', command=canvas.yview)
        canvas.configure(yscrollcommand=vs.set)
        canvas.pack(side='left', fill='both', expand=True)
        vs.pack(side='right', fill='y')
        inner = tk.Frame(canvas, bg=self.colors['bg'])
        win = canvas.create_window((0, 0), window=inner, anchor='nw')
        def _resize(_event=None):
            canvas.itemconfigure(win, width=canvas.winfo_width())
            canvas.configure(scrollregion=canvas.bbox('all'))
        inner.bind('<Configure>', _resize)
        canvas.bind('<Configure>', _resize)
        def _wheel(event, c=canvas):
            try:
                c.yview_scroll(int(-1 * (event.delta / 120)), 'units')
            except Exception:
                pass
        canvas.bind('<MouseWheel>', _wheel)
        inner.bind('<MouseWheel>', _wheel)
        self.page_frames[name] = outer
        return inner

    def show_page(self, name):
        for n, b in self.nav_buttons.items():
            b.configure(bg=self.colors['accent'] if n == name else self.colors['sidebar'], fg='white' if n == name else '#EDE9FE')
        self.page_title.configure(text=name)
        self.page_frames[name].tkraise()
        if name == 'Dashboard': self.refresh_dashboard()
        elif name == 'Gelen Kutusu': self.refresh_inbox()
        elif name == 'E-Posta': self.refresh_email()
        elif name == 'Teklifler': self.refresh_quotes()
        elif name == 'Katalog': self.refresh_catalog()
        elif name == 'Siparişler': self.refresh_orders()
        elif name == 'Üretim': self.refresh_jobs()
        elif name == 'Stok': self.refresh_inventory()
        elif name == 'Hammadde Fiyat Merkezi': self.refresh_raw_material_center()
        elif name == 'Kayıt Sıralama': self.refresh_record_manager()
        elif name == 'Müşteriler': self.refresh_customers()
        elif name == 'Mesajlar': self.refresh_templates()
        elif name == 'API Ayarları': self.refresh_api_center()
        elif name == 'Senkron': self.refresh_sync()
        elif name == 'Ayarlar': self.refresh_cost_items()

    def panel(self, parent, title='', **pack):
        f = ttk.LabelFrame(parent, text=title, padding=10) if title else ttk.Frame(parent, style='Panel.TFrame', padding=10)
        f.pack(**({'fill': 'x', 'pady': 6} | pack))
        return f

    def tree(self, parent, columns, headings=None, height=12):
        wrap = ttk.Frame(parent, style='Panel.TFrame')
        wrap.pack(fill='both', expand=True, pady=6)
        t = ttk.Treeview(wrap, columns=columns, show='headings', height=height)
        vs = ttk.Scrollbar(wrap, orient='vertical', command=t.yview)
        hs = ttk.Scrollbar(wrap, orient='horizontal', command=t.xview)
        t.configure(yscrollcommand=vs.set, xscrollcommand=hs.set)
        t.grid(row=0, column=0, sticky='nsew'); vs.grid(row=0, column=1, sticky='ns'); hs.grid(row=1, column=0, sticky='ew')
        wrap.columnconfigure(0, weight=1); wrap.rowconfigure(0, weight=1)
        headings = headings or {c: c for c in columns}
        for c in columns:
            t.heading(c, text=headings.get(c, c)); t.column(c, width=130, anchor='w')
        return t

    def entry(self, parent, label, var, row, col=0, width=20, show=None):
        ttk.Label(parent, text=label, style='Panel.TLabel').grid(row=row, column=col, sticky='w', padx=4, pady=4)
        e = ttk.Entry(parent, textvariable=var, width=width, show=show or '')
        e.grid(row=row, column=col+1, sticky='ew', padx=4, pady=4)
        return e

    def combo(self, parent, label, var, values, row, col=0, width=18):
        ttk.Label(parent, text=label, style='Panel.TLabel').grid(row=row, column=col, sticky='w', padx=4, pady=4)
        c = ttk.Combobox(parent, textvariable=var, values=values, width=width, state='readonly')
        c.grid(row=row, column=col+1, sticky='ew', padx=4, pady=4)
        return c

    def set_status(self, text):
        self.status.set(text)

    def selected_id(self, key):
        return self.selected.get(key)

    def bind_select(self, tree, key, callback=None):
        def _sel(_event=None):
            item = tree.selection()
            self.selected[key] = int(item[0]) if item else None
            if callback: callback()
        tree.bind('<<TreeviewSelect>>', _sel)

    def clear_tree(self, tree):
        for i in tree.get_children(): tree.delete(i)

    def copy(self, text):
        self.clipboard_clear(); self.clipboard_append(text or '')
        self.set_status('Panoya kopyalandı')

    def open_doc(self, relative_path):
        try:
            path = BASE_DIR / relative_path
            if path.exists():
                webbrowser.open(str(path))
            else:
                messagebox.showinfo('Doküman', f'Dosya bulunamadı:\n{path}')
        except Exception as e:
            messagebox.showerror('Doküman açılamadı', str(e))

    def refresh_all(self):
        for fn in [self.refresh_dashboard, self.refresh_inbox, self.refresh_email, self.refresh_quotes, self.refresh_catalog,
                   self.refresh_orders, self.refresh_jobs, self.refresh_inventory, self.refresh_raw_material_center, self.refresh_record_manager, self.refresh_customers, self.refresh_templates, self.refresh_api_center, self.refresh_sync, self.refresh_cost_items]:
            try: fn()
            except Exception: pass

    # ---------- Dashboard ----------
    def _dashboard_page(self):
        root = self.page('Dashboard')
        self.dash_cards = tk.Frame(root, bg=self.colors['bg']); self.dash_cards.pack(fill='x')
        quick_ops = self.panel(root, 'Hızlı işlemler ve ergonomi')
        for label, cmd, accent in [
            ('＋ Yeni yerel talep', lambda: self.show_page('Gelen Kutusu'), True),
            ('✉ Gelen mailleri çek', self.fetch_emails_thread, False),
            ('🧩 Katalog fiyatla', lambda: self.show_page('Katalog'), False),
            ('🖨 Üretim kuyruğu', lambda: self.show_page('Üretim'), False),
            ('🌐 Odoo/Bridge kontrol', lambda: self.show_page('Entegrasyonlar'), False),
            ('📤 Excel dışa aktar', self.export_all, False),
        ]:
            ttk.Button(quick_ops, text=label, style='Accent.TButton' if accent else 'TButton', command=cmd).pack(side='left', padx=4, pady=2)
        tk.Label(quick_ops, text='Kısayollar: F5 yenile • Ctrl+N talep • Ctrl+E mail • Ctrl+B bridge • Ctrl+K katalog', bg=self.colors['card'], fg=self.colors['muted'], font=('Segoe UI', 8)).pack(side='right', padx=8)
        body = tk.Frame(root, bg=self.colors['bg']); body.pack(fill='both', expand=True, pady=8)
        left = self.panel(body, 'Canlı operasyon özeti', fill='both', expand=True, side='left', padx=(0, 6))
        right = self.panel(body, 'Uyarılar ve son olaylar', fill='both', expand=True, side='left', padx=(6, 0))
        self.dash_text = tk.Text(left, bg=self.colors['card_alt'], fg=self.colors['ink'], insertbackground='white', bd=0, height=22, wrap='word', font=('Segoe UI', 10), padx=14, pady=12)
        self.dash_text.pack(fill='both', expand=True)
        self.events_tree = self.tree(right, ['time','level','title'], {'time':'Zaman','level':'Seviye','title':'Olay'}, height=12)
        row = tk.Frame(root, bg=self.colors['bg']); row.pack(fill='x')
        ttk.Button(row, text='Her şeyi yenile', style='Accent.TButton', command=self.refresh_all).pack(side='left', padx=3)
        ttk.Button(row, text='Tüm verileri Excel dışa aktar', command=self.export_all).pack(side='left', padx=3)
        ttk.Button(row, text='Veritabanı yedekle', command=self.backup_db).pack(side='left', padx=3)

    def card(self, parent, title, value, icon=''):
        f = tk.Frame(parent, bg=self.colors['card'], highlightbackground=self.colors['line'], highlightthickness=1)
        f.pack(side='left', fill='x', expand=True, padx=5, pady=5)
        tk.Frame(f, bg=self.colors['accent'], height=3).pack(fill='x')
        ttk.Label(f, text=f'{icon} {title}', style='CardTitle.TLabel').pack(anchor='w', padx=12, pady=(10, 2))
        ttk.Label(f, text=str(value), style='CardValue.TLabel').pack(anchor='w', padx=12, pady=(0, 12))
        return f

    def refresh_dashboard(self):
        for c in self.dash_cards.winfo_children(): c.destroy()
        s = db.stats(); cur = self.settings.get('currency','TL')
        self.card(self.dash_cards, 'Yeni gelen', s['inbox_new'], '📥')
        self.card(self.dash_cards, 'Yeni e-posta', s['emails_new'], '✉️')
        self.card(self.dash_cards, 'Açık teklif', s['quotes_open'], '💸')
        self.card(self.dash_cards, 'Açık sipariş', s['orders_open'], '🧾')
        self.card(self.dash_cards, 'Üretim işi', s['jobs_open'], '🖨️')
        self.card(self.dash_cards, 'Ciro', fmt_money(s['revenue'], cur), '📊')
        self.dash_text.configure(state='normal'); self.dash_text.delete('1.0','end')
        text = f"""Bugünkü kontrol rotası:

1) Gelen Kutusu sekmesinde WhatsApp / Forms / E-posta / Yerel talepleri incele.
2) Gramaj ve süre bilgisi varsa Teklife Dönüştür butonuyla fiyat çıkar.
3) Onaylanan teklifi Siparişe çevir, ardından Üretim işini oluştur.
4) Üretim tamamlanınca stoktan otomatik düşüş çalışır.
5) Senkron sekmesinden Odoo aktarım kuyruğunu kontrol et.

Cloud Bridge açıkken dış kanallardan gelen işler bu panele düşer.
Yerel işler için Gelen Kutusu > Manuel Talep Ekle kullanılır.
"""
        self.dash_text.insert('end', text); self.dash_text.configure(state='disabled')
        self.clear_tree(self.events_tree)
        for r in db.list_rows('app_events', order='id DESC', limit=20):
            self.events_tree.insert('', 'end', iid=r['id'], values=(r['created_at'], r['level'], r['title']))

    # ---------- Inbox ----------
    def _inbox_page(self):
        root = self.page('Gelen Kutusu')
        top = self.panel(root, 'Tek panel gelen kutusu: WhatsApp + Google Forms + E-posta + Web + Yerel')
        self.vars['inbox_name'] = tk.StringVar(); self.vars['inbox_phone'] = tk.StringVar(); self.vars['inbox_email'] = tk.StringVar()
        self.vars['inbox_source'] = tk.StringVar(value='Yerel'); self.vars['inbox_subject'] = tk.StringVar(); self.vars['inbox_material'] = tk.StringVar(value='PLA')
        self.vars['inbox_qty'] = tk.StringVar(value='1'); self.vars['inbox_grams'] = tk.StringVar(value='0'); self.vars['inbox_support'] = tk.StringVar(value='0'); self.vars['inbox_time'] = tk.StringVar(value='0')
        self.combo(top, 'Kaynak', self.vars['inbox_source'], SOURCES, 0, 0); self.entry(top, 'Müşteri', self.vars['inbox_name'], 0, 2)
        self.entry(top, 'Telefon', self.vars['inbox_phone'], 0, 4); self.entry(top, 'E-posta', self.vars['inbox_email'], 0, 6)
        self.entry(top, 'Konu', self.vars['inbox_subject'], 1, 0); self.combo(top, 'Malzeme', self.vars['inbox_material'], MATERIALS, 1, 2)
        self.entry(top, 'Adet', self.vars['inbox_qty'], 1, 4); self.entry(top, 'Gram', self.vars['inbox_grams'], 1, 6)
        self.entry(top, 'Destek g', self.vars['inbox_support'], 2, 0); self.entry(top, 'Süre dk', self.vars['inbox_time'], 2, 2)
        self.inbox_msg = scrolledtext.ScrolledText(top, height=3, width=80, font=('Segoe UI',9)); self.inbox_msg.grid(row=3,column=0,columnspan=8,sticky='ew',padx=4,pady=4)
        bar = tk.Frame(top, bg=self.colors['card']); bar.grid(row=4,column=0,columnspan=8,sticky='w',padx=4,pady=4)
        ttk.Button(bar, text='Manuel Talep Ekle', style='Accent.TButton', command=self.add_manual_inbox).pack(side='left', padx=3)
        ttk.Button(bar, text='Seçileni Forma Al', command=self.load_inbox_form).pack(side='left', padx=3)
        ttk.Button(bar, text='Güncelle', command=self.update_inbox).pack(side='left', padx=3)
        ttk.Button(bar, text='Sil', command=lambda: self.delete_selected_row('inbox_items', 'inbox', self.refresh_inbox)).pack(side='left', padx=3)
        ttk.Button(bar, text='Cloud Bridge’den Çek', command=self.pull_bridge).pack(side='left', padx=3)
        ttk.Button(bar, text='İçeriği Aç', command=self.show_selected_inbox_popup).pack(side='left', padx=3)
        ttk.Button(bar, text='İçeriği Kopyala', command=self.copy_selected_inbox).pack(side='left', padx=3)
        ttk.Button(bar, text='Seçileni Teklife Dönüştür', command=self.inbox_to_quote).pack(side='left', padx=3)
        ttk.Button(bar, text='Arşivle', command=self.archive_inbox).pack(side='left', padx=3)
        self.inbox_tree = self.tree(root, ['id','source','customer','subject','material','qty','grams','time','status','created'],
                                   {'id':'ID','source':'Kaynak','customer':'Müşteri','subject':'Konu','material':'Malzeme','qty':'Adet','grams':'g','time':'dk','status':'Durum','created':'Tarih'}, height=14)
        self.bind_select(self.inbox_tree, 'inbox', self.show_inbox_detail)
        detail = self.panel(root, 'Seçili talep detayı')
        self.inbox_detail = scrolledtext.ScrolledText(detail, height=5, font=('Segoe UI',9)); self.inbox_detail.pack(fill='x')

    def add_manual_inbox(self):
        rid = db.insert('inbox_items', {
            'source': self.vars['inbox_source'].get(), 'customer_name': self.vars['inbox_name'].get(), 'phone': self.vars['inbox_phone'].get(),
            'email': self.vars['inbox_email'].get(), 'subject': self.vars['inbox_subject'].get(), 'message': self.inbox_msg.get('1.0','end').strip(),
            'requested_material': self.vars['inbox_material'].get(), 'quantity': inum(self.vars['inbox_qty'].get(),1),
            'grams': fnum(self.vars['inbox_grams'].get()), 'support_grams': fnum(self.vars['inbox_support'].get()), 'time_min': fnum(self.vars['inbox_time'].get()),
        })
        db.log_event('Manuel talep eklendi', f'Inbox #{rid}')
        self.refresh_inbox(); self.set_status('Talep eklendi')

    def refresh_inbox(self):
        self.clear_tree(self.inbox_tree)
        for r in db.list_rows('inbox_items', order='id DESC', limit=500):
            self.inbox_tree.insert('', 'end', iid=r['id'], values=(r['id'], r['source'], r['customer_name'], r['subject'], r['requested_material'], r['quantity'], r['grams'], r['time_min'], r['status'], r['created_at']))

    def show_inbox_detail(self):
        rid = self.selected_id('inbox')
        r = db.get_row('inbox_items', rid) if rid else None
        self.inbox_detail.delete('1.0','end')
        if not r: return
        att = safe_json(r['attachment_urls'], [])
        detail = f"Kaynak: {r['source']}\nMüşteri: {r['customer_name']} | Tel: {r['phone']} | Mail: {r['email']}\nKonu: {r['subject']}\nMakerWorld: {r['makerworld_link']}\nEkler: {att}\n\nMesaj:\n{r['message']}"
        self.inbox_detail.insert('end', detail)

    def _inbox_text(self, r):
        att = safe_json(r['attachment_urls'], [])
        raw = r['raw_json'] or ''
        return f"Kaynak: {r['source']}\nMüşteri: {r['customer_name']}\nTelefon: {r['phone']}\nE-posta: {r['email']}\nInstagram: {r['instagram']}\nKonu: {r['subject']}\nMakerWorld: {r['makerworld_link']}\nEkler: {att}\nDurum: {r['status']}\nOluşturma: {r['created_at']}\n\nMesaj:\n{r['message']}\n\nHam JSON:\n{raw}"

    def show_large_text(self, title, body):
        win = tk.Toplevel(self)
        win.title(title)
        win.geometry('900x650')
        win.configure(bg=self.colors['bg'])
        txt = scrolledtext.ScrolledText(win, font=('Consolas', 10), bg=self.colors.get('card', '#111'), fg=self.colors.get('ink', '#fff'), insertbackground=self.colors.get('ink', '#fff'))
        txt.pack(fill='both', expand=True, padx=10, pady=10)
        txt.insert('end', body or '')
        bar = tk.Frame(win, bg=self.colors['bg'])
        bar.pack(fill='x', padx=10, pady=(0,10))
        ttk.Button(bar, text='Panoya Kopyala', command=lambda: self.copy(body)).pack(side='left', padx=3)
        ttk.Button(bar, text='Kapat', command=win.destroy).pack(side='right', padx=3)

    def show_selected_inbox_popup(self):
        rid = self.selected_id('inbox')
        if not rid:
            return messagebox.showwarning('Seçim yok', 'Önce bir gelen talep seç.')
        r = db.get_row('inbox_items', rid)
        if r:
            self.show_large_text(f'Gelen Talep #{rid}', self._inbox_text(r))

    def copy_selected_inbox(self):
        rid = self.selected_id('inbox')
        if not rid:
            return messagebox.showwarning('Seçim yok', 'Önce bir gelen talep seç.')
        r = db.get_row('inbox_items', rid)
        if r:
            self.copy(self._inbox_text(r))

    def pull_bridge(self):
        import requests
        url = self.settings.get('bridge_url','http://127.0.0.1:8787').rstrip('/') + '/api/inbox'
        try:
            res = requests.get(url, timeout=10)
            res.raise_for_status()
            count = 0
            for item in res.json().get('items', []):
                db.import_inbox_item(item, source_default=item.get('source','Bridge')); count += 1
            db.log_event('Cloud Bridge içeri aktarma', f'{count} kayıt kontrol edildi')
            self.refresh_inbox(); self.set_status(f'Bridge kontrol edildi: {count} kayıt')
        except Exception as e:
            messagebox.showerror('Bridge hatası', str(e))

    def inbox_to_quote(self):
        rid = self.selected_id('inbox')
        if not rid: return messagebox.showwarning('Seçim yok', 'Önce bir gelen talep seç.')
        r = db.get_row('inbox_items', rid)
        br = calculate_price(self.settings, r['requested_material'], r['grams'], r['support_grams'], r['time_min'], r['quantity'])
        qid = db.insert('quotes', {
            'inbox_id': rid, 'customer_name': r['customer_name'], 'phone': r['phone'], 'email': r['email'], 'title': r['subject'] or '3D Baskı Talebi',
            'source': r['source'], 'material': r['requested_material'], 'color': r['requested_color'], 'grams': r['grams'], 'support_grams': r['support_grams'],
            'time_min': r['time_min'], 'quantity': r['quantity'], 'cost_estimate': br['cost_estimate'], 'price': br['total_price'], 'margin_amount': br['margin_amount'],
            'notes': r['message']
        })
        db.update('inbox_items', rid, {'status':'Teklif Oluşturuldu', 'quote_id': qid})
        db.add_sync('quote', qid, 'Odoo', 'create_lead')
        db.log_event('Teklif oluşturuldu', f'Inbox #{rid} → Teklif #{qid}')
        self.refresh_inbox(); self.refresh_quotes(); self.set_status('Teklif oluşturuldu')

    def archive_inbox(self):
        rid = self.selected_id('inbox')
        if rid: db.update('inbox_items', rid, {'status':'Arşiv'}); self.refresh_inbox()

    # ---------- Email ----------
    def _email_page(self):
        root = self.page('E-Posta')

        oauth = self.panel(root, 'Gmail OAuth bağlantısı - App Password gerektirmez')
        self.vars['gmail_oauth_query'] = tk.StringVar(value=self.settings.get('gmail_oauth_query','in:inbox'))
        self.vars['gmail_oauth_limit'] = tk.StringVar(value=self.settings.get('gmail_oauth_limit','25'))
        oauth_top = tk.Frame(oauth, bg=self.colors['card'])
        oauth_top.pack(fill='x', pady=(0, 6))
        ttk.Label(oauth_top, text='Google Cloud credentials.json:', style='Panel.TLabel').pack(side='left', padx=4)
        status_text = 'Hazır' if google_oauth_client.has_credentials_file() else 'Seçilmedi'
        token_text = 'Var' if google_oauth_client.has_token() else 'Yok'
        self.gmail_oauth_status = tk.StringVar(value=f'İstemci dosyası: {status_text} | Yetki: {token_text}')
        ttk.Label(oauth_top, textvariable=self.gmail_oauth_status, style='Panel.TLabel').pack(side='left', padx=8)
        oauth_inputs = tk.Frame(oauth, bg=self.colors['card'])
        oauth_inputs.pack(fill='x', pady=4)
        ttk.Label(oauth_inputs, text='Gmail arama:', style='Panel.TLabel').pack(side='left', padx=4)
        ttk.Entry(oauth_inputs, textvariable=self.vars['gmail_oauth_query'], width=35).pack(side='left', padx=4)
        ttk.Label(oauth_inputs, text='Limit:', style='Panel.TLabel').pack(side='left', padx=4)
        ttk.Entry(oauth_inputs, textvariable=self.vars['gmail_oauth_limit'], width=8).pack(side='left', padx=4)
        oauth_buttons = tk.Frame(oauth, bg=self.colors['card'])
        oauth_buttons.pack(fill='x', pady=4)
        ttk.Button(oauth_buttons, text='credentials.json Seç', command=self.choose_gmail_credentials).pack(side='left', padx=3)
        ttk.Button(oauth_buttons, text='Gmail ile Bağlan / Yetki Ver', style='Accent.TButton', command=self.gmail_oauth_connect_thread).pack(side='left', padx=3)
        ttk.Button(oauth_buttons, text='Gmail API Mailleri Çek', command=self.fetch_gmail_oauth_thread).pack(side='left', padx=3)
        ttk.Button(oauth_buttons, text='OAuth Yetkisini Sıfırla', command=self.gmail_oauth_disconnect).pack(side='left', padx=3)
        ttk.Button(oauth_buttons, text='OAuth Rehberi', command=lambda: self.open_doc('docs/GMAIL_OAUTH_KURULUM.md')).pack(side='left', padx=3)

        cfg = self.panel(root, 'IMAP e-posta ayarları ve gelen mailler - yedek yöntem')
        self.vars['imap_host'] = tk.StringVar(value=self.settings.get('imap_host','imap.gmail.com'))
        self.vars['imap_port'] = tk.StringVar(value=self.settings.get('imap_port','993'))
        self.vars['imap_user'] = tk.StringVar(value=self.settings.get('imap_username',''))
        self.vars['imap_pass'] = tk.StringVar(value=self.settings.get('imap_password',''))
        self.vars['imap_box'] = tk.StringVar(value=self.settings.get('imap_mailbox','INBOX'))
        self.vars['imap_limit'] = tk.StringVar(value=self.settings.get('imap_fetch_limit','25'))
        self.entry(cfg, 'IMAP Host', self.vars['imap_host'], 0, 0); self.entry(cfg, 'Port', self.vars['imap_port'], 0, 2, width=8)
        self.entry(cfg, 'Kullanıcı', self.vars['imap_user'], 0, 4); self.entry(cfg, 'Parola / App Password', self.vars['imap_pass'], 1, 0, show='*')
        self.entry(cfg, 'Mailbox', self.vars['imap_box'], 1, 2, width=12); self.entry(cfg, 'Limit', self.vars['imap_limit'], 1, 4, width=8)
        row = tk.Frame(cfg, bg=self.colors['card']); row.grid(row=2,column=0,columnspan=6,sticky='w',padx=4,pady=4)
        ttk.Button(row, text='Ayarları Kaydet', command=self.save_email_settings).pack(side='left', padx=3)
        ttk.Button(row, text='IMAP Gelen Mailleri Çek', command=self.fetch_emails_thread).pack(side='left', padx=3)
        ttk.Button(row, text='Seçili Maili Aç', command=self.show_selected_email_popup).pack(side='left', padx=3)
        ttk.Button(row, text='İçeriği Kopyala', command=self.copy_selected_email).pack(side='left', padx=3)
        ttk.Button(row, text='Seçili Maili Talebe Dönüştür', style='Accent.TButton', command=self.email_to_inbox).pack(side='left', padx=3)
        ttk.Button(row, text='Seçili Maili Sil', command=lambda: self.delete_selected_row('email_messages', 'email', self.refresh_email)).pack(side='left', padx=3)
        self.email_tree = self.tree(root, ['id','from','subject','date','attachments','status'], {'id':'ID','from':'Gönderen','subject':'Konu','date':'Tarih','attachments':'Ek','status':'Durum'}, height=13)
        self.bind_select(self.email_tree, 'email', self.show_email_detail)
        detail = self.panel(root, 'Seçili e-posta içeriği')
        self.email_detail = scrolledtext.ScrolledText(detail, height=6, font=('Segoe UI',9)); self.email_detail.pack(fill='both')

    def refresh_gmail_oauth_status(self):
        try:
            status_text = 'Hazır' if google_oauth_client.has_credentials_file() else 'Seçilmedi'
            token_text = 'Var' if google_oauth_client.has_token() else 'Yok'
            if hasattr(self, 'gmail_oauth_status'):
                self.gmail_oauth_status.set(f'İstemci dosyası: {status_text} | Yetki: {token_text}')
        except Exception:
            pass

    def choose_gmail_credentials(self):
        path = filedialog.askopenfilename(
            title='Google OAuth credentials.json seç',
            filetypes=[('JSON dosyası', '*.json'), ('Tüm dosyalar', '*.*')]
        )
        if not path:
            return
        try:
            saved = google_oauth_client.set_credentials_file(path)
            db.save_settings({'gmail_oauth_configured': '1'})
            self.settings['gmail_oauth_configured'] = '1'
            self.refresh_gmail_oauth_status()
            messagebox.showinfo('Gmail OAuth', f'credentials.json kaydedildi:\n{saved}')
        except Exception as e:
            messagebox.showerror('Gmail OAuth hatası', str(e))

    def gmail_oauth_connect_thread(self):
        self.save_email_settings()
        self.set_status('Gmail OAuth yetki ekranı açılıyor...')
        threading.Thread(target=self._gmail_oauth_connect, daemon=True).start()

    def _gmail_oauth_connect(self):
        try:
            profile = google_oauth_client.get_profile()
            email = profile.get('emailAddress', 'Gmail')
            db.log_event('Gmail OAuth bağlandı', email)
            self.after(0, lambda: (self.refresh_gmail_oauth_status(), self.set_status(f'Gmail bağlı: {email}'), messagebox.showinfo('Gmail bağlantısı hazır', f'Bağlanan hesap: {email}')))
        except Exception as e:
            self.after(0, lambda: messagebox.showerror('Gmail OAuth hatası', str(e)))

    def fetch_gmail_oauth_thread(self):
        self.save_email_settings()
        self.set_status('Gmail API ile mailler çekiliyor...')
        threading.Thread(target=self._fetch_gmail_oauth, daemon=True).start()

    def _fetch_gmail_oauth(self):
        try:
            query = self.vars.get('gmail_oauth_query').get() if self.vars.get('gmail_oauth_query') else 'in:inbox'
            limit = self.vars.get('gmail_oauth_limit').get() if self.vars.get('gmail_oauth_limit') else '25'
            items = google_oauth_client.fetch_gmail_messages(limit=limit, query=query)
            imported = 0
            for it in items:
                existing = db.list_rows('email_messages', 'imap_uid=?', (it['imap_uid'],), limit=1)
                if existing:
                    continue
                eid = db.insert('email_messages', it)
                db.import_inbox_item({'source':'Email','external_id':f"gmail-{eid}", 'email': it['from_addr'], 'subject': it['subject'], 'message': it['body']}, source_default='Email')
                imported += 1
            db.log_event('Gmail API çekildi', f'{imported} yeni mail')
            self.after(0, lambda: (self.refresh_email(), self.refresh_inbox(), self.refresh_dashboard(), self.set_status(f'{imported} yeni Gmail içe aktarıldı')))
        except Exception as e:
            self.after(0, lambda: messagebox.showerror('Gmail API hatası', str(e)))

    def gmail_oauth_disconnect(self):
        if not messagebox.askyesno('Gmail OAuth', 'Gmail yetki tokenı silinsin mi? credentials.json dosyası kalır, tekrar bağlanabilirsin.'):
            return
        try:
            google_oauth_client.disconnect(delete_credentials=False)
            self.refresh_gmail_oauth_status()
            self.set_status('Gmail OAuth yetkisi sıfırlandı')
        except Exception as e:
            messagebox.showerror('Gmail OAuth hatası', str(e))

    def save_email_settings(self):
        vals = {'imap_host': self.vars['imap_host'].get(), 'imap_port': self.vars['imap_port'].get(), 'imap_username': self.vars['imap_user'].get(),
                'imap_password': self.vars['imap_pass'].get(), 'imap_mailbox': self.vars['imap_box'].get(), 'imap_fetch_limit': self.vars['imap_limit'].get(),
                'gmail_oauth_query': self.vars.get('gmail_oauth_query').get() if self.vars.get('gmail_oauth_query') else 'in:inbox',
                'gmail_oauth_limit': self.vars.get('gmail_oauth_limit').get() if self.vars.get('gmail_oauth_limit') else '25'}
        db.save_settings(vals); self.settings.update(vals); self.set_status('E-posta ayarları kaydedildi')

    def fetch_emails_thread(self):
        self.save_email_settings(); self.set_status('Mailler çekiliyor...')
        threading.Thread(target=self._fetch_emails, daemon=True).start()

    def _fetch_emails(self):
        try:
            items = email_client.fetch_imap_emails(self.vars['imap_host'].get(), self.vars['imap_port'].get(), self.vars['imap_user'].get(), self.vars['imap_pass'].get(), self.vars['imap_box'].get(), self.vars['imap_limit'].get(), only_unseen=False)
            imported = 0
            for it in items:
                existing = db.list_rows('email_messages', 'imap_uid=? AND from_addr=?', (it['imap_uid'], it['from_addr']), limit=1)
                if existing: continue
                eid = db.insert('email_messages', it)
                db.import_inbox_item({'source':'Email','external_id':f"email-{eid}", 'email': it['from_addr'], 'subject': it['subject'], 'message': it['body']}, source_default='Email')
                imported += 1
            db.log_event('E-posta çekildi', f'{imported} yeni mail')
            self.after(0, lambda: (self.refresh_email(), self.refresh_inbox(), self.set_status(f'{imported} yeni mail içe aktarıldı')))
        except Exception as e:
            self.after(0, lambda: messagebox.showerror('E-posta hatası', str(e)))

    def refresh_email(self):
        self.clear_tree(self.email_tree)
        for r in db.list_rows('email_messages', order='id DESC', limit=500):
            self.email_tree.insert('', 'end', iid=r['id'], values=(r['id'], r['from_addr'], r['subject'], r['date_text'], 'Var' if r['has_attachments'] else '', r['status']))

    def show_email_detail(self):
        rid = self.selected_id('email'); r = db.get_row('email_messages', rid) if rid else None
        self.email_detail.delete('1.0','end')
        if r: self.email_detail.insert('end', f"Gönderen: {r['from_addr']}\nKonu: {r['subject']}\nTarih: {r['date_text']}\n\n{r['body']}")

    def _email_text(self, r):
        return f"Gönderen: {r['from_addr']}\nAlıcı: {r['to_addr']}\nKonu: {r['subject']}\nTarih: {r['date_text']}\nEk: {'Var' if r['has_attachments'] else 'Yok'}\nDurum: {r['status']}\nOluşturma: {r['created_at']}\n\nİçerik:\n{r['body']}"

    def show_selected_email_popup(self):
        rid = self.selected_id('email')
        if not rid:
            return messagebox.showwarning('Seçim yok', 'Önce bir e-posta seç.')
        r = db.get_row('email_messages', rid)
        if r:
            self.show_large_text(f'E-posta #{rid}', self._email_text(r))

    def copy_selected_email(self):
        rid = self.selected_id('email')
        if not rid:
            return messagebox.showwarning('Seçim yok', 'Önce bir e-posta seç.')
        r = db.get_row('email_messages', rid)
        if r:
            self.copy(self._email_text(r))

    def email_to_inbox(self):
        rid = self.selected_id('email')
        if not rid: return
        r = db.get_row('email_messages', rid)
        iid = db.import_inbox_item({'source':'Email','external_id':f"email-manual-{rid}", 'email': r['from_addr'], 'subject': r['subject'], 'message': r['body']}, source_default='Email')
        db.update('email_messages', rid, {'status':'Talebe Dönüştü', 'inbox_id': iid})
        self.refresh_email(); self.refresh_inbox(); self.set_status('E-posta talebe dönüştürüldü')

    # ---------- Quotes ----------
    def _quotes_page(self):
        root = self.page('Teklifler')
        bar = self.panel(root, 'Teklif işlemleri')
        ttk.Button(bar, text='Seçili teklifi siparişe çevir', style='Accent.TButton', command=self.quote_to_order).pack(side='left', padx=3)
        ttk.Button(bar, text='Düzenle', command=self.edit_quote).pack(side='left', padx=3)
        ttk.Button(bar, text='Sil', command=lambda: self.delete_selected_row('quotes', 'quote', self.refresh_quotes)).pack(side='left', padx=3)
        ttk.Button(bar, text='Mesajı panoya kopyala', command=self.copy_quote_message).pack(side='left', padx=3)
        ttk.Button(bar, text='Yenile', command=self.refresh_quotes).pack(side='left', padx=3)
        self.quote_tree = self.tree(root, ['id','customer','title','material','qty','grams','time','price','status','created'],
                                    {'id':'ID','customer':'Müşteri','title':'Başlık','material':'Malzeme','qty':'Adet','grams':'g','time':'dk','price':'Fiyat','status':'Durum','created':'Tarih'}, height=18)
        self.bind_select(self.quote_tree, 'quote')
        detail = self.panel(root, 'Fiyat kırılımı')
        self.quote_breakdown = scrolledtext.ScrolledText(detail, height=7, font=('Segoe UI',9)); self.quote_breakdown.pack(fill='x')
        self.quote_tree.bind('<<TreeviewSelect>>', lambda e: self.show_quote_breakdown())

    def refresh_quotes(self):
        self.clear_tree(self.quote_tree); cur = self.settings.get('currency','TL')
        for r in db.list_rows('quotes', order='id DESC', limit=500):
            self.quote_tree.insert('', 'end', iid=r['id'], values=(r['id'], r['customer_name'], r['title'], r['material'], r['quantity'], r['grams'], r['time_min'], fmt_money(r['price'],cur), r['status'], r['created_at']))

    def show_quote_breakdown(self):
        rid = self.selected_id('quote'); r = db.get_row('quotes', rid) if rid else None
        self.quote_breakdown.delete('1.0','end')
        if not r: return
        br = calculate_price(self.settings, r['material'], r['grams'], r['support_grams'], r['time_min'], r['quantity'], r['design_minutes'])
        self.quote_breakdown.insert('end', format_breakdown(br, self.settings.get('currency','TL')))

    def quote_to_order(self):
        rid = self.selected_id('quote')
        if not rid: return messagebox.showwarning('Seçim yok', 'Önce teklif seç.')
        r = db.get_row('quotes', rid)
        oid = db.insert('orders', {'quote_id': rid, 'customer_name': r['customer_name'], 'phone': r['phone'], 'email': r['email'], 'source': r['source'],
                                   'item_name': r['title'], 'material': r['material'], 'grams': r['grams'], 'support_grams': r['support_grams'],
                                   'time_min': r['time_min'], 'quantity': r['quantity'], 'price': r['price'], 'cost_estimate': r['cost_estimate'], 'status':'Baskıya Hazır'})
        db.update('quotes', rid, {'status':'Siparişe Döndü'})
        db.add_sync('order', oid, 'Odoo', 'create_lead')
        self.refresh_quotes(); self.refresh_orders(); self.set_status('Sipariş oluşturuldu')

    def copy_quote_message(self):
        rid = self.selected_id('quote'); r = db.get_row('quotes', rid) if rid else None
        if not r: return
        msg = f"Merhaba {r['customer_name']}, {r['title']} için ön teklifimiz {fmt_money(r['price'], self.settings.get('currency','TL'))}. Malzeme: {r['material']}. Tahmini baskı süresi: {r['time_min']} dk. Onayınızla üretime alabiliriz."
        self.copy(msg)

    # ---------- Catalog ----------
    def _catalog_page(self):
        root = self.page('Katalog')
        form = self.panel(root, 'MakerWorld / hazır katalog fiyatlayıcı')
        keys = ['cat_link','cat_title','cat_mat','cat_qty','cat_grams','cat_support','cat_time','cat_grams_basis','cat_time_basis','cat_record_id','cat_model_id']
        defaults = ['', '', 'PLA', '1', '0', '0', '0', 'Toplam', 'Toplam', '', '']
        for k, d in zip(keys, defaults): self.vars[k] = tk.StringVar(value=d)
        self.vars['cat_id_edit_mode'] = tk.BooleanVar(value=False)
        self.entry(form, 'MakerWorld Link', self.vars['cat_link'], 0, 0, width=48); self.entry(form, 'Başlık', self.vars['cat_title'], 0, 2, width=30)
        self.combo(form, 'Malzeme', self.vars['cat_mat'], MATERIALS, 1, 0); self.entry(form, 'Adet', self.vars['cat_qty'], 1, 2, width=8)
        self.entry(form, 'Gram', self.vars['cat_grams'], 1, 4, width=10); self.combo(form, 'Gram tipi', self.vars['cat_grams_basis'], ['Parça başı','Toplam'], 1, 6, width=12)
        self.entry(form, 'Destek g', self.vars['cat_support'], 2, 0, width=10); self.entry(form, 'Süre dk', self.vars['cat_time'], 2, 2, width=10); self.combo(form, 'Süre tipi', self.vars['cat_time_basis'], ['Toplam','Parça başı'], 2, 4, width=12)
        row = tk.Frame(form, bg=self.colors['card']); row.grid(row=3,column=0,columnspan=10,sticky='w',padx=4,pady=4)
        ttk.Button(row, text='Linkten Başlık/ID Çıkar', command=self.cat_autofill).pack(side='left', padx=3)
        ttk.Button(row, text='Fiyat Önizle', command=self.catalog_preview_price).pack(side='left', padx=3)
        ttk.Button(row, text='Kataloğa Ekle', style='Accent.TButton', command=self.add_catalog).pack(side='left', padx=3)
        ttk.Button(row, text='Seçileni Forma Al', command=self.load_catalog_form).pack(side='left', padx=3)
        ttk.Button(row, text='Güncelle', command=self.update_catalog).pack(side='left', padx=3)
        ttk.Button(row, text='Sil', command=lambda: self.delete_selected_row('catalog', 'catalog', self.refresh_catalog)).pack(side='left', padx=3)
        ttk.Button(row, text='Formu Temizle', command=self.clear_catalog_form).pack(side='left', padx=3)
        self.cat_result = ttk.Label(row, text='', style='Panel.TLabel'); self.cat_result.pack(side='left', padx=12)

        idrow = tk.Frame(form, bg=self.colors['card'])
        idrow.grid(row=4, column=0, columnspan=10, sticky='ew', padx=4, pady=(2, 6))
        ttk.Checkbutton(idrow, text='ID düzenleme modu', variable=self.vars['cat_id_edit_mode']).pack(side='left', padx=(0, 10))
        ttk.Label(idrow, text='Kayıt ID', style='Panel.TLabel').pack(side='left', padx=(0, 4))
        ttk.Entry(idrow, textvariable=self.vars['cat_record_id'], width=9).pack(side='left', padx=(0, 10))
        ttk.Label(idrow, text='Model ID', style='Panel.TLabel').pack(side='left', padx=(0, 4))
        ttk.Entry(idrow, textvariable=self.vars['cat_model_id'], width=18).pack(side='left', padx=(0, 10))
        ttk.Button(idrow, text='ID / Model ID Güncelle', command=self.update_catalog_ids).pack(side='left', padx=3)
        ttk.Label(idrow, text='Not: Kayıt ID sadece seçili üründe ve mod açıkken değişir.', style='Panel.TLabel').pack(side='left', padx=10)

        self.cat_tree = self.tree(root, ['id','model','title','mat','qty','grams','gbasis','time','tbasis','price','status'], {'id':'ID','model':'Model ID','title':'Başlık','mat':'Malzeme','qty':'Adet','grams':'g','gbasis':'Gram tipi','time':'dk','tbasis':'Süre tipi','price':'Fiyat','status':'Durum'}, height=18)
        self.bind_select(self.cat_tree, 'catalog')

    def cat_autofill(self):
        link = self.vars['cat_link'].get()
        model_id = extract_model_id(link) or ''
        if not self.vars['cat_title'].get(): self.vars['cat_title'].set(title_from_link(link))
        if not self.vars['cat_model_id'].get(): self.vars['cat_model_id'].set(model_id)
        self.cat_result.configure(text=f"Model ID: {model_id or 'bulunamadı'}")

    def _catalog_price_inputs(self):
        qty = max(inum(self.vars.get('cat_qty').get(), 1), 1)
        grams_raw = fnum(self.vars.get('cat_grams').get())
        support_raw = fnum(self.vars.get('cat_support').get())
        time_raw = fnum(self.vars.get('cat_time').get())
        grams_basis = self.vars.get('cat_grams_basis').get() if self.vars.get('cat_grams_basis') else 'Toplam'
        time_basis = self.vars.get('cat_time_basis').get() if self.vars.get('cat_time_basis') else 'Toplam'
        total_grams, total_support, total_time = self._catalog_totals(qty, grams_raw, support_raw, time_raw, grams_basis, time_basis)
        return qty, grams_raw, support_raw, time_raw, grams_basis, time_basis, total_grams, total_support, total_time

    def _is_piece_basis(self, value):
        return str(value or '').strip().lower().startswith('par')

    def _catalog_totals(self, qty, grams_raw, support_raw, time_raw, grams_basis, time_basis):
        qty = max(inum(qty, 1), 1)
        total_grams = fnum(grams_raw) * qty if self._is_piece_basis(grams_basis) else fnum(grams_raw)
        total_support = fnum(support_raw) * qty if self._is_piece_basis(grams_basis) else fnum(support_raw)
        total_time = fnum(time_raw) * qty if self._is_piece_basis(time_basis) else fnum(time_raw)
        return total_grams, total_support, total_time

    def _catalog_breakdown_for_row(self, row):
        qty = max(inum(row['quantity'], 1), 1)
        grams_basis = row['grams_basis'] if 'grams_basis' in row.keys() else 'Toplam'
        time_basis = row['time_basis'] if 'time_basis' in row.keys() else 'Toplam'
        total_grams, total_support, total_time = self._catalog_totals(
            qty, row['grams'], row['support_grams'], row['time_min'], grams_basis, time_basis
        )
        return calculate_price(self.settings, row['material'], total_grams, total_support, total_time, 1)

    def catalog_preview_price(self):
        qty, grams_raw, support_raw, time_raw, grams_basis, time_basis, total_grams, total_support, total_time = self._catalog_price_inputs()
        br = calculate_price(self.settings, self.vars['cat_mat'].get(), total_grams, total_support, total_time, 1)
        cur = self.settings.get('currency','TL')
        unit_price = br['total_price'] / qty if qty else br['total_price']
        warning = ''
        if qty > 1 and (self._is_piece_basis(grams_basis) or self._is_piece_basis(time_basis)) and (total_grams > 5000 or total_time > 3000):
            warning = '  ⚠ Değer çok büyüdü; MakerWorld/Bambu verisi toplam ise Gram/Süre tipini Toplam seç.'
        self.cat_result.configure(text=f"Toplam {fmt_money(br['total_price'], cur)} | Birim {fmt_money(unit_price, cur)} | {total_grams:g} g, {total_time:g} dk | Mod: gram={grams_basis}, süre={time_basis}{warning}")
        return br

    def add_catalog(self):
        qty, grams_raw, support_raw, time_raw, grams_basis, time_basis, total_grams, total_support, total_time = self._catalog_price_inputs()
        br = calculate_price(self.settings, self.vars['cat_mat'].get(), total_grams, total_support, total_time, 1)
        model_id = (self.vars['cat_model_id'].get().strip() or extract_model_id(self.vars['cat_link'].get()) or '')
        db.insert('catalog', {'makerworld_link': self.vars['cat_link'].get(), 'model_id': model_id,
                              'title': self.vars['cat_title'].get() or title_from_link(self.vars['cat_link'].get()), 'material': self.vars['cat_mat'].get(),
                              'grams': grams_raw, 'support_grams': support_raw, 'time_min': time_raw,
                              'grams_basis': grams_basis, 'time_basis': time_basis,
                              'quantity': qty, 'estimated_price': br['total_price'], 'cost_estimate': br['cost_estimate'], 'margin_amount': br['margin_amount']})
        self.catalog_preview_price()
        self.refresh_catalog(); self.set_status('Katalog ürünü eklendi')

    def refresh_catalog(self):
        self.clear_tree(self.cat_tree); cur=self.settings.get('currency','TL')
        for r in db.list_rows('catalog', order='id DESC', limit=500):
            self.cat_tree.insert('', 'end', iid=r['id'], values=(r['id'], r['model_id'], r['title'], r['material'], r['quantity'], r['grams'], (r['grams_basis'] if 'grams_basis' in r.keys() else 'Toplam'), r['time_min'], (r['time_basis'] if 'time_basis' in r.keys() else 'Toplam'), fmt_money(r['estimated_price'],cur), r['status']))

    # ---------- Orders ----------
    def _orders_page(self):
        root = self.page('Siparişler')
        bar = self.panel(root, 'Sipariş işlemleri')
        ttk.Button(bar, text='Seçili siparişten üretim işi oluştur', style='Accent.TButton', command=self.order_to_job).pack(side='left', padx=3)
        ttk.Button(bar, text='Düzenle', command=self.edit_order).pack(side='left', padx=3)
        ttk.Button(bar, text='Sil', command=lambda: self.delete_selected_row('orders', 'order', self.refresh_orders)).pack(side='left', padx=3)
        ttk.Button(bar, text='Durumu Teslim Edildi Yap', command=lambda: self.update_order_status('Teslim Edildi')).pack(side='left', padx=3)
        self.order_tree = self.tree(root, ['id','customer','item','mat','qty','price','pay','status','due'], {'id':'ID','customer':'Müşteri','item':'Ürün','mat':'Malzeme','qty':'Adet','price':'Fiyat','pay':'Ödeme','status':'Durum','due':'Teslim'}, height=20)
        self.bind_select(self.order_tree, 'order')

    def refresh_orders(self):
        self.clear_tree(self.order_tree); cur=self.settings.get('currency','TL')
        for r in db.list_rows('orders', order='id DESC', limit=500):
            self.order_tree.insert('', 'end', iid=r['id'], values=(r['id'], r['customer_name'], r['item_name'], r['material'], r['quantity'], fmt_money(r['price'],cur), r['payment_status'], r['status'], r['due_date']))

    def order_to_job(self):
        rid = self.selected_id('order')
        if not rid: return
        r = db.get_row('orders', rid)
        jid = db.insert('production_jobs', {'order_id': rid, 'job_name': r['item_name'], 'material': r['material'], 'grams': r['grams'], 'support_grams': r['support_grams'], 'time_min': r['time_min'], 'status':'Baskıya Hazır'})
        db.update('orders', rid, {'status':'Baskıya Hazır'}); db.log_event('Üretim işi oluşturuldu', f'Job #{jid}')
        self.refresh_orders(); self.refresh_jobs()

    def update_order_status(self, status):
        rid = self.selected_id('order')
        if rid: db.update('orders', rid, {'status': status}); self.refresh_orders()

    # ---------- Production ----------
    def _production_page(self):
        root = self.page('Üretim')
        bar = self.panel(root, 'Üretim kuyruğu')
        ttk.Button(bar, text='Baskıya Al', command=lambda: self.update_job_status('Baskıda')).pack(side='left', padx=3)
        ttk.Button(bar, text='Tamamla ve Stoktan Düş', style='Accent.TButton', command=self.complete_job).pack(side='left', padx=3)
        ttk.Button(bar, text='Düzenle', command=self.edit_job).pack(side='left', padx=3)
        ttk.Button(bar, text='Sil', command=lambda: self.delete_selected_row('production_jobs', 'job', self.refresh_jobs)).pack(side='left', padx=3)
        ttk.Button(bar, text='Başarısız İşaretle', command=lambda: self.update_job_status('Başarısız')).pack(side='left', padx=3)
        self.job_tree = self.tree(root, ['id','order','job','printer','mat','grams','time','priority','status'], {'id':'ID','order':'Sipariş','job':'İş','printer':'Yazıcı','mat':'Malzeme','grams':'g','time':'dk','priority':'Öncelik','status':'Durum'}, height=20)
        self.bind_select(self.job_tree, 'job')

    def refresh_jobs(self):
        self.clear_tree(self.job_tree)
        for r in db.list_rows('production_jobs', order='id DESC', limit=500):
            self.job_tree.insert('', 'end', iid=r['id'], values=(r['id'], r['order_id'], r['job_name'], r['printer'], r['material'], r['grams']+r['support_grams'], r['time_min'], r['priority'], r['status']))

    def update_job_status(self, status):
        rid = self.selected_id('job')
        if rid: db.update('production_jobs', rid, {'status': status}); self.refresh_jobs()

    def complete_job(self):
        rid = self.selected_id('job')
        if not rid: return
        r = db.get_row('production_jobs', rid)
        mat = r['material']; grams = fnum(r['grams']) + fnum(r['support_grams'])
        stocks = db.list_rows('inventory', 'material=?', (mat,), order='current_qty DESC', limit=1)
        if stocks:
            s = stocks[0]
            db.update('inventory', s['id'], {'current_qty': max(fnum(s['current_qty']) - grams, 0)})
        db.update('production_jobs', rid, {'status':'Tamamlandı', 'completed_at': db.now()})
        if r['order_id']: db.update('orders', r['order_id'], {'status':'Son İşlem'})
        db.log_event('Üretim tamamlandı', f'{r["job_name"]} | {grams} g stoktan düşüldü')
        self.refresh_jobs(); self.refresh_inventory(); self.refresh_orders()

    # ---------- Inventory ----------
    def _inventory_page(self):
        root = self.page('Stok')
        form = self.panel(root, 'Stok kartı')
        for k,d in [('inv_item',''),('inv_cat','Filament'),('inv_mat','PLA'),('inv_color',''),('inv_qty','1000'),('inv_min','200'),('inv_cost','0.65')]: self.vars[k]=tk.StringVar(value=d)
        self.entry(form,'Ürün',self.vars['inv_item'],0,0); self.entry(form,'Kategori',self.vars['inv_cat'],0,2); self.combo(form,'Malzeme',self.vars['inv_mat'],MATERIALS,0,4)
        self.entry(form,'Renk',self.vars['inv_color'],1,0); self.entry(form,'Miktar',self.vars['inv_qty'],1,2); self.entry(form,'Min',self.vars['inv_min'],1,4); self.entry(form,'Birim maliyet',self.vars['inv_cost'],1,6)
        btnrow = tk.Frame(form, bg=self.colors['card']); btnrow.grid(row=2,column=0,columnspan=8,sticky='w',padx=4,pady=4)
        ttk.Button(btnrow,text='Stok Ekle',style='Accent.TButton',command=self.add_inventory).pack(side='left',padx=3)
        ttk.Button(btnrow,text='Seçileni Forma Al',command=self.load_inventory_form).pack(side='left',padx=3)
        ttk.Button(btnrow,text='Stok Güncelle',command=self.update_inventory).pack(side='left',padx=3)
        ttk.Button(btnrow,text='Sil',command=lambda: self.delete_selected_row('inventory', 'inventory', self.refresh_inventory)).pack(side='left',padx=3)
        ttk.Button(btnrow,text='Birim Maliyeti Fiyatlamaya Aktar',command=self.inventory_cost_to_pricing).pack(side='left',padx=3)
        ttk.Button(btnrow,text='Formu Temizle',command=self.clear_inventory_form).pack(side='left',padx=3)
        self.inv_tree = self.tree(root, ['id','item','cat','mat','color','qty','min','cost'], {'id':'ID','item':'Ürün','cat':'Kategori','mat':'Malzeme','color':'Renk','qty':'Mevcut','min':'Min','cost':'Birim maliyet'}, height=18)
        self.bind_select(self.inv_tree,'inventory', lambda: None)

    def add_inventory(self):
        db.insert('inventory', {'item': self.vars['inv_item'].get(), 'category': self.vars['inv_cat'].get(), 'material': self.vars['inv_mat'].get(), 'color': self.vars['inv_color'].get(), 'current_qty': fnum(self.vars['inv_qty'].get()), 'min_qty': fnum(self.vars['inv_min'].get()), 'unit_cost': fnum(self.vars['inv_cost'].get())})
        self.refresh_inventory()

    def refresh_inventory(self):
        self.clear_tree(self.inv_tree)
        for r in db.list_rows('inventory', order='id DESC', limit=500):
            self.inv_tree.insert('', 'end', iid=r['id'], values=(r['id'],r['item'],r['category'],r['material'],r['color'],r['current_qty'],r['min_qty'],r['unit_cost']))

    # ---------- Customers ----------

    # ---------- Global record ID / sort manager ----------
    def _record_manager_page(self):
        root = self.page('Kayıt Sıralama')
        info = self.panel(root, 'Global ID ve sıralama merkezi')
        tk.Label(info, text='Bu ekran bütün ana tablolar için ID ve sıralama düzeltme merkezidir. Normal kayıt düzenlemeleri kendi menüsünde yapılır; burada kayıt ID, sıra ve liste konumu güvenli şekilde yönetilir.', bg=self.colors['card'], fg=self.colors['muted'], wraplength=1100, justify='left', font=('Segoe UI', 10)).pack(anchor='w')
        form = self.panel(root, 'Kayıt seçimi ve güvenli düzenleme')
        self.vars['rm_module'] = tk.StringVar(value='Katalog')
        self.vars['rm_current_id'] = tk.StringVar(value='')
        self.vars['rm_new_id'] = tk.StringVar(value='')
        self.vars['rm_sort_order'] = tk.StringVar(value='')
        self.vars['rm_confirm'] = tk.BooleanVar(value=False)
        self.combo(form, 'Modül', self.vars['rm_module'], list(GLOBAL_RECORD_TABLES.keys()), 0, 0, width=22)
        ttk.Button(form, text='Listeyi Yenile', command=self.refresh_record_manager).grid(row=0, column=2, sticky='w', padx=4, pady=4)
        self.entry(form, 'Seçili ID', self.vars['rm_current_id'], 1, 0, width=12)
        self.entry(form, 'Yeni ID', self.vars['rm_new_id'], 1, 2, width=12)
        self.entry(form, 'Sıra değeri', self.vars['rm_sort_order'], 1, 4, width=12)
        ttk.Checkbutton(form, text='ID değişimini onaylıyorum', variable=self.vars['rm_confirm']).grid(row=1, column=6, sticky='w', padx=8, pady=4)
        btns = tk.Frame(form, bg=self.colors['card']); btns.grid(row=2, column=0, columnspan=8, sticky='w', padx=4, pady=8)
        ttk.Button(btns, text='Seçileni Forma Al', command=self.load_record_manager_selection).pack(side='left', padx=3)
        ttk.Button(btns, text='ID Değiştir', command=self.record_manager_change_id).pack(side='left', padx=3)
        ttk.Button(btns, text='Sıra Kaydet', command=self.record_manager_save_sort).pack(side='left', padx=3)
        ttk.Button(btns, text='Yukarı Taşı', command=lambda: self.record_manager_move('up')).pack(side='left', padx=3)
        ttk.Button(btns, text='Aşağı Taşı', command=lambda: self.record_manager_move('down')).pack(side='left', padx=3)
        ttk.Button(btns, text='En Üste Al', style='Accent.TButton', command=lambda: self.record_manager_move('top')).pack(side='left', padx=3)
        ttk.Button(btns, text='En Alta Al', command=lambda: self.record_manager_move('bottom')).pack(side='left', padx=3)
        ttk.Button(btns, text='Bu Kaydı Aç', command=self.record_manager_open_module).pack(side='left', padx=3)
        warn = tk.Label(form, text='Sıralama: sort değeri büyük olan üstte görünür. ID değişimi ilişki bulunan alanlarda otomatik taşınır ama yine de dikkatli kullanılmalıdır.', bg=self.colors['card'], fg=self.colors['warning'], font=('Segoe UI', 9), wraplength=1000, justify='left')
        warn.grid(row=3, column=0, columnspan=8, sticky='w', padx=4, pady=(0, 4))
        self.record_tree = self.tree(root, ['id','sort','title','detail','status','created','updated'], {'id':'ID','sort':'Sıra','title':'Başlık','detail':'Detay','status':'Durum/Kategori','created':'Oluşturma','updated':'Güncelleme'}, height=18)
        self.bind_select(self.record_tree, 'record_manager', self.load_record_manager_selection)
        self.vars['rm_module'].trace_add('write', lambda *_: self.refresh_record_manager())

    def _record_meta(self):
        return GLOBAL_RECORD_TABLES.get(self.vars.get('rm_module', tk.StringVar(value='Katalog')).get(), GLOBAL_RECORD_TABLES['Katalog'])

    def _row_value(self, row, col, default=''):
        try:
            if col and col in row.keys():
                return row[col]
        except Exception:
            pass
        return default

    def refresh_record_manager(self):
        if not hasattr(self, 'record_tree'):
            return
        self.clear_tree(self.record_tree)
        meta = self._record_meta(); table = meta['table']
        try:
            rows = db.list_rows(table, order='sort_order DESC, id DESC', limit=1000)
        except Exception as exc:
            self.set_status(f'Kayıt merkezi hata: {exc}')
            return
        for r in rows:
            title = self._row_value(r, meta.get('title'), '')
            detail = self._row_value(r, meta.get('detail'), '')
            status = self._row_value(r, meta.get('status'), '')
            sort_order = self._row_value(r, 'sort_order', r['id'])
            created = self._row_value(r, 'created_at', '')
            updated = self._row_value(r, 'updated_at', '')
            self.record_tree.insert('', 'end', iid=r['id'], values=(r['id'], sort_order, title, detail, status, created, updated))
        self.set_status(f'{self.vars["rm_module"].get()} kayıtları listelendi')

    def load_record_manager_selection(self):
        rid = self.selected_id('record_manager')
        if not rid:
            return
        meta = self._record_meta()
        r = db.get_row(meta['table'], rid)
        if not r:
            return
        self.vars['rm_current_id'].set(str(r['id']))
        self.vars['rm_new_id'].set(str(r['id']))
        self.vars['rm_sort_order'].set(str(self._row_value(r, 'sort_order', r['id'])))

    def _refresh_related_module(self, meta):
        try:
            fn = getattr(self, meta.get('refresh', ''), None)
            if fn:
                fn()
        except Exception:
            logging.exception('Related module refresh failed')
        try:
            self.refresh_record_manager()
        except Exception:
            pass

    def record_manager_change_id(self):
        meta = self._record_meta(); table = meta['table']
        old_raw = self.vars['rm_current_id'].get().strip(); new_raw = self.vars['rm_new_id'].get().strip()
        if not old_raw or not new_raw:
            return messagebox.showwarning('Eksik bilgi', 'Eski ve yeni ID alanlarını doldur.')
        try:
            old_id = int(old_raw); new_id = int(new_raw)
        except Exception:
            return messagebox.showwarning('Geçersiz ID', 'ID değerleri tam sayı olmalı.')
        if old_id == new_id:
            return messagebox.showinfo('Değişiklik yok', 'Yeni ID mevcut ID ile aynı.')
        if not self.vars['rm_confirm'].get():
            return messagebox.showinfo('Onay gerekli', 'ID değiştirmek için “ID değişimini onaylıyorum” kutusunu işaretle.')
        if not messagebox.askyesno('ID değiştirilsin mi?', f'{self.vars["rm_module"].get()} kaydı #{old_id}, #{new_id} yapılacak. Devam edilsin mi?'):
            return
        try:
            db.change_record_id(table, old_id, new_id)
            self.selected[meta['key']] = new_id
            self.selected['record_manager'] = new_id
            self.vars['rm_current_id'].set(str(new_id)); self.vars['rm_new_id'].set(str(new_id)); self.vars['rm_confirm'].set(False)
            self._refresh_related_module(meta)
            self.set_status('ID güncellendi')
        except Exception as exc:
            messagebox.showerror('ID güncelleme hatası', str(exc))

    def record_manager_save_sort(self):
        meta = self._record_meta(); table = meta['table']
        rid = self.selected_id('record_manager') or inum(self.vars['rm_current_id'].get(), 0)
        if not rid:
            return messagebox.showwarning('Seçim yok', 'Önce kayıt seç.')
        try:
            sort_order = float(str(self.vars['rm_sort_order'].get()).replace(',', '.'))
            db.set_record_sort_order(table, rid, sort_order)
            self._refresh_related_module(meta)
            self.set_status('Sıra değeri kaydedildi')
        except Exception as exc:
            messagebox.showerror('Sıra hatası', str(exc))

    def record_manager_move(self, direction):
        meta = self._record_meta(); table = meta['table']
        rid = self.selected_id('record_manager') or inum(self.vars['rm_current_id'].get(), 0)
        if not rid:
            return messagebox.showwarning('Seçim yok', 'Önce kayıt seç.')
        try:
            db.move_record(table, rid, direction)
            self._refresh_related_module(meta)
            self.set_status('Sıralama güncellendi')
        except Exception as exc:
            messagebox.showerror('Sıralama hatası', str(exc))

    def record_manager_open_module(self):
        meta = self._record_meta(); module = self.vars['rm_module'].get()
        rid = self.selected_id('record_manager') or inum(self.vars['rm_current_id'].get(), 0)
        if rid:
            self.selected[meta['key']] = rid
        self.show_page(module)
        self.set_status(f'{module} ekranına geçildi')


    # ---------- Raw material price center ----------
    def _raw_material_price_page(self):
        root = self.page('Hammadde Fiyat Merkezi')
        head = self.panel(root, 'Tek merkezden hammadde fiyatları')
        tk.Label(head, text='PLA, PETG, ABS, ASA, TPU ve Support maliyetlerini buradan değiştir. Kaydettiğinde fiyatlama motoru, katalog, teklif ve stok maliyetleri yeni değerleri kullanır.', bg=self.colors['card'], fg=self.colors['muted'], wraplength=1150, justify='left', font=('Segoe UI', 10)).pack(anchor='w')
        self.raw_price_vars = {}
        form = self.panel(root, 'Malzeme + operasyon fiyatları - tüm uygulamaya işler')
        materials = [('pla_cost_kg','PLA','PLA filament'), ('petg_cost_kg','PETG','PETG filament'), ('abs_cost_kg','ABS','ABS filament'), ('asa_cost_kg','ASA','ASA filament'), ('tpu_cost_kg','TPU','TPU filament'), ('support_cost_kg','SUPPORT','Destek filament')]
        for i, (key, mat, label) in enumerate(materials):
            self.raw_price_vars[key] = tk.StringVar(value=self.settings.get(key, '0'))
            self.entry(form, f'{label} TL/kg', self.raw_price_vars[key], i//2, (i%2)*2, width=18)

        sep = tk.Label(form, text='Operasyon ve satış ayarları', bg=self.colors['card'], fg=self.colors['accent'], font=('Segoe UI', 10, 'bold'))
        sep.grid(row=3, column=0, columnspan=4, sticky='w', padx=4, pady=(10, 4))
        ops = [
            ('machine_hour_rate', 'Makine saat ücreti', '60'),
            ('minimum_price', 'Minimum fiyat', '250'),
            ('labor_fee', 'İşçilik', '60'),
            ('post_process_fee', 'Son işlem', '40'),
            ('packaging_fee', 'Paketleme', '25'),
            ('failure_rate', 'Fire / başarısız baskı payı', '0.12'),
            ('vat_rate', 'KDV', '0.20'),
            ('commission_rate', 'Komisyon', '0'),
            ('profit_rate', 'Kâr oranı', '0.70'),
        ]
        for j, (key, label, default) in enumerate(ops):
            self.raw_price_vars[key] = tk.StringVar(value=self.settings.get(key, default))
            self.entry(form, label, self.raw_price_vars[key], 4 + (j // 2), (j % 2) * 2, width=18)
        hint = tk.Label(form, text='Oran alanları yüzde değil katsayıdır: 0.12 = %12, 0.20 = %20, 0.70 = %70. 70 yazma, fiyatı uçurur.', bg=self.colors['card'], fg=self.colors['muted'], font=('Segoe UI', 9), wraplength=900, justify='left')
        hint.grid(row=9, column=0, columnspan=4, sticky='w', padx=4, pady=(4, 2))
        row = tk.Frame(form, bg=self.colors['card']); row.grid(row=10, column=0, columnspan=4, sticky='w', padx=4, pady=8)
        ttk.Button(row, text='Hammadde Fiyatlarını Kaydet ve Uygula', style='Accent.TButton', command=self.save_raw_material_prices).pack(side='left', padx=3)
        ttk.Button(row, text='Stoktan Birim Maliyetleri Yeniden Hesapla', command=self.apply_raw_prices_to_inventory).pack(side='left', padx=3)
        ttk.Button(row, text='Fiyat Önizle', command=self.preview_raw_material_price).pack(side='left', padx=3)
        ttk.Button(row, text='Varsayılanları Geri Yükle', command=self.restore_default_cost_items).pack(side='left', padx=3)
        mid = tk.Frame(root, bg=self.colors['bg']); mid.pack(fill='both', expand=True, pady=6)
        left = self.panel(mid, 'Aktif hammadde maliyetleri', fill='both', expand=True, side='left', padx=(0,6))
        right = self.panel(mid, 'Örnek fiyat hesabı', fill='both', expand=True, side='left', padx=(6,0))
        self.raw_tree = self.tree(left, ['material','kg','gram','stock','used'], {'material':'Malzeme','kg':'TL/kg','gram':'TL/g','stock':'Stok g','used':'Fiyatlamada'}, height=10)
        self.raw_preview = scrolledtext.ScrolledText(right, height=12, bg=self.colors['card_alt'], fg=self.colors['ink'], insertbackground=self.colors['ink'], font=('Consolas',10))
        self.raw_preview.pack(fill='both', expand=True, padx=4, pady=4)

    def _upsert_cost_setting(self, key, name, group_name, unit, value, notes=''):
        value = fnum(value)
        db.save_setting(key, value)
        self.settings[key] = str(value)
        rows = db.list_rows('cost_items', 'setting_key=?', (key,), limit=1)
        if rows:
            db.update('cost_items', rows[0]['id'], {'name': name, 'group_name': group_name, 'unit': unit, 'value': value, 'active': 1, 'notes': notes})
        else:
            db.insert('cost_items', {'setting_key': key, 'name': name, 'group_name': group_name, 'unit': unit, 'value': value, 'active': 1, 'notes': notes})

    def save_raw_material_prices(self):
        mapping = {
            'pla_cost_kg': ('PLA', 'PLA filament kg maliyeti'),
            'petg_cost_kg': ('PETG', 'PETG filament kg maliyeti'),
            'abs_cost_kg': ('ABS', 'ABS filament kg maliyeti'),
            'asa_cost_kg': ('ASA', 'ASA filament kg maliyeti'),
            'tpu_cost_kg': ('TPU', 'TPU filament kg maliyeti'),
            'support_cost_kg': ('SUPPORT', 'Support filament kg maliyeti'),
        }
        for key, (mat, label) in mapping.items():
            self._upsert_cost_setting(key, label, 'Malzeme', 'TL/kg', self.raw_price_vars[key].get(), f'{mat} fiyat merkezi üzerinden güncellendi')
        operation_items = [
            ('machine_hour_rate', 'Makine saat ücreti', 'Operasyon', 'TL/saat'),
            ('minimum_price', 'Minimum fiyat', 'Satış', 'TL'),
            ('labor_fee', 'İşçilik', 'Operasyon', 'TL'),
            ('post_process_fee', 'Son işlem', 'Operasyon', 'TL'),
            ('packaging_fee', 'Paketleme', 'Operasyon', 'TL'),
            ('failure_rate', 'Fire / başarısız baskı payı', 'Risk', 'oran'),
            ('vat_rate', 'KDV', 'Vergi', 'oran'),
            ('commission_rate', 'Komisyon', 'Satış', 'oran'),
            ('profit_rate', 'Kâr oranı', 'Satış', 'oran'),
        ]
        for key, name, group_name, unit in operation_items:
            self._upsert_cost_setting(key, name, group_name, unit, self.raw_price_vars[key].get(), 'Fiyat merkezi üzerinden güncellendi')
        self.apply_raw_prices_to_inventory(silent=True)
        updated = self.recalculate_saved_prices()
        if hasattr(self, 'setting_vars'):
            for k, v in self.raw_price_vars.items():
                if k in self.setting_vars:
                    self.setting_vars[k].set(v.get())
        self.refresh_raw_material_center()
        self.refresh_cost_items()
        self.set_status('Hammadde fiyatları tüm fiyatlama motoruna işlendi')
        messagebox.showinfo('Hammadde Fiyat Merkezi', f'Fiyatlar kaydedildi. {updated} kayıt yeni maliyetlerle yeniden hesaplandı.')

    def recalculate_saved_prices(self):
        updated = 0
        for r in db.list_rows('catalog', order='id ASC', limit=10000):
            br = self._catalog_breakdown_for_row(r)
            db.update('catalog', r['id'], {
                'estimated_price': br['total_price'],
                'cost_estimate': br['cost_estimate'],
                'margin_amount': br['margin_amount'],
            })
            updated += 1
        for table in ('quotes', 'orders'):
            for r in db.list_rows(table, order='id ASC', limit=10000):
                br = calculate_price(
                    self.settings,
                    r['material'],
                    r['grams'],
                    r['support_grams'],
                    r['time_min'],
                    r['quantity'],
                    r['design_minutes'] if table == 'quotes' and 'design_minutes' in r.keys() else 0,
                )
                data = {'price': br['total_price'], 'cost_estimate': br['cost_estimate']}
                if 'margin_amount' in r.keys():
                    data['margin_amount'] = br['margin_amount']
                db.update(table, r['id'], data)
                updated += 1
        for refresh in (self.refresh_catalog, self.refresh_quotes, self.refresh_orders):
            try:
                refresh()
            except Exception:
                logging.exception('Saved price refresh failed')
        db.log_event('Fiyatlar yeniden hesaplandı', f'{updated} katalog/teklif/sipariş kaydı güncellendi')
        return updated

    def apply_raw_prices_to_inventory(self, silent=False):
        material_to_key = {'PLA':'pla_cost_kg','PETG':'petg_cost_kg','ABS':'abs_cost_kg','ASA':'asa_cost_kg','TPU':'tpu_cost_kg','SUPPORT':'support_cost_kg'}
        updated = 0
        for mat, key in material_to_key.items():
            kg = fnum(self.raw_price_vars[key].get() if hasattr(self, 'raw_price_vars') and key in self.raw_price_vars else self.settings.get(key,0))
            gram_cost = kg / 1000.0
            for r in db.list_rows('inventory', 'UPPER(material)=?', (mat,), limit=1000):
                db.update('inventory', r['id'], {'unit_cost': gram_cost})
                updated += 1
        self.refresh_inventory()
        if not silent:
            self.refresh_raw_material_center()
            messagebox.showinfo('Stok güncellendi', f'{updated} stok kartının birim maliyeti güncellendi.')

    def preview_raw_material_price(self):
        temp = dict(self.settings)
        if hasattr(self, 'raw_price_vars'):
            for k,v in self.raw_price_vars.items():
                temp[k]=v.get()
        br = calculate_price(temp, 'PLA', 100, 0, 120, 1)
        txt = (
            'Örnek PLA hesap: 100 g, 120 dk, 1 adet\n'
            f"Minimum fiyat: {temp.get('minimum_price', '250')} TL | İşçilik: {temp.get('labor_fee', '60')} TL | Son işlem: {temp.get('post_process_fee', '40')} TL | Paketleme: {temp.get('packaging_fee', '25')} TL\n"
            f"Fire: {temp.get('failure_rate', '0.12')} | KDV: {temp.get('vat_rate', '0.20')} | Komisyon: {temp.get('commission_rate', '0')} | Kâr: {temp.get('profit_rate', '0.70')}\n\n"
            + format_breakdown(br, temp.get('currency','TL'))
        )
        if hasattr(self, 'raw_preview'):
            self.raw_preview.delete('1.0','end'); self.raw_preview.insert('end', txt)
        else:
            messagebox.showinfo('Fiyat önizleme', txt)

    def refresh_raw_material_center(self):
        if not hasattr(self, 'raw_tree'):
            return
        self.clear_tree(self.raw_tree)
        rows = db.list_rows('inventory', order='material, color', limit=500)
        stock = {}
        for r in rows:
            mat = (r['material'] or '').upper()
            stock[mat] = stock.get(mat, 0) + fnum(r['current_qty'])
        pairs = [('PLA','pla_cost_kg'),('PETG','petg_cost_kg'),('ABS','abs_cost_kg'),('ASA','asa_cost_kg'),('TPU','tpu_cost_kg'),('SUPPORT','support_cost_kg')]
        for mat, key in pairs:
            kg = fnum(self.settings.get(key, 0))
            self.raw_tree.insert('', 'end', values=(mat, f'{kg:.2f}', f'{kg/1000:.4f}', f'{stock.get(mat,0):.1f}', key))
            if hasattr(self, 'raw_price_vars') and key in self.raw_price_vars:
                self.raw_price_vars[key].set(str(self.settings.get(key, '0')))

    def _customers_page(self):
        root = self.page('Müşteriler')
        form = self.panel(root,'Müşteri ekle')
        for k in ['cust_name','cust_phone','cust_email','cust_instagram']: self.vars[k]=tk.StringVar()
        self.entry(form,'Ad',self.vars['cust_name'],0,0); self.entry(form,'Telefon',self.vars['cust_phone'],0,2); self.entry(form,'E-posta',self.vars['cust_email'],0,4); self.entry(form,'Instagram',self.vars['cust_instagram'],0,6)
        crow=tk.Frame(form,bg=self.colors['card']); crow.grid(row=1,column=0,columnspan=8,sticky='w',padx=4,pady=4)
        ttk.Button(crow,text='Müşteri Ekle',style='Accent.TButton',command=self.add_customer).pack(side='left',padx=3)
        ttk.Button(crow,text='Seçileni Forma Al',command=self.load_customer_form).pack(side='left',padx=3)
        ttk.Button(crow,text='Güncelle',command=self.update_customer).pack(side='left',padx=3)
        ttk.Button(crow,text='Sil',command=lambda: self.delete_selected_row('customers', 'customer', self.refresh_customers)).pack(side='left',padx=3)
        ttk.Button(crow,text='Formu Temizle',command=self.clear_customer_form).pack(side='left',padx=3)
        self.cust_tree = self.tree(root, ['id','name','phone','email','ig','created'], {'id':'ID','name':'Ad','phone':'Telefon','email':'E-posta','ig':'Instagram','created':'Tarih'}, height=20)
        self.bind_select(self.cust_tree, 'customer')

    def add_customer(self):
        db.insert('customers', {'name':self.vars['cust_name'].get(), 'phone':self.vars['cust_phone'].get(), 'email':self.vars['cust_email'].get(), 'instagram':self.vars['cust_instagram'].get()})
        self.refresh_customers()

    def refresh_customers(self):
        self.clear_tree(self.cust_tree)
        for r in db.list_rows('customers', order='id DESC', limit=500): self.cust_tree.insert('', 'end', iid=r['id'], values=(r['id'],r['name'],r['phone'],r['email'],r['instagram'],r['created_at']))

    # ---------- Messages ----------
    def _messages_page(self):
        root = self.page('Mesajlar')
        form = self.panel(root, 'Hazır mesaj şablonları')
        self.vars['tpl_name']=tk.StringVar(); self.vars['tpl_channel']=tk.StringVar(value='WhatsApp')
        self.entry(form,'Ad',self.vars['tpl_name'],0,0); self.combo(form,'Kanal',self.vars['tpl_channel'],['WhatsApp','Email','Instagram'],0,2)
        self.tpl_body=scrolledtext.ScrolledText(form,height=4,font=('Segoe UI',9)); self.tpl_body.grid(row=1,column=0,columnspan=4,sticky='ew',padx=4,pady=4)
        trow=tk.Frame(form,bg=self.colors['card']); trow.grid(row=2,column=0,columnspan=4,sticky='w',padx=4,pady=4)
        ttk.Button(trow,text='Şablon Ekle',style='Accent.TButton',command=self.add_template).pack(side='left',padx=3)
        ttk.Button(trow,text='Seçileni Forma Al',command=self.load_template_form).pack(side='left',padx=3)
        ttk.Button(trow,text='Güncelle',command=self.update_template).pack(side='left',padx=3)
        ttk.Button(trow,text='Sil',command=lambda: self.delete_selected_row('message_templates', 'template', self.refresh_templates)).pack(side='left',padx=3)
        ttk.Button(trow,text='Formu Temizle',command=self.clear_template_form).pack(side='left',padx=3)
        self.tpl_tree = self.tree(root, ['id','name','channel','body'], {'id':'ID','name':'Ad','channel':'Kanal','body':'Metin'}, height=18)
        self.bind_select(self.tpl_tree, 'template')
        ttk.Button(root,text='Seçili şablonu panoya kopyala',command=self.copy_template).pack(anchor='w',pady=4)

    def add_template(self):
        db.insert('message_templates', {'name':self.vars['tpl_name'].get(), 'channel':self.vars['tpl_channel'].get(), 'body':self.tpl_body.get('1.0','end').strip()})
        self.refresh_templates()

    def refresh_templates(self):
        self.clear_tree(self.tpl_tree)
        for r in db.list_rows('message_templates', order='id DESC', limit=500): self.tpl_tree.insert('', 'end', iid=r['id'], values=(r['id'],r['name'],r['channel'],r['body'][:120]))

    def copy_template(self):
        rid=self.selected_id('template'); r=db.get_row('message_templates',rid) if rid else None
        if r: self.copy(r['body'])


    # ---------- CRUD / Edit helpers ----------
    def delete_selected_row(self, table, key, refresh_callback, label='kayıt'):
        rid = self.selected_id(key)
        if not rid:
            return messagebox.showwarning('Seçim yok', 'Önce silinecek kaydı seç tennim.')
        if not messagebox.askyesno('Silme onayı', f'#{rid} numaralı {label} silinsin mi? Bu işlem geri alınamaz.'):
            return
        db.delete_row(table, rid)
        self.selected[key] = None
        refresh_callback()
        self.set_status(f'#{rid} kaydı silindi')

    def edit_record_dialog(self, table, key, fields, title, on_save=None):
        rid = self.selected_id(key)
        if not rid:
            return messagebox.showwarning('Seçim yok', 'Önce düzenlenecek kaydı seç tennim.')
        row = db.get_row(table, rid)
        if not row:
            return messagebox.showerror('Bulunamadı', 'Seçili kayıt veritabanında bulunamadı.')
        win = tk.Toplevel(self)
        win.title(title)
        win.configure(bg=self.colors['bg'])
        self._center_window(win, 760, 620)
        frm = tk.Frame(win, bg=self.colors['card'], padx=14, pady=14)
        frm.pack(fill='both', expand=True, padx=12, pady=12)
        widgets = {}
        vars_ = {}
        rindex = 0
        for col, label, kind, values in fields:
            tk.Label(frm, text=label, bg=self.colors['card'], fg=self.colors['ink'], font=('Segoe UI', 9, 'bold')).grid(row=rindex, column=0, sticky='nw', padx=5, pady=5)
            if kind == 'text':
                w = scrolledtext.ScrolledText(frm, height=5, width=54, font=('Segoe UI', 9))
                w.insert('1.0', str(row[col] if row[col] is not None else ''))
                w.grid(row=rindex, column=1, sticky='ew', padx=5, pady=5)
                widgets[col] = w
            elif kind == 'combo':
                v = tk.StringVar(value=str(row[col] if row[col] is not None else ''))
                w = ttk.Combobox(frm, textvariable=v, values=values or [], state='readonly', width=34)
                w.grid(row=rindex, column=1, sticky='ew', padx=5, pady=5)
                vars_[col] = v
            else:
                v = tk.StringVar(value=str(row[col] if row[col] is not None else ''))
                w = ttk.Entry(frm, textvariable=v, width=38)
                w.grid(row=rindex, column=1, sticky='ew', padx=5, pady=5)
                vars_[col] = v
            rindex += 1
        frm.columnconfigure(1, weight=1)
        def _save():
            data = {}
            for col, label, kind, values in fields:
                if kind == 'text':
                    data[col] = widgets[col].get('1.0', 'end').strip()
                elif kind == 'float':
                    data[col] = fnum(vars_[col].get())
                elif kind == 'int':
                    data[col] = inum(vars_[col].get(), 0)
                else:
                    data[col] = vars_[col].get()
            if on_save:
                extra = on_save(row, data) or {}
                data.update(extra)
            db.update(table, rid, data)
            win.destroy()
            self.refresh_all()
            self.set_status(f'{title} kaydedildi')
        bar = tk.Frame(frm, bg=self.colors['card'])
        bar.grid(row=rindex, column=0, columnspan=2, sticky='e', pady=(10, 0))
        ttk.Button(bar, text='Kaydet', style='Accent.TButton', command=_save).pack(side='right', padx=4)
        ttk.Button(bar, text='Vazgeç', command=win.destroy).pack(side='right', padx=4)

    def edit_quote(self):
        def recalc(_old, data):
            br = calculate_price(self.settings, data.get('material'), data.get('grams'), data.get('support_grams'), data.get('time_min'), data.get('quantity'), data.get('design_minutes'))
            return {'cost_estimate': br['cost_estimate'], 'price': br['total_price'], 'margin_amount': br['margin_amount']}
        self.edit_record_dialog('quotes', 'quote', [
            ('customer_name','Müşteri','str',None), ('title','Başlık','str',None), ('material','Malzeme','combo',MATERIALS),
            ('color','Renk','str',None), ('grams','Gram','float',None), ('support_grams','Destek g','float',None),
            ('time_min','Süre dk','float',None), ('quantity','Adet','int',None), ('design_minutes','Modelleme dk','float',None),
            ('status','Durum','combo',QUOTE_STATUSES), ('notes','Not','text',None)
        ], 'Teklif Düzenle', recalc)

    def edit_order(self):
        self.edit_record_dialog('orders', 'order', [
            ('customer_name','Müşteri','str',None), ('item_name','Ürün','str',None), ('material','Malzeme','combo',MATERIALS),
            ('grams','Gram','float',None), ('support_grams','Destek g','float',None), ('time_min','Süre dk','float',None), ('quantity','Adet','int',None),
            ('price','Satış fiyatı','float',None), ('cost_estimate','Maliyet','float',None), ('status','Durum','combo',ORDER_STATUSES),
            ('payment_status','Ödeme','combo',PAYMENT_STATUSES), ('due_date','Teslim tarihi','str',None), ('notes','Not','text',None)
        ], 'Sipariş Düzenle')

    def edit_job(self):
        self.edit_record_dialog('production_jobs', 'job', [
            ('job_name','İş adı','str',None), ('printer','Yazıcı','str',None), ('material','Malzeme','combo',MATERIALS),
            ('grams','Gram','float',None), ('support_grams','Destek g','float',None), ('time_min','Süre dk','float',None),
            ('priority','Öncelik','combo',PRIORITIES), ('status','Durum','combo',JOB_STATUSES), ('notes','Not','text',None)
        ], 'Üretim İşi Düzenle')

    def load_inbox_form(self):
        rid = self.selected_id('inbox'); r = db.get_row('inbox_items', rid) if rid else None
        if not r: return
        self.vars['inbox_source'].set(r['source']); self.vars['inbox_name'].set(r['customer_name']); self.vars['inbox_phone'].set(r['phone']); self.vars['inbox_email'].set(r['email'])
        self.vars['inbox_subject'].set(r['subject']); self.vars['inbox_material'].set(r['requested_material']); self.vars['inbox_qty'].set(str(r['quantity']))
        self.vars['inbox_grams'].set(str(r['grams'])); self.vars['inbox_support'].set(str(r['support_grams'])); self.vars['inbox_time'].set(str(r['time_min']))
        self.inbox_msg.delete('1.0','end'); self.inbox_msg.insert('end', r['message'])
        self.set_status('Seçili talep forma alındı')

    def update_inbox(self):
        rid = self.selected_id('inbox')
        if not rid: return messagebox.showwarning('Seçim yok', 'Önce talep seç.')
        db.update('inbox_items', rid, {
            'source': self.vars['inbox_source'].get(), 'customer_name': self.vars['inbox_name'].get(), 'phone': self.vars['inbox_phone'].get(),
            'email': self.vars['inbox_email'].get(), 'subject': self.vars['inbox_subject'].get(), 'message': self.inbox_msg.get('1.0','end').strip(),
            'requested_material': self.vars['inbox_material'].get(), 'quantity': inum(self.vars['inbox_qty'].get(),1),
            'grams': fnum(self.vars['inbox_grams'].get()), 'support_grams': fnum(self.vars['inbox_support'].get()), 'time_min': fnum(self.vars['inbox_time'].get())
        })
        self.refresh_inbox(); self.set_status('Talep güncellendi')

    def load_catalog_form(self):
        rid = self.selected_id('catalog'); r = db.get_row('catalog', rid) if rid else None
        if not r: return
        self.vars['cat_link'].set(r['makerworld_link']); self.vars['cat_title'].set(r['title']); self.vars['cat_mat'].set(r['material']); self.vars['cat_qty'].set(str(r['quantity']))
        self.vars['cat_record_id'].set(str(r['id'])); self.vars['cat_model_id'].set(str(r['model_id'] or ''))
        self.vars['cat_grams'].set(str(r['grams'])); self.vars['cat_support'].set(str(r['support_grams'])); self.vars['cat_time'].set(str(r['time_min']))
        if 'cat_grams_basis' in self.vars: self.vars['cat_grams_basis'].set((r['grams_basis'] if 'grams_basis' in r.keys() else 'Toplam'))
        if 'cat_time_basis' in self.vars: self.vars['cat_time_basis'].set((r['time_basis'] if 'time_basis' in r.keys() else 'Toplam'))
        self.cat_result.configure(text=f"Model ID: {r['model_id']}")
        self.set_status('Katalog ürünü forma alındı')

    def clear_catalog_form(self):
        for k, d in [('cat_link',''),('cat_title',''),('cat_mat','PLA'),('cat_qty','1'),('cat_grams','0'),('cat_support','0'),('cat_time','0'),('cat_grams_basis','Toplam'),('cat_time_basis','Toplam'),('cat_record_id',''),('cat_model_id','')]:
            self.vars[k].set(d)
        self.vars['cat_id_edit_mode'].set(False)
        self.cat_result.configure(text='')

    def update_catalog(self):
        rid = self.selected_id('catalog')
        if not rid: return messagebox.showwarning('Seçim yok', 'Önce katalog ürünü seç.')
        qty, grams_raw, support_raw, time_raw, grams_basis, time_basis, total_grams, total_support, total_time = self._catalog_price_inputs()
        br = calculate_price(self.settings, self.vars['cat_mat'].get(), total_grams, total_support, total_time, 1)
        model_id = (self.vars['cat_model_id'].get().strip() if self.vars['cat_id_edit_mode'].get() else '') or extract_model_id(self.vars['cat_link'].get()) or self.vars['cat_model_id'].get().strip()
        db.update('catalog', rid, {'makerworld_link': self.vars['cat_link'].get(), 'model_id': model_id,
            'title': self.vars['cat_title'].get() or title_from_link(self.vars['cat_link'].get()), 'material': self.vars['cat_mat'].get(),
            'grams': grams_raw, 'support_grams': support_raw, 'time_min': time_raw,
            'grams_basis': grams_basis, 'time_basis': time_basis,
            'quantity': qty, 'estimated_price': br['total_price'], 'cost_estimate': br['cost_estimate'], 'margin_amount': br['margin_amount']})
        self.catalog_preview_price()
        self.refresh_catalog(); self.set_status('Katalog ürünü güncellendi')

    def update_catalog_ids(self):
        rid = self.selected_id('catalog')
        if not rid:
            return messagebox.showwarning('Seçim yok', 'Önce katalog ürünü seç.')
        if not self.vars['cat_id_edit_mode'].get():
            return messagebox.showinfo('ID düzenleme kapalı', 'ID değiştirmek için önce ID düzenleme modunu aç.')
        new_model_id = self.vars['cat_model_id'].get().strip()
        raw_new_id = self.vars['cat_record_id'].get().strip()
        if not raw_new_id:
            return messagebox.showwarning('Eksik ID', 'Kayıt ID boş bırakılamaz.')
        try:
            new_id = int(raw_new_id)
            if new_id <= 0:
                raise ValueError
        except Exception:
            return messagebox.showwarning('Geçersiz ID', 'Kayıt ID pozitif tam sayı olmalı. Örn: 12')
        if new_id != rid:
            if not messagebox.askyesno('Kayıt ID değişsin mi?', f'Seçili katalog ID #{rid}, #{new_id} olarak değiştirilecek. Devam edilsin mi?'):
                return
            try:
                with db.connect() as conn:
                    exists = conn.execute('SELECT id FROM catalog WHERE id=?', (new_id,)).fetchone()
                    if exists:
                        return messagebox.showerror('ID kullanılıyor', f'#{new_id} ID zaten başka bir katalog ürününde kullanılıyor.')
                    conn.execute('UPDATE catalog SET id=?, model_id=?, updated_at=? WHERE id=?', (new_id, new_model_id, db.now(), rid))
                    conn.commit()
                self.selected['catalog'] = new_id
            except Exception as exc:
                return messagebox.showerror('ID güncelleme hatası', str(exc))
        else:
            db.update('catalog', rid, {'model_id': new_model_id})
        self.refresh_catalog()
        self.vars['cat_record_id'].set(str(new_id))
        self.vars['cat_model_id'].set(new_model_id)
        self.set_status('Katalog ID / Model ID güncellendi')

    def clear_inventory_form(self):
        for k, d in [('inv_item',''),('inv_cat','Filament'),('inv_mat','PLA'),('inv_color',''),('inv_qty','1000'),('inv_min','200'),('inv_cost','0.65')]:
            self.vars[k].set(d)

    def load_inventory_form(self):
        rid = self.selected_id('inventory'); r = db.get_row('inventory', rid) if rid else None
        if not r: return
        self.vars['inv_item'].set(r['item']); self.vars['inv_cat'].set(r['category']); self.vars['inv_mat'].set(r['material'] or 'PLA'); self.vars['inv_color'].set(r['color'])
        self.vars['inv_qty'].set(str(r['current_qty'])); self.vars['inv_min'].set(str(r['min_qty'])); self.vars['inv_cost'].set(str(r['unit_cost']))
        self.set_status('Stok kartı forma alındı')

    def update_inventory(self):
        rid = self.selected_id('inventory')
        if not rid: return messagebox.showwarning('Seçim yok', 'Önce stok kartı seç.')
        db.update('inventory', rid, {'item': self.vars['inv_item'].get(), 'category': self.vars['inv_cat'].get(), 'material': self.vars['inv_mat'].get(), 'color': self.vars['inv_color'].get(),
            'current_qty': fnum(self.vars['inv_qty'].get()), 'min_qty': fnum(self.vars['inv_min'].get()), 'unit_cost': fnum(self.vars['inv_cost'].get())})
        self.refresh_inventory(); self.set_status('Stok kartı güncellendi')

    def inventory_cost_to_pricing(self):
        rid = self.selected_id('inventory'); r = db.get_row('inventory', rid) if rid else None
        if not r: return messagebox.showwarning('Seçim yok', 'Önce stok kartı seç.')
        mat = (r['material'] or '').upper()
        key = f'{mat.lower()}_cost_kg'
        if mat not in MATERIALS or mat == 'SUPPORT':
            key = 'support_cost_kg' if mat == 'SUPPORT' else ''
        if not key:
            return messagebox.showwarning('Malzeme yok', 'Bu stok kartında fiyatlamaya aktarılacak malzeme kodu yok.')
        kg_price = fnum(r['unit_cost']) * 1000.0
        if not messagebox.askyesno('Fiyatlamaya aktar', f'{r["item"]} birim maliyeti {fnum(r["unit_cost"])} TL/g görünüyor.\n{key} = {kg_price:.2f} TL/kg olarak güncellensin mi?'):
            return
        db.save_setting(key, kg_price)
        existing = db.list_rows('cost_items', 'setting_key=?', (key,), limit=1)
        if existing:
            db.update('cost_items', existing[0]['id'], {'value': kg_price, 'active': 1})
        else:
            db.insert('cost_items', {'setting_key': key, 'name': f'{mat} kg maliyeti', 'group_name': 'Malzeme', 'unit': 'TL/kg', 'value': kg_price, 'active': 1})
        self.settings[key] = str(kg_price)
        self.refresh_cost_items(); self.set_status('Stok maliyeti fiyatlama ayarlarına aktarıldı')

    def clear_customer_form(self):
        for k in ['cust_name','cust_phone','cust_email','cust_instagram']:
            self.vars[k].set('')

    def load_customer_form(self):
        rid = self.selected_id('customer'); r = db.get_row('customers', rid) if rid else None
        if not r: return
        self.vars['cust_name'].set(r['name']); self.vars['cust_phone'].set(r['phone']); self.vars['cust_email'].set(r['email']); self.vars['cust_instagram'].set(r['instagram'])
        self.set_status('Müşteri forma alındı')

    def update_customer(self):
        rid = self.selected_id('customer')
        if not rid: return messagebox.showwarning('Seçim yok', 'Önce müşteri seç.')
        db.update('customers', rid, {'name': self.vars['cust_name'].get(), 'phone': self.vars['cust_phone'].get(), 'email': self.vars['cust_email'].get(), 'instagram': self.vars['cust_instagram'].get()})
        self.refresh_customers(); self.set_status('Müşteri güncellendi')

    def clear_template_form(self):
        self.vars['tpl_name'].set(''); self.vars['tpl_channel'].set('WhatsApp'); self.tpl_body.delete('1.0','end')

    def load_template_form(self):
        rid = self.selected_id('template'); r = db.get_row('message_templates', rid) if rid else None
        if not r: return
        self.vars['tpl_name'].set(r['name']); self.vars['tpl_channel'].set(r['channel']); self.tpl_body.delete('1.0','end'); self.tpl_body.insert('end', r['body'])
        self.set_status('Şablon forma alındı')

    def update_template(self):
        rid = self.selected_id('template')
        if not rid: return messagebox.showwarning('Seçim yok', 'Önce şablon seç.')
        db.update('message_templates', rid, {'name': self.vars['tpl_name'].get(), 'channel': self.vars['tpl_channel'].get(), 'body': self.tpl_body.get('1.0','end').strip()})
        self.refresh_templates(); self.set_status('Şablon güncellendi')

    # ---------- Integrations ----------
    def _integrations_page(self):
        root = self.page('Entegrasyonlar')
        status_panel = self.panel(root, 'Entegrasyon durum merkezi')
        cards = tk.Frame(status_panel, bg=self.colors['card'])
        cards.pack(fill='x')
        self._status_card(cards, 'Cloud Bridge', 'bridge')
        self._status_card(cards, 'Gmail OAuth', 'gmail')
        self._status_card(cards, 'Instagram DM', 'instagram')
        self._status_card(cards, 'Google Forms', 'forms')
        self._status_card(cards, 'WhatsApp', 'whatsapp')
        self._status_card(cards, 'Odoo', 'odoo')
        btns = tk.Frame(status_panel, bg=self.colors['card'])
        btns.pack(fill='x', pady=(8, 0))
        ttk.Button(btns, text='Bridge Başlat', style='Accent.TButton', command=self.start_bridge).pack(side='left', padx=3)
        ttk.Button(btns, text='Bridge Durdur', command=self.stop_bridge).pack(side='left', padx=3)
        ttk.Button(btns, text='Bridge Yeniden Başlat', command=self.restart_bridge).pack(side='left', padx=3)
        ttk.Button(btns, text='Tümünü Test Et', command=self.test_all_integrations).pack(side='left', padx=3)
        ttk.Button(btns, text='Logları Aç', command=self.open_bridge_log).pack(side='left', padx=3)
        ttk.Button(btns, text='Yenile', command=self.refresh_integration_status_cards).pack(side='left', padx=3)

        form = self.panel(root, 'Cloud Bridge + Odoo + Meta + Webhook ayarları')
        self.vars['bridge_url']=tk.StringVar(value=self.settings.get('bridge_url','http://127.0.0.1:8787'))
        self.vars['public_bridge_url']=tk.StringVar(value=self.settings.get('public_bridge_url',''))
        self.vars['odoo_url']=tk.StringVar(value=self.settings.get('odoo_url','https://bunudabastik3d.odoo.com'))
        self.vars['odoo_db']=tk.StringVar(value=self.settings.get('odoo_db',''))
        self.vars['odoo_user']=tk.StringVar(value=self.settings.get('odoo_username',''))
        self.vars['odoo_key']=tk.StringVar(value=self.settings.get('odoo_api_key',''))
        self.vars['meta_verify_token']=tk.StringVar(value=self.settings.get('meta_verify_token','bunudabastik3d_verify'))
        self.vars['instagram_page_token']=tk.StringVar(value=self.settings.get('instagram_page_token',''))
        self.entry(form,'Yerel Bridge URL',self.vars['bridge_url'],0,0,width=42)
        self.entry(form,'Public Bridge URL',self.vars['public_bridge_url'],0,2,width=42)
        self.entry(form,'Odoo URL',self.vars['odoo_url'],1,0,width=42)
        self.entry(form,'Odoo DB',self.vars['odoo_db'],1,2)
        self.entry(form,'Odoo Kullanıcı',self.vars['odoo_user'],2,0)
        self.entry(form,'Odoo API Key',self.vars['odoo_key'],2,2,show='*')
        self.entry(form,'Meta Verify Token',self.vars['meta_verify_token'],3,0,width=30)
        self.entry(form,'Instagram Page Access Token',self.vars['instagram_page_token'],3,2,width=42,show='*')
        row=tk.Frame(form,bg=self.colors['card']); row.grid(row=4,column=0,columnspan=4,sticky='w',padx=4,pady=4)
        ttk.Button(row,text='Ayarları Kaydet',style='Accent.TButton',command=self.save_integration_settings).pack(side='left',padx=3)
        ttk.Button(row,text='Bridge Health Test',command=self.bridge_health).pack(side='left',padx=3)
        ttk.Button(row,text='Odoo Test',command=self.odoo_test).pack(side='left',padx=3)
        ttk.Button(row,text='Webhook Adreslerini Kopyala',command=self.copy_webhook_addresses).pack(side='left',padx=3)
        ttk.Button(row,text='Test Talebi Gönder',command=self.send_test_bridge_payload).pack(side='left',padx=3)
        ttk.Button(row,text='Instagram Kurulum Rehberi',command=lambda: self.open_doc('docs/INSTAGRAM_DM_KURULUM.md')).pack(side='left',padx=3)

        body = tk.Frame(root, bg=self.colors['bg'])
        body.pack(fill='both', expand=True, pady=6)
        info = self.panel(body,'Webhook adresleri', side='left', fill='both', expand=True, padx=(0,5))
        self.webhook_text=scrolledtext.ScrolledText(info,height=15,font=('Consolas',10)); self.webhook_text.pack(fill='both',expand=True)
        logp = self.panel(body,'Entegrasyon logları', side='left', fill='both', expand=True, padx=(5,0))
        self.integration_events_tree = self.tree(logp, ['time','level','title','detail'], {'time':'Zaman','level':'Seviye','title':'Olay','detail':'Detay'}, height=12)
        self.bind_select(self.integration_events_tree, 'integration_event', self.show_integration_event_detail)
        self.integration_event_detail = scrolledtext.ScrolledText(logp, height=5, font=('Consolas',9)); self.integration_event_detail.pack(fill='x')
        self.refresh_webhook_info()
        self.refresh_integration_status_cards()
        self.refresh_integration_events()

    def _status_card(self, parent, title, key):
        frame = tk.Frame(parent, bg=self.colors.get('card_alt', self.colors['card']), highlightbackground=self.colors['line'], highlightthickness=1)
        frame.pack(side='left', fill='x', expand=True, padx=4, pady=4)
        ttk.Label(frame, text=title, style='Panel.TLabel').pack(anchor='w', padx=8, pady=(7,1))
        var = tk.StringVar(value='Bekliyor')
        self.integration_status_vars[key] = var
        tk.Label(frame, textvariable=var, bg=self.colors.get('card_alt', self.colors['card']), fg=self.colors['muted'], font=('Segoe UI', 11, 'bold')).pack(anchor='w', padx=8, pady=(0,7))
        return frame

    def save_integration_settings(self):
        vals={
            'bridge_url':self.vars['bridge_url'].get(),
            'public_bridge_url':self.vars['public_bridge_url'].get(),
            'odoo_url':self.vars['odoo_url'].get(),
            'odoo_db':self.vars['odoo_db'].get(),
            'odoo_username':self.vars['odoo_user'].get(),
            'odoo_api_key':self.vars['odoo_key'].get(),
            'meta_verify_token':self.vars['meta_verify_token'].get(),
            'instagram_page_token':self.vars['instagram_page_token'].get(),
        }
        db.save_settings(vals); self.settings.update(vals); self.refresh_webhook_info(); self.refresh_integration_status_cards(); self.set_status('Entegrasyon ayarları kaydedildi')

    def refresh_webhook_info(self):
        if not hasattr(self,'webhook_text'): return
        local=self.vars.get('bridge_url',tk.StringVar(value=self.settings.get('bridge_url','http://127.0.0.1:8787'))).get().rstrip('/')
        public=self.vars.get('public_bridge_url',tk.StringVar(value=self.settings.get('public_bridge_url',''))).get().rstrip('/') or local
        token=self.vars.get('meta_verify_token',tk.StringVar(value=self.settings.get('meta_verify_token','bunudabastik3d_verify'))).get()
        text=f"""Kullanılacak webhook adresleri:

Yerel Bridge URL:
{local}

Public Bridge URL - Instagram / WhatsApp / Google Forms için önerilen:
{public}

Google Forms / Apps Script POST:
{public}/webhook/google-forms

WhatsApp Cloud API Webhook:
{public}/webhook/whatsapp

Instagram DM Webhook:
{public}/webhook/instagram

E-posta servisleri / özel formlar POST:
{public}/webhook/email

Manuel dış sistem POST:
{public}/webhook/manual

Meta Verify Token:
{token}

Masaüstü uygulaması Bridge’den şu endpoint ile çeker:
{local}/api/inbox

Notlar:
- 127.0.0.1 sadece bu bilgisayarın içinden çalışır.
- Instagram DM ve WhatsApp için Public HTTPS gerekir: ngrok, Cloudflare Tunnel, VPS veya domain.
- Instagram DM için Instagram hesabı Professional olmalı ve Facebook Page bağlantısı gerekir.
- Meta tarafında Webhooks > Instagram veya Messenger/Instagram Messaging alanına callback URL ve verify token girilir.
"""
        self.webhook_text.delete('1.0','end'); self.webhook_text.insert('end',text)

    def copy_webhook_addresses(self):
        self.copy(self.webhook_text.get('1.0','end') if hasattr(self,'webhook_text') else '')

    def _bridge_base_url(self):
        return self.vars.get('bridge_url', tk.StringVar(value=self.settings.get('bridge_url','http://127.0.0.1:8787'))).get().rstrip('/')

    def _bridge_port(self):
        port = self.vars.get('bridge_port', tk.StringVar(value=self.settings.get('bridge_port', '8787'))).get()
        return str(max(inum(port, 8787), 1))

    def _bridge_env(self):
        env = os.environ.copy()
        env['BDB_BRIDGE_DB'] = str(db.DB_PATH)
        env['BDB_BRIDGE_PORT'] = self._bridge_port()
        env['PORT'] = self._bridge_port()
        secret = self.vars.get('webhook_secret', tk.StringVar(value=self.settings.get('webhook_secret', ''))).get()
        verify = self.vars.get('meta_verify_token', tk.StringVar(value=self.settings.get('meta_verify_token', 'bunudabastik3d_verify'))).get()
        env['BDB_WEBHOOK_SECRET'] = secret
        env['WHATSAPP_VERIFY_TOKEN'] = verify
        return env

    def _bridge_health_ok(self):
        import requests
        try:
            r=requests.get(self._bridge_base_url()+'/health',timeout=3); r.raise_for_status()
            return True, r.json()
        except Exception as e:
            return False, str(e)

    def refresh_integration_status_cards(self):
        try:
            ok, data = self._bridge_health_ok()
            self.integration_status_vars.get('bridge', tk.StringVar()).set('Açık' if ok else 'Kapalı')
        except Exception: pass
        try:
            self.integration_status_vars.get('gmail', tk.StringVar()).set('Bağlı' if google_oauth_client.has_token() else 'Bekliyor')
        except Exception: pass
        try:
            self.integration_status_vars.get('instagram', tk.StringVar()).set('Token Var' if self.settings.get('instagram_page_token') else 'Kurulum Bekliyor')
        except Exception: pass
        try:
            self.integration_status_vars.get('forms', tk.StringVar()).set('Bridge ile Hazır')
            self.integration_status_vars.get('whatsapp', tk.StringVar()).set('Bridge ile Hazır')
            self.integration_status_vars.get('odoo', tk.StringVar()).set('Ayarlandı' if self.settings.get('odoo_db') and self.settings.get('odoo_api_key') else 'Eksik Ayar')
        except Exception: pass
        try: self.refresh_integration_events()
        except Exception: pass

    def start_bridge(self):
        try:
            ok, _ = self._bridge_health_ok()
            if ok:
                self.set_status('Bridge zaten açık')
                self.refresh_integration_status_cards()
                return
            bat = BASE_DIR / 'run_bridge_windows.bat'
            env = self._bridge_env()
            if bat.exists():
                self.bridge_process = subprocess.Popen(str(bat), cwd=str(BASE_DIR), shell=True, env=env)
            else:
                cmd = [sys.executable, '-m', 'uvicorn', 'cloud_bridge.main:app', '--host', '127.0.0.1', '--port', self._bridge_port()]
                self.bridge_process = subprocess.Popen(cmd, cwd=str(BASE_DIR), env=env)
            db.log_event('Bridge başlatıldı', 'Uygulama içinden başlatma denendi')
            self.after(2500, self.refresh_integration_status_cards)
            self.set_status('Cloud Bridge başlatılıyor...')
        except Exception as e:
            messagebox.showerror('Bridge başlatılamadı', str(e))

    def _terminate_bridge_on_port(self):
        if not sys.platform.startswith('win'):
            return False
        port = self._bridge_port()
        cmd = f'for /f "tokens=5" %a in (\'netstat -ano ^| findstr :{port}\') do taskkill /PID %a /T /F'
        result = subprocess.run(cmd, shell=True, cwd=str(BASE_DIR), capture_output=True, text=True)
        return result.returncode == 0

    def stop_bridge(self):
        try:
            if self.bridge_process and self.bridge_process.poll() is None:
                self.bridge_process.terminate()
                self.bridge_process = None
                db.log_event('Bridge durduruldu', 'Uygulama içinden durduruldu')
                self.set_status('Bridge durduruldu')
            elif self._terminate_bridge_on_port():
                db.log_event('Bridge durduruldu', f'Port {self._bridge_port()} üzerindeki süreç kapatıldı')
                self.set_status('Bridge durduruldu')
            else:
                messagebox.showinfo('Bridge', 'Bu oturumdan başlatılan Bridge süreci bulunamadı. Ayrı açılan CMD penceresini kapatman gerekebilir.')
            self.after(1000, self.refresh_integration_status_cards)
        except Exception as e:
            messagebox.showerror('Bridge durdurulamadı', str(e))

    def restart_bridge(self):
        self.stop_bridge()
        self.after(1000, self.start_bridge)

    def open_bridge_log(self):
        try:
            local_log = BASE_DIR / 'logs' / 'run_safe_console.log'
            app_log = LOG_DIR / 'app_debug.log'
            if local_log.exists(): webbrowser.open(str(local_log))
            elif app_log.exists(): webbrowser.open(str(app_log))
            else: messagebox.showinfo('Log', f'Log bulunamadı. Beklenen konum:\n{local_log}\n{app_log}')
        except Exception as e:
            messagebox.showerror('Log açılamadı', str(e))

    def bridge_health(self):
        ok, data = self._bridge_health_ok()
        if ok:
            db.log_event('Bridge health OK', str(data))
            messagebox.showinfo('Bridge OK',str(data))
        else:
            db.log_event('Bridge health hata', str(data), level='ERROR')
            messagebox.showerror('Bridge Hatası', f'Bridge çalışmıyor olabilir. Önce Bridge Başlat butonuna bas.\n\nDetay:\n{data}')
        self.refresh_integration_status_cards()

    def send_test_bridge_payload(self):
        import requests
        try:
            payload={'source':'Manual','customer_name':'Test Müşteri','subject':'Bridge test talebi','message':'Bu kayıt Entegrasyonlar > Test Talebi Gönder ile oluşturuldu.'}
            r=requests.post(self._bridge_base_url()+'/webhook/manual', json=payload, timeout=8); r.raise_for_status()
            db.log_event('Bridge test payload OK', str(r.json()))
            self.pull_bridge(); self.refresh_integration_status_cards()
            messagebox.showinfo('Test başarılı', f'Test talebi gönderildi:\n{r.json()}')
        except Exception as e:
            messagebox.showerror('Test payload hatası', str(e))

    def test_all_integrations(self):
        self.bridge_health()
        try:
            self.refresh_gmail_oauth_status()
        except Exception: pass
        try:
            if self.settings.get('odoo_db') and self.settings.get('odoo_api_key'):
                self.odoo_test()
        except Exception: pass
        self.refresh_integration_status_cards()

    def odoo_test(self):
        try:
            c=OdooClient(OdooConfig(self.vars['odoo_url'].get(),self.vars['odoo_db'].get(),self.vars['odoo_user'].get(),self.vars['odoo_key'].get()))
            uid=c.authenticate(); db.log_event('Odoo bağlantı OK', f'UID {uid}'); messagebox.showinfo('Odoo OK',f'Bağlandı. UID: {uid}')
        except Exception as e:
            db.log_event('Odoo bağlantı hatası', str(e), level='ERROR'); messagebox.showerror('Odoo Hatası',str(e))
        self.refresh_integration_status_cards()

    def refresh_integration_events(self):
        if not hasattr(self, 'integration_events_tree'): return
        self.clear_tree(self.integration_events_tree)
        for r in db.list_rows('app_events', order='id DESC', limit=60):
            self.integration_events_tree.insert('', 'end', iid=r['id'], values=(r['created_at'], r['level'], r['title'], r['detail']))

    def show_integration_event_detail(self):
        rid = self.selected_id('integration_event')
        r = db.get_row('app_events', rid) if rid else None
        if not hasattr(self, 'integration_event_detail'): return
        self.integration_event_detail.delete('1.0','end')
        if r:
            self.integration_event_detail.insert('end', f"{r['created_at']} | {r['level']} | {r['title']}\n\n{r['detail']}")

    # ---------- Sync ----------

    # ---------- API Settings Center ----------
    def _api_settings_page(self):
        root = self.page('API Ayarları')
        top = self.panel(root, 'API Ayarları Merkezi')
        tk.Label(top, text='Tüm dış bağlantıları ayrı sayfalardan kur, test et ve takip et: Gmail, Instagram DM, WhatsApp Business, Google Forms, Odoo ve Cloud Bridge.', bg=self.colors['card'], fg=self.colors['muted'], wraplength=1200, justify='left', font=('Segoe UI', 10)).pack(anchor='w')
        bar = tk.Frame(top, bg=self.colors['card']); bar.pack(fill='x', pady=(8,0))
        ttk.Button(bar, text='Tüm API Durumlarını Yenile', style='Accent.TButton', command=self.refresh_api_center).pack(side='left', padx=3)
        ttk.Button(bar, text='Bridge Başlat', command=self.start_bridge).pack(side='left', padx=3)
        ttk.Button(bar, text='Bridge Durdur', command=self.stop_bridge).pack(side='left', padx=3)
        ttk.Button(bar, text='Webhook Adreslerini Kopyala', command=self.copy_api_webhooks).pack(side='left', padx=3)
        self.api_tabs = ttk.Notebook(root)
        self.api_tabs.pack(fill='both', expand=True, pady=8)
        tabs = {}
        for title in ['Genel Durum','Gmail API','Instagram DM API','WhatsApp Business API','Google Forms API','Odoo API','Cloud Bridge API','Webhook Yöneticisi','API Logları']:
            frame = tk.Frame(self.api_tabs, bg=self.colors['bg'])
            self.api_tabs.add(frame, text=title)
            tabs[title] = frame
        self._api_general_tab(tabs['Genel Durum'])
        self._api_gmail_tab(tabs['Gmail API'])
        self._api_instagram_tab(tabs['Instagram DM API'])
        self._api_whatsapp_tab(tabs['WhatsApp Business API'])
        self._api_forms_tab(tabs['Google Forms API'])
        self._api_odoo_tab(tabs['Odoo API'])
        self._api_bridge_tab(tabs['Cloud Bridge API'])
        self._api_webhooks_tab(tabs['Webhook Yöneticisi'])
        self._api_logs_tab(tabs['API Logları'])

    def api_entry(self, parent, label, key, default='', row=0, col=0, width=36, show=None):
        self.vars.setdefault(key, tk.StringVar(value=self.settings.get(key, default)))
        self.entry(parent, label, self.vars[key], row, col, width=width, show=show)
        return self.vars[key]

    def _api_general_tab(self, root):
        self.api_status_vars = {}
        grid = tk.Frame(root, bg=self.colors['bg']); grid.pack(fill='x', pady=8)
        services = [('bridge','Cloud Bridge'),('gmail','Gmail OAuth'),('instagram','Instagram DM'),('whatsapp','WhatsApp Business'),('forms','Google Forms'),('odoo','Odoo')]
        for i,(key,label) in enumerate(services):
            card = tk.Frame(grid, bg=self.colors['card'], highlightbackground=self.colors['line'], highlightthickness=1)
            card.grid(row=i//3, column=i%3, sticky='ew', padx=6, pady=6)
            grid.columnconfigure(i%3, weight=1)
            tk.Label(card, text=label, bg=self.colors['card'], fg=self.colors['muted'], font=('Segoe UI', 9, 'bold')).pack(anchor='w', padx=12, pady=(10,2))
            self.api_status_vars[key] = tk.StringVar(value='Kontrol bekliyor')
            tk.Label(card, textvariable=self.api_status_vars[key], bg=self.colors['card'], fg=self.colors['ink'], font=('Segoe UI', 14, 'bold')).pack(anchor='w', padx=12, pady=(0,10))
        info = self.panel(root, 'Kurulum yol haritası', fill='both', expand=True)
        self._readonly_text(info, '1) Cloud Bridge API sekmesinden yerel/public URL ayarla.\n2) Gmail API sekmesinden credentials.json seç ve Google ile bağlan.\n3) Instagram/WhatsApp için Meta token ve webhook bilgilerini gir.\n4) Google Forms için webhook URL’yi Apps Script’e yapıştır.\n5) Odoo API sekmesinden DB, kullanıcı ve API key gir.\n6) API Logları sekmesinden hata/başarı geçmişini takip et.')

    def _api_gmail_tab(self, root):
        form = self.panel(root, 'Gmail API - OAuth ile şifresiz bağlantı')
        self.vars['gmail_oauth_query'] = tk.StringVar(value=self.settings.get('gmail_oauth_query','in:inbox'))
        self.vars['gmail_oauth_limit'] = tk.StringVar(value=self.settings.get('gmail_oauth_limit','25'))
        self.entry(form, 'Gmail arama sorgusu', self.vars['gmail_oauth_query'], 0, 0, width=38)
        self.entry(form, 'Limit', self.vars['gmail_oauth_limit'], 0, 2, width=8)
        self.gmail_api_status = tk.StringVar(value='Bekliyor')
        ttk.Label(form, text='Durum:', style='Panel.TLabel').grid(row=1, column=0, sticky='w', padx=4, pady=4)
        ttk.Label(form, textvariable=self.gmail_api_status, style='Panel.TLabel').grid(row=1, column=1, sticky='w', padx=4, pady=4)
        row = tk.Frame(form, bg=self.colors['card']); row.grid(row=2, column=0, columnspan=4, sticky='w', padx=4, pady=8)
        ttk.Button(row, text='credentials.json Seç', command=self.choose_gmail_credentials).pack(side='left', padx=3)
        ttk.Button(row, text='Gmail ile Bağlan', style='Accent.TButton', command=self.gmail_oauth_connect_thread).pack(side='left', padx=3)
        ttk.Button(row, text='Mailleri Çek', command=self.fetch_gmail_oauth_thread).pack(side='left', padx=3)
        ttk.Button(row, text='Yetkiyi Sıfırla', command=self.gmail_oauth_disconnect).pack(side='left', padx=3)
        ttk.Button(row, text='Kurulum Rehberi', command=lambda: self.open_doc('docs/GMAIL_OAUTH_KURULUM.md')).pack(side='left', padx=3)

    def _api_instagram_tab(self, root):
        form = self.panel(root, 'Instagram DM API - Meta webhook ayarları')
        self.api_entry(form, 'Instagram App ID', 'instagram_app_id', '', 0, 0)
        self.api_entry(form, 'Instagram App Secret', 'instagram_app_secret', '', 0, 2, show='*')
        self.api_entry(form, 'Facebook Page ID', 'instagram_page_id', '', 1, 0)
        self.api_entry(form, 'Page Access Token', 'instagram_page_token', '', 1, 2, show='*')
        self.api_entry(form, 'Verify Token', 'meta_verify_token', 'bunudabastik3d_verify', 2, 0)
        row = tk.Frame(form, bg=self.colors['card']); row.grid(row=3,column=0,columnspan=4,sticky='w',padx=4,pady=8)
        ttk.Button(row, text='Instagram Ayarlarını Kaydet', style='Accent.TButton', command=self.save_api_settings).pack(side='left', padx=3)
        ttk.Button(row, text='Webhook URL Kopyala', command=lambda: self.copy(self._public_bridge_url() + '/webhook/instagram')).pack(side='left', padx=3)
        ttk.Button(row, text='Rehber', command=lambda: self.open_doc('docs/INSTAGRAM_DM_KURULUM.md')).pack(side='left', padx=3)
        helpbox = self.panel(root, 'Gerekenler', fill='both', expand=True)
        self._readonly_text(helpbox, 'Instagram hesabı Professional/Business olmalı, Facebook Page bağlantısı olmalı, public HTTPS webhook gerekir. DM olayları Cloud Bridge > /webhook/instagram adresine düşer ve Gelen Kutusu’na aktarılır.')

    def _api_whatsapp_tab(self, root):
        form = self.panel(root, 'WhatsApp Business Cloud API')
        self.api_entry(form, 'Phone Number ID', 'whatsapp_phone_number_id', '', 0, 0)
        self.api_entry(form, 'Business Account ID', 'whatsapp_business_account_id', '', 0, 2)
        self.api_entry(form, 'Access Token', 'whatsapp_access_token', '', 1, 0, show='*')
        self.api_entry(form, 'Verify Token', 'whatsapp_verify_token', self.settings.get('meta_verify_token','bunudabastik3d_verify'), 1, 2)
        row = tk.Frame(form, bg=self.colors['card']); row.grid(row=2,column=0,columnspan=4,sticky='w',padx=4,pady=8)
        ttk.Button(row, text='WhatsApp Ayarlarını Kaydet', style='Accent.TButton', command=self.save_api_settings).pack(side='left', padx=3)
        ttk.Button(row, text='Webhook URL Kopyala', command=lambda: self.copy(self._public_bridge_url() + '/webhook/whatsapp')).pack(side='left', padx=3)
        ttk.Button(row, text='Bridge Test', command=self.send_test_bridge_payload).pack(side='left', padx=3)

    def _api_forms_tab(self, root):
        form = self.panel(root, 'Google Forms / Apps Script')
        self.api_entry(form, 'Google Form ID', 'google_form_id', '', 0, 0)
        self.api_entry(form, 'Apps Script URL', 'google_apps_script_url', '', 0, 2)
        self.api_entry(form, 'Webhook Secret', 'webhook_secret', '', 1, 0, show='*')
        row = tk.Frame(form, bg=self.colors['card']); row.grid(row=2,column=0,columnspan=4,sticky='w',padx=4,pady=8)
        ttk.Button(row, text='Forms Ayarlarını Kaydet', style='Accent.TButton', command=self.save_api_settings).pack(side='left', padx=3)
        ttk.Button(row, text='Forms Webhook Kopyala', command=lambda: self.copy(self._public_bridge_url() + '/webhook/google-forms')).pack(side='left', padx=3)
        ttk.Button(row, text='Test Payload Gönder', command=self.send_test_bridge_payload).pack(side='left', padx=3)
        ttk.Button(row, text='Apps Script Rehberi', command=lambda: self.open_doc('docs/GOOGLE_FORMS_APPS_SCRIPT.md')).pack(side='left', padx=3)

    def _api_odoo_tab(self, root):
        form = self.panel(root, 'Odoo API')
        self.api_entry(form, 'Odoo URL', 'odoo_url', 'https://bunudabastik3d.odoo.com', 0, 0)
        self.api_entry(form, 'Odoo Database', 'odoo_db', '', 0, 2)
        self.api_entry(form, 'Odoo Kullanıcı', 'odoo_username', '', 1, 0)
        self.api_entry(form, 'Odoo API Key', 'odoo_api_key', '', 1, 2, show='*')
        row = tk.Frame(form, bg=self.colors['card']); row.grid(row=2,column=0,columnspan=4,sticky='w',padx=4,pady=8)
        ttk.Button(row, text='Odoo Ayarlarını Kaydet', style='Accent.TButton', command=self.save_api_settings).pack(side='left', padx=3)
        ttk.Button(row, text='Odoo Test', command=self.odoo_test_from_api).pack(side='left', padx=3)
        ttk.Button(row, text='Odoo Rehberi', command=lambda: self.open_doc('docs/ODOO.md')).pack(side='left', padx=3)

    def _api_bridge_tab(self, root):
        form = self.panel(root, 'Cloud Bridge API')
        self.api_entry(form, 'Yerel Bridge URL', 'bridge_url', 'http://127.0.0.1:8787', 0, 0)
        self.api_entry(form, 'Public Bridge URL', 'public_bridge_url', '', 0, 2)
        self.api_entry(form, 'Bridge Port', 'bridge_port', '8787', 1, 0)
        row = tk.Frame(form, bg=self.colors['card']); row.grid(row=2,column=0,columnspan=4,sticky='w',padx=4,pady=8)
        ttk.Button(row, text='Bridge Ayarlarını Kaydet', style='Accent.TButton', command=self.save_api_settings).pack(side='left', padx=3)
        ttk.Button(row, text='Başlat', command=self.start_bridge).pack(side='left', padx=3)
        ttk.Button(row, text='Durdur', command=self.stop_bridge).pack(side='left', padx=3)
        ttk.Button(row, text='Yeniden Başlat', command=self.restart_bridge).pack(side='left', padx=3)
        ttk.Button(row, text='Health Test', command=self.bridge_health).pack(side='left', padx=3)
        ttk.Button(row, text='Logları Aç', command=self.open_bridge_log).pack(side='left', padx=3)

    def _api_webhooks_tab(self, root):
        box = self.panel(root, 'Webhook adresleri')
        self.api_webhook_text = scrolledtext.ScrolledText(box, height=20, bg=self.colors['card_alt'], fg=self.colors['ink'], insertbackground=self.colors['ink'], font=('Consolas',10))
        self.api_webhook_text.pack(fill='both', expand=True)
        row = tk.Frame(root, bg=self.colors['bg']); row.pack(fill='x', pady=6)
        ttk.Button(row, text='Adresleri Yenile', style='Accent.TButton', command=self.refresh_api_webhooks).pack(side='left', padx=3)
        ttk.Button(row, text='Panoya Kopyala', command=self.copy_api_webhooks).pack(side='left', padx=3)

    def _api_logs_tab(self, root):
        self.api_log_tree = self.tree(root, ['time','level','title','detail'], {'time':'Zaman','level':'Seviye','title':'Olay','detail':'Detay'}, height=18)
        row = tk.Frame(root, bg=self.colors['bg']); row.pack(fill='x', pady=6)
        ttk.Button(row, text='Logları Yenile', style='Accent.TButton', command=self.refresh_api_logs).pack(side='left', padx=3)
        ttk.Button(row, text='Veri Klasörünü Aç', command=lambda: webbrowser.open(str(db.APP_DIR))).pack(side='left', padx=3)

    def _readonly_text(self, parent, text):
        txt = scrolledtext.ScrolledText(parent, height=8, bg=self.colors['card_alt'], fg=self.colors['ink'], insertbackground=self.colors['ink'], font=('Consolas',10))
        txt.pack(fill='both', expand=True)
        txt.insert('end', text)
        txt.configure(state='disabled')
        return txt

    def _public_bridge_url(self):
        public = self.vars.get('public_bridge_url', tk.StringVar(value=self.settings.get('public_bridge_url',''))).get().strip().rstrip('/')
        return public or self.vars.get('bridge_url', tk.StringVar(value=self.settings.get('bridge_url','http://127.0.0.1:8787'))).get().strip().rstrip('/')

    def save_api_settings(self):
        keys = ['bridge_url','public_bridge_url','bridge_port','webhook_secret','meta_verify_token','instagram_app_id','instagram_app_secret','instagram_page_id','instagram_page_token','whatsapp_phone_number_id','whatsapp_business_account_id','whatsapp_access_token','whatsapp_verify_token','google_form_id','google_apps_script_url','odoo_url','odoo_db','odoo_username','odoo_api_key','gmail_oauth_query','gmail_oauth_limit']
        vals = {}
        for k in keys:
            if k in self.vars:
                vals[k] = self.vars[k].get()
        db.save_settings(vals); self.settings.update(vals)
        aliases = {'odoo_user':'odoo_username','odoo_key':'odoo_api_key'}
        for var_key, set_key in aliases.items():
            if var_key in self.vars and set_key in vals:
                self.vars[var_key].set(vals[set_key])
        self.refresh_api_center()
        try: self.refresh_webhook_info()
        except Exception: pass
        self.set_status('API ayarları kaydedildi')

    def refresh_api_center(self):
        try:
            ok,_ = self._bridge_health_ok()
        except Exception:
            ok=False
        status_map = {
            'bridge': 'Açık' if ok else 'Kapalı',
            'gmail': 'Bağlı' if google_oauth_client.has_token() else 'Bekliyor',
            'instagram': 'Token Var' if self.settings.get('instagram_page_token') else 'Kurulum Bekliyor',
            'whatsapp': 'Token Var' if self.settings.get('whatsapp_access_token') else 'Kurulum Bekliyor',
            'forms': 'Webhook Hazır' if self._public_bridge_url() else 'URL Bekliyor',
            'odoo': 'Ayarlandı' if self.settings.get('odoo_db') and self.settings.get('odoo_api_key') else 'Eksik Ayar',
        }
        for d in (getattr(self,'api_status_vars',{}), getattr(self,'integration_status_vars',{})):
            for k,v in status_map.items():
                if k in d:
                    d[k].set(v)
        if hasattr(self, 'gmail_api_status'):
            self.gmail_api_status.set(('Token var' if google_oauth_client.has_token() else 'Token yok') + ' | ' + ('credentials var' if google_oauth_client.has_credentials_file() else 'credentials yok'))
        self.refresh_api_webhooks()
        self.refresh_api_logs()

    def refresh_api_webhooks(self):
        if not hasattr(self, 'api_webhook_text'):
            return
        base = self._public_bridge_url()
        local = self.vars.get('bridge_url', tk.StringVar(value=self.settings.get('bridge_url','http://127.0.0.1:8787'))).get().rstrip('/')
        token = self.vars.get('meta_verify_token', tk.StringVar(value=self.settings.get('meta_verify_token','bunudabastik3d_verify'))).get()
        text = (
            f'Webhook adresleri\n\nYerel Bridge: {local}\nPublic Bridge: {base}\n\n'
            f'Instagram DM: {base}/webhook/instagram\nWhatsApp Business: {base}/webhook/whatsapp\n'
            f'Google Forms: {base}/webhook/google-forms\nE-posta / özel servis: {base}/webhook/email\n'
            f'Manuel sistem: {base}/webhook/manual\nMasaüstü çekme endpointi: {local}/api/inbox\nHealth: {local}/health\n\n'
            f'Meta Verify Token: {token}\n\nNot: Instagram ve WhatsApp için public HTTPS şarttır. Yerelde test için 127.0.0.1 yeterli ama dış servisler erişemez.'
        )
        self.api_webhook_text.delete('1.0','end'); self.api_webhook_text.insert('end', text)

    def copy_api_webhooks(self):
        if hasattr(self, 'api_webhook_text'):
            self.copy(self.api_webhook_text.get('1.0','end'))
        else:
            self.copy(self._public_bridge_url())

    def refresh_api_logs(self):
        if not hasattr(self, 'api_log_tree'):
            return
        self.clear_tree(self.api_log_tree)
        for r in db.list_rows('app_events', order='id DESC', limit=100):
            self.api_log_tree.insert('', 'end', iid=r['id'], values=(r['created_at'], r['level'], r['title'], r['detail']))

    def odoo_test_from_api(self):
        self.save_api_settings()
        self.vars['odoo_user'] = tk.StringVar(value=self.settings.get('odoo_username',''))
        self.vars['odoo_key'] = tk.StringVar(value=self.settings.get('odoo_api_key',''))
        self.odoo_test()

    def _sync_page(self):
        root=self.page('Senkron')
        bar=self.panel(root,'Odoo senkron kuyruğu')
        ttk.Button(bar,text='Seçili kaydı Odoo’ya gönder',style='Accent.TButton',command=self.sync_selected).pack(side='left',padx=3)
        ttk.Button(bar,text='Seçili Kuyruk Kaydını Sil',command=lambda: self.delete_selected_row('sync_queue', 'sync', self.refresh_sync)).pack(side='left',padx=3)
        ttk.Button(bar,text='Yenile',command=self.refresh_sync).pack(side='left',padx=3)
        self.sync_tree=self.tree(root,['id','entity','entity_id','target','action','status','error','created'],{'id':'ID','entity':'Tip','entity_id':'Kayıt','target':'Hedef','action':'İşlem','status':'Durum','error':'Hata','created':'Tarih'},height=20)
        self.bind_select(self.sync_tree,'sync')

    def refresh_sync(self):
        self.clear_tree(self.sync_tree)
        for r in db.list_rows('sync_queue',order='id DESC',limit=500): self.sync_tree.insert('', 'end', iid=r['id'], values=(r['id'],r['entity_type'],r['entity_id'],r['target'],r['action'],r['status'],r['last_error'][:60],r['created_at']))

    def sync_selected(self):
        sid=self.selected_id('sync')
        if not sid: return
        s=db.get_row('sync_queue',sid)
        try:
            c=OdooClient(OdooConfig(self.settings.get('odoo_url'),self.settings.get('odoo_db'),self.settings.get('odoo_username'),self.settings.get('odoo_api_key')))
            if s['entity_type']=='quote':
                q=db.get_row('quotes',s['entity_id']); oid=c.create_crm_lead(q['title'],q['customer_name'],q['phone'],q['email'],q['price'],q['notes']); db.update('quotes',q['id'],{'odoo_id':str(oid)})
            elif s['entity_type']=='order':
                o=db.get_row('orders',s['entity_id']); oid=c.create_crm_lead(o['item_name'],o['customer_name'],o['phone'],o['email'],o['price'],o['notes']); db.update('orders',o['id'],{'odoo_lead_id':str(oid)})
            elif s['entity_type']=='catalog':
                p=db.get_row('catalog',s['entity_id']); oid=c.create_product(p['title'],p['estimated_price'],p['sku'],p['makerworld_link']); db.update('catalog',p['id'],{'odoo_product_id':str(oid)})
            db.update('sync_queue',sid,{'status':'Tamamlandı','last_error':''}); self.refresh_sync(); self.set_status('Odoo senkron tamamlandı')
        except Exception as e:
            db.update('sync_queue',sid,{'status':'Hata','last_error':str(e)}); self.refresh_sync(); messagebox.showerror('Senkron hatası',str(e))

    # ---------- Settings ----------
    def _settings_page(self):
        root=self.page('Ayarlar')
        visual=self.panel(root,'Arayüz, operatör ve animasyon ayarları')
        self.ui_setting_vars={}
        self.ui_setting_vars['operator_name']=tk.StringVar(value=self.operator_name if self.operator_name in OPERATORS else 'Selim')
        self.ui_setting_vars['ui_theme']=tk.StringVar(value=self.settings.get('ui_theme','Nebula Mor'))
        self.ui_setting_vars['background_effect']=tk.StringVar(value=self.settings.get('background_effect','Aurora Pulse'))
        self.ui_setting_vars['button_style']=tk.StringVar(value=self.settings.get('button_style','Glow Neon'))
        self.ui_setting_vars['animation_level']=tk.StringVar(value=self.settings.get('animation_level','Hafif'))
        self.combo(visual,'Operatör',self.ui_setting_vars['operator_name'],OPERATORS,0,0,width=18)
        self.combo(visual,'Tema',self.ui_setting_vars['ui_theme'],list(THEME_PRESETS.keys()),0,2,width=18)
        self.combo(visual,'Arka plan efekti',self.ui_setting_vars['background_effect'],BACKGROUND_EFFECTS,0,4,width=18)
        self.combo(visual,'Buton stili',self.ui_setting_vars['button_style'],BUTTON_STYLES,1,0,width=18)
        self.combo(visual,'Animasyon seviyesi',self.ui_setting_vars['animation_level'],ANIMATION_LEVELS,1,2,width=18)
        tk.Label(visual,text='Not: Değişiklikler kaydedilir; tema renklerinin tamamı uygulamayı yeniden açınca kusursuz uygulanır. Ambiyans şeridi anında yenilenir.',bg=self.colors['card'],fg=self.colors['muted'],font=('Segoe UI',8)).grid(row=2,column=0,columnspan=6,sticky='w',padx=4,pady=(4,8))
        bar=tk.Frame(visual,bg=self.colors['card']); bar.grid(row=3,column=0,columnspan=6,sticky='w',padx=4,pady=6)
        ttk.Button(bar,text='Arayüz Ayarlarını Kaydet',style='Accent.TButton',command=self.save_ui_settings).pack(side='left',padx=3)
        ttk.Button(bar,text='Ambiyans Önizle',command=self.preview_ambient).pack(side='left',padx=3)

        form=self.panel(root,'Fiyatlandırma ayarları')
        keys=['pla_cost_kg','petg_cost_kg','abs_cost_kg','asa_cost_kg','tpu_cost_kg','support_cost_kg','machine_hour_rate','labor_fee','design_hour_rate','post_process_fee','packaging_fee','failure_rate','profit_rate','vat_rate','commission_rate','minimum_price','currency']
        labels=['PLA kg','PETG kg','ABS kg','ASA kg','TPU kg','Support kg','Makine saat','İşçilik','Modelleme saat','Son işlem','Paketleme','Fire oran','Kâr oran','KDV','Komisyon','Minimum fiyat','Para birimi']
        self.setting_vars={}
        for i,(k,l) in enumerate(zip(keys,labels)):
            self.setting_vars[k]=tk.StringVar(value=self.settings.get(k,''))
            self.entry(form,l,self.setting_vars[k],i//3,(i%3)*2,width=14)
        ttk.Button(form,text='Fiyatlandırmayı Kaydet',style='Accent.TButton',command=self.save_pricing_settings).grid(row=6,column=0,sticky='w',padx=4,pady=8)

        cost=self.panel(root,'Maliyet kalemleri / ürün fiyatları yönetimi')
        self.vars['cost_id']=tk.StringVar(value='')
        self.vars['cost_key']=tk.StringVar(value='')
        self.vars['cost_name']=tk.StringVar(value='')
        self.vars['cost_group']=tk.StringVar(value='Malzeme')
        self.vars['cost_unit']=tk.StringVar(value='TL/kg')
        self.vars['cost_value']=tk.StringVar(value='0')
        self.entry(cost,'Anahtar',self.vars['cost_key'],0,0,width=24)
        self.entry(cost,'Ad',self.vars['cost_name'],0,2,width=30)
        self.entry(cost,'Grup',self.vars['cost_group'],0,4,width=14)
        self.entry(cost,'Birim',self.vars['cost_unit'],1,0,width=12)
        self.entry(cost,'Değer',self.vars['cost_value'],1,2,width=14)
        costrow=tk.Frame(cost,bg=self.colors['card']); costrow.grid(row=2,column=0,columnspan=6,sticky='w',padx=4,pady=4)
        ttk.Button(costrow,text='Maliyet Kalemi Ekle',style='Accent.TButton',command=self.add_cost_item).pack(side='left',padx=3)
        ttk.Button(costrow,text='Seçileni Forma Al',command=self.load_cost_item_form).pack(side='left',padx=3)
        ttk.Button(costrow,text='Güncelle',command=self.update_cost_item).pack(side='left',padx=3)
        ttk.Button(costrow,text='Sil / Pasifleştir',command=self.delete_cost_item).pack(side='left',padx=3)
        ttk.Button(costrow,text='Varsayılan Maliyetleri Geri Yükle',command=self.restore_default_cost_items).pack(side='left',padx=3)
        ttk.Button(costrow,text='Formu Temizle',command=self.clear_cost_item_form).pack(side='left',padx=3)
        cost_tree_host=tk.Frame(cost,bg=self.colors['card'])
        cost_tree_host.grid(row=3,column=0,columnspan=6,sticky='nsew',padx=4,pady=(6,4))
        cost.rowconfigure(3,weight=1)
        for _c in range(6):
            cost.columnconfigure(_c,weight=1)
        self.cost_tree=self.tree(cost_tree_host,['id','key','name','group','unit','value','active'],{'id':'ID','key':'Anahtar','name':'Ad','group':'Grup','unit':'Birim','value':'Değer','active':'Aktif'},height=7)
        self.bind_select(self.cost_tree,'cost_item')

        tools=self.panel(root,'Veri araçları')
        ttk.Button(tools,text='Tüm Verileri Excel Dışa Aktar',command=self.export_all).pack(side='left',padx=3)
        ttk.Button(tools,text='Veritabanı Yedekle',command=self.backup_db).pack(side='left',padx=3)
        ttk.Button(tools,text='Veri Klasörünü Aç',command=lambda: webbrowser.open(str(db.APP_DIR))).pack(side='left',padx=3)

    def preview_ambient(self):
        if hasattr(self, 'ui_setting_vars'):
            self.background_effect=self.ui_setting_vars['background_effect'].get()
            self.animation_level=self.ui_setting_vars['animation_level'].get()
            self.button_style=self.ui_setting_vars['button_style'].get()
        self.fx_tick += 1
        self._draw_fx_frame()
        self.set_status('Ambiyans önizleme yenilendi')

    def save_ui_settings(self):
        vals={k:v.get() for k,v in self.ui_setting_vars.items()}
        if vals.get('operator_name') not in OPERATORS:
            vals['operator_name']='Selim'
        db.save_settings(vals)
        self.settings.update(vals)
        self.operator_var.set(vals['operator_name'])
        self.change_operator()
        self.ui_theme=vals.get('ui_theme','Nebula Mor')
        self.background_effect=vals.get('background_effect','Aurora Pulse')
        self.button_style=vals.get('button_style','Glow Neon')
        self.animation_level=vals.get('animation_level','Hafif')
        self.colors=self._build_colors()
        self._style()
        self._draw_fx_frame()
        self.set_status('Arayüz ayarları kaydedildi. Tam tema için uygulamayı yeniden açabilirsin.')

    def save_pricing_settings(self):
        vals={k:v.get() for k,v in self.setting_vars.items()}; db.save_settings(vals); self.settings.update(vals); self.set_status('Fiyatlandırma ayarları kaydedildi')


    # ---------- Cost items ----------
    def refresh_cost_items(self):
        if not hasattr(self, 'cost_tree'):
            return
        self.clear_tree(self.cost_tree)
        for r in db.list_rows('cost_items', order='group_name, name', limit=500):
            self.cost_tree.insert('', 'end', iid=r['id'], values=(r['id'], r['setting_key'], r['name'], r['group_name'], r['unit'], r['value'], 'Evet' if r['active'] else 'Hayır'))

    def clear_cost_item_form(self):
        for k, v in [('cost_id',''),('cost_key',''),('cost_name',''),('cost_group','Malzeme'),('cost_unit','TL/kg'),('cost_value','0')]:
            if k in self.vars:
                self.vars[k].set(v)

    def load_cost_item_form(self):
        rid = self.selected_id('cost_item'); r = db.get_row('cost_items', rid) if rid else None
        if not r: return
        self.vars['cost_id'].set(str(r['id'])); self.vars['cost_key'].set(r['setting_key']); self.vars['cost_name'].set(r['name'])
        self.vars['cost_group'].set(r['group_name']); self.vars['cost_unit'].set(r['unit']); self.vars['cost_value'].set(str(r['value']))
        self.set_status('Maliyet kalemi forma alındı')

    def add_cost_item(self):
        key = self.vars['cost_key'].get().strip()
        name = self.vars['cost_name'].get().strip()
        if not key or not name:
            return messagebox.showwarning('Eksik bilgi', 'Anahtar ve ad zorunlu tennim.')
        val = fnum(self.vars['cost_value'].get())
        try:
            cid = db.insert('cost_items', {'setting_key': key, 'name': name, 'group_name': self.vars['cost_group'].get(), 'unit': self.vars['cost_unit'].get(), 'value': val, 'active': 1})
        except Exception:
            return messagebox.showerror('Aynı anahtar var', 'Bu anahtar zaten kayıtlı. Seçili kaydı forma alıp Güncelle kullan.')
        db.save_setting(key, val)
        self.settings[key] = str(val)
        self.refresh_cost_items(); self.set_status(f'Maliyet kalemi eklendi #{cid}')

    def update_cost_item(self):
        rid = self.selected_id('cost_item') or inum(self.vars.get('cost_id', tk.StringVar()).get(), 0)
        if not rid: return messagebox.showwarning('Seçim yok', 'Önce maliyet kalemi seç.')
        key = self.vars['cost_key'].get().strip(); name = self.vars['cost_name'].get().strip(); val = fnum(self.vars['cost_value'].get())
        if not key or not name: return messagebox.showwarning('Eksik bilgi', 'Anahtar ve ad zorunlu.')
        db.update('cost_items', rid, {'setting_key': key, 'name': name, 'group_name': self.vars['cost_group'].get(), 'unit': self.vars['cost_unit'].get(), 'value': val, 'active': 1})
        db.save_setting(key, val)
        self.settings[key] = str(val)
        # Eski hızlı fiyatlandırma alanını da güncelle.
        if hasattr(self, 'setting_vars') and key in self.setting_vars:
            self.setting_vars[key].set(str(val))
        self.refresh_cost_items(); self.set_status('Maliyet kalemi güncellendi ve fiyatlamaya işlendi')

    def delete_cost_item(self):
        rid = self.selected_id('cost_item')
        if not rid: return messagebox.showwarning('Seçim yok', 'Önce maliyet kalemi seç.')
        r = db.get_row('cost_items', rid)
        if not r: return
        if not messagebox.askyesno('Sil / pasifleştir', f'{r["name"]} pasifleştirilsin mi?\n\nBu işlem ilgili ayarı 0 yapar, fiyat hesabını etkiler.'):
            return
        db.update('cost_items', rid, {'active': 0, 'value': 0})
        if r['setting_key']:
            db.save_setting(r['setting_key'], 0)
            self.settings[r['setting_key']] = '0'
            if hasattr(self, 'setting_vars') and r['setting_key'] in self.setting_vars:
                self.setting_vars[r['setting_key']].set('0')
        self.refresh_cost_items(); self.set_status('Maliyet kalemi pasifleştirildi')

    def restore_default_cost_items(self):
        if not messagebox.askyesno('Varsayılanları geri yükle', 'Maliyet ayarları varsayılan değerlere döndürülsün mü?'):
            return
        db.restore_default_cost_items()
        self.settings = db.get_settings()
        if hasattr(self, 'setting_vars'):
            for k, v in self.setting_vars.items():
                if k in self.settings:
                    v.set(self.settings[k])
        self.refresh_cost_items(); self.set_status('Varsayılan maliyetler geri yüklendi')

    # ---------- Common ----------
    def export_all(self):
        path=filedialog.asksaveasfilename(defaultextension='.xlsx',filetypes=[('Excel','*.xlsx')],initialfile='BunuDaBastik3D_tum_veriler.xlsx')
        if path:
            exporters.export_all(path); self.set_status('Excel dışa aktarıldı')

    def backup_db(self):
        p=db.backup_database(); messagebox.showinfo('Yedek alındı',str(p))


if __name__ == '__main__':
    try:
        logging.info('Main entry invoked argv=%s', sys.argv)
        App().mainloop()
        logging.info('Mainloop exited normally')
    except Exception:
        logging.critical('Fatal startup/runtime error', exc_info=True)
        try:
            root = tk.Tk(); root.withdraw()
            log_path = LOG_DIR / 'app_debug.log'
            messagebox.showerror('BunuDaBastık3D Hata', 'Uygulama açılırken hata oluştu. Log dosyası:\n' + str(log_path))
            root.destroy()
        except Exception:
            pass
        raise
