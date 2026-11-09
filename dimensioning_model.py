"""Parte B: estimación comercial PRE-discovery, separada del ROI de la oferta."""
from __future__ import annotations
from collections import defaultdict


def calculate_dimensioning(dimensioning: dict, approved_budget: float) -> dict:
    """Hasta mes 12 escala el trabajo inicial; luego crece sólo el soporte mensual."""
    assessment = float(dimensioning['assessment_usd'])
    monthly = float(dimensioning['managed_monthly_usd'])
    months = int(dimensioning.get('horizon_months', dimensioning['managed_months']))
    if not 1 <= months <= 24:
        raise ValueError('El plazo del dimensionamiento debe estar entre 1 y 24 meses.')
    period_factor = min(months, 12) / 12.0  # Ingeniería inicial no crece después del mes 12
    items = dimensioning['service_lines']
    # Fixed lines have been assigned explicitly by the original workbook.
    def breakdown(factor: float):
        categories = defaultdict(float)
        records = []
        engineer_total = 0.0
        for line in items:
            hours = int(line['hours'])
            rate = float(line['hourly_rate_usd'])
            adjusted_hours = hours * factor * period_factor
            cost = adjusted_hours * rate
            engineer_total += cost
            categories[line['category']] += cost
            records.append({
                'Categoría': line['category'], 'Actividad':line['activity'],
                'Horas base': hours, 'Tarifa USD/h': rate,
                'Horas ajustadas': adjusted_hours, 'Total USD':cost,
            })
        categories['Cloud Security & Compliance'] += assessment
        categories['Cloud Operations & Reliability'] += monthly * months
        total = engineer_total + assessment + monthly * months
        return {'total':total, 'engineer_total': engineer_total,
                'assessment':assessment, 'recurring': monthly * months,
                'percentage_budget':total / approved_budget if approved_budget else 0.0,
                'horizon_months': months,
                'by_category':dict(categories), 'records':records}
    scenarios = {
        name: breakdown(float(multiplier))
        for name,multiplier in dimensioning['multipliers'].items()
    }
    return {'scenarios':scenarios, 'base':scenarios['Base']}
