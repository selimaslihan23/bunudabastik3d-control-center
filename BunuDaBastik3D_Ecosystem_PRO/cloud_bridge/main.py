from __future__ import annotations
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import PlainTextResponse

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app import db

BRIDGE_DB = Path(os.environ.get('BDB_BRIDGE_DB', db.DB_PATH))
# Bridge ve masaüstü aynı DB'yi kullanabilir; deployment'ta BDB_BRIDGE_DB ile ayrı DB verilebilir.
db.DB_PATH = BRIDGE_DB
db.init_db(BRIDGE_DB)
VERIFY_TOKEN = os.environ.get('WHATSAPP_VERIFY_TOKEN', 'bunudabastik3d_verify')
WEBHOOK_SECRET = os.environ.get('BDB_WEBHOOK_SECRET', '')

app = FastAPI(title='BunuDaBastık3D Cloud Bridge', version='3.0.0-final-connector')


def _headers_ok(request: Request) -> bool:
    if not WEBHOOK_SECRET:
        return True
    return request.headers.get('x-bdb-secret') == WEBHOOK_SECRET


def _insert(payload: Dict[str, Any], source_default: str):
    rid = db.import_inbox_item(payload, source_default=source_default)
    db.log_event(f'{source_default} webhook alındı', f'Inbox #{rid}')
    return rid


def _flatten_google_form(payload: Dict[str, Any]) -> Dict[str, Any]:
    # Apps Script örneği bu alanları doğrudan gönderir. Farklı isimler gelirse burada toparlıyoruz.
    lower = {str(k).lower(): v for k, v in payload.items()}
    def pick(*keys, default=''):
        for k in keys:
            if k in payload and payload[k] not in (None, ''):
                return payload[k]
            if k.lower() in lower and lower[k.lower()] not in (None, ''):
                return lower[k.lower()]
        return default
    return {
        'source': 'Google Forms',
        'external_id': str(pick('response_id', 'Response ID', 'timestamp', default='')),
        'customer_name': pick('Ad Soyad', 'name', 'customer_name', 'Müşteri Adı'),
        'phone': pick('Telefon', 'phone', 'whatsapp'),
        'email': pick('E-posta', 'Email', 'email'),
        'subject': pick('Ürün / Proje Adı', 'Konu', 'subject', 'title', default='Google Forms Talebi'),
        'message': pick('Açıklama', 'message', 'body', 'Notlar'),
        'makerworld_link': pick('MakerWorld Link', 'makerworld_link', 'Link'),
        'requested_material': pick('Malzeme', 'material', default='PLA'),
        'requested_color': pick('Renk', 'color'),
        'quantity': pick('Adet', 'quantity', default=1),
        'grams': pick('Gram', 'grams', default=0),
        'support_grams': pick('Destek Gram', 'support_grams', default=0),
        'time_min': pick('Baskı Süresi Dakika', 'time_min', default=0),
        'attachment_urls': pick('Dosya Linkleri', 'attachments', default=[]),
        'raw_json': payload,
    }


def _parse_whatsapp(payload: Dict[str, Any]) -> list[Dict[str, Any]]:
    items = []
    try:
        entries = payload.get('entry', [])
        for entry in entries:
            for change in entry.get('changes', []):
                value = change.get('value', {})
                contacts = {c.get('wa_id'): c.get('profile', {}).get('name', '') for c in value.get('contacts', [])}
                phone_number_id = value.get('metadata', {}).get('phone_number_id', '')
                for msg in value.get('messages', []):
                    wa_id = msg.get('from', '')
                    body = ''
                    attachments = []
                    msg_type = msg.get('type')
                    if msg_type == 'text':
                        body = msg.get('text', {}).get('body', '')
                    elif msg_type in ('image', 'document', 'audio', 'video'):
                        media = msg.get(msg_type, {})
                        body = media.get('caption', f'{msg_type} dosyası gönderildi')
                        attachments.append({'type': msg_type, 'id': media.get('id'), 'filename': media.get('filename', '')})
                    else:
                        body = json.dumps(msg, ensure_ascii=False)
                    items.append({
                        'source': 'WhatsApp',
                        'channel_id': phone_number_id,
                        'external_id': msg.get('id', ''),
                        'customer_name': contacts.get(wa_id, ''),
                        'phone': wa_id,
                        'subject': 'WhatsApp Talebi',
                        'message': body,
                        'attachment_urls': attachments,
                        'raw_json': msg,
                    })
    except Exception:
        items.append({'source': 'WhatsApp', 'subject': 'WhatsApp Raw Payload', 'message': json.dumps(payload, ensure_ascii=False), 'raw_json': payload})
    return items


def _parse_instagram(payload: Dict[str, Any]) -> list[Dict[str, Any]]:
    """Meta Instagram Messaging webhook payloadlarını gelen kutusu formatına çevirir.

    Desteklenen yaygın şekiller:
    - entry[].messaging[]  -> Messenger API for Instagram mesajları
    - entry[].changes[]    -> bazı Meta webhook test payloadları / yorum varyantları
    """
    items: list[Dict[str, Any]] = []
    try:
        for entry in payload.get('entry', []):
            page_id = entry.get('id', '')
            # Instagram Messaging webhook formatı
            for ev in entry.get('messaging', []) or []:
                sender_id = str((ev.get('sender') or {}).get('id', ''))
                recipient_id = str((ev.get('recipient') or {}).get('id', page_id))
                msg = ev.get('message') or {}
                body = msg.get('text') or ''
                attachments = []
                for a in msg.get('attachments') or []:
                    payload_url = (a.get('payload') or {}).get('url') or (a.get('payload') or {}).get('id') or ''
                    attachments.append({'type': a.get('type', 'attachment'), 'url': payload_url})
                if not body and attachments:
                    body = 'Instagram DM eki gönderildi'
                if not body:
                    body = json.dumps(ev, ensure_ascii=False)
                items.append({
                    'source': 'Instagram',
                    'channel_id': recipient_id,
                    'external_id': msg.get('mid') or str(ev.get('timestamp', '')),
                    'customer_name': '',
                    'instagram': sender_id,
                    'subject': 'Instagram DM',
                    'message': body,
                    'attachment_urls': attachments,
                    'raw_json': ev,
                })
            # Daha genel changes formatı; test/yorum payloadları için ham içerik düşürür.
            for change in entry.get('changes', []) or []:
                value = change.get('value', {})
                field = change.get('field', 'instagram')
                msg_text = value.get('text') or value.get('message') or value.get('body') or json.dumps(value, ensure_ascii=False)
                items.append({
                    'source': 'Instagram',
                    'channel_id': page_id,
                    'external_id': str(value.get('id') or value.get('mid') or ''),
                    'customer_name': value.get('from', {}).get('username', '') if isinstance(value.get('from'), dict) else '',
                    'instagram': value.get('from', {}).get('id', '') if isinstance(value.get('from'), dict) else '',
                    'subject': f'Instagram {field}',
                    'message': msg_text,
                    'attachment_urls': value.get('attachments') or [],
                    'raw_json': change,
                })
    except Exception:
        items.append({'source': 'Instagram', 'subject': 'Instagram Raw Payload', 'message': json.dumps(payload, ensure_ascii=False), 'raw_json': payload})
    return items


@app.get('/health')
def health():
    return {'ok': True, 'service': 'BunuDaBastık3D Cloud Bridge', 'db': str(BRIDGE_DB)}


@app.get('/webhook/whatsapp')
def verify_whatsapp(request: Request):
    params = dict(request.query_params)
    mode = params.get('hub.mode')
    token = params.get('hub.verify_token')
    challenge = params.get('hub.challenge')
    if mode == 'subscribe' and token == VERIFY_TOKEN:
        return PlainTextResponse(challenge or '')
    raise HTTPException(status_code=403, detail='Verify token hatalı')


@app.post('/webhook/whatsapp')
async def whatsapp_webhook(request: Request):
    if not _headers_ok(request):
        raise HTTPException(status_code=401, detail='Secret hatalı')
    payload = await request.json()
    ids = []
    for item in _parse_whatsapp(payload):
        ids.append(_insert(item, 'WhatsApp'))
    return {'ok': True, 'inserted': ids}


@app.get('/webhook/instagram')
def verify_instagram(request: Request):
    params = dict(request.query_params)
    mode = params.get('hub.mode')
    token = params.get('hub.verify_token')
    challenge = params.get('hub.challenge')
    if mode == 'subscribe' and token == VERIFY_TOKEN:
        return PlainTextResponse(challenge or '')
    raise HTTPException(status_code=403, detail='Verify token hatalı')


@app.post('/webhook/instagram')
async def instagram_webhook(request: Request):
    if not _headers_ok(request):
        raise HTTPException(status_code=401, detail='Secret hatalı')
    payload = await request.json()
    ids = []
    for item in _parse_instagram(payload):
        ids.append(_insert(item, 'Instagram'))
    return {'ok': True, 'inserted': ids}


@app.post('/webhook/google-forms')
async def google_forms_webhook(request: Request):
    if not _headers_ok(request):
        raise HTTPException(status_code=401, detail='Secret hatalı')
    payload = await request.json()
    item = _flatten_google_form(payload)
    rid = _insert(item, 'Google Forms')
    return {'ok': True, 'inbox_id': rid}


@app.post('/webhook/email')
async def email_webhook(request: Request):
    if not _headers_ok(request):
        raise HTTPException(status_code=401, detail='Secret hatalı')
    payload = await request.json()
    item = {
        'source': 'Email',
        'external_id': payload.get('message_id') or payload.get('id') or '',
        'customer_name': payload.get('from_name') or '',
        'email': payload.get('from_email') or payload.get('from') or '',
        'subject': payload.get('subject') or 'E-posta Talebi',
        'message': payload.get('body') or payload.get('text') or '',
        'attachment_urls': payload.get('attachments') or [],
        'raw_json': payload,
    }
    rid = _insert(item, 'Email')
    return {'ok': True, 'inbox_id': rid}


@app.post('/webhook/manual')
async def manual_webhook(request: Request):
    if not _headers_ok(request):
        raise HTTPException(status_code=401, detail='Secret hatalı')
    payload = await request.json()
    rid = _insert(payload, payload.get('source', 'Manual'))
    return {'ok': True, 'inbox_id': rid}


@app.get('/api/inbox')
def api_inbox(since_id: int = 0, limit: int = 200):
    rows = db.list_rows('inbox_items', 'id > ?', (since_id,), order='id ASC', limit=limit)
    return {'ok': True, 'items': [dict(r) for r in rows]}


@app.post('/api/inbox/{item_id}/status')
async def update_status(item_id: int, request: Request):
    payload = await request.json()
    db.update('inbox_items', item_id, {'status': payload.get('status', 'İncelenecek')})
    return {'ok': True}


if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host='0.0.0.0', port=int(os.environ.get('PORT', '8787')))
