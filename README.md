# Parcial Final · La red de propiedad de la Notaría 2 de Cali (1938–1944)

App interactiva del parcial final de *Introducción a la Complejidad* (Univalle).
Los estudiantes analizan la **red real** de compraventas de la Notaría 2 y
responden 11 puntos en 4 partes. Presencial, en parejas.

## Correr localmente

```bash
python3.11 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

streamlit run parcial_app.py     # estudiantes  → http://localhost:8501
streamlit run dashboard.py       # docente (contraseña)
```

Sin credenciales de Google, las respuestas se guardan en `respuestas_local.csv`.

## Regenerar los datos

```bash
python construir_datos.py        # ../data/consolidado + alias curados -> datos/red_parcial.csv
```

## Estructura

- `parcial_app.py` — app de estudiantes (registro + 4 partes + envío).
- `dashboard.py` — panel docente para leer/calificar.
- `lib/` — `red.py` (métricas), `viz.py` (Plotly), `storage.py` (Sheets/CSV), `textos.py`.
- `datos/red_parcial.csv` — red dirigida limpia (vendedor→comprador).

Ver `CLAUDE.md` para el detalle de decisiones (limpieza curada, hallazgo del
"bazar fragmentado", persistencia, deploy).

Diseño: **Boris Salazar y Daniel Otero**.
