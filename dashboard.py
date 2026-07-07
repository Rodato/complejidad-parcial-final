"""Dashboard docente del Parcial Final — lectura de respuestas para calificar.

Protegido por contraseña (secrets["dashboard"]["password"]). Muestra una fila
por pareja con sus 11 respuestas, más un resumen de entregas.
"""
import streamlit as st

from lib import storage, textos

st.set_page_config(page_title="Parcial · Docente", page_icon="🧑‍🏫",
                   layout="wide")


def _password_ok() -> bool:
    try:
        esperada = st.secrets["dashboard"]["password"]
    except Exception:
        return True  # sin secret configurado (uso local) -> abierto
    if st.session_state.get("dash_ok"):
        return True
    pw = st.text_input("Contraseña docente", type="password")
    if pw and pw == esperada:
        st.session_state["dash_ok"] = True
        return True
    if pw:
        st.error("Contraseña incorrecta.")
    return False


st.title("🧑‍🏫 Parcial Final · Panel docente")

if not _password_ok():
    st.stop()

df = storage.leer_respuestas()
if df.empty:
    st.info("Aún no hay respuestas registradas.")
    st.stop()

# resumen
puntos = [f"resp_{p}" for p in [f"p{i}" for i in range(1, 12)]]
df["_respondidos"] = df[puntos].apply(
    lambda r: sum(1 for x in r if str(x).strip()), axis=1)
df["_enviado"] = df["timestamp_final"].apply(lambda x: bool(str(x).strip()))

c = st.columns(4)
c[0].metric("Parejas", len(df))
c[1].metric("Enviados (final)", int(df["_enviado"].sum()))
c[2].metric("Prom. puntos respondidos", round(df["_respondidos"].mean(), 1))
c[3].metric("Almacenamiento", storage.modo_almacenamiento())

st.divider()

filtro = st.text_input("Filtrar por nombre o código", "")
vista = df
if filtro.strip():
    f = filtro.strip().lower()
    mask = df.apply(lambda r: f in " ".join(str(v).lower() for v in r.values), axis=1)
    vista = df[mask]

st.caption(f"{len(vista)} pareja(s)")

for _, fila in vista.iterrows():
    quienes = fila.get("integrante1", "")
    if str(fila.get("integrante2", "")).strip():
        quienes += f" & {fila['integrante2']}"
    estado = "✅ enviado" if fila["_enviado"] else "✏️ en curso"
    cab = f"{quienes}  ·  {fila['_respondidos']}/11  ·  {estado}"
    with st.expander(cab):
        st.caption(f"Códigos: {fila.get('codigo1','')} · {fila.get('codigo2','')}"
                   f"  |  inicio: {fila.get('timestamp','')}"
                   f"  |  final: {fila.get('timestamp_final','')}")
        for clave, (_, titulo, _, _) in textos.PUNTOS.items():
            resp = str(fila.get(f"resp_{clave}", "")).strip()
            st.markdown(f"**{titulo}**")
            st.markdown(resp if resp else "_(sin responder)_")
            st.divider()
