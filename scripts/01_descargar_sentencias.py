"""Descarga las versiones públicas listadas por el portal del PJ de Aguascalientes.
Reanudable: omite los PDF ya guardados. Pausa entre peticiones para no cargar el servidor."""
import base64, json, pathlib, sys, time
import requests

BASE = pathlib.Path(__file__).resolve().parent.parent / "datos"
SALIDA = BASE / "sentencias_pdf"
URL = "https://api.poderjudicialags.gob.mx/SICSEN/Consulta/ConvierteBase64"
H = {"Origin": "https://www.poderjudicialags.gob.mx",
     "Referer": "https://www.poderjudicialags.gob.mx/Web/ConsultaSentencias",
     "User-Agent": "Mozilla/5.0"}
PAUSA = 0.6

pend = []
for area in (32, 96, 97):
    for e in json.load(open(BASE / "listas_portal" / f"lista_{area}.json"))["Expediente"]:
        for s in e["Sentencias"]:
            pend.append((area, e["Consecutivo"].replace("/", "-"), s["SentenciaId"], s["ArchivoFinalRuta"]))

ok = err = omit = 0
fallos = []
for i, (area, exp, sid, ruta) in enumerate(pend, 1):
    dest = SALIDA / f"{area}_{exp}_{sid}.pdf"
    if dest.exists() and dest.stat().st_size > 0:
        omit += 1
        continue
    for intento in range(3):
        try:
            r = requests.post(URL, json={"ArchivoFinalRuta": ruta}, headers=H, timeout=120)
            b = r.json().get("ArchivoBase64")
            if b:
                dest.write_bytes(base64.b64decode(b.split(",")[-1]))
                ok += 1
                break
            motivo = str(r.json().get("Error"))
        except Exception as ex:
            motivo = repr(ex)
        time.sleep(5 * (intento + 1))
    else:
        err += 1
        fallos.append({"area": area, "exp": exp, "sid": sid, "motivo": motivo})
    time.sleep(PAUSA)
    if i % 100 == 0:
        print(i, len(pend), "ok", ok, "err", err, flush=True)
json.dump(fallos, open(BASE / "fallos_descarga.json", "w"), ensure_ascii=False, indent=1)
print("FIN total", len(pend), "nuevas", ok, "omitidas", omit, "errores", err)
