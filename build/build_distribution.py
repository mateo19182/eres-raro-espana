#!/usr/bin/env python3
"""
Construye la distribución conjunta ponderada de 7 ejes binarios a partir de los
microdatos del Barómetro del CIS (estudio nº 3557, abril 2026).

Salida: web/distribution.json  -> consumido por la página estática.

Cada eje se reduce a Sí (1) / No (0). Se usan casos completos: una persona
entra en la tabla solo si tiene respuesta válida en los 7 ejes. Se aplica el
coeficiente de ponderación oficial PESO.

La tabla conjunta son 128 celdas (2^7). El índice de cada celda es un bitmask
donde el bit i (orden de AXES) vale 1 si la respuesta del eje i es Sí.
"""
import json
import os
import numpy as np
import pyreadstat

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SAV = os.path.join(ROOT, "data", "raw", "3557.sav")
OUT = os.path.join(ROOT, "web", "distribution.json")

# --- Definición de los 7 ejes -------------------------------------------------
# Cada eje: (clave, etiqueta corta, pregunta Sí/No, función que devuelve una
# Serie con valores {1: Sí, 0: No, NaN: excluir}).
def axis_in(series, yes_vals, no_vals):
    """1 si está en yes_vals, 0 si está en no_vals, NaN en cualquier otro caso."""
    out = np.full(len(series), np.nan)
    out[series.isin(yes_vals).values] = 1.0
    out[series.isin(no_vals).values] = 0.0
    return out


def build_axes(df):
    axes = []

    # 1. Ideología: izquierda (1-4) vs centro/derecha (5-10). NS/NC excluidos.
    axes.append(dict(
        key="izquierda",
        label="Se sitúa a la izquierda",
        question="En política, ¿te sitúas a la izquierda?",
        detail="Posiciones 1 a 4 en la escala ideológica 1–10.",
        values=axis_in(df.ESCIDEOL, list(range(1, 5)), list(range(5, 11))),
    ))

    # 2. Religión: católico/a practicante (1) vs resto de creencias. NC excluido.
    axes.append(dict(
        key="catolico_practicante",
        label="Es católico/a practicante",
        question="¿Eres católico/a practicante?",
        detail="Frente a católicos no practicantes, otras religiones, agnósticos, indiferentes y ateos.",
        values=axis_in(df.RELIGION, [1], [2, 3, 4, 5, 6]),
    ))

    # 3. Intención de voto a la derecha (PP o VOX). Resto = No (incluye indecisos).
    axes.append(dict(
        key="voto_derecha",
        label="Votaría a PP o VOX",
        question="¿Votarías a PP o a VOX en unas generales?",
        detail="Intención de voto declarada. El resto (otros partidos, indecisos, abstención) cuenta como No.",
        values=axis_in(
            df.INTENCIONG,
            [2, 3],
            # No = cualquier valor presente que no sea PP/VOX
            [v for v in df.INTENCIONG.dropna().unique() if v not in (2, 3)],
        ),
    ))

    # 4. Confianza en Sánchez: mucha/bastante (1,2) vs poca/ninguna (3,4). NS/NC excluidos.
    axes.append(dict(
        key="confia_sanchez",
        label="Confía en Pedro Sánchez",
        question="¿Te inspira confianza Pedro Sánchez?",
        detail="Mucha o bastante confianza, frente a poca o ninguna.",
        values=axis_in(df.CONFIANZAPTE, [1, 2], [3, 4]),
    ))

    # 5. Estudios universitarios (diplomatura/grado/licenciatura/máster/doctorado...).
    axes.append(dict(
        key="universitario",
        label="Tiene estudios universitarios",
        question="¿Tienes estudios universitarios?",
        detail="Diplomatura, grado, licenciatura, ingeniería, máster oficial o doctorado.",
        values=axis_in(df.NIVELESTENTREV, list(range(9, 16)),
                       [1, 2, 3, 4, 5, 6, 7, 8, 16]),
    ))

    # 6. Hábitat urbano: municipios de más de 50.000 habitantes.
    axes.append(dict(
        key="ciudad",
        label="Vive en una ciudad (>50.000 hab.)",
        question="¿Vives en una ciudad de más de 50.000 habitantes?",
        detail="Frente a pueblos y municipios pequeños.",
        values=axis_in(df.TAMUNI, [4, 5, 6, 7], [1, 2, 3]),
    ))

    # 7. Quiere acabar con el cambio de hora (1) vs no (seguir / indiferente). NS/NC excluidos.
    axes.append(dict(
        key="acabar_cambio_hora",
        label="Quiere acabar con el cambio de hora",
        question="¿Quieres que se acabe con el cambio de hora?",
        detail="Frente a quienes prefieren seguir cambiando la hora dos veces al año o les da igual.",
        values=axis_in(df.P6, [1], [2, 3]),
    ))

    return axes


def main():
    df, meta = pyreadstat.read_sav(SAV)
    w = df["PESO"].to_numpy(dtype=float)
    axes = build_axes(df)

    mat = np.column_stack([a["values"] for a in axes])  # (n, 7)
    valid = ~np.isnan(mat).any(axis=1)
    n_total = len(df)
    n_valid = int(valid.sum())

    m = mat[valid].astype(int)
    wv = w[valid]
    wv_total = wv.sum()

    n_axes = len(axes)
    weights = [0.0] * (2 ** n_axes)
    counts = [0] * (2 ** n_axes)
    for row, weight in zip(m, wv):
        idx = 0
        for i, bit in enumerate(row):
            if bit:
                idx |= (1 << i)
        weights[idx] += float(weight)
        counts[idx] += 1
    # normaliza a proporciones
    weights = [x / wv_total for x in weights]

    # marginales ponderados por eje (para mostrar en la UI)
    marginals = []
    for i, a in enumerate(axes):
        col = m[:, i]
        p = float(np.average(col, weights=wv))
        marginals.append(round(p, 4))

    out = dict(
        meta=dict(
            source="CIS · Centro de Investigaciones Sociológicas",
            study="Estudio nº 3557 — Barómetro de abril 2026",
            fieldwork="Trabajo de campo: abril de 2026",
            universe="Población residente en España de 18 años y más",
            n_design=4000,
            n_total=n_total,
            n_valid=n_valid,
            weight="PESO (ponderación oficial del CIS)",
            note=("Casos completos sobre los 7 ejes. Porcentajes ponderados. "
                  "Las celdas son la distribución conjunta, por lo que conservan "
                  "las correlaciones reales entre respuestas."),
        ),
        axes=[dict(key=a["key"], label=a["label"], question=a["question"],
                   detail=a["detail"], marginal=marginals[i])
              for i, a in enumerate(axes)],
        weights=[round(x, 8) for x in weights],
        counts=counts,
    )

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    # también como data.js para que la página funcione abierta con file://
    with open(os.path.join(ROOT, "web", "data.js"), "w", encoding="utf-8") as f:
        f.write("window.CIS_DATA = ")
        json.dump(out, f, ensure_ascii=False)
        f.write(";\n")

    print(f"N total          : {n_total}")
    print(f"N casos válidos  : {n_valid}  ({100*n_valid/n_total:.1f}% retenido)")
    print(f"Suma proporciones: {sum(weights):.6f}")
    print("Marginales ponderados (% Sí):")
    for a, p in zip(axes, marginals):
        print(f"  {100*p:5.1f}%  {a['label']}")
    # celda más común y más rara (con al menos 1 obs)
    nz = [(p, i) for i, p in enumerate(weights) if counts[i] > 0]
    nz.sort()
    print(f"Celdas no vacías : {len(nz)}/128")
    print(f"Escrito en       : {OUT}")


if __name__ == "__main__":
    main()
