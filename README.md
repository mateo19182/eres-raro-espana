# ¿Cómo de raro eres? — Explorador del español medio

Versión española de [«You're Weird: Explorer»](https://www.atvbt.com/youre-weird-explorer/).
Construye un perfil con 7 ejes (Sí / No / Cualquiera) y muestra qué porcentaje de
la población española adulta encaja con él, conservando las correlaciones reales
entre respuestas (distribución conjunta de 128 celdas, no producto de marginales).

## Datos

- **Fuente:** CIS — Estudio nº **3557**, Barómetro de **abril de 2026** (microdatos abiertos).
- Es el barómetro **más reciente con microdatos publicados** (los de mayo, est. 3562,
  aún no estaban disponibles al construir esto: solo el avance de resultados).
- N = 4.020 entrevistas; 3.751 válidas tras exigir respuesta en los 7 ejes (93,3 %).
- Ponderado con el coeficiente oficial `PESO`.

### Los 7 ejes
| Eje | Variable CIS | Sí = |
|---|---|---|
| Se sitúa a la izquierda | `ESCIDEOL` | 1–4 en escala 1–10 |
| Es católico/a practicante | `RELIGION` | =1 |
| Votaría a PP o VOX | `INTENCIONG` | PP(2) o VOX(3) |
| Confía en Pedro Sánchez | `CONFIANZAPTE` | mucha/bastante (1,2) |
| Tiene estudios universitarios | `NIVELESTENTREV` | 9–15 |
| Vive en ciudad >50.000 hab. | `TAMUNI` | 4–7 |
| Quiere acabar con el cambio de hora | `P6` | =1 |

## Estructura

```
data/raw/        microdatos del CIS (3557.sav, cuestionario, códigos…)
build/build_distribution.py   genera web/distribution.json y web/data.js
web/index.html   página estática (sin dependencias)
web/data.js      datos embebidos (funciona también abriendo el HTML con file://)
```

## Reconstruir

```bash
python -m venv .venv && . .venv/bin/activate
pip install pandas pyreadstat
python build/build_distribution.py
```

## Previsualizar

```bash
cd web && python -m http.server 8765   # http://localhost:8765
```

(Abrir `web/index.html` directamente también funciona gracias a `data.js`.)

## Cambiar de barómetro

Descarga el nuevo microdato (`https://www.cis.es/documents/d/guest/MD<ESTUDIO>-zip`),
descomprímelo en `data/raw/`, ajusta el nombre del `.sav` y, si cambian las variables,
las definiciones de ejes en `build/build_distribution.py`. Vuelve a ejecutar el build.
