"""Dashboard Streamlit listo para GitHub / Streamlit Community Cloud."""
import copy
import json

import pandas as pd
import streamlit as st

from finance_model import calculate, load_config, phase_pricing
from it_costs import budget_and_savings

st.set_page_config(page_title="Grupo Fénix | Caso financiero", layout="wide", page_icon="📈")
config = copy.deepcopy(load_config())
f = config["financial_inputs"]

st.title("Grupo Fénix - caso financiero de modernización")
st.caption("Modelo de escenarios hipotéticos")

with st.sidebar:
    st.header("Supuestos editables")
    f["annual_it_spend"] = st.number_input("Gasto TI anual (USD)", 1000000, 1000000000, int(f["annual_it_spend"]), 100000)
    f["monthly_aws_cost"] = st.number_input("AWS mensual (USD)", 0, 10000000, int(f["monthly_aws_cost"]), 10000)
    f["annual_company_revenue"] = st.number_input("Facturación grupo anual (USD)", 1000000, 10000000000, int(f["annual_company_revenue"]), 10000000)
    f["monthly_credit_applications"] = st.number_input("Solicitudes de crédito / mes", 1, 1000000, int(f["monthly_credit_applications"]), 100)
    f["net_incremental_margin_per_extra_approved_credit"] = st.number_input("Margen neto por crédito incremental (USD)", 0, 100000, int(f["net_incremental_margin_per_extra_approved_credit"]), 100)
    f["monthly_incremental_support_after_year_1"] = st.number_input("Soporte adicional mensual desde año 2 (USD)", 0, 1000000, int(f["monthly_incremental_support_after_year_1"]), 500)
    f["monthly_incremental_cloud_cost"] = st.number_input("Nuevo gasto cloud/licencias mensual (USD, años 2+)", 0, 1000000, int(f["monthly_incremental_cloud_cost"]), 1000)
    f["revenue_exposed_to_order_system_percent"] = st.slider("Ventas expuestas al sistema de pedidos", 0.0, 1.0, float(f["revenue_exposed_to_order_system_percent"]), .05)
    f["unrecoverable_revenue_during_outage_percent"] = st.slider("Ventas afectadas no recuperables", 0.0, 1.0, float(f["unrecoverable_revenue_during_outage_percent"]), .05)
    f["contribution_margin_on_lost_revenue_percent"] = st.slider("Margen de contribución de esas ventas", 0.0, 1.0, float(f["contribution_margin_on_lost_revenue_percent"]), .05)
    f["annual_discount_rate"] = st.slider("Tasa de descuento anual", 0.0, .40, float(f["annual_discount_rate"]), .01)
    f["benefit_realization_factor"] = st.slider("Realización de beneficios (sensibilidad por alcance reducido)", 0.0, 1.0, float(f["benefit_realization_factor"]), .05)
    f["include_reserve_in_roi"] = st.checkbox("Contabilizar USD 300K de reserva comercial como gasto adicional (si se aprueba)", value=bool(f["include_reserve_in_roi"]))
    with st.expander("Data center Guatemala — hipótesis editables"):
        d = config["dc_guatemala"]
        d["racks"] = st.number_input("Racks equivalentes", 1, 250, int(d["racks"]))
        d["it_kw_per_rack"] = st.number_input("Potencia IT promedio (kW/rack)", 0.5, 30.0, float(d["it_kw_per_rack"]), .5)
        d["pue"] = st.number_input("PUE medido/hipotético", 1.0, 3.0, float(d["pue"]), .05)
        d["electricity_usd_per_kwh"] = st.number_input("Tarifa eléctrica (USD/kWh)", 0.01, 1.0, float(d["electricity_usd_per_kwh"]), .01)
        for field, label in [
            ("annual_equipment_depreciation", "Depreciación de equipos USD/año"),
            ("annual_oem_maintenance", "Mantenimiento OEM USD/año"),
            ("annual_facility_equipment_maintenance", "UPS/HVAC/generadores USD/año"),
            ("annual_space_security_insurance", "Local/seguridad/seguros USD/año"),
        ]:
            d[field] = st.number_input(label,0,10000000,int(d[field]),10000)
    with st.expander("Presupuesto restante de TI — escenarios hipotéticos"):
        for cat in config["it_budget_categories"]:
            cat["annual_budget"] = st.number_input(cat["name"]+" (USD/año)",0,50000000,int(cat["annual_budget"]),10000,key="budget"+cat["name"])
        st.caption("El resto necesario para cuadrar el presupuesto de TI va a Aplicaciones y datos (remanente). No es una factura real.")
    st.markdown("**Palancas por escenario**")
    for name, s in config["scenarios"].items():
        with st.expander(name):
            s["aws_savings_pct"] = st.slider(f"Ahorro AWS ({name})", 0.0, .50, float(s["aws_savings_pct"]), .01, key=f"aws{name}")
            s["avoided_outage_hours_annually"] = st.number_input(f"Horas de caída evitadas/año ({name})", 0, 200, int(s["avoided_outage_hours_annually"]), 1, key=f"out{name}")
            s["credit_conversion_uplift_pp"] = st.number_input(f"Mejora conversión puntos porcentuales ({name})", 0, 50, int(s["credit_conversion_uplift_pp"]), 1, key=f"cred{name}")

try:
    result = calculate(config)
    budget_result = budget_and_savings(config)
except ValueError as e:
    st.error(str(e)); st.stop()
shared = result["shared"]
fmt = lambda x: f"${x:,.0f}"
columns = st.columns(4)
for col, (label, value) in zip(columns, [
    ("Gasto TI actual anual", shared["annual_it_spend"]),
    ("Meta ahorro TI (15%)", shared["annual_it_savings_target"]),
    ("AWS anual", shared["annual_aws_spend"]),
    ("Contrato técnico Escala", shared["project_investment"]),
]):
    col.metric(label, fmt(value))

st.info(f"**Presupuesto aprobado:** {fmt(shared['approved_budget'])} = **servicios tecnológicos** {fmt(shared['project_investment'])} + **reserva comercial NO comprometida** {fmt(shared['commercial_reserve'])}. La reserva no es ingreso de Escala. Reasignarla a ABM exige autorización de Finanzas.")
st.caption("La oportunidad preliminar de la Parte B era USD 664,700 antes de discovery; la oferta revisada de Parte E es un escenario separado. No se suman.")
st.subheader("Comparación de escenarios — tres años")
rows = []
for name, s in result["scenarios"].items():
    rows.append({"Escenario":name, "Ahorro AWS anual":s["aws_annual_savings"],
       "Pérdida por caídas evitada/año":s["avoided_outage_annual_margin"],
       "Margen créditos recuperado/año":s["credit_annual_margin"],
       "Beneficios acumulados 3 años":s["three_year_benefits"], "TCO incremental 3 años":s["three_year_tco"],
       "ROI 3 años":s["three_year_roi"], "VPN (3 años)":s["npv_3_years"],
       "Payback (meses)":s["payback_month"],
       "Ahorro neto TI anual estabilizado":s["steady_net_it_savings"],
       "Brecha a meta 15% TI":s["remaining_it_target_gap"]})
df = pd.DataFrame(rows).set_index("Escenario")
st.dataframe(df.style.format({c:"${:,.0f}" for c in df.columns if c not in ["ROI 3 años", "Payback (meses)"]}).format({"ROI 3 años":"{:.1%}", "Payback (meses)":"{:.1f}"}), use_container_width=True)

st.caption("Beneficios recuperados por créditos y caídas NO cuentan como ahorro del presupuesto TI. El soporte adicional sí reduce el ahorro neto de TI.")
st.bar_chart(df[["Beneficios acumulados 3 años", "TCO incremental 3 años"]])

scenario_name = st.selectbox("Ver flujo mensual", list(result["scenarios"]), index=1)
s = result["scenarios"][scenario_name]
cf = pd.DataFrame(s["cashflows"][:36]).set_index("month")
st.line_chart(cf[["cumulative_net"]].rename(columns={"cumulative_net": "Flujo neto acumulado (USD)"}))
with st.expander("Flujo de caja mensual detallado y descarga"):
    st.dataframe(cf.style.format("${:,.0f}"), use_container_width=True)
    st.download_button("Descargar flujo mensual CSV", cf.to_csv().encode("utf-8-sig"), file_name=f"flujo_fenix_{scenario_name.lower()}.csv", mime="text/csv")


st.subheader("Desglose del gasto TI total (hipótesis, USD/año)")
bud = budget_result["budget"]
st.dataframe(pd.DataFrame([{"Partida":n,"Anual (USD)":v,"% TI":v/shared["annual_it_spend"]} for n,v in bud.items()]).set_index("Partida").style.format({"Anual (USD)":"${:,.0f}","% TI":"{:.1%}"}),use_container_width=True)
st.caption("El caso confirma AWS y 40% de cargas on-prem en Guatemala; NO confirma contratos, racks ni distribución monetaria por partida. No asumir que 40% de cargas equivale a 40% del gasto.")

dc = budget_result["dc"]
st.subheader("Costo orientativo del data center principal, Guatemala")
cols = st.columns(4)
for col,(label,val) in zip(cols,[
    ("Carga IT",f"{dc['it_kw']:,.0f} kW"),
    ("Electricidad anual",fmt(dc["electricity_usd"])),
    ("Operación DC anual, incl. depreciación",fmt(dc["annual_total"])),
    ("Peso del DC en TI",f"{dc['annual_total']/shared['annual_it_spend']:.1%}")]):
    col.metric(label,val)
st.dataframe(pd.DataFrame([{"Costo anual":k,"USD":v} for k,v in dc["cost_components"].items()]).set_index("Costo anual").style.format("${:,.0f}"),use_container_width=True)
st.caption("Referencia de energía Guatemala USD0.19/kWh (ACOGRACE 2025); PUE1.65 y 24 racks son hipótesis, no un inventario confirmado. Depreciación de USD1.1M/año NO es ahorro de caja inmediato.")
with st.expander("Comparación informativa con colocation — NO equivale a ahorro"):
    st.write(f"Guatemala: 24 racks × USD1,100 × 12 = {fmt(dc['colo_gt_reference_usd_year'])}/año (iTec). Potencia y términos del contrato no equivalentes.")
    st.write(f"Costa Rica: capacidad equivalente a 2kW/medio-rack a USD899/mes = {fmt(dc['colo_cr_reference_usd_year'])}/año sin IVA (Navégalo). Excluye migración, interconexión y otras necesidades.")

st.subheader("Oportunidades adicionales de ahorro TI — NO incluidas en el ROI del programa")
extra = []
for name, outcome in budget_result["scenario_savings"].items():
    extra.append({"Escenario":name,"AWS ahorro anual":outcome["aws_usd"],
        "DC ahorro hipotético":outcome["dc_usd"],"Otras partidas hipotéticas":sum(outcome["other_noaws_usd"].values()),
        "Ahorro bruto total potencial":outcome["gross_usd"],"Nuevo soporte anual":outcome["new_support_usd"],
        "Ahorro TI neto potencial":outcome["net_usd"],"Brecha meta CFO":outcome["gap_usd"],
        "% meta cubierta":outcome["target_coverage_pct"]})
extra_df=pd.DataFrame(extra).set_index("Escenario")
st.dataframe(extra_df.style.format({c:"${:,.0f}" for c in extra_df.columns if c!="% meta cubierta"}).format({"% meta cubierta":"{:.1%}"}),use_container_width=True)

st.subheader("Desglose de las tres fases (horas × tarifa)")
line_items, totals = phase_pricing(config)
price_df = pd.DataFrame(line_items)
price_df = price_df.rename(columns={"phase":"Fase", "months":"Meses", "workstream":"Entregable/actividad", "role":"Perfil", "hours":"Horas", "hourly_rate":"USD/h", "cost":"USD"})
st.dataframe(price_df.style.format({"USD/h":"${:,.0f}", "USD":"${:,.0f}"}), use_container_width=True)
st.caption("El contrato técnico de USD 1.5M corresponde a 520K + 620K + 360K. Horas y tarifas son hipótesis de reparto, no precios oficiales ni cotizaciones de Escala.")
st.subheader("Reserva comercial propuesta — República Dominicana")
abm = pd.DataFrame(config["commercial_reserve_allocation"])
st.dataframe(abm.rename(columns={"program":"Iniciativa", "amount":"USD", "measurement":"Cómo medir"}).style.format({"USD":"${:,.0f}"}), use_container_width=True, hide_index=True)
st.caption("USD 80K producción, 50K PR, 70K ABM y 100K ventas locales (versión final). El Excel histórico tiene otra distribución de USD 300K; no se suman. Ningún ingreso ni ROI de estos eventos está confirmado. Su uso requiere aprobación de Finanzas.")
st.subheader("Archivos Excel originales y trazabilidad")
st.caption("Estos archivos están incluidos en el repositorio como referencias documentales. Los controles de esta app usan assumptions.json; cambiar un Excel no actualiza por sí solo el modelo interactivo.")
from pathlib import Path
for label, filename in [
    ("Modelo CFO TI USD 20M y data center", "Fenix_Modelo_Financiero_CFO_20M_DC_Regional.xlsx"),
    ("Presupuesto revisado: 1.5M + 300K", "Fenix_Presupuesto_Revisado_1_5M_y_Reserva_300K.xlsx"),
    ("Dimensionamiento original Parte B: 664.7K", "Grupo_Fenix_Dimensionamiento_12M_Con_Recursos.xlsx")]:
    source = Path(__file__).parent / "data" / "excel_originales" / filename
    if source.is_file():
        st.download_button(f"Descargar Excel: {label}", source.read_bytes(), file_name=filename, mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", key=filename)


st.subheader("Transparencia de supuestos")
st.write("**Costo por hora de interrupción:** facturación anual / (días × horas) × ventas expuestas × porcentaje no recuperable × margen de contribución.")
st.write("**Beneficio por créditos:** solicitudes mensuales × mejora en conversión (puntos porcentuales) × margen NETO por crédito adicional.")
st.write("**VPN:** flujos netos mensuales descontados con tasa anual editable. **TCO incremental:** inversión + soporte adicional + nuevos costos cloud modelados.")

st.download_button("Descargar supuestos del modelo (JSON)", json.dumps(config,ensure_ascii=False,indent=2).encode("utf-8"),"fenix_supuestos_editados.json",mime="application/json")
