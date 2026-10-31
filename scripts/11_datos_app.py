"""Prepara app/datos.js: solo coeficientes y cifras agregadas, sin partes, juzgadores ni fichas."""
import collections as C, json, pathlib
import numpy as np, pandas as pd
from sklearn.linear_model import LogisticRegression
RAIZ = pathlib.Path(__file__).resolve().parent.parent
DAT = RAIZ / "datos"
V = pd.read_csv(DAT / "ordinarios_vigentes.csv", usecols=["sid", "tramite"]).set_index("sid")
K = ["renuncia_escrita", "renuncia_verbal", "abandono", "negativa_despido", "inexistencia_relacion", "ofrecimiento_trabajo", "prescripcion", "rescision", "contrato_determinado", "convenio_finiquito", "pago", "falta_accion", "oscuridad"]
F, tab = [], C.defaultdict(C.Counter)
for s in V.index:
    p = DAT / "lectura" / f"{s}.json"
    if not p.exists():
        continue
    x = json.load(open(p))
    if x.get("contesto") is not True:
        continue
    es = [e for e in x.get("defensas") or [] if isinstance(e, dict)]
    for e in es:
        tab[e.get("defensa")][e.get("resultado")] += 1
    if x.get("prospero_accion_principal") in ("si", "no"):
        ds = {e.get("defensa") for e in es}
        F.append(dict(y=int(x["prospero_accion_principal"] == "no"), reinstalacion=int(V.tramite[s] == "Reinstalación"), **{k: int(k in ds) for k in K}))
D = pd.DataFrame(F)
col = K + ["reinstalacion"]
X, y = D[col], D.y.values
M = lambda: LogisticRegression(C=.5, max_iter=2000)
f = M().fit(X, y)
rng = np.random.default_rng(7)
B = []
for _ in range(200):
    i = rng.integers(0, len(y), len(y))
    b = M().fit(X.iloc[i], y[i])
    B.append([round(float(b.intercept_[0]), 3)] + [round(float(c), 3) for c in b.coef_[0]])
A = json.load(open(DAT / "analisis.json"))
E = json.load(open(DAT / "estimador_lectura.json"))
datos = dict(columnas=col, intercepto=float(f.intercept_[0]), coef=f.coef_[0].tolist(), bootstrap=B, n=len(y), base=float(y.mean()), casos={k: int(X[k].sum()) for k in col},
             defensas={k: dict(v) for k, v in tab.items() if k in K}, rebeldia=A["rebeldia"], contestados=A["defendidos"],
             prueba=dict(auc=E["auc"], auc_reciente=E["temporal"]["auc"], n_reciente=E["temporal"]["prueba"]))
(RAIZ / "app" / "datos.js").write_text("window.RATIO=" + json.dumps(datos, ensure_ascii=False, separators=(",", ":")) + ";\n", encoding="utf8")
print(len(y), round(y.mean(), 3), datos["casos"], {k: round(a, 2) for k, a in zip(col, f.coef_[0])})
e = {k: 0 for k in col}; print("base contraste", 1 / (1 + np.exp(-f.intercept_[0])))
