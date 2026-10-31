"""Integra las fichas de lectura (datos/lectura/*.json) a la bóveda. Correr después de 08_generar_boveda.py."""
import collections as C, json, pathlib, re
import pandas as pd

RAIZ = pathlib.Path(__file__).resolve().parent.parent
DAT = RAIZ / "datos"
B = RAIZ / "Cerebro Ramón"
S = pd.read_csv(DAT / "sentencias.csv", low_memory=False)
S = S[~S.sid.astype(str).isin(json.load(open(DAT / "excluidas.json")))]
VIG = set(pd.read_csv(DAT / "ordinarios_vigentes.csv", usecols=["sid"]).sid)
meta = {int(r.sid): r for r in S.itertuples()}
TOTAL = len(json.load(open(DAT / "lotes.json")))
F, malas = [], 0
for f in sorted((DAT / "lectura").glob("*.json")):
    try:
        x = json.loads(f.read_text(encoding="utf8"))
        x["sid"] = int(f.stem)
        if x["sid"] in meta:
            F.append(x)
    except Exception:
        malas += 1
nota = lambda sid: f"{meta[sid].tribunal} {str(meta[sid].exp).replace('/', '-')} s{sid}"
enl = lambda sid: f"[[{nota(sid)}]]"
per = lambda sid: meta[sid].periodo
NOM = {"renuncia_escrita": "Renuncia escrita", "renuncia_verbal": "Renuncia verbal", "abandono": "Abandono de empleo", "negativa_despido": "Negativa del despido", "inexistencia_relacion": "Inexistencia de la relación laboral",
       "ofrecimiento_trabajo": "Ofrecimiento de trabajo", "prescripcion": "Prescripción", "rescision": "Rescisión justificada", "contrato_determinado": "Contrato por tiempo u obra determinados", "convenio_finiquito": "Convenio, finiquito y cosa juzgada",
       "pago": "Pago", "falta_accion": "Falta de acción y derecho", "oscuridad": "Oscuridad de la demanda", "sustitucion_solidaria": "Sustitución y solidaridad", "confianza": "Trabajador de confianza", "otra": "Otras defensas"}
ls = lambda v: v if isinstance(v, list) else []
TODAS = F
F = [x for x in F if x["sid"] in VIG and x.get("contesto") is True]
d = C.defaultdict(list)
for x in F:
    for e in ls(x.get("defensas")):
        if isinstance(e, dict):
            d[e.get("defensa", "otra")].append((x["sid"], e.get("resultado", ""), e.get("razon", "")))
def tabla_d():
    o = ["| Defensa | Veces | Acogida | Parcial | Desestimada | No estudiada |", "|---|---:|---:|---:|---:|---:|"]
    for k, v in sorted(d.items(), key=lambda a: -len(a[1])):
        c = C.Counter(r for _, r, _ in v)
        o.append(f"| [[Lectura - {NOM.get(k, k)}\\|{NOM.get(k, k)}]] | {len(v)} | {c['acogida']} | {c['parcial']} | {c['desestimada']} | {c['no_estudiada']} |")
    return "\n".join(o)
L = B / "04 Lectura"
L.mkdir(exist_ok=True)
for k, v in d.items():
    t = [f"# Lectura: {NOM.get(k, k)}", f"{len(v)} apariciones en las fichas leídas. Razones como las resumió la lectura; verificar en la sentencia antes de usarlas.", ""]
    for res, tit in (("acogida", "Acogida"), ("parcial", "Parcial"), ("desestimada", "Desestimada"), ("no_estudiada", "No estudiada")):
        g = [a for a in v if a[1] == res]
        if g:
            t.append(f"## {tit} ({len(g)})")
            t += [f"- {enl(s)} ({per(s).replace('_', ' ')}): {r}" for s, _, r in g]
            t.append("")
    (L / f"Lectura - {NOM.get(k, k)}.md").write_text("\n".join(t), encoding="utf8")
pr = C.defaultdict(C.Counter); prz = C.defaultdict(list)
for x in F:
    for p in ls(x.get("pruebas")):
        if isinstance(p, dict):
            k = (p.get("tipo", "otra"), p.get("oferente", ""))
            pr[k][p.get("efecto", "")] += 1
            prz[k].append((x["sid"], p.get("efecto", ""), p.get("razon", "")))
t = ["# Lectura: pruebas", "| Prueba | Oferente | Favorable | Desfavorable | Neutra | Desierta | Desechada |", "|---|---|---:|---:|---:|---:|---:|"]
for k, c in sorted(pr.items(), key=lambda a: -sum(a[1].values())):
    t.append(f"| {k[0]} | {k[1]} | {c['favorable_oferente']} | {c['desfavorable_oferente']} | {c['neutra']} | {c['desierta']} | {c['desechada']} |")
for k in [("testimonial", "demandado"), ("documental", "demandado"), ("pericial", "demandado"), ("confesional", "demandado"), ("inspeccion", "demandado")]:
    t += ["", f"## {k[0].capitalize()} del demandado: por qué falló"]
    t += [f"- {enl(s)}: {r}" for s, e, r in prz[k] if e in ("desfavorable_oferente", "desierta", "desechada") and r]
(L / "Lectura - Pruebas.md").write_text("\n".join(t), encoding="utf8")
for campo, tit, arch in (("errores_patronales", "Errores patronales", "Errores patronales"), ("criterios_tribunal", "Criterios del tribunal", "Criterios del tribunal")):
    t = [f"# {tit}", "Listado por sentencia; las reglas son resumen de lectura, no transcripción. Citar solo tras revisar la sentencia.", ""]
    for x in F:
        v = [a for a in ls(x.get(campo)) if isinstance(a, str) and a]
        if v:
            t.append(f"### {enl(x['sid'])} · {per(x['sid']).replace('_', ' ')}")
            t += [f"- {a}" for a in v]
    (L / f"{arch}.md").write_text("\n".join(t), encoding="utf8")
# Ficha en cada sentencia
for x in TODAS:
    p = B / "Sentencias" / meta[x["sid"]].tribunal / (nota(x["sid"]) + ".md")
    if p.exists():
        s = p.read_text(encoding="utf8")
        s += f"\n## Lectura\n**Litis:** {x.get('litis','')}\n\n**Carga:** {x.get('carga_prueba','')}\n\n**Factor decisivo:** {x.get('factor_decisivo','')}\n\n**Oportunidad patronal:** {x.get('oportunidad_patronal','')}\n\n**Cita:** {x.get('cita','')}\n\nFicha completa: `datos/lectura/{x['sid']}.json`\n"
        p.write_text(s, encoding="utf8")
# Contraste con las reglas
v = pd.read_csv(DAT / "ordinarios_vigentes.csv", low_memory=False).set_index("sid")
ac = tot = 0; dif = []
for x in F:
    h = x.get("prospero_accion_principal"); r = v.accion_principal.get(x["sid"])
    if h in ("si", "no") and r in ("si", "no"):
        tot += 1; ac += h == r
        if h != r: dif.append(x["sid"])
juez = C.Counter(x.get("juzgador", "") for x in F)
txt = f"""# Lectura a fondo: estado
**{len(TODAS)} sentencias** tienen ficha. Las tablas usan {len(F)} sentencias ordinarias contestadas, la última de cada expediente. Lectura hecha por subagentes y no revisada una por una.

Contraste con las reglas automáticas sobre la acción principal: coinciden en {ac} de {tot}. Diferencias a revisar: {", ".join(enl(s) for s in dif) or "ninguna"}.

## Defensas según la lectura
{tabla_d()}

## Continuar
- [[Lectura - Pruebas]]
- [[Errores patronales]]
- [[Criterios del tribunal]]
"""
(L / "Lectura a fondo.md").write_text(txt, encoding="utf8")
i = B / "00 Inicio.md"
i.write_text(i.read_text(encoding="utf8").replace("## Corte", "- [[Hallazgos de la lectura]]: síntesis para litigio y lista de control\n- [[Lectura a fondo]]: fichas por sentencia, criterios y errores\n\n## Corte"), encoding="utf8")
print(len(F), "malas", malas, "coinciden", ac, tot, dif)
print(txt[txt.index("## Defensas"):txt.index("## Continuar")])
c = C.Counter(a for x in F for a in ls(x.get("errores_patronales")) if isinstance(a, str))
print(len(c)); print(juez.most_common(8))
