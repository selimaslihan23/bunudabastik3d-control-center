from __future__ import annotations
import base64
import os
import shutil
from pathlib import Path
from typing import Any, Dict, List, Optional

# Bu dosya bilinçli olarak Google bağımlılıklarını fonksiyon içinde import eder.
# Böylece Google paketleri kurulmamışsa uygulamanın tamamı açılmaya devam eder.
try:
    import db  # type: ignore
    APP_DIR = db.APP_DIR
except Exception:
    APP_DIR = Path.home() / '.bunudabastik3d_ecosystem'
    APP_DIR.mkdir(parents=True, exist_ok=True)

CREDENTIALS_PATH = APP_DIR / 'gmail_credentials.json'
TOKEN_PATH = APP_DIR / 'gmail_token.json'
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']


def _imports():
    try:
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow
        from google.auth.transport.requests import Request
        from googleapiclient.discovery import build
        return Credentials, InstalledAppFlow, Request, build
    except Exception as exc:
        raise RuntimeError(
            'Google OAuth paketleri kurulu değil. requirements.txt güncel paketle kurulum yapın veya build dosyasını yeniden çalıştırın. '\
            'Gerekli paketler: google-api-python-client, google-auth-oauthlib, google-auth-httplib2.\n\nDetay: ' + str(exc)
        )


def set_credentials_file(source_path: str | Path) -> Path:
    src = Path(source_path)
    if not src.exists():
        raise FileNotFoundError('credentials.json dosyası bulunamadı.')
    if src.suffix.lower() != '.json':
        raise ValueError('Google OAuth istemci dosyası .json olmalı.')
    APP_DIR.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, CREDENTIALS_PATH)
    return CREDENTIALS_PATH


def has_credentials_file() -> bool:
    return CREDENTIALS_PATH.exists()


def has_token() -> bool:
    return TOKEN_PATH.exists()


def disconnect(delete_credentials: bool = False) -> None:
    if TOKEN_PATH.exists():
        TOKEN_PATH.unlink()
    if delete_credentials and CREDENTIALS_PATH.exists():
        CREDENTIALS_PATH.unlink()


def build_service(interactive: bool = True):
    Credentials, InstalledAppFlow, Request, build = _imports()
    creds = None
    if TOKEN_PATH.exists():
        try:
            creds = Credentials.from_authorized_user_file(str(TOKEN_PATH), SCOPES)
        except Exception:
            creds = None

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not interactive:
                raise RuntimeError('Gmail OAuth yetkisi yok. Önce “Gmail ile Bağlan / Yetki Ver” butonunu kullanın.')
            if not CREDENTIALS_PATH.exists():
                raise RuntimeError(
                    'Gmail OAuth credentials.json bulunamadı. Önce Google Cloud’dan Desktop OAuth istemci JSON dosyasını indirip uygulamada seçin.'
                )
            flow = InstalledAppFlow.from_client_secrets_file(str(CREDENTIALS_PATH), SCOPES)
            # port=0 boş bir yerel port seçer; Google giriş ekranı tarayıcıda açılır.
            creds = flow.run_local_server(port=0, prompt='consent')
        TOKEN_PATH.write_text(creds.to_json(), encoding='utf-8')

    return build('gmail', 'v1', credentials=creds, cache_discovery=False)


def get_profile() -> Dict[str, Any]:
    service = build_service(interactive=True)
    return service.users().getProfile(userId='me').execute()


def _header(headers: List[Dict[str, str]], name: str) -> str:
    target = name.lower()
    for h in headers or []:
        if h.get('name', '').lower() == target:
            return h.get('value', '')
    return ''


def _decode_body(data: str) -> str:
    if not data:
        return ''
    try:
        padded = data + '=' * (-len(data) % 4)
        return base64.urlsafe_b64decode(padded.encode('utf-8')).decode('utf-8', errors='replace')
    except Exception:
        return ''


def _walk_parts(payload: Dict[str, Any]):
    yield payload
    for p in payload.get('parts', []) or []:
        yield from _walk_parts(p)


def _extract_text_and_attachments(payload: Dict[str, Any]) -> tuple[str, int]:
    plain_chunks: List[str] = []
    html_chunks: List[str] = []
    attachment_count = 0
    for part in _walk_parts(payload):
        filename = part.get('filename') or ''
        body = part.get('body') or {}
        mime = part.get('mimeType') or ''
        if filename:
            attachment_count += 1
            continue
        data = body.get('data') or ''
        if not data:
            continue
        text = _decode_body(data)
        if mime == 'text/plain':
            plain_chunks.append(text)
        elif mime == 'text/html':
            # Basit temizlik; teklif talebine dönüştürmek için düz metin yeterli.
            import re
            cleaned = re.sub(r'<br\s*/?>', '\n', text, flags=re.I)
            cleaned = re.sub(r'<[^>]+>', ' ', cleaned)
            cleaned = re.sub(r'\s+', ' ', cleaned).strip()
            html_chunks.append(cleaned)
    body_text = '\n\n'.join([c.strip() for c in plain_chunks if c.strip()])
    if not body_text:
        body_text = '\n\n'.join([c.strip() for c in html_chunks if c.strip()])
    return body_text[:12000], attachment_count


def fetch_gmail_messages(limit: int | str = 25, query: str = 'in:inbox', include_spam_trash: bool = False) -> List[Dict[str, Any]]:
    service = build_service(interactive=False)
    try:
        limit_int = max(1, min(int(limit or 25), 100))
    except Exception:
        limit_int = 25
    q = (query or 'in:inbox').strip()
    req = service.users().messages().list(
        userId='me',
        maxResults=limit_int,
        q=q,
        includeSpamTrash=include_spam_trash,
    )
    resp = req.execute()
    rows: List[Dict[str, Any]] = []
    for msg in resp.get('messages', []) or []:
        mid = msg.get('id')
        if not mid:
            continue
        full = service.users().messages().get(userId='me', id=mid, format='full').execute()
        payload = full.get('payload') or {}
        headers = payload.get('headers') or []
        body, attachment_count = _extract_text_and_attachments(payload)
        rows.append({
            'imap_uid': 'gmail-' + str(mid),
            'from_addr': _header(headers, 'From'),
            'to_addr': _header(headers, 'To'),
            'subject': _header(headers, 'Subject') or '(Konu yok)',
            'body': body or full.get('snippet', ''),
            'date_text': _header(headers, 'Date'),
            'has_attachments': 1 if attachment_count else 0,
            'status': 'Yeni',
        })
    return rows
