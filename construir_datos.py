#!/usr/bin/env python3
"""
Genera datos/red_parcial.csv para la app del parcial final.

Fuente: ../data/consolidado_notaria2.csv + ../data/alias_curados.csv
Reusa la limpieza 'curada' de ../data/limpiar_red.py (moderada + alias curados):
normaliza, quita apoderados, separa co-partes y unifica los actores curados.

Salida (una fila por par vendedor->comprador, con atributos del registro):
  registro, anio, source, target, valor, area, negocio, escritura

- 'registro' identifica la transacción original: la app agrupa por registro
  para no doble-contar cuando una casilla trae varias partes.
- valor viene de valor_num del consolidado; area se parsea aquí.

Correr (dev, dentro del monorepo):  python construir_datos.py
Volver a correr si cambian los datos o la tabla de alias.
"""
import csv
import re
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
DATA = AQUI.parent / "data"
sys.path.insert(0, str(DATA))

import limpiar_red as LR  # noqa: E402

SALIDA = AQUI / "datos" / "red_parcial.csv"
CAMPOS = ["registro", "anio", "source", "target", "valor", "area",
          "negocio", "escritura"]


def limpiar_texto(s):
    return re.sub(r"\s+", " ", str(s or "").strip())


def parse_anio(s):
    m = re.search(r"\d{4}", str(s or ""))
    return int(m.group()) if m else ""


def parse_area(s):
    """Area a número (m²): toma el primer número, resolviendo miles/decimales.
    Maneja '144 m²', '~140.68 m²', '28,795 m²', '4,507 m² total'."""
    if not s:
        return ""
    txt = str(s).lower()
    if "especificada" in txt:
        return ""
    m = re.search(r"[\d.,]+", txt)
    if not m:
        return ""
    num = m.group().strip(".,")
    if "." in num and "," in num:
        if num.rfind(".") > num.rfind(","):     # US: 1,234.56
            num = num.replace(",", "")
        else:                                    # euro: 1.234,56
            num = num.replace(".", "").replace(",", ".")
    elif "," in num:                             # 28,795 -> miles ; 12,5 -> decimal
        num = num.replace(",", "" if len(num.split(",")[-1]) == 3 else ".")
    elif "." in num and len(num.split(".")[-1]) == 3:   # 1.234 -> miles
        num = num.replace(".", "")
    try:
        v = float(num)
    except ValueError:
        return ""
    return f"{v:.2f}".rstrip("0").rstrip(".")


def main():
    curados = LR.cargar_alias_curados()

    def canon(n):
        return curados.get(LR.clave_match(n), n)

    filas = []
    for i, r in enumerate(LR.leer_registros()):
        S = [canon(x) for x in LR.limpia_nodo_moderada(r.get("vendedor"))]
        B = [canon(x) for x in LR.limpia_nodo_moderada(r.get("comprador"))]
        if not S or not B:
            continue
        anio = parse_anio(r.get("anio"))
        valor = r.get("valor_num") or ""
        area = parse_area(r.get("area"))
        negocio = limpiar_texto(r.get("negocio"))
        escritura = limpiar_texto(r.get("escritura"))
        for s in S:
            for b in B:
                if s != b:
                    filas.append({
                        "registro": i, "anio": anio,
                        "source": s, "target": b,
                        "valor": valor, "area": area,
                        "negocio": negocio, "escritura": escritura,
                    })

    SALIDA.parent.mkdir(exist_ok=True)
    with open(SALIDA, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=CAMPOS)
        w.writeheader()
        w.writerows(filas)

    nodos = {x for fila in filas for x in (fila["source"], fila["target"])}
    registros = {fila["registro"] for fila in filas}
    print(f"Aristas (pares s->b): {len(filas)}")
    print(f"Registros con partes:  {len(registros)}")
    print(f"Actores (nodos):       {len(nodos)}")
    print(f"Salida: {SALIDA.relative_to(AQUI)}")


if __name__ == "__main__":
    main()
