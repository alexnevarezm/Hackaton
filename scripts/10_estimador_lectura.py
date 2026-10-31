"""Prueba un estimador solo con defensas opuestas, según las fichas (sin usar cómo se resolvieron)."""
import json, pathlib
import numpy as np, pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import brier_score_loss, roc_auc_score
from sklearn.model_selection import RepeatedStratifiedKFold
DAT = pathlib.Path(__file__).resolve().parent.parent / "datos"
V = pd.read_csv(DAT / "ordinarios_vigentes.csv", usecols=["sid", "periodo", "tramite"]).set_index("sid")
K = ["renuncia_escrita", "renuncia_verbal", "abandono", "negativa_despido", "inexistencia_relacion", "ofrecimiento_trabajo", "prescripcion", "rescision", "contrato_determinado", "convenio_finiquito", "pago", "falta_accion", "oscuridad"]
F = []
for s in V.index:
    p = DAT / "lectura" / f"{s}.json"
    if p.exists():
        x = json.load(open(p))
        if x.get("contesto") is True and x.get("prospero_accion_principal") in ("si", "no"):
            ds = {e.get("defensa") for e in x.get("defensas") or [] if isinstance(e, dict)}
            F.append(dict(sid=s, y=int(x["prospero_accion_principal"] == "no"), reinst=int(V.tramite[s] == "Reinstalación"), per=V.periodo[s], **{k: int(k in ds) for k in K}))
D = pd.DataFrame(F); X = D[K + ["reinst"]]; y = D.y.values
p = np.zeros(len(y)); n = np.zeros(len(y))
for a, b in RepeatedStratifiedKFold(n_splits=5, n_repeats=10, random_state=1).split(X, y):
    p[b] += LogisticRegression(C=.5, max_iter=2000).fit(X.iloc[a], y[a]).predict_proba(X.iloc[b])[:, 1]; n[b] += 1
p /= n
A = (D.per == "antes_2025_09").values
m = LogisticRegression(C=.5, max_iter=2000).fit(X[A], y[A]); q = m.predict_proba(X[~A])[:, 1]
R = dict(n=len(y), base=round(y.mean(), 3), auc=round(roc_auc_score(y, p), 3), brier=round(brier_score_loss(y, p), 4), brier_base=round(brier_score_loss(y, np.full(len(y), y.mean())), 4),
         temporal=dict(prueba=int((~A).sum()), auc=round(roc_auc_score(y[~A], q), 3), brier=round(brier_score_loss(y[~A], q), 4), predicho=round(q.mean(), 3), real=round(y[~A].mean(), 3)))
f = LogisticRegression(C=.5, max_iter=2000).fit(X, y); R["coef"] = {k: round(c, 2) for k, c in zip(X.columns, f.coef_[0])}
json.dump(R, open(DAT / "estimador_lectura.json", "w"), ensure_ascii=False, indent=1); print(R)
