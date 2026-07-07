# CLAUDE.md — Parcial Final (App Streamlit)

## Qué es esto

App Streamlit del **Parcial Final** del curso *Introducción a la Complejidad
2026-I* (Universidad del Valle). Los estudiantes analizan la **red real** de la
Notaría 2 de Cali (**1938–1944**, serie completa) y responden 11 puntos en 4
partes. **Presencial, en parejas (máx. 2), enfoque mixto** (algunas cifras
dadas, otras las obtienen moviendo controles; todo con anclaje empírico).

- **Red DIRIGIDA** vendedor → comprador. Métrica central = **grado de entrada
  = compras = acumulación de tierra** (misma filosofía del Taller 5).
- **Hallazgo que estructura el examen — "bazar fragmentado":** la red real NO
  tiene la estructura rica de la red *simulada* del Taller 4. Con cualquier
  limpieza: clustering ≈ 0, **betweenness ≈ 0 (casi no hay brokers)**, componente
  gigante ≤ 6 %, 80 % de actores en un solo trato. PERO hay fuerte concentración
  en la compra (cola larga, CV≈1.28). El examen pregunta *por qué* no hay
  brokers / por qué está desconectado, en vez de "encuentra el broker".

## Quick start (local)

```bash
/opt/homebrew/bin/python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run parcial_app.py          # app de estudiantes
streamlit run dashboard.py            # panel docente
```

Sin `secrets.toml`, las respuestas van a `respuestas_local.csv` (gitignoreado).

## Arquitectura

```
parcial_app.py        # App estudiantes: registro (pareja) + 4 partes (tabs) + envío
dashboard.py          # Panel docente (contraseña) — una ficha por pareja
construir_datos.py    # DEV: ../data/consolidado + alias_curados -> datos/red_parcial.csv
datos/red_parcial.csv # Edge list dirigida y LIMPIA (curada). Una fila por par s->b
                      # con atributos del registro (registro, anio, valor, area, ...)
lib/
  red.py              # carga + métricas cacheadas (resumen, ranking, cv_por_anio)
  canvas.py           # GRAFO de la red: D3 force-directed en canvas (portado del
                      #   Taller 5 RedRealCanvas.tsx) embebido con components.v1.html
  viz.py              # Plotly (distribución de grado, rankings, CV por año)
  storage.py          # Google Sheets / CSV local (una fila por PAREJA)
  textos.py           # INTRO, PARTES, los 11 PUNTOS
.streamlit/
  config.toml         # tema claro
  secrets.example.toml
```

## Pipeline de datos (2 pasos, DEV)

1. En `../data/`: `python3 consolidar.py` → `consolidado_notaria2.csv` (308→**724**
   registros, 1938–1944). Luego la limpieza vive en `../data/limpiar_red.py`
   (modo **`curada`** = moderada + `../data/alias_curados.csv`).
2. Aquí: `python construir_datos.py` → `datos/red_parcial.csv`. **Re-correr si
   cambian los datos o la tabla de alias.** (El builder importa `limpiar_red`
   vía `sys.path`; solo se corre en el monorepo, pero su salida se commitea.)

### Depuración de nombres (decisión 2026-07)
- Se comparó **moderada vs. a fondo (fuzzy automática)**. La automática
  **sobre-fusiona** (juntaba 16 "Rafael" distintos, y Banco Central+Agrario+
  Agrícola). Se descartó.
- Elegido: **moderada + tabla de alias curada a mano** (`../data/alias_curados.csv`,
  ~28 merges, aprobada por Daniel). Une Caicedo→13, Royal Bank, Compañía Central,
  typos de OCR; **mantiene cada banco separado**. Editable: agregar `variante,
  canonico` y re-correr `construir_datos.py`.

## Los 11 puntos (en `lib/textos.py`)

- **I. Anatomía**: p1 campana vs cola larga (CV) · p2 por qué desconectada ·
  p3 clustering ≈ 0.
- **II. Actores**: p4 top acumuladores · p5 ¿por qué no hay brokers? (excepción =
  quien compra Y vende) · p6 rankear por #compras vs área vs valor (¡dan actores
  distintos!) · p7 papel del Municipio de Cali (vende 41, compra 8).
- **III. Régimen**: p8 slider de años → ¿sube el CV? (salvedad: 1943 domina el
  volumen) · p9 vinculación preferencial (caso Caicedo; cautela: no es prueba
  de ley de potencia).
- **IV. Interpretación**: p10 ensayo "¿cómo emergió el espacio urbano?" · p11
  límites de la red (una sola notaría, 1938–44) y qué fuente/método agregar.

**SIN grupos A/B/C**: el parcial es transversal, se evalúa solo sobre la red
inmobiliaria (Notaría 2) para todos (como el Taller 4, que también quitó el
selector de grupo). NO reintroducir un selector de grupo ni preguntas por grupo.

## Persistencia (Google Sheets)

- Mismo spreadsheet del Taller 3/4 (`1pquFP4e-SMK1gTYJQNSz8AtV2Ce7V0MDwlPSSQhKW3c`),
  **pestaña nueva `parcial_final`** (se crea sola al primer envío).
- Service account `detective-redes@complejidad-496215` (ya tiene permiso).
- **Una fila por pareja.** Columnas: `timestamp, integrante1, codigo1,
  integrante2, codigo2, grupo, resp_p1..resp_p11, timestamp_final`.
- Dashboard docente protegido por `secrets["dashboard"]["password"]`.

## Pitfalls (heredados del Taller 4 — respetar)

- **scipy obligatorio** en requirements (`nx.spring_layout` con N grande lo pide).
- **Strings con LaTeX → `r"""..."""`** (Python 3.12+ avisa por `\g`, `\s`, etc.).
- Streamlit 1.59: `use_container_width` **ya está deprecado** → usar
  `width="stretch"` en `st.plotly_chart` (ya migrado).
- **El grafo de la red NO es Plotly** — es un **D3 force-directed en canvas**
  (`lib/canvas.py`), portado 1:1 del Taller 5 (`RedRealCanvas.tsx`): mismas
  constantes de fuerza, flechas vendedor→comprador, rampa de calor por compras
  (azul claro→rojo), hover con vecinos, zoom/pan, botón "Centrar". Se embebe con
  `components.v1.html` (d3 por CDN). **`st.iframe` NO sirve** (requiere URL, no
  acepta HTML+JS inline) → se ignora el deprecation warning de `components.v1.html`.
- Filtro `conectados` (comp≥3, default) / `todos` / `nucleos` (comp≥4): solo
  cambia lo que se DIBUJA; las métricas usan siempre la red completa.
- Verificación visual del canvas: Playwright con el chromium ya cacheado
  (`~/Library/Caches/ms-playwright/chromium_headless_shell-1223/...`), screenshot
  de `localhost:8501` (el AppTest NO ejecuta el JS del iframe).

## Verificación

- `streamlit.testing.v1.AppTest` corre ambos scripts sin excepción y cubre el
  flujo: registro (pareja) → guardar punto → slider de años → radio de métrica →
  enviar → dashboard. Correr ese smoke test antes de tocar la UI.

## Deploy (pendiente de decidir con el usuario)

- Streamlit Cloud, dos entry points (`parcial_app.py` y `dashboard.py`) desde el
  mismo repo, como el Taller 3. **Falta**: crear repo (¿`Rodato`?), subir secrets
  (mismas keys del Taller 4 + `[dashboard] password`, `worksheet="parcial_final"`).

## Autoría

Diseño del parcial y app: **Boris Salazar y Daniel Otero**.
