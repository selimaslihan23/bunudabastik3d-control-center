from __future__ import annotations
import email
import imaplib
from email.header import decode_header
from email.utils import parseaddr


def _decode(value):
    if not value:
        return ''
    parts = decode_header(value)
    out = ''
    for text, enc in parts:
        if isinstance(text, bytes):
            out += text.decode(enc or 'utf-8', errors='replace')
        else:
            out += text
    return out


def _body_from_message(msg):
    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            disp = str(part.get('Content-Disposition') or '')
            if content_type == 'text/plain' and 'attachment' not in disp.lower():
                payload = part.get_payload(decode=True)
                if payload:
                    return payload.decode(part.get_content_charset() or 'utf-8', errors='replace')
        for part in msg.walk():
            if part.get_content_type() == 'text/html':
                payload = part.get_payload(decode=True)
                if payload:
                    html = payload.decode(part.get_content_charset() or 'utf-8', errors='replace')
                    return html.replace('<br>', '\n').replace('<br/>', '\n').replace('<br />', '\n')
    else:
        payload = msg.get_payload(decode=True)
        if payload:
            return payload.decode(msg.get_content_charset() or 'utf-8', errors='replace')
    return ''


def fetch_imap_emails(host, port, username, password, mailbox='INBOX', limit=25, only_unseen=True):
    if not host or not username or not password:
        raise ValueError('IMAP host, kullanıcı adı ve parola gerekli.')
    limit = max(int(limit or 25), 1)
    items = []
    with imaplib.IMAP4_SSL(host, int(port or 993)) as mail:
        mail.login(username, password)
        mail.select(mailbox or 'INBOX')
        criteria = '(UNSEEN)' if only_unseen else 'ALL'
        status, data = mail.search(None, criteria)
        if status != 'OK':
            raise RuntimeError('E-posta arama başarısız oldu.')
        ids = data[0].split()[-limit:]
        for uid in reversed(ids):
            status, msg_data = mail.fetch(uid, '(RFC822)')
            if status != 'OK' or not msg_data:
                continue
            raw = msg_data[0][1]
            msg = email.message_from_bytes(raw)
            from_name, from_addr = parseaddr(_decode(msg.get('From', '')))
            to_name, to_addr = parseaddr(_decode(msg.get('To', '')))
            has_attachments = 0
            if msg.is_multipart():
                for part in msg.walk():
                    disp = str(part.get('Content-Disposition') or '')
                    if 'attachment' in disp.lower():
                        has_attachments = 1
                        break
            items.append({
                'imap_uid': uid.decode() if isinstance(uid, bytes) else str(uid),
                'from_addr': from_addr or from_name,
                'to_addr': to_addr or to_name,
                'subject': _decode(msg.get('Subject', '')),
                'body': _body_from_message(msg)[:8000],
                'date_text': _decode(msg.get('Date', '')),
                'has_attachments': has_attachments,
            })
    return items
