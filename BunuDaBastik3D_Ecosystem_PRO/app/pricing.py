from __future__ import annotations


def fnum(value, default=0.0):
    try:
        if value is None:
            return default
        return float(str(value).strip().replace(',', '.'))
    except Exception:
        return default


def inum(value, default=0):
    try:
        return int(float(str(value).strip().replace(',', '.')))
    except Exception:
        return default


def calculate_price(settings: dict, material: str, grams: float, support_grams: float, time_min: float, quantity: int = 1,
                    design_minutes: float = 0, post_process_fee: float | None = None):
    material = (material or 'PLA').upper()
    grams = fnum(grams)
    support_grams = fnum(support_grams)
    time_min = fnum(time_min)
    quantity = max(inum(quantity, 1), 1)
    design_minutes = fnum(design_minutes)

    mat_key = f"{material.lower()}_cost_kg"
    mat_kg_cost = fnum(settings.get(mat_key), fnum(settings.get('pla_cost_kg'), 650))
    support_kg_cost = fnum(settings.get('support_cost_kg'), 1400)
    machine_hour_rate = fnum(settings.get('machine_hour_rate'), 70)
    labor_fee = fnum(settings.get('labor_fee'), 60)
    design_hour_rate = fnum(settings.get('design_hour_rate'), 350)
    if post_process_fee is None:
        post_process_fee = fnum(settings.get('post_process_fee'), 40)
    packaging_fee = fnum(settings.get('packaging_fee'), 25)
    failure_rate = fnum(settings.get('failure_rate'), 0.12)
    profit_rate = fnum(settings.get('profit_rate'), 0.70)
    vat_rate = fnum(settings.get('vat_rate'), 0.20)
    commission_rate = fnum(settings.get('commission_rate'), 0.00)
    minimum_price = fnum(settings.get('minimum_price'), 250)

    material_cost = (grams / 1000.0) * mat_kg_cost
    support_cost = (support_grams / 1000.0) * support_kg_cost
    machine_cost = (time_min / 60.0) * machine_hour_rate
    design_cost = (design_minutes / 60.0) * design_hour_rate
    direct_cost = material_cost + support_cost + machine_cost + labor_fee + design_cost + post_process_fee + packaging_fee
    risk_cost = direct_cost * failure_rate
    cost_with_risk = direct_cost + risk_cost
    profit = cost_with_risk * profit_rate
    subtotal = cost_with_risk + profit
    commission = subtotal * commission_rate
    vat = (subtotal + commission) * vat_rate
    single_price = max(subtotal + commission + vat, minimum_price)
    total_price = single_price * quantity
    total_cost = cost_with_risk * quantity

    return {
        'material_cost': material_cost * quantity,
        'support_cost': support_cost * quantity,
        'machine_cost': machine_cost * quantity,
        'labor_fee': labor_fee * quantity,
        'design_cost': design_cost * quantity,
        'post_process_fee': post_process_fee * quantity,
        'packaging_fee': packaging_fee * quantity,
        'risk_cost': risk_cost * quantity,
        'profit': profit * quantity,
        'commission': commission * quantity,
        'vat': vat * quantity,
        'cost_estimate': total_cost,
        'single_price': single_price,
        'total_price': total_price,
        'margin_amount': total_price - total_cost,
    }


def fmt_money(value, currency='TL'):
    try:
        return f"{float(value):,.2f} {currency}".replace(',', '_').replace('.', ',').replace('_', '.')
    except Exception:
        return f"{value} {currency}"


def format_breakdown(breakdown: dict, currency='TL'):
    labels = [
        ('material_cost', 'Model malzemesi'),
        ('support_cost', 'Destek malzemesi'),
        ('machine_cost', 'Makine süresi'),
        ('labor_fee', 'İşçilik'),
        ('design_cost', 'Modelleme'),
        ('post_process_fee', 'Son işlem'),
        ('packaging_fee', 'Paketleme'),
        ('risk_cost', 'Fire / başarısız baskı payı'),
        ('profit', 'Kâr'),
        ('commission', 'Komisyon'),
        ('vat', 'KDV'),
        ('total_price', 'Toplam teklif'),
    ]
    return '\n'.join(f"{label}: {fmt_money(breakdown.get(key, 0), currency)}" for key, label in labels)
