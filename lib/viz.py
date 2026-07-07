"""Visualizaciones Plotly para el parcial. Todo estático (sin física animada)."""
from __future__ import annotations

import networkx as nx
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from lib.red import bonito

# paleta coherente
AZUL = "#2c6fbb"
ROJO = "#c0392b"
GRIS = "#95a5a6"
VERDE = "#27ae60"


def fig_distribucion_grado(tabla: pd.DataFrame) -> go.Figure:
    """Histograma del grado de entrada (compras)."""
    vals = tabla["compras"].to_numpy()
    fig = go.Figure(go.Histogram(
        x=vals, xbins=dict(start=0, end=max(1, vals.max()) + 1, size=1),
        marker_color=AZUL, marker_line_color="white", marker_line_width=1,
    ))
    fig.update_layout(
        title="Distribución del grado de entrada (nº de compras por actor)",
        xaxis_title="compras (grado de entrada)",
        yaxis_title="nº de actores",
        yaxis_type="log", bargap=0.05, height=380,
        margin=dict(l=10, r=10, t=50, b=10),
    )
    fig.add_annotation(x=0.98, y=0.95, xref="paper", yref="paper",
                       text="eje Y en escala log", showarrow=False,
                       font=dict(size=11, color=GRIS))
    return fig


def _fmt_valor(metrica: str, x: float) -> str:
    if metrica in ("compras", "ventas", "grado_total"):
        return f"{int(x)}"
    if metrica == "betweenness":
        return f"{x:.5f}"
    if metrica == "valor_comprado":
        return f"${x:,.0f}"
    if metrica == "area_comprada":
        return f"{x:,.0f} m²"
    return f"{x:g}"


def fig_ranking(tabla: pd.DataFrame, metrica: str, titulo: str,
                n: int = 10, color: str = AZUL) -> go.Figure:
    sub = (tabla.dropna(subset=[metrica])
           .sort_values(metrica, ascending=False).head(n).iloc[::-1])
    etiquetas = [bonito(a) for a in sub["actor"]]
    textos = [_fmt_valor(metrica, v) for v in sub[metrica]]
    fig = go.Figure(go.Bar(
        x=sub[metrica], y=etiquetas, orientation="h",
        marker_color=color, text=textos, textposition="auto",
        hovertemplate="%{y}<br>" + metrica.replace("_", " ") + ": %{text}<extra></extra>",
    ))
    fig.update_layout(
        title=titulo, height=max(320, 34 * len(sub) + 90),
        margin=dict(l=10, r=10, t=50, b=10),
        xaxis_title=metrica.replace("_", " "),
    )
    if metrica == "betweenness":
        fig.update_xaxes(tickformat=".4f")
    return fig


@st.cache_data(show_spinner=False)
def _layout(edges: tuple, seed: int = 42) -> dict:
    G = nx.Graph()
    G.add_edges_from(edges)
    return {n: (float(p[0]), float(p[1]))
            for n, p in nx.spring_layout(G, seed=seed, k=0.5).items()}


def fig_red(res: dict, min_componente: int = 3, n_etiquetas: int = 6) -> go.Figure:
    """Dibuja la red mostrando solo componentes de tamaño >= min_componente
    (para legibilidad). Tamaño del nodo = compras; color = compra−vende
    (ROJO = compra más, AZUL = vende más). Rotula los n_etiquetas más activos."""
    G: nx.DiGraph = res["G"]
    tabla = res["tabla"].set_index("actor")
    Gu = G.to_undirected()
    nodos = [n for c in nx.connected_components(Gu)
             if len(c) >= min_componente for n in c]
    H = G.subgraph(nodos)
    edges = tuple(sorted(H.to_undirected().edges()))
    if not edges:
        return go.Figure()
    pos = _layout(edges)

    ex, ey = [], []
    for u, v in H.edges():
        if u in pos and v in pos:
            ex += [pos[u][0], pos[v][0], None]
            ey += [pos[u][1], pos[v][1], None]
    edge_trace = go.Scatter(x=ex, y=ey, mode="lines",
                            line=dict(width=0.6, color="#d5dbe3"),
                            hoverinfo="none")

    nx_, ny_, size, color, text, activos = [], [], [], [], [], []
    for n in H.nodes():
        if n not in pos:
            continue
        c = int(tabla.at[n, "compras"]) if n in tabla.index else 0
        v = int(tabla.at[n, "ventas"]) if n in tabla.index else 0
        nx_.append(pos[n][0]); ny_.append(pos[n][1])
        size.append(9 + 3.4 * c)
        color.append(c - v)
        text.append(f"{bonito(n)}<br>compras: {c} · ventas: {v}")
        activos.append((c + v, n, pos[n]))
    node_trace = go.Scatter(
        x=nx_, y=ny_, mode="markers", hoverinfo="text", text=text,
        marker=dict(size=size, color=color, colorscale="RdBu_r",
                    cmid=0, cmin=-12, cmax=12, opacity=0.92,
                    line=dict(width=0.7, color="#64748b"),
                    colorbar=dict(title="compra − vende", thickness=12,
                                  tickvals=[-12, 0, 12],
                                  ticktext=["vende +", "0", "compra +"])),
    )

    activos.sort(reverse=True)
    top = activos[:n_etiquetas]
    label_trace = go.Scatter(
        x=[p[0] for _, _, p in top], y=[p[1] for _, _, p in top],
        mode="text", hoverinfo="none",
        text=[bonito(n) for _, n, _ in top],
        textposition="top center",
        textfont=dict(size=11, color="#1e293b"),
    )

    fig = go.Figure([edge_trace, node_trace, label_trace])
    fig.update_layout(
        title=f"Componentes con ≥{min_componente} actores "
              f"(el resto son tratos aislados)",
        showlegend=False, height=580, margin=dict(l=10, r=10, t=50, b=10),
        xaxis=dict(visible=False), yaxis=dict(visible=False),
        plot_bgcolor="white",
    )
    return fig


def fig_cv_por_anio(dfc: pd.DataFrame) -> go.Figure:
    fig = go.Figure()
    fig.add_bar(x=dfc["anio"], y=dfc["transacciones"], name="transacciones",
                marker_color=GRIS, yaxis="y2", opacity=0.4)
    fig.add_scatter(x=dfc["anio"], y=dfc["cv_compras"], name="CV del grado de entrada",
                    mode="lines+markers", line=dict(color=ROJO, width=3))
    fig.update_layout(
        title=dict(text="Concentración (CV) y volumen por año", y=0.97),
        height=420, margin=dict(l=10, r=10, t=50, b=70),
        yaxis=dict(title="CV del grado de entrada"),
        yaxis2=dict(title="transacciones", overlaying="y", side="right",
                    showgrid=False),
        legend=dict(orientation="h", y=-0.22, x=0.5, xanchor="center"),
    )
    return fig
