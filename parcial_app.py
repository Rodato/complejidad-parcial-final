"""Parcial Final — La red de propiedad de la Notaría 2 de Cali (1938–1944).

App de estudiantes (parejas). Presencial, enfoque mixto: algunas cifras dadas,
otras las obtienen moviendo controles; todo debe anclarse en los datos.
"""
import streamlit as st

from lib import red, textos, viz, canvas
from lib import storage

st.set_page_config(page_title="Parcial Final · Redes", page_icon="🕸️",
                   layout="wide", initial_sidebar_state="expanded")

# ---------------------------------------------------------------- estado
ss = st.session_state
ss.setdefault("registrado", False)
ss.setdefault("row_index", None)
ss.setdefault("identidad", {})
ss.setdefault("respuestas", {})

RES = red.resumen(anio_hasta=None)          # red completa (cacheada)
TABLA = RES["tabla"]


# ---------------------------------------------------------------- helpers
def guardar(punto: str, texto: str, final: bool = False):
    ok, err, destino = storage.guardar_respuesta(ss.row_index, punto, texto, final)
    ss.respuestas[punto] = texto
    if ok:
        st.toast(f"Guardado ({destino}) ✅")
    else:
        st.toast(f"Guardado local; Sheets falló: {err}", icon="⚠️")


def punto_ui(clave: str):
    """Enunciado + área de respuesta + botón guardar de un punto."""
    _, titulo, enunciado, alto = textos.PUNTOS[clave]
    st.markdown(f"#### {titulo}")
    st.markdown(enunciado)
    key = f"ta_{clave}"
    valor_previo = ss.respuestas.get(clave, "")
    texto = st.text_area("Su respuesta", value=valor_previo, height=alto,
                         key=key, label_visibility="collapsed",
                         disabled=not ss.registrado,
                         placeholder="Escriban aquí su respuesta…")
    col1, col2 = st.columns([1, 5])
    with col1:
        if st.button("💾 Guardar", key=f"btn_{clave}", disabled=not ss.registrado):
            guardar(clave, texto)
    with col2:
        if not ss.registrado:
            st.caption("Regístrense a la izquierda para poder responder.")


def actor_stats(nombre_norm: str) -> dict | None:
    fila = TABLA[TABLA["actor"] == nombre_norm]
    return fila.iloc[0].to_dict() if not fila.empty else None


# ---------------------------------------------------------------- sidebar
with st.sidebar:
    st.header("👥 Su pareja")
    if not ss.registrado:
        with st.form("registro"):
            i1 = st.text_input("Integrante 1 · nombre")
            c1 = st.text_input("Integrante 1 · código")
            i2 = st.text_input("Integrante 2 · nombre (opcional)")
            c2 = st.text_input("Integrante 2 · código (opcional)")
            enviar = st.form_submit_button("Iniciar parcial", type="primary")
        if enviar:
            if not i1.strip() or not c1.strip():
                st.error("Al menos el Integrante 1 (nombre y código) es obligatorio.")
            else:
                payload = {"integrante1": i1.strip(), "codigo1": c1.strip(),
                           "integrante2": i2.strip(), "codigo2": c2.strip()}
                ok, err, destino, row = storage.crear_fila_pareja(payload)
                ss.registrado = True
                ss.row_index = row
                ss.identidad = payload
                if ok:
                    st.success(f"¡Registrados! Guardando en: {destino}")
                else:
                    st.warning(f"Registrados (local). Sheets: {err}")
                st.rerun()
    else:
        ident = ss.identidad
        st.success("Registrados ✅")
        st.write(f"**{ident.get('integrante1','')}**")
        if ident.get("integrante2"):
            st.write(f"**{ident.get('integrante2','')}**")
        st.caption(f"Almacenamiento: {storage.modo_almacenamiento()}")

    st.divider()
    st.caption("Diseño: Boris Salazar y Daniel Otero · Introducción a la Complejidad")


# ---------------------------------------------------------------- cuerpo
st.title("🕸️ " + textos.TITULO)
st.markdown(textos.INTRO)

t_intro, t1, t2, t3, t4 = st.tabs(
    ["📊 La red", "① Anatomía", "② Actores", "③ Régimen", "④ Interpretación"])

# --- pestaña panorámica ---
with t_intro:
    st.subheader("Panorama de la red completa (1938–1944)")
    c = st.columns(4)
    c[0].metric("Actores (N)", RES["N"])
    c[1].metric("Transacciones (aristas)", RES["L"])
    c[2].metric("Grado medio ⟨k⟩", RES["k_prom"])
    c[3].metric("Componentes", RES["n_componentes"])
    c = st.columns(4)
    c[0].metric("Componente gigante", f'{RES["gigante_pct"]}%')
    c[1].metric("Clustering global", RES["clustering"])
    c[2].metric("CV grado de entrada", RES["cv_compras"], help=textos.CV_AYUDA)
    c[3].metric("En un solo trato", RES["solo_un_trato"])
    filtro = st.segmented_control(
        "Qué mostrar", options=["conectados", "todos", "nucleos"],
        default="conectados", label_visibility="collapsed",
        format_func=lambda f: {"conectados": "Conectados (grupos de 3+)",
                               "todos": "Toda la red",
                               "nucleos": "Núcleos (4+)"}[f]) or "conectados"
    nvis, ntot = canvas.red_canvas(RES, filtro=filtro, height=580)
    st.caption(f"Mostrando **{nvis}** de {ntot} actores. Arrastra para mover, "
               "rueda para zoom, pasa el mouse sobre un actor para ver sus "
               "cifras y vecinos. La flecha va del **vendedor → comprador** "
               "(sigue la tierra). Tamaño y color = nº de compras (azul claro "
               "= pocas, rojo = muchas = acumula tierra).")

# --- Parte I ---
with t1:
    titulo, intro = textos.PARTES["I"]
    st.subheader(titulo)
    st.markdown(intro)

    st.plotly_chart(viz.fig_distribucion_grado(TABLA), width="stretch")
    c = st.columns(3)
    c[0].metric("CV del grado de entrada", RES["cv_compras"], help=textos.CV_AYUDA)
    c[1].metric("Máximo de compras", RES["max_compras"])
    c[2].metric("Grado medio ⟨k⟩", RES["k_prom"])
    st.info(textos.CV_EXPLICACION)
    punto_ui("p1")
    st.divider()

    c = st.columns(4)
    c[0].metric("Componentes", RES["n_componentes"])
    c[1].metric("Componente gigante", f'{RES["gigante_pct"]}%')
    c[2].metric("Actores (N)", RES["N"])
    c[3].metric("En un solo trato", RES["solo_un_trato"])
    st.caption(f"Tamaño de los mayores componentes: {RES['tam_componentes']}")
    punto_ui("p2")
    st.divider()

    st.metric("Clustering global (transitividad)", RES["clustering"])
    punto_ui("p3")

# --- Parte II ---
with t2:
    titulo, intro = textos.PARTES["II"]
    st.subheader(titulo)
    st.markdown(intro)

    st.plotly_chart(
        viz.fig_ranking(TABLA, "compras", "Top acumuladores (grado de entrada)",
                        n=10, color=viz.AZUL),
        width="stretch")
    punto_ui("p4")
    st.divider()

    colA, colB = st.columns(2)
    with colA:
        st.plotly_chart(
            viz.fig_ranking(TABLA, "betweenness", "Top intermediación (betweenness)",
                            n=8, color=viz.VERDE),
            width="stretch")
        st.metric("Betweenness máxima de la red", RES["betw_max"],
                  help="Cerca de 0 = casi no hay intermediarios")
    with colB:
        st.plotly_chart(
            viz.fig_ranking(TABLA, "grado_total",
                            "Más activos (compras + ventas)", n=8, color=viz.GRIS),
            width="stretch")
    punto_ui("p5")
    st.divider()

    st.markdown("**Elijan la medida de acumulación:**")
    metrica = st.radio(
        "métrica", ["compras", "area_comprada", "valor_comprado"],
        format_func=lambda m: {"compras": "Nº de compras",
                               "area_comprada": "Área comprada (m²)",
                               "valor_comprado": "Valor comprado ($)"}[m],
        horizontal=True, label_visibility="collapsed")
    st.plotly_chart(
        viz.fig_ranking(TABLA, metrica, f"Top por {metrica.replace('_',' ')}",
                        n=10, color=viz.AZUL),
        width="stretch")
    punto_ui("p6")
    st.divider()

    muni = actor_stats("municipio de cali")
    if muni:
        c = st.columns(3)
        c[0].metric("Municipio de Cali · vende", int(muni["ventas"]))
        c[1].metric("Municipio de Cali · compra", int(muni["compras"]))
        c[2].metric("Grado total", int(muni["grado_total"]))
    punto_ui("p7")

# --- Parte III ---
with t3:
    titulo, intro = textos.PARTES["III"]
    st.subheader(titulo)
    st.markdown(intro)

    dfc = red.cv_por_anio()
    st.plotly_chart(viz.fig_cv_por_anio(dfc), width="stretch")

    anios = red.anios_disponibles()
    hasta = st.select_slider("Ver la red acumulada hasta el año:",
                             options=anios, value=anios[-1])
    r_anio = red.resumen(anio_hasta=hasta)
    c = st.columns(4)
    c[0].metric(f"Actores hasta {hasta}", r_anio["N"])
    c[1].metric("Transacciones", r_anio["L"])
    c[2].metric("CV grado de entrada", r_anio["cv_compras"], help=textos.CV_AYUDA)
    c[3].metric("Máx. compras", r_anio["max_compras"])
    punto_ui("p8")
    st.divider()

    cai = actor_stats("sebastián caicedo")
    if cai:
        c = st.columns(3)
        c[0].metric("Sebastián Caicedo · compra", int(cai["compras"]))
        c[1].metric("Sebastián Caicedo · vende", int(cai["ventas"]))
        c[2].metric("Betweenness", round(float(cai["betweenness"]), 4))
    punto_ui("p9")

# --- Parte IV ---
with t4:
    titulo, intro = textos.PARTES["IV"]
    st.subheader(titulo)
    st.markdown(intro)

    punto_ui("p10")
    st.divider()
    punto_ui("p11")
    st.divider()

    if ss.registrado:
        st.markdown("### ✅ Terminar y enviar")
        st.caption("Al enviar se marca la hora final. Pueden seguir editando "
                   "y guardando puntos individuales después si les queda tiempo.")
        if st.button("📨 Enviar parcial", type="primary"):
            # re-guarda todos los puntos por si algo quedó sin guardar
            for p in textos.PUNTOS:
                storage.guardar_respuesta(ss.row_index, p,
                                          ss.respuestas.get(p, ""), final=False)
            storage.guardar_respuesta(ss.row_index, "p11",
                                      ss.respuestas.get("p11", ""), final=True)
            st.success("¡Parcial enviado! Gracias. 🎉")
            st.balloons()
