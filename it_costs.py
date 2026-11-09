"""Escenarios de gasto TI y data center on-prem. Solo biblioteca estándar.

NO incorporar estos ahorros al ROI contractual sin scope, fechas y costos validados.
"""
from __future__ import annotations
from typing import Any

SCENARIOS = ("Conservador", "Base", "Alto")


def dc_cost(config: dict[str, Any]) -> dict[str, float]:
    dc = config["dc_guatemala"]
    power_kw = dc["racks"] * dc["it_kw_per_rack"]
    energy_kwh = power_kw * dc["pue"] * dc["hours_per_year"]
    electricity = energy_kwh * dc["electricity_usd_per_kwh"]
    costs = {
      "Electricidad":electricity,
      "OEM soporte":dc["annual_oem_maintenance"],
      "UPS HVAC generadores":dc["annual_facility_equipment_maintenance"],
      "Local y seguridad física":dc["annual_space_security_insurance"],
      "Depreciación (no caja)":dc["annual_equipment_depreciation"],
    }
    savings = {}
    for scenario in SCENARIOS:
        savings[scenario] = sum(cost * dc["savings_rates"][key][scenario] for key,cost in costs.items())
    return {"it_kw":power_kw,"energy_kwh":energy_kwh,"electricity_usd":electricity,
      "annual_total":sum(costs.values()),"cost_components":costs,"savings":savings,
      "colo_gt_reference_usd_year":dc["racks"]*dc["rack_colo_guatemala_usd_month"]*12,
      "colo_cr_reference_usd_year":power_kw/2*dc["half_rack_colo_cr_usd_month"]*12}


def budget_and_savings(config: dict[str, Any]) -> dict[str, Any]:
    f = config["financial_inputs"]
    dc = dc_cost(config)
    annual_aws = f["monthly_aws_cost"] * 12
    budget = {"AWS":annual_aws,"DC Guatemala":dc["annual_total"]}
    for item in config["it_budget_categories"]:
        budget[item["name"]] = item["annual_budget"]
    residual = f["annual_it_spend"] - sum(budget.values())
    if residual < 0:
        raise ValueError("Partidas fijas exceden gasto TI total; reduzca supuestos o aumente gasto TI.")
    budget["Apps y datos (remanente no verificado)"] = residual
    scenario_savings = {}
    for scenario in SCENARIOS:
        aws = annual_aws * config["scenarios"][scenario]["aws_savings_pct"] * f["benefit_realization_factor"]
        dc_saving = dc["savings"][scenario]
        other = {item["name"]: item["annual_budget"]*item["savings_pct"][scenario]
                 for item in config["it_budget_categories"]}
        non_aws = dc_saving + sum(other.values())
        gross = aws + non_aws
        additional_support = 12*(f["monthly_incremental_support_after_year_1"] + f["monthly_incremental_cloud_cost"])
        net = gross - additional_support
        target = f["annual_it_spend"] * f["it_savings_target_percent"]
        scenario_savings[scenario] = {"aws_usd":aws,"dc_usd":dc_saving,
         "other_noaws_usd":other,"noaws_usd":non_aws,"gross_usd":gross,
         "new_support_usd":additional_support,"net_usd":net,
         "target_usd":target,"gap_usd":max(0,target-net),"target_coverage_pct":net/target if target else 0}
    return {"budget":budget,"dc":dc,"scenario_savings":scenario_savings,
            "annual_it_budget_check":sum(budget.values())-f["annual_it_spend"]}
