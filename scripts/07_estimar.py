"""Estimación para un caso. Uso: 07_estimar.py '{"contesta": true, "renuncia": true, "renuncia_escrita": true}'
Claves: contesta, renuncia, renuncia_escrita, renuncia_verbal, abandono, negativa_despido, inexistencia_relacion,
ofrecimiento_trabajo, prescripcion, rescision, contrato_determinado, convenio_finiquito, pago, obscuridad, pericial_grafica, reinstalacion."""
import json, math, pathlib, sys

DAT = pathlib.Path(__file__).resolve().parent.parent / "datos"
E = json.load(open(DAT / "estimador.json"))
c = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
A = json.load(open(DAT / "analisis.json"))
if not c.get("contesta", True):
    print(json.dumps(dict(escenario="sin contestación admitida", pct_no_prospera=A["rebeldia"]["pct"], n=A["rebeldia"]["n"], aviso="Base descriptiva de la muestra, no predicción."), ensure_ascii=False))
    sys.exit()
x = []
for k in E["columnas"]:
    if k == "desde_2025_09":
        x.append(1)
    else:
        x.append(1 if c.get(k[4:] if k.startswith("def_") else k) else 0)
sig = lambda z: 1 / (1 + math.exp(-z))
p = sig(E["intercepto"] + sum(a * b for a, b in zip(E["coef"], x)))
bs = sorted(sig(b[0] + sum(a * v for a, v in zip(b[1:], x))) for b in E["bootstrap"])
print(json.dumps(dict(pct_no_prospera=round(100 * p, 1), rango_80=[round(100 * bs[int(.1 * len(bs))], 1), round(100 * bs[int(.9 * len(bs))], 1)],
                      base_contestados=round(100 * E["evaluacion"]["tasa_base"], 1), n_modelo=E["evaluacion"]["n"],
                      aviso="Estimación con datos del tribunal: resultado probable, no real. Puede cambiar según el juicio y su desarrollo probatorio."), ensure_ascii=False))
