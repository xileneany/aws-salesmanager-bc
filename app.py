"""Grupo Fénix: dimensionamiento pre-discovery y oferta financiera, por separado."""
import copy
import json
from pathlib import Path
import pandas as pd
import streamlit as st
from finance_model import calculate, load_config, phase_pricing
from it_costs import budget_and_savings
from dimensioning_model import calculate_dimensioning

st.set_page_config(page_title="Grupo Fénix | Modelos financieros", layout="wide", page_icon="📊")

# Identidad visual extraída de la presentación ejecutiva de Grupo Fénix.
# Los colores se mantienen aquí para que la app funcione incluso sin config.toml.
FENIX = {
    "forest": "#155440",  # Verde profundo: encabezados y llamadas a la acción
    "teal": "#25957B",    # Verde teal: segunda fase / acentos
    "aqua": "#6EC8BD",    # Turquesa claro: tercera fase
    "mint": "#A1E1D9",    # Fondo de sección y tarjetas
    "sage": "#AAD59D",    # Retención y expansión
    "pale": "#E3F4F1",    # Filas y tablas suaves
    "white": "#FFFFFE",   # Fondo de documento
    "ink": "#193F36",     # Texto principal
}

st.markdown("""
<style>
/* Fondo y tipografía — equivalentes a las páginas del business case. */
.stApp, [data-testid="stAppViewContainer"] { background: #FFFFFE; color: #193F36; }
.block-container { max-width: 1280px; padding-top: 1.35rem; padding-bottom: 4rem; }
html, body, [data-testid="stMarkdownContainer"], [data-testid="stAppViewContainer"] {
    font-family: 'Aptos', 'Inter', 'Arial', sans-serif;
}
h1, h2, h3, [data-testid="stHeadingWithActionElements"] { color: #155440 !important; letter-spacing: -.025em; }
h2 { border-bottom: 2px solid #A1E1D9; padding-bottom: .35rem; }
a { color: #197C6D !important; }

/* Portada compacta a juego con la presentación. */
.fenix-header {
    border-radius: 23px;
    background: linear-gradient(112deg, #155440 0%, #216F60 63%, #3A9F94 100%);
    padding: 27px 31px 24px;
    color: #FFFFFF;
    margin: 0 0 23px;
    box-shadow: 0 6px 22px rgba(21,84,64,.11);
    position: relative;
    overflow: hidden;
}
.fenix-header::after {
    content: ''; position:absolute; width:170px;height:170px;right:-54px;top:-80px;
    border-radius:50%; border:31px solid rgba(161,225,217,.24);
}
.fenix-eyebrow {color:#D1F1E9;font-size:.77rem;font-weight:800;letter-spacing:.15em;margin:0 0 10px;}
.fenix-title {color:#FFFFFF !important;font-size:2.12rem;line-height:1.14;font-weight:800;margin:0 0 9px;letter-spacing:-.035em;}
.fenix-subtitle {color:#E4F7F1;font-size:.98rem;max-width:820px;line-height:1.48;margin:0;}
.fenix-stripe {display:flex;gap:5px;margin-top:18px;width:min(620px,95%)}
.fenix-stripe span {display:block;height:7px;border-radius:30px;flex:1;}
.fenix-stripe span:nth-child(-n+2){background:#155440;border:1px solid #A1E1D9}
.fenix-stripe span:nth-child(3){background:#25957B}
.fenix-stripe span:nth-child(4){background:#6EC8BD}
.fenix-stripe span:nth-child(5){background:#A1E1D9}
.fenix-stripe span:nth-child(6){background:#AAD59D}
.fenix-strip-note{font-size:.81rem;color:#D1F1E9;margin-top:10px;}

/* Pestañas visualmente iguales a las etiquetas redondeadas de la oferta. */
.stTabs [data-baseweb="tab-list"] { gap:10px; background:#E3F4F1; padding:7px; border-radius:17px; }
.stTabs [data-baseweb="tab"] {
    border-radius:12px; padding:10px 19px; color:#155440; font-weight:700;
    background:transparent; border:0 !important;
}
.stTabs [aria-selected="true"] { background:#155440 !important; color:#FFFFFF !important; }
.stTabs [data-baseweb="tab-highlight"], .stTabs [data-baseweb="tab-border"] {display:none !important;}

/* Métricas estilo tarjeta ejecutiva. */
[data-testid="stMetric"] {
    background: #E3F4F1;
    border: 1px solid #C5E8DF;
    border-radius: 16px;
    padding: 15px 17px;
    min-height: 99px;
}
[data-testid="stMetricLabel"] { color: #397466; font-weight:650; }
[data-testid="stMetricValue"] { color: #155440; font-weight:800; letter-spacing:-.035em; }

/* Inputs, contenedores, tablas y avisos. */
[data-testid="stExpander"] { border: 1px solid #CCEAE3 !important; border-radius:16px !important; background:#FAFEFC; }
[data-testid="stVerticalBlockBorderWrapper"] > div[style*="border"] { border-color:#D5EBE5 !important; border-radius:15px !important; }
[data-testid="stDataFrame"], [data-testid="stTable"] { border:1px solid #D5EBE5; border-radius:13px; overflow:hidden; }
[data-testid="stAlert"] { border-radius:13px; border-left:4px solid #25957B; }
[data-testid="stDownloadButton"] button, [data-testid="stButton"] button[kind="primary"] {
    color:#FFFFFF !important; background:#155440 !important; border:1px solid #155440 !important;
    border-radius:11px !important; font-weight:700;
}
[data-testid="stDownloadButton"] button:hover, [data-testid="stButton"] button[kind="primary"]:hover { background:#25957B !important; }
[data-testid="stSelectbox"] > div, [data-testid="stNumberInput"] > div { border-radius:10px; }
[data-testid="stCaptionContainer"] { color:#55736A; }
[data-testid="stSlider"] [role="slider"] { box-shadow:0 0 0 2px #A1E1D9; }
hr {border-color:#DBEEE9;}
@media (max-width: 690px) {
    .block-container {padding-top:.8rem;}
    .fenix-header {padding:21px 20px;border-radius:17px;}
    .fenix-title {font-size:1.56rem;}
    .stTabs [data-baseweb="tab"] {padding:8px 10px;font-size:.86rem;}
}
</style>
""", unsafe_allow_html=True)

# Formato ejecutivo: solo cambia la visualización, nunca los cálculos ni los CSV.
def show_financial_table(frame, currency=(), percentages=(), numbers=(), integers=(), hide_index=False):
    """Forzar como texto el formato visible (Streamlit puede ignorar Styler.format)."""
    out = frame.copy()
    spec = {**{c: "currency" for c in currency},
            **{c: "percentage" for c in percentages},
            **{c: "number" for c in numbers},
            **{c: "integer" for c in integers}}

    def display(value, kind):
        if value is None or pd.isna(value):
            return "—"
        val = float(value)
        if kind == "currency":
            return f"USD {val:,.2f}"
        if kind == "percentage":
            return f"{val * 100:,.2f}%"
        if kind == "integer":
            return f"{val:,.0f}"
        return f"{val:,.2f}"

    for col in out.columns:
        if col in spec:
            out[col] = out[col].map(lambda v, k=spec[col]: display(v, k))
        elif pd.api.types.is_float_dtype(out[col]):
            out[col] = out[col].map(lambda v: display(v, "number"))
    st.dataframe(out, use_container_width=True, hide_index=hide_index)

config = copy.deepcopy(load_config())
st.markdown("""
<section class="fenix-header">
  <div class="fenix-eyebrow">GRUPO FÉNIX · BUSINESS CASE AWS</div>
  <div class="fenix-title">Supuestos y escenarios financieros</div>
  <p class="fenix-subtitle">Del dimensionamiento preliminar a la inversión propuesta: explora los supuestos, compara escenarios y evalúa su impacto financiero.</p>
  <div class="fenix-stripe"><span></span><span></span><span></span><span></span><span></span><span></span></div>
  <div class="fenix-strip-note">Parte B · Dimensionamiento &nbsp;&nbsp; | &nbsp;&nbsp; Parte E · Oferta y retorno</div>
</section>
""", unsafe_allow_html=True)
st.caption("Modelo comercial basado en supuestos editables. Valores referenciales; no constituyen cotización oficial de Escala.")
tab_dim, tab_offer = st.tabs(["01 · Dimensionamiento preliminar", "02 · Supuestos de la oferta"])

with tab_dim:
    st.header("Parte B · Dimensionamiento de la oportunidad")
    st.write("Estimación de servicios Escala durante 12 meses, **antes del descubrimiento técnico**. El escenario base corresponde al análisis presentado: USD 664,700.")
    dim = config["dimensioning"]
    with st.expander("Editar supuestos de dimensionamiento", expanded=False):
        c1, c2, c3 = st.columns(3)
        with c1:
            dim["assessment_usd"] = st.number_input("Assessment inicial (USD)", min_value=0.0, max_value=1000000.0, value=float(dim["assessment_usd"]), step=500.0, format="%.2f", key="dim_assess")
        with c2:
            dim["managed_months"] = st.number_input("Meses de soporte", min_value=0, max_value=36, value=int(dim["managed_months"]), step=1, key="dim_months")
        with c3:
            dim["managed_monthly_usd"] = st.number_input("Soporte mensual (USD)", min_value=0.0, max_value=250000.0, value=float(dim["managed_monthly_usd"]), step=250.0, format="%.2f", key="dim_support")
        st.markdown("**Esfuerzo y tarifas por línea de servicio**")
        for index, line in enumerate(dim["service_lines"]):
            st.caption(line["category"] + " · " + line["activity"])
            x, y = st.columns(2)
            with x:
                line["hours"] = st.number_input("Horas base", min_value=0, max_value=20000, value=int(line["hours"]), step=10, key=f"dim_hours_{index}")
            with y:
                line["hourly_rate_usd"] = st.number_input("Tarifa USD/h", min_value=0.0, max_value=1000.0, value=float(line["hourly_rate_usd"]), step=5.0, format="%.2f", key=f"dim_rate_{index}")
        st.markdown("**Factores de alcance**")
        cs = st.columns(3)
        for col, (name, factor) in zip(cs, dim["multipliers"].items()):
            with col:
                dim["multipliers"][name] = st.number_input(f"Factor {name}", min_value=0.0, max_value=3.0, value=float(factor), step=0.05, format="%.2f", key=f"dim_factor_{name}")

    dimensioning = calculate_dimensioning(dim, float(config["financial_inputs"]["approved_modernization_budget"]))
    base = dimensioning["base"]
    p1, p2, p3 = st.columns(3)
    p1.metric("Servicios de proyecto · base", f"USD {base['engineer_total'] + base['assessment']:,.2f}")
    p2.metric("Servicios recurrentes · base", f"USD {base['recurring']:,.2f}")
    p3.metric("Oportunidad total · base", f"USD {base['total']:,.2f}")

    st.subheader("Comparación de escenarios")
    dim_rows = []
    for name, info in dimensioning["scenarios"].items():
        dim_rows.append({"Escenario": name,
                        "Factor de esfuerzo": dim["multipliers"][name],
                        "Ingeniería USD": info["engineer_total"],
                        "Assessment USD": info["assessment"],
                        "Soporte USD": info["recurring"],
                        "Total USD": info["total"],
                        "% presupuesto 1.8M": info["percentage_budget"]})
    dim_df = pd.DataFrame(dim_rows).set_index("Escenario")
    st.dataframe(dim_df.style.format({"Factor de esfuerzo":"{:.2f}",
            "Ingeniería USD":"${:,.2f}", "Assessment USD":"${:,.2f}",
            "Soporte USD":"${:,.2f}", "Total USD":"${:,.2f}",
            "% presupuesto 1.8M":"{:.2%}"}), use_container_width=True)
    st.bar_chart(dim_df[["Total USD"]], color=FENIX["teal"])

    st.subheader("Categorías de servicio según escenario")
    order = [line["category"] for line in dim["service_lines"]]
    cat_rows = []
    for category in order:
        cat_rows.append({"Categoría":category, **{name:result["by_category"].get(category,0.0) for name,result in dimensioning["scenarios"].items()}})
    cat_df = pd.DataFrame(cat_rows).set_index("Categoría")
    st.dataframe(cat_df.style.format("${:,.2f}"),use_container_width=True)

    st.subheader("Desglose del escenario base")
    detailed = pd.DataFrame(base["records"])
    st.dataframe(detailed.style.format({"Horas base":"{:,.0f}",
        "Horas ajustadas":"{:,.2f}","Tarifa USD/h":"${:,.2f}","Total USD":"${:,.2f}"}),
        use_container_width=True, hide_index=True)
    st.caption(f"A los honorarios de ingeniería se suman el assessment único de USD {dim['assessment_usd']:,.2f} y el soporte de {dim['managed_months']} meses × USD {dim['managed_monthly_usd']:,.2f}. Los multiplicadores alteran horas de ingeniería, no los cargos fijos.")
    st.info("Este cálculo estima honorarios de servicios, no consumo de AWS. La oportunidad de USD 664,700 NO se suma a la oferta de USD 1.5M de la siguiente pestaña.")
    with st.expander("Referencia de servicios AWS y archivos del dimensionamiento"):
        st.write("El Excel original estima además cargos AWS ilustrativos por **USD 11,620.80 al año** (KMS, CloudWatch, AWS Backup, Glue, QuickSight y CodePipeline). Son gastos AWS potenciales separados, no ingresos de Escala.")
        original = Path(__file__).parent / "data" / "excel_originales" / "Grupo_Fenix_Dimensionamiento_12M_Con_Recursos.xlsx"
        if original.exists():
            st.download_button("Descargar Excel original de dimensionamiento", original.read_bytes(), file_name=original.name, mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", key="dim_excel")
    st.download_button("Descargar escenarios de dimensionamiento (CSV)", dim_df.to_csv().encode("utf-8-sig"), file_name="fenix_dimensionamiento_escenarios.csv", mime="text/csv", key="dim_csv")

with tab_offer:
    st.header("Parte E · Supuestos de la oferta posterior al descubrimiento")
    st.write("Propuesta revisada: USD 1.5M para modernización y USD 300K reservados para iniciativas comerciales, sujetos a aprobación de Finanzas.")
    f = config["financial_inputs"]
    with st.expander("Editar supuestos de la oferta", expanded=False):
        st.subheader("Supuestos financieros y comerciales")
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
        st.markdown("**Data center Guatemala — hipótesis editables**")
        with st.container(border=True):
            d = config["dc_guatemala"]
            d["racks"] = st.number_input("Racks equivalentes", 1, 250, int(d["racks"]))
            d["it_kw_per_rack"] = st.number_input("Potencia IT promedio (kW/rack)", 0.5, 30.0, float(d["it_kw_per_rack"]), .5, format="%.2f")
            d["pue"] = st.number_input("PUE medido/hipotético", 1.0, 3.0, float(d["pue"]), .05, format="%.2f")
            d["electricity_usd_per_kwh"] = st.number_input("Tarifa eléctrica (USD/kWh)", 0.01, 1.0, float(d["electricity_usd_per_kwh"]), .01, format="%.2f")
            for field, label in [
                ("annual_equipment_depreciation", "Depreciación de equipos USD/año"),
                ("annual_oem_maintenance", "Mantenimiento OEM USD/año"),
                ("annual_facility_equipment_maintenance", "UPS/HVAC/generadores USD/año"),
                ("annual_space_security_insurance", "Local/seguridad/seguros USD/año"),
            ]:
                d[field] = st.number_input(label,0,10000000,int(d[field]),10000)
        st.markdown("**Presupuesto restante de TI — escenarios hipotéticos**")
        with st.container(border=True):
            for cat in config["it_budget_categories"]:
                cat["annual_budget"] = st.number_input(cat["name"]+" (USD/año)",0,50000000,int(cat["annual_budget"]),10000,key="budget"+cat["name"])
            st.caption("El resto necesario para cuadrar el presupuesto de TI va a Aplicaciones y datos (remanente). No es una factura real.")
        st.markdown("**Palancas por escenario**")
        for name, s in config["scenarios"].items():
            st.markdown(f"**{name}**")
            with st.container(border=True):
                s["aws_savings_pct"] = st.slider(f"Ahorro AWS ({name})", 0.0, .50, float(s["aws_savings_pct"]), .01, key=f"aws{name}")
                s["avoided_outage_hours_annually"] = st.number_input(f"Horas de caída evitadas/año ({name})", 0, 200, int(s["avoided_outage_hours_annually"]), 1, key=f"out{name}")
                s["credit_conversion_uplift_pp"] = st.number_input(f"Mejora conversión puntos porcentuales ({name})", 0, 50, int(s["credit_conversion_uplift_pp"]), 1, key=f"cred{name}")

    try:
        result = calculate(config)
        budget_result = budget_and_savings(config)
    except ValueError as e:
        st.error(str(e)); st.stop()
    shared = result["shared"]
    fmt = lambda x: f"USD {x:,.2f}"
    columns = st.columns(4)
    for col, (label, value) in zip(columns, [
        ("Gasto TI actual anual", shared["annual_it_spend"]),
        ("Meta ahorro TI (15%)", shared["annual_it_savings_target"]),
        ("AWS anual", shared["annual_aws_spend"]),
        ("Contrato técnico Escala", shared["project_investment"]),
    ]):
        col.metric(label, fmt(value))

    st.info(f"**Presupuesto aprobado:** {fmt(shared['approved_budget'])} = **servicios tecnológicos** {fmt(shared['project_investment'])} + **reserva comercial NO comprometida** {fmt(shared['commercial_reserve'])}. La reserva no es ingreso de Escala. Reasignarla a ABM exige autorización de Finanzas.")
    st.caption("Esta oferta posterior al descubrimiento es distinta del dimensionamiento preliminar mostrado en la primera pestaña. No deben sumarse como contratos independientes.")
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
    show_financial_table(df,
        currency=[c for c in df.columns if c not in ["ROI 3 años", "Payback (meses)" ]],
        percentages=["ROI 3 años"], numbers=["Payback (meses)"])

    st.caption("Beneficios recuperados por créditos y caídas NO cuentan como ahorro del presupuesto TI. El soporte adicional sí reduce el ahorro neto de TI.")
    st.bar_chart(df[["Beneficios acumulados 3 años", "TCO incremental 3 años"]].round(2), color=[FENIX["teal"], FENIX["mint"]])

    scenario_name = st.selectbox("Ver flujo mensual", list(result["scenarios"]), index=1)
    s = result["scenarios"][scenario_name]
    cf = pd.DataFrame(s["cashflows"][:36]).set_index("month")
    st.line_chart(cf[["cumulative_net"]].round(2).rename(columns={"cumulative_net": "Flujo neto acumulado (USD)"}), color=FENIX["forest"])
    with st.expander("Flujo de caja mensual detallado y descarga"):
        show_financial_table(cf, currency=cf.columns)
        st.download_button("Descargar flujo mensual CSV", cf.to_csv().encode("utf-8-sig"), file_name=f"flujo_fenix_{scenario_name.lower()}.csv", mime="text/csv")


    st.subheader("Desglose del gasto TI total (hipótesis, USD/año)")
    bud = budget_result["budget"]
    show_financial_table(pd.DataFrame([{"Partida":n,"Anual (USD)":v,"% TI":v/shared["annual_it_spend"]} for n,v in bud.items()]).set_index("Partida"), currency=["Anual (USD)"], percentages=["% TI"])
    st.caption("El caso confirma AWS y 40% de cargas on-prem en Guatemala; NO confirma contratos, racks ni distribución monetaria por partida. No asumir que 40% de cargas equivale a 40% del gasto.")

    dc = budget_result["dc"]
    st.subheader("Costo orientativo del data center principal, Guatemala")
    cols = st.columns(4)
    for col,(label,val) in zip(cols,[
        ("Carga IT",f"{dc['it_kw']:,.2f} kW"),
        ("Electricidad anual",fmt(dc["electricity_usd"])),
        ("Operación DC anual, incl. depreciación",fmt(dc["annual_total"])),
        ("Peso del DC en TI",f"{dc['annual_total']/shared['annual_it_spend']:.2%}")]):
        col.metric(label,val)
    show_financial_table(pd.DataFrame([{"Costo anual":k,"USD":v} for k,v in dc["cost_components"].items()]).set_index("Costo anual"), currency=["USD"])
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
    show_financial_table(extra_df, currency=[c for c in extra_df.columns if c != "% meta cubierta"], percentages=["% meta cubierta"])
    st.warning("NO sumar los ahorros de otros contratos al ROI de Escala sin validación de viabilidad, alcance contractual, costo de implementación y fecha de captura. El ahorro en personal y depreciación se deja en 0 por prudencia. La meta del 15% del gasto TI NO está demostrada.")

    st.subheader("Desglose de las tres fases (horas × tarifa)")
    line_items, totals = phase_pricing(config)
    price_df = pd.DataFrame(line_items)
    price_df = price_df.rename(columns={"phase":"Fase", "months":"Meses", "workstream":"Entregable/actividad", "role":"Perfil", "hours":"Horas", "hourly_rate":"USD/h", "cost":"USD"})
    show_financial_table(price_df, currency=["USD/h", "USD"], integers=["Horas"])
    st.caption("El contrato técnico de USD 1.5M corresponde a 520K + 620K + 360K. Horas y tarifas son hipótesis de reparto, no precios oficiales ni cotizaciones de Escala.")
    st.subheader("Reserva comercial propuesta — República Dominicana")
    abm = pd.DataFrame(config["commercial_reserve_allocation"])
    show_financial_table(abm.rename(columns={"program":"Iniciativa", "amount":"USD", "measurement":"Cómo medir"}), currency=["USD"], hide_index=True)
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
