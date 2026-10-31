"""Entrena y prueba el estimador de 'la acción principal no prospera' en juicios ordinarios contestados.
Guarda datos/estimador.json para que 07_estimar.py funcione sin dependencias de aprendizaje automático."""
import json, pathlib
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import brier_score_loss, roc_auc_score
from sklearn.model_selection import RepeatedStratifiedKFold

DAT = pathlib.Path(__file__).resolve().parent.parent / "datos"
v = pd.read_csv(DAT / "ordinarios_vigentes.csv", low_memory=False)
v = v[~v.rebeldia_res & v.accion_principal.isin(["si", "no"])].copy()
v["y"] = (v.accion_principal == "no").astype(int)
TAGS = ["renuncia", "abandono", "negativa_despido", "inexistencia_relacion", "ofrecimiento_trabajo", "prescripcion", "rescision",
        "contrato_determinado", "convenio_finiquito", "pago", "obscuridad"]
X = pd.DataFrame({("def_" + t): v["def_" + t].astype(int) for t in TAGS})
X["renuncia_escrita"] = (v.def_renuncia & v.renuncia_escrita).astype(int)
X["renuncia_verbal"] = (v.def_renuncia & v.renuncia_verbal).astype(int)
X["pericial_grafica"] = v.pericial_grafica.astype(int)
X["reinstalacion"] = (v.tramite == "Reinstalación").astype(int)
X["desde_2025_09"] = (v.periodo == "desde_2025_09").astype(int)
y = v.y.values
M = lambda: LogisticRegression(C=0.5, max_iter=2000)
pred = np.zeros(len(y)); veces = np.zeros(len(y))
for tr, te in RepeatedStratifiedKFold(n_splits=5, n_repeats=10, random_state=1).split(X, y):
    pred[te] += M().fit(X.iloc[tr], y[tr]).predict_proba(X.iloc[te])[:, 1]; veces[te] += 1
pred /= veces
base = np.full(len(y), y.mean())
R = dict(n=len(y), tasa_base=round(float(y.mean()), 3), cv_auc=round(roc_auc_score(y, pred), 3), cv_brier=round(brier_score_loss(y, pred), 4), brier_base=round(brier_score_loss(y, base), 4))
bins = [0, .1, .2, .35, .5, 1]
c = pd.DataFrame(dict(p=pred, y=y)); c["g"] = pd.cut(c.p, bins)
R["calibracion"] = [dict(rango=str(k), n=int(len(g)), predicho=round(g.p.mean(), 3), real=round(g.y.mean(), 3)) for k, g in c.groupby("g", observed=True)]
ante = (v.periodo == "antes_2025_09").values
sinp = X.drop(columns=["desde_2025_09"])
m = M().fit(sinp[ante], y[ante]); q = m.predict_proba(sinp[~ante])[:, 1]
R["temporal"] = dict(entrena=int(ante.sum()), prueba=int((~ante).sum()), auc=round(roc_auc_score(y[~ante], q), 3), brier=round(brier_score_loss(y[~ante], q), 4),
                     brier_base=round(brier_score_loss(y[~ante], np.full((~ante).sum(), y[ante].mean())), 4), predicho=round(q.mean(), 3), real=round(y[~ante].mean(), 3))
f = M().fit(X, y)
rng = np.random.default_rng(7); B = []
for _ in range(300):
    i = rng.integers(0, len(y), len(y))
    if y[i].sum() == 0: continue
    b = M().fit(X.iloc[i], y[i]); B.append(np.r_[b.intercept_, b.coef_[0]])
json.dump(dict(columnas=list(X.columns), intercepto=float(f.intercept_[0]), coef=f.coef_[0].tolist(), bootstrap=np.array(B).round(4).tolist(), evaluacion=R), open(DAT / "estimador.json", "w"))
R["coef"] = {k: round(float(a), 2) for k, a in zip(X.columns, f.coef_[0])}
print(json.dumps(R, ensure_ascii=False, indent=0))
