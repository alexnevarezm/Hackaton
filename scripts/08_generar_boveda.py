"""Genera la bóveda de Obsidian 'Cerebro Ramón' a partir de los datos procesados. Sin nombres de partes."""
import json, pathlib, re, shutil
import pandas as pd

RAIZ = pathlib.Path(__file__).resolve().parent.parent
DAT = RAIZ / "datos"
B = RAIZ / "Cerebro Ramón"
A = json.load(open(DAT / "analisis.json"))
E = json.load(open(DAT / "estimador.json"))["evaluacion"]
J = json.load(open(DAT / "jurisprudencia.json"))
C = json.load(open(DAT / "citas_por_registro.json"))
S = pd.read_csv(DAT / "sentencias.csv", low_memory=False)
EMB = json.load(open(DAT / "embudo.json"))

for sub in ("Sentencias", "Jurisprudencia", "Juzgadores", "Defensas"):
    shutil.rmtree(B / sub, ignore_errors=True)

def w(rel, txt):
    p = B / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(txt.strip() + "\n", encoding="utf8")

def seguro(s, n=90):
    return re.sub(r'[\\/:*?"<>|#^\[\]]', "", s)[:n].strip()

def t(d):
    return f"{d['pct']}% ({d['gana_patron']} de {d['n']}; IC 95%: {d['ic_inf']}–{d['ic_sup']}%)"

AVISO = "> Cifras descriptivas de sentencias públicas de juicios ordinarios. No son probabilidad de ganar un caso concreto. Ver [[Calibración y límites]]."

NOM = {"renuncia": "Renuncia", "abandono": "Abandono de empleo", "negativa_despido": "Negativa del despido", "inexistencia_relacion": "Inexistencia de la relación laboral",
       "ofrecimiento_trabajo": "Ofrecimiento de trabajo", "prescripcion": "Prescripción", "rescision": "Rescisión justificada", "contrato_determinado": "Contrato por tiempo u obra determinados",
       "convenio_finiquito": "Convenio, finiquito y cosa juzgada", "pago": "Pago", "falta_legitimacion": "Falta de legitimación", "obscuridad": "Oscuridad de la demanda",
       "sustitucion_solidaria": "Sustitución y solidaridad", "confianza": "Trabajador de confianza"}
LECT = {
 "renuncia": "Separar siempre escrita y verbal. La escrita genera presunción, y si se objeta el contenido o la firma la pericial suele decidir. Un párrafo de renuncia dentro de un finiquito se ha tratado como simple indicio. La verbal exige precisar tiempo, modo y lugar en la contestación, y la testimonial sola se ha estimado insuficiente.",
 "abandono": "Se cita con frecuencia que la negativa del despido con la aclaración de que el trabajador dejó de presentarse no configura excepción, y que la carga queda en el patrón (registros 200634 y 202649).",
 "ofrecimiento_trabajo": "Se ha razonado que el ofrecimiento no revierte la carga si además se opone abandono: debe ser liso y llano. Si las condiciones difieren de las reales puede calificarse de mala fe.",
 "prescripcion": "Suele recortar prestaciones (art. 516 LFT) sin derrotar la acción principal. Se ha desestimado por redacción vaga, cuando no precisa el periodo prescrito. La prescripción de la acción de despido sí puede llevar a absolución.",
 "rescision": "Muestra pequeña. Se ha considerado inoperante una causal no planteada como rescisión en la contestación. Revisar aviso y causal desde el inicio.",
 "inexistencia_relacion": "La negativa lisa y llana suele dejar en el actor la carga de probar el vínculo. En pluralidad de demandados, un codemandado puede salir absuelto aunque otro sea condenado.",
 "convenio_finiquito": "La cosa juzgada por convenio previo ha llevado a absolución total. Revisar autenticidad y ratificación del convenio.",
}

# Inicio
w("00 Inicio.md", f"""
# Cerebro de Ramón
Mapa de trabajo para litigio laboral en juicios individuales de los tribunales laborales locales con sede en la ciudad de Aguascalientes.

## Empieza aquí
- [[Anatomía de servicio]]: cómo responder cada tipo de encargo
- [[Informe de fondo]]: hallazgos principales
- [[Calibración y límites]]: qué tan confiable es cada dato
- [[Panorama del tribunal]]: embudo de expedientes
- [[Índice de juzgadores]], [[Índice de defensas]], [[Pruebas]]
- [[Índice de jurisprudencia]] ({len(J):,} criterios de la SCJN)
- [[Índice de sentencias]] ({len(S):,} versiones públicas)

## Corte
Listas de acuerdos hasta el 30/10/2026. Sentencias publicadas en el portal, descargadas el 31/10/2026.
""")

ev = E
w("01 Funciones/Anatomía de servicio.md", """
# Anatomía de servicio
Cada función indica qué consultar y qué entregar. En todas: separar periodos antes y después del 01/09/2025, señalar tamaño de muestra y citar el expediente de apoyo.

## Estimar un caso
1. ¿Hay contestación admitida? Si no, ver [[Informe de fondo#Rebeldía]].
2. Identificar acción, defensas y pruebas. Correr `scripts/07_estimar.py`.
3. Entregar rango, comparables, factores que moverían la estimación y advertencia de [[Calibración y límites]].

## Revisar demanda o contestación
Contrastar cada hecho y excepción con [[Índice de defensas]] y [[Pruebas]]. Señalar contradicciones, omisiones de tiempo, modo y lugar, y cargas probatorias.

## Diseñar estrategia probatoria
Partir de quién carga con cada hecho. Ver [[Pruebas]] y las sentencias enlazadas de la defensa.

## Buscar jurisprudencia
Empezar por [[Índice de jurisprudencia]] y por los criterios más citados en el tribunal. Verificar vigencia en el Semanario antes de citar.

## Conciliar o litigar
Combinar [[Panorama del tribunal]] con la estimación. Falta el dato de montos: los resolutivos suelen venir testados.

## Compliance
Convertir cada causa de derrota en control preventivo: contestación oportuna, renuncias, controles de asistencia, recibos.

## Ventas y contenido de Ratio
Usar solo cifras de [[Calibración y límites]] con su alcance. Sin nombres de juzgadores ni promesas de resultado.

## Reglas de conducta
- Enfoque patronal. Ramón no es abogado con cédula: el criterio final es del abogado responsable.
- Sin nombres de partes en esta bóveda, aunque la base los tenga.
- Nunca presentar una estimación como resultado real.
""")

# Panorama
dc = EMB["destino_contenciosos"]; tot = sum(dc.values())
w("02 Tribunal/Panorama del tribunal.md", f"""
# Panorama del tribunal
Fuente: base de acuerdos del 06/07/2022 al 30/10/2026. Juicios individuales contenciosos identificados: **{tot:,}** (excluye los que siguen en secreto).

| Primera terminación visible | Juicios | % |
|---|---:|---:|
""" + "\n".join(f"| {k.replace('_',' ')} | {v:,} | {100*v/tot:.1f}% |" for k, v in dc.items()) + f"""

La clasificación viene de palabras en los acuerdos y "sin terminación visible" incluye muchos asuntos recientes.

Mediana de días del primer acuerdo registrado a sentencia, por tribunal: {EMB['mediana_dias_sentencia']}. A convenio: {EMB['mediana_dias_convenio']}. El primer acuerdo registrado no es la fecha de presentación.
""")

# Informe
D = A["defensas"]
w("03 Análisis/Informe de fondo.md", f"""
# Informe de fondo (versión inicial)
{AVISO}

Base: {A['sentencias_ordinarias']} sentencias ordinarias públicas de {A['expedientes']} expedientes; se usa la última de cada expediente. "Gana el patrón" significa que la acción principal no prosperó, aunque haya condena por otras prestaciones.

## Rebeldía
De {A['expedientes']} expedientes, **{A['con_rebeldia']}** tienen resolutivos que indican falta de contestación o excepciones. En ellos la acción no prosperó en {t(A['rebeldia'])}. Es el factor más fuerte de la muestra. El criterio más citado de la SCJN en el tribunal trata de esto: registro 2019360.

## Con contestación
La acción principal no prosperó en {t(A['defendidos'])}.

## Periodos
- Antes del 01/09/2025: {t(A['por_periodo_defendidos']['antes_2025_09'])}.
- Desde el 01/09/2025: {t(A['por_periodo_defendidos']['desde_2025_09'])}.
- Los intervalos se traslapan: todavía no se puede afirmar un cambio.
- Rebeldía: {A['por_periodo_rebeldia_pct']['antes_2025_09']}% antes, {A['por_periodo_rebeldia_pct']['desde_2025_09']}% después. Hay retraso de publicación, así que el periodo reciente puede cambiar.

## Renuncia: escrita y verbal
- Con señal de renuncia escrita: {t(A['renuncia_escrita'])}.
- Con señal de renuncia verbal: {t(A['renuncia_verbal'])}.
- Es la diferencia más útil hallada, aunque es asociación y depende de etiquetas automáticas.

## Defensas
| Defensa | n | Acción no prospera | IC 95% | Sin esa defensa |
|---|---:|---:|---|---:|
""" + "\n".join(f"| [[{NOM[k]}]] | {d['n']} | {d['pct']}% | {d['ic_inf']}–{d['ic_sup']}% | {d['sin']}% |" for k, d in sorted(D.items(), key=lambda x: -x[1]['n'])) + f"""

Una defensa que aparece no siempre es la que decidió el juicio, y suelen oponerse varias a la vez.

## Amparo
{A['reposiciones']['expedientes_con_varias']} expedientes tienen más de una sentencia publicada. En {A['reposiciones']['cambio_de_sentido']} de {A['reposiciones']['comparables']} comparables cambió el sentido sobre la acción principal entre la primera y la última. Revisar el amparo antes de leer una sentencia como definitiva.

## Citas
{A['citas']['sentencias_con_cita']} sentencias citan registros digitales ({A['citas']['citas_total']:,} citas, {A['citas']['registros_distintos']} registros). {A['citas']['en_santo_grial']} están en el santo grial. Muchas citas frecuentes son de tribunales colegiados y quedan fuera de esa compilación. Ver [[Índice de jurisprudencia]].

## Áreas de oportunidad
1. Asegurar contestación admitida, antes que cualquier otra táctica.
2. No sostener renuncia verbal sin hechos precisos y pruebas que se refuercen entre sí.
3. Preparar la pericial cuando se exhiba una renuncia escrita.
4. Oponer prescripción con periodos concretos.
5. Evitar combinar ofrecimiento de trabajo con abandono si se busca revertir la carga.

## Pendiente
Este informe se basa en reglas automáticas y lectura de muestras, no en la lectura completa de todas las sentencias.
""")

ca = E["calibracion"]
w("03 Análisis/Calibración y límites.md", f"""
# Calibración y límites

## Extracción
- Resultado y rebeldía: 39 de 40 aciertos cada uno en muestra aleatoria leída a mano (`datos/calibracion_resolutivos_40.csv`). Muestra pequeña, medida antes de ajustes finales menores.
- Defensas: cerca de 21 de 30 etiquetas revisadas eran claras. Después se excluyeron rubros de tesis citados, sin volver a medir. Tratar como confianza media.
- Pruebas y su valoración: no validadas. Solo orientativas.

## Estimador
Regresión logística sobre {E['n']} juicios contestados. Tasa base: {100*E['tasa_base']:.1f}%.
- Validación cruzada: AUC {E['cv_auc']}, Brier {E['cv_brier']} frente a {E['brier_base']} de la tasa base.
- Prueba temporal, entrenado antes del corte y probado después ({E['temporal']['prueba']} casos): AUC {E['temporal']['auc']}, Brier {E['temporal']['brier']} frente a {E['temporal']['brier_base']}; predicho {100*E['temporal']['predicho']:.1f}%, real {100*E['temporal']['real']:.1f}%.

| Rango predicho | n | Predicho | Real |
|---|---:|---:|---:|
""" + "\n".join(f"| {c['rango']} | {c['n']} | {100*c['predicho']:.1f}% | {100*c['real']:.1f}% |" for c in ca) + """

**Fuga de información:** las variables se extraen de la sentencia final, que ya refleja el juicio. El desempeño real con solo demanda y contestación probablemente será menor. Hay que probarlo con escritos reales antes de ofrecerlo.

## Sesgos
- Los juicios conciliados o desistidos no llegan a sentencia.
- No todas las sentencias dictadas están publicadas.
- La muestra de jueces actuales es pequeña y los anteriores dominan el modelo.
- Montos y muchos datos están testados.
- La SCJN no se verificó por vigencia; la compilación tampoco lo hace.
""")

# Juzgadores
idx = []
for nom, d in A["por_juez_defendidos"].items():
    sub = S[(S.juicio == "Procedimiento Ordinario") & (S.juez.fillna("Sin identificar").str.startswith(nom[:18]))]
    per = sub.periodo.value_counts().to_dict()
    aviso = "\n**Muestra pequeña: no usar como perfil individual.**\n" if d["n"] < 30 else ""
    w(f"Juzgadores/{seguro(nom)}.md", f"""
# {nom}
{AVISO}
{aviso}
- Sentencias ordinarias firmadas identificadas: {len(sub)} (por periodo: {per}).
- Con contestación, acción principal no prosperó: {t(d)}.
- Tribunales: {sub.tribunal.value_counts().to_dict()}.

La identidad sale de la firma en el texto. Las diferencias entre juzgadores no controlan el tipo de caso y sus intervalos pueden traslaparse.
""")
    idx.append(f"| [[{seguro(nom)}]] | {d['n']} | {d['pct']}% | {d['ic_inf']}–{d['ic_sup']}% |")
w("Juzgadores/Índice de juzgadores.md", f"# Índice de juzgadores\n{AVISO}\n\n| Juzgador | Contestados | Acción no prospera | IC 95% |\n|---|---:|---:|---|\n" + "\n".join(idx) + "\n\nUso interno. No difundir perfiles individuales.")

# Sentencias
vig = set(pd.read_csv(DAT / "ordinarios_vigentes.csv", usecols=["sid"]).sid)
porsid = {}
for r in S.itertuples():
    nombre = f"{r.tribunal} {str(r.exp).replace('/', '-')} s{r.sid}"
    porsid[int(r.sid)] = nombre
    defs = [k for k in NOM if getattr(r, "def_" + k, False) == True]
    regs = [x for x in str(r.registros).split(";") if x and x != "nan"]
    lj = {str(x["registro"]) for x in J}
    w(f"Sentencias/{r.tribunal}/{nombre}.md", f"""---
tribunal: {r.tribunal}
expediente: "{r.exp}"
fecha: {r.fecha}
tramite: "{r.tramite}"
periodo: {r.periodo}
resultado: {r.resultado}
accion_principal: {r.accion_principal}
rebeldia: {str(r.rebeldia_res).lower()}
vigente: {str(int(r.sid) in vig).lower()}
---
# {r.tribunal} {r.exp}
Juzgador: {f"[[{seguro(str(r.juez))}]]" if isinstance(r.juez, str) and r.juez != "Sin identificar" else "sin identificar"}. PDF: `datos/sentencias_pdf/{r.archivo}`

Defensas detectadas: {", ".join(f"[[{NOM[k]}]]" for k in defs) or "ninguna"}

Citas: {", ".join((f"[[R{x}]]" if x in lj else x) for x in regs) or "ninguna detectada"}

## Resolutivos (versión pública)
{str(r.resolutivos)[:2500]}
""")
w("Sentencias/Índice de sentencias.md", "# Índice de sentencias\nUna nota por versión pública, con propiedades para filtrar por tribunal, periodo, resultado y rebeldía.\n\n" + "\n".join(f"- {k}: {v}" for k, v in S.tribunal.value_counts().items()))

# Defensas
for k, d in D.items():
    col = "def_" + k
    casos = S[(S.juicio == "Procedimiento Ordinario") & (S[col] == True) & (~S.rebeldia_res) & (S.sid.isin(vig))].sort_values("fecha", ascending=False)
    gana = casos[casos.accion_principal == "no"].head(15); pierde = casos[casos.accion_principal == "si"].head(15)
    w(f"Defensas/{NOM[k]}.md", f"""
# {NOM[k]}
{AVISO}

- Acción principal no prosperó con esta señal: {t(d)}.
- Sin esta señal: {d['sin']}%.

## Lectura
{LECT.get(k, "Pendiente de lectura detallada.")}

## Casos donde no prosperó
""" + "\n".join(f"- [[{porsid[int(s)]}]]" for s in gana.sid) + "\n\n## Casos donde prosperó\n" + "\n".join(f"- [[{porsid[int(s)]}]]" for s in pierde.sid))
w("Defensas/Índice de defensas.md", "# Índice de defensas\n" + AVISO + "\n\n" + "\n".join(f"- [[{NOM[k]}]]: {d['n']} casos, {d['pct']}%" for k, d in sorted(D.items(), key=lambda x: -x[1]['n'])))

P = A["pruebas"]
w("03 Análisis/Pruebas.md", "# Pruebas\n" + AVISO + "\n\nConteos automáticos de juicios contestados donde se menciona la prueba. No miden su eficacia.\n\n| Prueba | Juicios | Acción no prospera |\n|---|---:|---:|\n" + "\n".join(f"| {k} | {v['con']['n']} | {v['con']['pct']}% |" for k, v in P.items()) + f"""

## Observado en la lectura de muestras
- **Testimonial:** se le resta eficacia si los testigos no coinciden entre sí o con la contestación, o agregan circunstancias no alegadas.
- **Documental objetada:** la renuncia escrita genera presunción que el actor puede destruir con prueba de su objeción.
- **Pericial en firma:** con señal de pericial gráfica, {t(A['pericial_grafica'])}. Puede decidir en cualquiera de los dos sentidos.
- **Contrato:** no es el medio idóneo para acreditar renuncia.
- **Confesional:** surte efectos en lo que perjudica a quien confiesa (registro 184931, muy citado).
""")

# Jurisprudencia
caps = {}
for x in J:
    nom = f"R{x['registro']}"
    n = len(C.get(str(x["registro"]), []))
    caps.setdefault(x["capitulo"], []).append((x, n))
    enl = "\n".join(f"- [[{porsid[s]}]]" for s in C.get(str(x["registro"]), [])[:20] if s in porsid)
    aviso = "\n> Criterio anterior a la reforma de 2019: verificar vigencia.\n" if x["epoca"] not in ("Undécima Época", "Duodécima Época") else ""
    w(f"Jurisprudencia/{seguro(x['capitulo'], 50)}/{nom}.md", f"""---
registro: "{x['registro']}"
instancia: {x['instancia']}
epoca: {x['epoca']}
citas_en_tribunal: {n}
subtema: "{x['subtema'] or ''}"
---
# {x['rubro']}
Registro digital {x['registro']} · {x['instancia']} · {x['epoca']} · {x['clave']}
{aviso}
{x['texto']}

**Precedentes:** {x['precedentes']}

## Citada en
{enl or "Sin citas detectadas."}
""")
L = ["# Índice de jurisprudencia", "Verificar vigencia en el Semanario antes de citar.", "", "## Más citadas en el tribunal"]
L += [f"- [[R{x['registro']}]] ({x['citas']} citas): {x['rubro']}" for x in A["top_scjn"]]
L += ["", "## Registros muy citados fuera de la compilación", "Sin rubro extraído; consultar en el Semanario."]
L += [f"- {x['registro']}: {x['citas']} citas" for x in A["top_otros"][:15]]
L += ["", "## Por capítulo"]
for c, v in caps.items():
    L += [f"### {c}"] + [f"- [[R{x['registro']}]] {x['rubro'][:110]}" for x, n in sorted(v, key=lambda a: -a[1])[:25]]
w("Jurisprudencia/Índice de jurisprudencia.md", "\n".join(L))
print("notas", sum(1 for _ in B.rglob("*.md")))
