from __future__ import annotations
import re


def extract_model_id(link: str) -> str:
    if not link:
        return ''
    patterns = [r'/models/(\d+)', r'modelId=(\d+)', r'model_id=(\d+)', r'[?&]id=(\d+)']
    for p in patterns:
        m = re.search(p, link)
        if m:
            return m.group(1)
    m = re.search(r'(\d{4,})', link)
    return m.group(1) if m else ''


def title_from_link(link: str) -> str:
    if not link:
        return ''
    tail = link.rstrip('/').split('/')[-1]
    tail = tail.split('?')[0].replace('-', ' ').replace('_', ' ')
    return tail.title()[:80]
