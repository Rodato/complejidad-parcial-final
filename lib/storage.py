"""Persistencia de respuestas del Parcial Final.

Backend primario: Google Sheets vía service account (mismo spreadsheet del
Taller 3/4, pestaña `parcial_final`). Fallback: CSV local cuando no hay
credenciales. Una fila por PAREJA (máx. 2 integrantes); la primera escritura
crea la fila y las siguientes actualizan la celda del punto enviado.

Reusa el patrón de 4. Taller/app/lib/storage.py.
"""
from __future__ import annotations

import csv
import re
from datetime import datetime
from pathlib import Path
from typing import Optional

import pandas as pd
import streamlit as st

# 11 puntos del parcial (p1..p11)
PUNTOS = [f"p{i}" for i in range(1, 12)]

COLUMNAS = [
    "timestamp",
    "integrante1", "codigo1",
    "integrante2", "codigo2",
    *[f"resp_{p}" for p in PUNTOS],
    "timestamp_final",
]

PUNTO_A_COLUMNA = {p: f"resp_{p}" for p in PUNTOS}

ARCHIVO_LOCAL = Path(__file__).parent.parent / "respuestas_local.csv"
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]


def _tiene_credenciales_google() -> bool:
    try:
        return bool(st.secrets.get("gcp_service_account")) and bool(st.secrets.get("sheets"))
    except Exception:
        return False


def _column_letter(n: int) -> str:
    s = ""
    while n > 0:
        n, r = divmod(n - 1, 26)
        s = chr(65 + r) + s
    return s


@st.cache_resource
def _abrir_hoja():
    import gspread
    from google.oauth2.service_account import Credentials

    creds = Credentials.from_service_account_info(
        dict(st.secrets["gcp_service_account"]), scopes=SCOPES,
    )
    client = gspread.authorize(creds)
    cfg = st.secrets["sheets"]
    if "url" in cfg:
        sh = client.open_by_url(cfg["url"])
    elif "id" in cfg:
        sh = client.open_by_key(cfg["id"])
    else:
        raise RuntimeError("Falta sheets.url o sheets.id en secrets.toml")

    ws_name = cfg.get("worksheet", "parcial_final")
    try:
        ws = sh.worksheet(ws_name)
    except gspread.WorksheetNotFound:
        ws = sh.add_worksheet(title=ws_name, rows=1000, cols=len(COLUMNAS))

    if ws.row_values(1) != COLUMNAS:
        if ws.col_count < len(COLUMNAS):
            ws.resize(rows=ws.row_count, cols=len(COLUMNAS))
        ws.update(values=[COLUMNAS],
                  range_name=f"A1:{_column_letter(len(COLUMNAS))}1",
                  value_input_option="RAW")
    return ws


def _parse_row_index(updated_range: str) -> Optional[int]:
    m = re.search(r"!\s*[A-Z]+(\d+)\s*:", updated_range)
    return int(m.group(1)) if m else None


def _guardar_local(fila: list) -> int:
    nuevo = not ARCHIVO_LOCAL.exists()
    with ARCHIVO_LOCAL.open("a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        if nuevo:
            w.writerow(COLUMNAS)
        w.writerow(fila)
    with ARCHIVO_LOCAL.open(encoding="utf-8") as f:
        return sum(1 for _ in f)


def _actualizar_celda_local(row_index: int, columna: str, valor: str):
    if not ARCHIVO_LOCAL.exists():
        return
    df = pd.read_csv(ARCHIVO_LOCAL, dtype=str, keep_default_na=False, na_filter=False)
    idx = row_index - 2
    if idx < 0 or idx >= len(df):
        return
    df.loc[idx, columna] = valor
    df.to_csv(ARCHIVO_LOCAL, index=False)


def crear_fila_pareja(payload: dict) -> tuple[bool, Optional[str], str, Optional[int]]:
    """Crea la fila inicial de la pareja. Devuelve (ok, error, destino, row_index).

    En modo Sheets NO se cae a CSV local: el índice de una fila local no es
    compatible con el de Sheets, y reusarlo después pisaría la fila de otra
    pareja. Si Sheets falla se devuelve un error honesto para que reintenten.
    """
    fila = [
        datetime.utcnow().isoformat(timespec="seconds"),
        payload.get("integrante1", ""), payload.get("codigo1", ""),
        payload.get("integrante2", ""), payload.get("codigo2", ""),
        *["" for _ in PUNTOS],
        "",
    ]
    if _tiene_credenciales_google():
        try:
            ws = _abrir_hoja()
            result = ws.append_row(fila, value_input_option="RAW")
            row = _parse_row_index(result.get("updates", {}).get("updatedRange", ""))
            if row is None:
                return False, "No se pudo determinar la fila creada en Sheets", "error", None
            return True, None, "sheets", row
        except Exception as e:
            return False, f"Error escribiendo a Sheets: {e}", "error", None
    row = _guardar_local(fila)
    return True, None, "local", row


def guardar_respuesta(row_index: int, punto: str, texto: str,
                      final: bool = False) -> tuple[bool, Optional[str], str]:
    """Actualiza la celda de un punto. punto ∈ PUNTO_A_COLUMNA."""
    columna = PUNTO_A_COLUMNA.get(punto)
    if not columna or not row_index:
        return False, f"Punto inválido o row_index faltante: {punto}", "ninguno"
    if _tiene_credenciales_google():
        try:
            ws = _abrir_hoja()
            col_idx = COLUMNAS.index(columna) + 1
            ws.update(values=[[texto]],
                      range_name=f"{_column_letter(col_idx)}{row_index}",
                      value_input_option="RAW")
            if final:
                col_ts = COLUMNAS.index("timestamp_final") + 1
                ws.update(values=[[datetime.utcnow().isoformat(timespec="seconds")]],
                          range_name=f"{_column_letter(col_ts)}{row_index}",
                          value_input_option="RAW")
            return True, None, "sheets"
        except Exception as e:
            # Modo Sheets: NO caer a CSV local (índices incompatibles y el
            # docente lee directo del Sheet). Error honesto para reintentar.
            return False, f"Error actualizando Sheets: {e}", "error"
    _actualizar_celda_local(row_index, columna, texto)
    if final:
        _actualizar_celda_local(row_index, "timestamp_final",
                                datetime.utcnow().isoformat(timespec="seconds"))
    return True, None, "local"


def modo_almacenamiento() -> str:
    return "sheets" if _tiene_credenciales_google() else "local"


def leer_respuestas() -> pd.DataFrame:
    """Lee todas las respuestas (Sheets o CSV local) para el dashboard docente."""
    if _tiene_credenciales_google():
        try:
            ws = _abrir_hoja()
            registros = ws.get_all_records(expected_headers=COLUMNAS)
            return pd.DataFrame(registros, columns=COLUMNAS)
        except Exception:
            pass
    if ARCHIVO_LOCAL.exists():
        return pd.read_csv(ARCHIVO_LOCAL, dtype=str, keep_default_na=False)
    return pd.DataFrame(columns=COLUMNAS)
