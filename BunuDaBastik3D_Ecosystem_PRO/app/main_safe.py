from __future__ import annotations
import os
import sys

# Safe mode: splash/login ekranlarını atlar ve ana pencereyi direkt açar.
os.environ['BDB_SAFE_MODE'] = '1'
os.environ['BDB_DEBUG'] = '1'

from main import App, logging

if __name__ == '__main__':
    logging.info('Safe launcher invoked argv=%s', sys.argv)
    App().mainloop()
