"""Modelo financiero reproducible de Grupo Fénix. Solo biblioteca estándar."""
from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path
from typing import Any

DEFAULT_CONFIG = Path(__file__).with_name("assumptions.json")


def load_config(path: str | Path = DEFAULT_CONFIG) -> dict[str, Any]:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def phase_pricing(config: dict[str, Any]) -> tuple[list[dict[str, Any]], dict[int, float]]:
    items = []
    totals: dict[int, float] = defaultdict(float)
    for item in config["phase_line_items"]:
        cost = float(item["hours"]) * float(item["hourly_rate"])
        items.append({**item, "cost": cost})
        totals[int(item["phase"])] += cost
    return items, dict(totals)


def hourly_outage_cost(f: dict[str, float]) -> float:
    """Solo margen irreparable; evita confundir facturación con beneficio."""
    rev_hour = f["annual_company_revenue"] / (f["working_days_per_year"] * f["operating_hours_per_day"])
    return rev_hour * f["revenue_exposed_to_order_system_percent"] * f["unrecoverable_revenue_during_outage_percent"] * f["contribution_margin_on_lost_revenue_percent"]


def validate_config(config: dict[str, Any]) -> None:
    f = config["financial_inputs"]
    if f["monthly_aws_cost"] * 12 > f["annual_it_spend"]:
        raise ValueError("AWS anual no puede superar el gasto TI total sin justificación.")
    if f["analysis_horizon_months"] < 12 or f["payback_horizon_months"] < f["analysis_horizon_months"]:
        raise ValueError("Horizontes de análisis inconsistentes.")
    for k in ("it_savings_target_percent", "revenue_exposed_to_order_system_percent", "unrecoverable_revenue_during_outage_percent", "contribution_margin_on_lost_revenue_percent"):
        if not 0 <= f[k] <= 1:
            raise ValueError(f"{k} debe estar entre 0 y 1.")
    _, totals = phase_pricing(config)
    target = config["project_phase_budgets"]
    for p in (1, 2, 3):
        if abs(totals.get(p, 0) - float(target[str(p)])) > 0.01:
            raise ValueError(f"Fase {p}: detalle USD {totals.get(p, 0):,.2f} != presupuesto {target[str(p)]}")
    if abs(sum(totals.values()) - f["first_year_project_cost"]) > 0.01:
        raise ValueError("Suma de fases no coincide con precio del proyecto.")
    if abs(f["first_year_project_cost"] + f["commercial_reserve"] - f["approved_modernization_budget"]) > 0.01:
        raise ValueError("Oferta técnica más reserva no coincide con presupuesto aprobado.")
    if abs(sum(x["amount"] for x in config["commercial_reserve_allocation"]) - f["commercial_reserve"]) > 0.01:
        raise ValueError("El desglose ABM debe coincidir con la reserva comercial.")
    if not 0 <= f["benefit_realization_factor"] <= 1:
        raise ValueError("El factor de realización debe estar entre 0 y 1.")
    if any(f[k] < 1 for k in ("working_days_per_year", "operating_hours_per_day", "monthly_credit_applications")):
        raise ValueError("Días/horas/solicitudes deben ser positivos.")


def calculate(config: dict[str, Any]) -> dict[str, Any]:
    validate_config(config)
    f = config["financial_inputs"]
    _, phases = phase_pricing(config)
    aws_year = f["monthly_aws_cost"] * 12
    target_savings = f["annual_it_spend"] * f["it_savings_target_percent"]
    outage_cost = hourly_outage_cost(f)
    month_discount = (1 + f["annual_discount_rate"]) ** (1/12) - 1
    outcome: dict[str, Any] = {
        "shared": {
            "annual_it_spend": f["annual_it_spend"], "annual_aws_spend": aws_year,
            "aws_share_it": aws_year / f["annual_it_spend"],
            "non_aws_it_spend": f["annual_it_spend"] - aws_year,
            "annual_it_savings_target": target_savings,
            "it_spend_target": f["annual_it_spend"] - target_savings,
            "revenue_per_operating_hour": f["annual_company_revenue"] / (f["working_days_per_year"] * f["operating_hours_per_day"]),
            "lost_contribution_per_outage_hour": outage_cost,
            "project_investment": sum(phases.values()),
            "approved_budget": f["approved_modernization_budget"],
            "commercial_reserve": f["commercial_reserve"],
            "commercial_reserve_counted_in_roi": f["include_reserve_in_roi"],
            "phase_budgets": phases,
            "three_year_incremental_tco": f["first_year_project_cost"] + (f["commercial_reserve"] if f["include_reserve_in_roi"] else 0) + (f["monthly_incremental_support_after_year_1"] + f["monthly_incremental_cloud_cost"]) * 24,
        }, "scenarios": {}
    }
    starts = {"aws": int(f["start_month_aws_savings"]), "outage": int(f["start_month_outage_improvements"]), "credit": int(f["start_month_credit_conversion"])}
    for name, s in config["scenarios"].items():
        realization = f["benefit_realization_factor"]
        aws_monthly = f["monthly_aws_cost"] * s["aws_savings_pct"] * realization
        outage_monthly = outage_cost * s["avoided_outage_hours_annually"] / 12 * realization
        credit_monthly = f["monthly_credit_applications"] * s["credit_conversion_uplift_pp"] / 100 * f["net_incremental_margin_per_extra_approved_credit"] * realization
        annual_aws = 12 * aws_monthly
        annual_outage = 12 * outage_monthly
        annual_credit = 12 * credit_monthly
        cashflows = []
        cumulative = 0.0
        payback_month: float | None = None
        for month in range(1, int(f["payback_horizon_months"]) + 1):
            aws_benefit = aws_monthly if month >= starts["aws"] else 0
            outage_benefit = outage_monthly if month >= starts["outage"] else 0
            credit_benefit = credit_monthly if month >= starts["credit"] else 0
            if month <= 3:
                capex = phases[1] / 3
            elif month <= 8:
                capex = phases[2] / 5
            elif month <= 12:
                capex = phases[3] / 4
            else:
                capex = 0
            commercial_outlay = (f["commercial_reserve"] / 4 if f["include_reserve_in_roi"] and 9 <= month <= 12 else 0)
            capex += commercial_outlay
            new_ops_cost = 0 if month <= 12 else (f["monthly_incremental_support_after_year_1"] + f["monthly_incremental_cloud_cost"])
            total_benefit = aws_benefit + outage_benefit + credit_benefit
            net = total_benefit - capex - new_ops_cost
            prev = cumulative
            cumulative += net
            if payback_month is None and prev < 0 <= cumulative and month > 1:
                payback_month = (month - 1) + (-prev / net) if net > 0 else None
            cashflows.append({"month": month, "aws_savings": aws_benefit, "avoided_outage_margin": outage_benefit,
                              "incremental_credit_margin": credit_benefit, "total_benefit": total_benefit,
                              "implementation_cost": capex, "incremental_recurring_cost": new_ops_cost,
                              "net_flow": net, "cumulative_net": cumulative})
        three_year = cashflows[: int(f["analysis_horizon_months"])]
        benefits3 = sum(x["total_benefit"] for x in three_year)
        cost3 = sum(x["implementation_cost"] + x["incremental_recurring_cost"] for x in three_year)
        npv3 = sum(x["net_flow"] / ((1 + month_discount)**x["month"]) for x in three_year)
        year1 = cashflows[:12]
        aws_y1 = sum(x["aws_savings"] for x in year1)
        year1_it_spend = f["annual_it_spend"] - aws_y1 + f["first_year_project_cost"]  # incremental cloud cost starts year2
        later_it_spend = f["annual_it_spend"] - annual_aws + 12 * (f["monthly_incremental_support_after_year_1"] + f["monthly_incremental_cloud_cost"])
        annual_net_it_savings = f["annual_it_spend"] - later_it_spend
        outcome["scenarios"][name] = {
            "aws_annual_savings": annual_aws,
            "avoided_outage_annual_margin": annual_outage,
            "additional_loans_per_month": f["monthly_credit_applications"] * s["credit_conversion_uplift_pp"] / 100 * realization,
            "credit_annual_margin": annual_credit,
            "annual_stabilized_benefit": annual_aws + annual_outage + annual_credit,
            "year1_aws_savings": aws_y1,
            "year1_benefits": sum(x["total_benefit"] for x in year1),
            "year2_benefits": sum(x["total_benefit"] for x in cashflows[12:24]),
            "year3_benefits": sum(x["total_benefit"] for x in cashflows[24:36]),
            "three_year_benefits": benefits3,
            "three_year_tco": cost3,
            "three_year_roi": (benefits3-cost3) / cost3,
            "npv_3_years": npv3,
            "payback_month": payback_month,
            "year1_total_it_cash_spend": year1_it_spend,
            "year1_it_spend_change_pct": year1_it_spend / f["annual_it_spend"] - 1,
            "year1_commercial_spend_if_approved": f["commercial_reserve"] if f["include_reserve_in_roi"] else 0,
            "steady_it_spend_with_incremental_support": later_it_spend,
            "steady_net_it_savings": annual_net_it_savings,
            "steady_net_it_savings_pct": annual_net_it_savings / f["annual_it_spend"],
            "share_of_it_target_met": annual_net_it_savings / target_savings,
            "remaining_it_target_gap": target_savings - annual_net_it_savings,
            "cashflows": cashflows
        }
    return outcome


if __name__ == "__main__":
    result = calculate(load_config())
    print(json.dumps({"shared": result["shared"], "scenarios": {k: {a:b for a,b in s.items() if a != "cashflows"} for k,s in result["scenarios"].items()}}, indent=2, ensure_ascii=False))
