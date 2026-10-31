"""Estadística de juicios ordinarios: resultados por periodo, juzgador, defensa, prueba y citas."""
import json, math, pathlib, re
import pandas as pd

RAIZ = pathlib.Path(__file__).resolve().parent.parent
DAT = RAIZ / "datos"

JUEZ = {}  # Variantes de escritura de nombres; se define localmente.

def wilson(k, n, z=1.96):
    if n == 0:
        return (None, None)
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    m = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (round(100 * (c - m), 1), round(100 * (c + m), 1))

def tasa(df):
    """% de sentencias donde la acción principal NO prosperó (el patrón la ganó)."""
    x = df[df.accion_principal.isin(["si", "no"])]
    k, n = int((x.accion_principal == "no").sum()), len(x)
    a, b = wilson(k, n)
    return dict(n=n, gana_patron=k, pct=round(100 * k / n, 1) if n else None, ic_inf=a, ic_sup=b)

def cargar():
    d = pd.read_csv(DAT / "sentencias.csv", low_memory=False)
    d = d[~d.sid.astype(str).isin(json.load(open(DAT / "excluidas.json")))]
    d["juez"] = d["juez"].replace(JUEZ).fillna("Sin identificar")
    d["registros"] = d["registros"].fillna("")
    return d

def main():
    d = cargar()
    o = d[d.juicio == "Procedimiento Ordinario"].sort_values("fecha").copy()
    vig = o.groupby(["area", "exp"]).tail(1).copy()  # última sentencia de cada expediente
    vig["defendido"] = ~vig.rebeldia_res
    D = vig[vig.defendido]
    R = {"sentencias_ordinarias": len(o), "expedientes": len(vig), "con_rebeldia": int(vig.rebeldia_res.sum()),
         "resultado": vig.resultado.value_counts().to_dict(), "accion_principal": vig.accion_principal.value_counts().to_dict(),
         "general": tasa(vig), "rebeldia": tasa(vig[vig.rebeldia_res]), "defendidos": tasa(D)}
    R["por_periodo_defendidos"] = {k: tasa(g) for k, g in D.groupby("periodo")}
    R["por_periodo_todos"] = {k: tasa(g) for k, g in vig.groupby("periodo")}
    R["por_periodo_rebeldia_pct"] = {k: round(100 * g.rebeldia_res.mean(), 1) for k, g in vig.groupby("periodo")}
    R["por_juez_defendidos"] = {k: dict(tasa(g), **{"total_con_rebeldia": int(len(vig[vig.juez == k]))}) for k, g in D.groupby("juez")}
    R["por_tribunal_defendidos"] = {k: tasa(g) for k, g in D.groupby("tribunal")}
    R["por_tramite_defendidos"] = {k: tasa(g) for k, g in D.groupby("tramite") if len(g) >= 5}
    defs = [c for c in o if c.startswith("def_")]
    R["defensas"] = {c[4:]: dict(tasa(D[D[c]]), sin=tasa(D[~D[c]])["pct"]) for c in defs}
    R["renuncia_escrita"] = tasa(D[D.def_renuncia & D.renuncia_escrita])
    R["renuncia_verbal"] = tasa(D[D.def_renuncia & D.renuncia_verbal])
    R["oferta"] = {k: tasa(g) for k, g in D[D.oferta_calif.notna()].groupby("oferta_calif")}
    prs = ["confesional", "testimonial", "inspeccion", "pericial", "documental"]
    R["pruebas"] = {p: dict(con=tasa(D[D["pr_" + p] > 0]), neg=int((D["pr_" + p + "_neg"] > 0).sum()), pos=int((D["pr_" + p + "_pos"] > 0).sum())) for p in prs}
    R["pericial_grafica"] = tasa(D[D.pericial_grafica])
    R["objecion_firma"] = tasa(D[D.objecion_firma])
    # Amparo
    mult = o.groupby(["area", "exp"]).filter(lambda g: len(g) > 1)
    cambios = 0
    grupos = 0
    for _, g in mult.groupby(["area", "exp"]):
        a = g.accion_principal.iloc[0]
        b = g.accion_principal.iloc[-1]
        if a in ("si", "no") and b in ("si", "no"):
            grupos += 1
            cambios += a != b
    R["reposiciones"] = dict(expedientes_con_varias=int(mult.groupby(["area", "exp"]).ngroups), comparables=grupos, cambio_de_sentido=cambios,
                             sentencias_con_ejecutoria=int(o.ejecutoria.sum()))
    # Citas
    J = {str(x["registro"]): x for x in json.load(open(DAT / "jurisprudencia.json"))}
    c = {}
    por_reg = {}
    for r in o.itertuples():
        for g in str(r.registros).split(";"):
            if g:
                c[g] = c.get(g, 0) + 1
                por_reg.setdefault(g, []).append(int(r.sid))
    tot = sum(c.values())
    enSG = {k: v for k, v in c.items() if k in J}
    R["citas"] = dict(sentencias_con_cita=int((o.registros != "").sum()), citas_total=tot, registros_distintos=len(c),
                      en_santo_grial=len(enSG), citas_en_santo_grial=sum(enSG.values()))
    R["top_scjn"] = [dict(registro=k, citas=v, rubro=J[k]["rubro"][:120], instancia=J[k]["instancia"], epoca=J[k]["epoca"]) for k, v in sorted(enSG.items(), key=lambda x: -x[1])[:25]]
    R["top_otros"] = [dict(registro=k, citas=v) for k, v in sorted(c.items(), key=lambda x: -x[1]) if k not in J][:25]
    json.dump(por_reg, open(DAT / "citas_por_registro.json", "w"))
    vig.to_csv(DAT / "ordinarios_vigentes.csv", index=False)
    json.dump(R, open(DAT / "analisis.json", "w"), ensure_ascii=False, indent=1, default=str)
    return R

if __name__ == "__main__":
    print(json.dumps(main(), ensure_ascii=False, indent=0, default=str))
