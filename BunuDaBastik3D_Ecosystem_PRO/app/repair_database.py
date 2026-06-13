from __future__ import annotations
import sys
from pathlib import Path

CURRENT_DIR = Path(__file__).resolve().parent
if str(CURRENT_DIR) not in sys.path:
    sys.path.insert(0, str(CURRENT_DIR))

import db

if __name__ == '__main__':
    db.init_db()
    print('BunuDaBastık3D veritabanı kontrol edildi ve eski sürüm kolonları onarıldı.')
    print(f'Veritabanı: {db.DB_PATH}')
