"""Convierte el PDF 'santo grial' en datos/jurisprudencia.json (una ficha por criterio)."""
import json, pathlib, re, sys
import fitz

PDF = pathlib.Path(sys.argv[1])
BASE = pathlib.Path(__file__).resolve().parent.parent / "datos"
d = fitz.open(PDF)

def norm(x):
    return re.sub(r"\s+", " ", x).strip()

cap = sub = None
titulos = set()
ind = {}
inicio = None
for nivel, titulo, pag in d.get_toc():
    t = titulo.strip()
    if nivel == 1 and re.match(r"\d+\. [A-ZÁÉÍÓÚÑ][a-záéíóúñ]", t):
        cap, sub = t, None
        inicio = inicio or pag
    elif re.match(r"\d+\.\d+\. ", t):
        sub = t
    else:
        m = re.match(r"(\d+)\. (.+)", t)
        if m and cap:
            ind[int(m.group(1))] = {"capitulo": cap, "subtema": sub, "pag": pag, "_rubro": norm(m.group(2))}
        continue
    titulos.add(norm(t))

lineas = []
for n in range(inicio - 1, d.page_count):
    for l in d[n].get_text().split("\n"):
        l = norm(l)
        if not l or l in titulos or re.fullmatch(r"\d+ criterios?", l) or l.startswith("NEMA Estudio Jurídico ·") or re.fullmatch(r"Página \d+ de \d+", l):
            continue
        lineas.append((n + 1, l))

fichas, i, esperado = [], 0, 1
inicios = []
for k, (pag, l) in enumerate(lineas):
    m = re.match(r"(\d+)\. (\S.*)", l)
    if m and int(m.group(1)) == esperado and esperado in ind:
        cab = m.group(2)
        if ind[esperado]["_rubro"].startswith(cab[:40]):
            inicios.append((k, esperado))
            esperado += 1
inicios.append((len(lineas), None))

for (a, num), (b, _) in zip(inicios, inicios[1:]):
    bloque = [x[1] for x in lineas[a:b]]
    r = next(j for j, x in enumerate(bloque) if x.startswith("Registro digital:"))
    rubro = re.sub(r"^\d+\. ", "", " ".join(bloque[:r]))
    meta = bloque[r]
    resto = bloque[r + 1:]
    loc = ""
    if resto and resto[0].startswith("Localización:"):
        loc = resto.pop(0).replace("Localización:", "").strip()
    cuerpo = " ".join(resto)
    prec = ""
    p = cuerpo.find("Precedentes:")
    if p >= 0:
        cuerpo, prec = cuerpo[:p].strip(), cuerpo[p + 12:].strip()
    partes = [x.strip() for x in meta.replace("Registro digital:", "").split("·")]
    ficha = {"num": num, "rubro": rubro, "registro": partes[0], "instancia": partes[1] if len(partes) > 1 else "",
             "epoca": partes[2] if len(partes) > 2 else "", "clave": partes[4] if len(partes) > 4 else "",
             "localizacion": loc, "texto": cuerpo, "precedentes": prec, **{a: b for a, b in ind[num].items() if a != "_rubro"}}
    fichas.append(ficha)

json.dump(fichas, open(BASE / "jurisprudencia.json", "w"), ensure_ascii=False, indent=0)
print(len(fichas))
