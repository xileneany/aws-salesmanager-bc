# Grupo Fénix — Business Case | Finanzas, FinOps y expansión comercial

**Dashboard interactivo** para el ejercicio de Escala 24x7, preparado para GitHub + Streamlit Community Cloud. Modelo hipotético, **no cotización oficial ni datos reales del cliente**.

## Cómo ejecutarlo

1. Descomprime el ZIP y crea un repositorio nuevo en GitHub.
2. Sube **el contenido de esta carpeta** directamente al repositorio (debe verse `app.py` en la raíz).
3. En [share.streamlit.io](https://share.streamlit.io/), selecciona el repositorio, rama `main` y archivo principal `app.py`.
4. Alternativa local: `pip install -r requirements.txt` y `streamlit run app.py`.

## Tres referencias financieras distintas (no confundir)

| Fuente / propósito | USD | Cómo se interpreta |
|---|---:|---|
| Parte B: oportunidad preliminar antes de discovery | 664,700 | Estimación de servicios; no se agrega a Parte E. |
| Parte E: oferta técnica Escala revisada | 1,500,000 | 520K + 620K + 360K; se incluye en TCO/ROI técnico. |
| Parte E: reserva de crecimiento República Dominicana | 300,000 | Sin contratar; fuera del ROI por defecto, requiere aprobación de Finanzas. |
| Presupuesto total disponible según caso | 1,800,000 | No es ingreso automático de Escala. |

**Gasto TI supuesto:** USD 20M/año, AWS USD 180K/mes = USD 2.16M/año (10.8% del total, aproximadamente 10%). **Meta CFO:** 15% de TI total = USD 3M/año; **no es una proyección garantizada de ahorro**.

## Qué datos incluye GitHub

- `assumptions.json`: datos que usa la app (escenarios, desglose TI, cotización técnica hipotética, reserva ABM).
- `data/excel_originales/`: tres Excel originales, descargables también desde el dashboard.
- `data/presupuesto_fases.csv`: desglose actualizado 520K/620K/360K, extraído del Excel de presupuesto revisado.
- `data/reserva_abm_rd.csv`: 80K producción, 50K PR, 70K ABM, 100K ventas locales, según el one-pager final.
- `data/dimensionamiento_pre_discovery.csv`: Parte B USD 664,700.
- `finance_model.py`: cálculo mensual ROI, VPN, payback y ahorro TI separado de ingresos recuperados.
- `it_costs.py`: data center Guatemala y oportunidades NO confirmadas de ahorro no AWS.
- `test_model.py`, `test_it_costs.py`: validaciones automáticas.

**Versiones de la reserva comercial:** el Excel de presupuesto revisado conserva una distribución anterior de USD 75K / 135K / 90K en tres programas; la propuesta ABM final y la aplicación utilizan el presupuesto posterior USD 80K / 50K / 70K / 100K. No sumar ambas versiones.

**Importante:** los Excel son fuentes documentales. **Editar un Excel no actualiza automáticamente `assumptions.json`**: los valores interactivos se controlan desde la app y cambios permanentes se realizan en JSON/GitHub. Si en el futuro quieres Excel como única fuente de datos, sería una fase de integración posterior.

## Transparencia y límites

Los supuestos de costos de interrupciones, solicitudes de crédito, ahorros AWS y costos regionales requieren validación. Reducir el alcance tecnológico de USD 1.8M a 1.5M puede reducir sus beneficios: utiliza el control **Realización de beneficios** para probar esa sensibilidad. La reserva ABM no tiene ingresos futuros modelados ni se presume aprobada. El gasto on-premises es una hipótesis de 24 racks en Guatemala, no inventario verificado. No suma 40% de cargas on-premises como 40% de gasto. La meta 15% de TI total no se confunde con el ahorro AWS.

**Uso de IA:** ChatGPT apoyó la organización del análisis y el desarrollo del prototipo; los supuestos de la propuesta deben revisarse y validarse antes de una decisión financiera.

## Dashboard actualizado: dos pestañas

**01 — Supuestos de dimensionamiento (Parte B):** escenarios Conservador, Base y Alto.
El Excel de dimensionamiento parte de 600 h de seguridad a USD 150/h, 600 h de resiliencia a USD 140/h, 280 h FinOps a USD 125/h, 1,200 h de aplicaciones a USD 145/h, 750 h de datos a USD 140/h y 320 h DevOps a USD 135/h; se añaden USD 12K de assessment único y 12 meses de soporte desde el mes 1 a USD 10,125/mes (USD 121,500 anuales). Esta mensualidad es una hipótesis comercial revisada, no un precio de Escala. El factor cambia solo horas de ingeniería:

| Escenario | Multiplicador | Total servicios 12 meses |
|---|---:|---:|
| Conservador | 0.75 | USD 531,900 |
| Base | 1.00 | **USD 664,700** |
| Alto | 1.50 | USD 930,300 |

**02 — Supuestos de la oferta (Parte E):** mantiene el cálculo financiero de USD 1.5M en servicios tecnológicos más USD 300K de reserva comercial y los escenarios de ROI, TCO, data center y ahorros. Los escenarios de dimensionamiento **no son escenarios de retorno financiero**. No se suman Parte B y Parte E.

Los montos y porcentajes se muestran con **máximo dos decimales**. Para cambiar los valores predeterminados en el despliegue, edita `assumptions.json`; los cambios interactivos en la pantalla no se guardan automáticamente en GitHub.

**Actualización desde una instalación anterior:** reemplaza `app.py` y `assumptions.json` en la raíz del repositorio y añade el nuevo `dimensioning_model.py`. Reemplaza también `data/excel_originales/Grupo_Fenix_Dimensionamiento_12M_Con_Recursos.xlsx`, que refleja el supuesto de soporte desde el mes 1.
