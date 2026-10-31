"""Embudo de los juicios individuales a partir de la base de acuerdos."""
import json, pathlib, re
import pandas as pd

RAIZ = pathlib.Path(__file__).resolve().parent.parent
X = pathlib.Path(RAIZ.parent) / "NEMA Estudio Juridico" / "JUICIOS AGUASCALIENTES" / "Juicios_Laborales_Ags.xlsx"
fr = []
for s in ["Tribunal Laboral", "1ro Laboral", "2do Laboral"]:
    d = pd.read_excel(X, sheet_name=s)
    d["hoja"] = s
    fr.append(d)
D = pd.concat(fr)
D = D[D["Expediente"].notna() & D["Fecha de acuerdo"].notna()].copy()
D["txt"] = D["Acuerdo (extracto)"].astype(str).str.upper()
D["fecha"] = pd.to_datetime(D["Fecha de acuerdo"], errors="coerce")
D["notas"] = D["Notas"].astype(str)

def nat(x):
    v = x[x != "SECRETO"]
    return v.mode().iloc[0] if len(v) else "SECRETO"

G = D.groupby(["hoja", "Expediente"])
E = G.agg(naturaleza=("Naturaleza", nat), primero=("fecha", "min"), ultimo=("fecha", "max"), acuerdos=("fecha", "size"),
          actor=("Actor", "first"), demandado=("Demandado", "first")).reset_index()

def fecha_si(mask, nombre):
    s = D[mask].groupby(["hoja", "Expediente"])["fecha"].min().rename(nombre)
    return E.merge(s, on=["hoja", "Expediente"], how="left")

t = D["txt"]
E = fecha_si(D["notas"].str.contains("Convenio") & t.str.contains("CONVENIO") & ~t.str.contains("CUMPLIMIENTO A SENTENCIA|DAR CUMPLIMIENTO"), "f_convenio")
E = fecha_si(D["notas"].str.contains("Desistimiento"), "f_desist")
E = fecha_si(D["notas"].str.contains("Sentencia") & t.str.contains(r"(?:DICTA|EMITE|DICTÓ)\s+SENTENCIA|SENTENCIA DEFINITIVA|SENTENCIA QUE RESUELVE"), "f_sentencia")
E = fecha_si(t.str.contains("REBELD|CONFESIÓN FICTA|CONFESION FICTA|SENTIDO AFIRMATIVO"), "f_rebeldia")
E = fecha_si(D["notas"].str.contains("Amparo") | D["Naturaleza"].astype(str).str.contains("AMPARO"), "f_amparo")
E = fecha_si(t.str.contains("AUDIENCIA PRELIMINAR"), "f_prelim")
E = fecha_si(t.str.contains("AUDIENCIA DE JUICIO"), "f_juicio")
E = fecha_si(t.str.contains("CAUSADO ESTADO"), "f_estado")
E["anio_exp"] = pd.to_numeric(E["Expediente"].str.extract(r"/(\d{4})")[0], errors="coerce")

ind = E["naturaleza"].str.contains("PROCEDIMIENTO ORDINARIO|ESPECIAL INDIVIDUAL", na=False)
E["individual"] = ind
E["contencioso"] = E["naturaleza"].str.contains("PROCEDIMIENTO ORDINARIO", na=False) | E["naturaleza"].str.contains("PRESTACIONES QUE NO EXCEDEN|INDEMNIZACION POR MUERTE|DETERMINACION DE ANTIGUEDAD|JORNADAS", na=False)

def destino(r):
    fs = {k: r[k] for k in ("f_sentencia", "f_convenio", "f_desist") if pd.notna(r[k])}
    if not fs:
        return "sin_terminacion_visible"
    return {"f_sentencia": "sentencia", "f_convenio": "convenio", "f_desist": "desistimiento"}[min(fs, key=fs.get)]

E["destino"] = E.apply(destino, axis=1)
E["dias_a_sentencia"] = (E["f_sentencia"] - E["primero"]).dt.days
E["dias_a_convenio"] = (E["f_convenio"] - E["primero"]).dt.days
E["dem_moral"] = E["demandado"].astype(str).str.upper().str.contains(r"S\.?\s?A\.?|S\. ?DE|C\.?V\.?|SOCIEDAD|S\.?C\.?\b|ASOCIACION|A\.C\.|S\.?R\.?L|S\.?A\.?P\.?I")
out = RAIZ / "datos" / "expedientes_base.csv"
E.to_csv(out, index=False)

C = E[E["contencioso"]]
res = {
    "todos_expedientes": len(E), "individuales": int(ind.sum()), "contenciosos": len(C),
    "destino_contenciosos": C["destino"].value_counts().to_dict(),
    "destino_por_tribunal": pd.crosstab(C["hoja"], C["destino"]).to_dict("index"),
    "destino_por_anio": pd.crosstab(C["anio_exp"], C["destino"]).to_dict("index"),
    "destino_por_naturaleza": pd.crosstab(C["naturaleza"], C["destino"]).to_dict("index"),
    "mediana_dias_sentencia": C.groupby("hoja")["dias_a_sentencia"].median().to_dict(),
    "mediana_dias_convenio": C.groupby("hoja")["dias_a_convenio"].median().to_dict(),
    "rebeldia_senal_en_sentenciados": float(C[C["destino"] == "sentencia"]["f_rebeldia"].notna().mean()),
    "con_rebeldia": int(C["f_rebeldia"].notna().sum()),
}
json.dump(res, open(RAIZ / "datos" / "embudo.json", "w"), ensure_ascii=False, indent=1, default=str)
print(json.dumps(res, ensure_ascii=False, indent=1, default=str))
# Etapa del convenio
z = C[C["destino"] == "convenio"]
print("convenio antes prelim", (z["f_prelim"].isna() | (z["f_convenio"] < z["f_prelim"])).mean(), "tras prelim antes juicio", ((z["f_convenio"] >= z["f_prelim"]) & (z["f_juicio"].isna() | (z["f_convenio"] < z["f_juicio"]))).mean())
print(E[E["contencioso"]].groupby("anio_exp").size())
