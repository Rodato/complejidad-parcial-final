"""Capa de datos y métricas de la red del parcial (Notaría 2, 1938–1944).

La red es DIRIGIDA: vendedor -> comprador (la tierra fluye al comprador).
La métrica central es el GRADO DE ENTRADA = compras = acumulación de tierra.

Se carga datos/red_parcial.csv (una fila por par vendedor->comprador con los
atributos del registro) y se agregan métricas por actor y globales. Todo está
cacheado con @st.cache_data; el filtro por año permite la vista longitudinal.
"""
from __future__ import annotations

from pathlib import Path

import networkx as nx
import numpy as np
import pandas as pd
import streamlit as st

DATOS = Path(__file__).parent.parent / "datos" / "red_parcial.csv"


def bonito(nombre: str) -> str:
    """Título legible para un actor (respeta siglas y partículas)."""
    if not isinstance(nombre, str):
        return str(nombre)
    menores = {"de", "del", "la", "las", "los", "y", "e", "vda", "v",
               "of", "the", "del", "en"}
    siglas = {"s.a", "sa", "s.a.", "cía", "cia"}
    palabras = []
    for w in nombre.split():
        wl = w.lower()
        if wl in siglas:
            palabras.append(w.upper())
        elif wl in menores:
            palabras.append(wl)
        else:
            palabras.append(w[:1].upper() + w[1:])
    txt = " ".join(palabras)
    return txt[:1].upper() + txt[1:] if txt else txt


@st.cache_data(show_spinner=False)
def cargar_df() -> pd.DataFrame:
    df = pd.read_csv(DATOS, dtype=str, keep_default_na=False)
    df["valor"] = pd.to_numeric(df["valor"], errors="coerce")
    df["area"] = pd.to_numeric(df["area"], errors="coerce")
    df["anio"] = pd.to_numeric(df["anio"], errors="coerce").astype("Int64")
    df["registro"] = pd.to_numeric(df["registro"], errors="coerce").astype("Int64")
    return df


def anios_disponibles() -> list[int]:
    df = cargar_df()
    return sorted(int(a) for a in df["anio"].dropna().unique())


def _tabla_actores(df: pd.DataFrame) -> pd.DataFrame:
    """Una fila por actor con compras/ventas/valor/area (sin doble-contar
    cuando un registro tiene varias partes: se deduplica por registro)."""
    compras_reg = df.drop_duplicates(["registro", "target"])
    ventas_reg = df.drop_duplicates(["registro", "source"])

    compras = compras_reg.groupby("target").size().rename("compras")
    ventas = ventas_reg.groupby("source").size().rename("ventas")
    valor_c = compras_reg.groupby("target")["valor"].sum(min_count=1).rename("valor_comprado")
    area_c = compras_reg.groupby("target")["area"].sum(min_count=1).rename("area_comprada")

    tabla = pd.concat([compras, ventas, valor_c, area_c], axis=1)
    tabla = tabla.reindex(sorted(set(df["source"]) | set(df["target"])))
    for col in ("compras", "ventas"):
        tabla[col] = tabla[col].fillna(0).astype(int)
    tabla.index.name = "actor"
    return tabla.reset_index()


@st.cache_data(show_spinner=False)
def resumen(anio_hasta: int | None = None) -> dict:
    """Métricas globales + tabla de actores. anio_hasta=None -> toda la serie
    (1938–1944 acumulada). Si se pasa un año, filtra registros <= ese año."""
    df = cargar_df()
    if anio_hasta is not None:
        df = df[df["anio"].notna() & (df["anio"] <= anio_hasta)]

    if df.empty:
        return {"N": 0, "L": 0}

    G = nx.from_pandas_edgelist(
        df.drop_duplicates(["source", "target"]),
        "source", "target", create_using=nx.DiGraph,
    )
    N, L = G.number_of_nodes(), G.number_of_edges()
    Gu = G.to_undirected()
    comps = sorted(nx.connected_components(Gu), key=len, reverse=True)
    gigante = len(comps[0]) if comps else 0

    tabla = _tabla_actores(df)
    betw = nx.betweenness_centrality(G)
    tabla["betweenness"] = tabla["actor"].map(betw).fillna(0.0)
    tabla["grado_total"] = tabla["compras"] + tabla["ventas"]

    compras_vals = tabla["compras"].to_numpy(dtype=float)
    mu = compras_vals.mean() if len(compras_vals) else 0.0
    cv = float(compras_vals.std() / mu) if mu else 0.0

    return {
        "df": df,
        "G": G,
        "tabla": tabla,
        "N": N,
        "L": L,
        "k_prom": round(2 * L / N, 2) if N else 0,
        "densidad": round(nx.density(G), 5) if N else 0,
        "n_componentes": len(comps),
        "gigante": gigante,
        "gigante_pct": round(100 * gigante / N, 1) if N else 0,
        "tam_componentes": [len(c) for c in comps[:8]],
        "clustering": round(nx.transitivity(G), 5) if N else 0,
        "cv_compras": round(cv, 2),
        "max_compras": int(tabla["compras"].max()) if N else 0,
        "betw_max": round(float(tabla["betweenness"].max()), 4) if N else 0,
        "solo_un_trato": int((tabla["grado_total"] == 1).sum()),
    }


def ranking(tabla: pd.DataFrame, metrica: str, n: int = 10) -> pd.DataFrame:
    """metrica in {compras, ventas, valor_comprado, area_comprada,
    betweenness, grado_total}. Devuelve top-n ordenado desc."""
    base = ["actor", "compras", "ventas", "valor_comprado",
            "area_comprada", "betweenness"]
    cols = base if metrica in base else base + [metrica]
    out = (tabla.dropna(subset=[metrica])
           .sort_values(metrica, ascending=False)
           .head(n)[cols].copy())
    out["actor"] = out["actor"].map(bonito)
    return out.reset_index(drop=True)


@st.cache_data(show_spinner=False)
def cv_por_anio() -> pd.DataFrame:
    """CV del grado de entrada y # transacciones por año (para la vista
    longitudinal del Acto III)."""
    filas = []
    df = cargar_df()
    for a in anios_disponibles():
        sub = df[df["anio"] == a]
        if sub.empty:
            continue
        tabla = _tabla_actores(sub)
        vals = tabla["compras"].to_numpy(dtype=float)
        mu = vals.mean() if len(vals) else 0
        cv = float(vals.std() / mu) if mu else 0
        filas.append({
            "anio": a,
            "transacciones": int(sub["registro"].nunique()),
            "actores": int(tabla.shape[0]),
            "cv_compras": round(cv, 2),
            "max_compras": int(tabla["compras"].max()),
        })
    return pd.DataFrame(filas)
