from __future__ import annotations
import xmlrpc.client
from dataclasses import dataclass


@dataclass
class OdooConfig:
    url: str
    db: str
    username: str
    api_key: str


class OdooClient:
    def __init__(self, config: OdooConfig):
        self.config = config
        self.uid = None

    def _common(self):
        return xmlrpc.client.ServerProxy(f"{self.config.url.rstrip('/')}/xmlrpc/2/common")

    def _models(self):
        return xmlrpc.client.ServerProxy(f"{self.config.url.rstrip('/')}/xmlrpc/2/object")

    def authenticate(self):
        if not all([self.config.url, self.config.db, self.config.username, self.config.api_key]):
            raise ValueError('Odoo URL, database, kullanıcı ve API key gerekli.')
        self.uid = self._common().authenticate(self.config.db, self.config.username, self.config.api_key, {})
        if not self.uid:
            raise RuntimeError('Odoo kimlik doğrulama başarısız.')
        return self.uid

    def execute_kw(self, model, method, args=None, kwargs=None):
        if self.uid is None:
            self.authenticate()
        return self._models().execute_kw(self.config.db, self.uid, self.config.api_key, model, method, args or [], kwargs or {})

    def create_partner(self, name, phone='', email=''):
        vals = {'name': name or 'BunuDaBastık3D Müşteri', 'phone': phone, 'email': email}
        return self.execute_kw('res.partner', 'create', [vals])

    def create_crm_lead(self, title, customer_name='', phone='', email='', expected_revenue=0, description=''):
        partner_id = False
        if customer_name:
            partner_id = self.create_partner(customer_name, phone, email)
        vals = {
            'name': title or '3D Baskı Talebi',
            'contact_name': customer_name,
            'phone': phone,
            'email_from': email,
            'expected_revenue': float(expected_revenue or 0),
            'description': description,
        }
        if partner_id:
            vals['partner_id'] = partner_id
        return self.execute_kw('crm.lead', 'create', [vals])

    def create_product(self, name, price, default_code='', description=''):
        vals = {
            'name': name or '3D Baskı Ürünü',
            'list_price': float(price or 0),
            'default_code': default_code,
            'description_sale': description,
            'type': 'service',
        }
        return self.execute_kw('product.template', 'create', [vals])
