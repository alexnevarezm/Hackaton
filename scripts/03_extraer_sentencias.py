"""Extrae variables de cada versión pública (reglas, no lectura humana) a datos/sentencias.csv.
Trabaja sobre texto 'comprimido' (sin espacios ni acentos) porque los PDF parten palabras."""
import json, pathlib, re, unicodedata
import fitz
import pandas as pd

RAIZ = pathlib.Path(__file__).resolve().parent.parent
DAT = RAIZ / "datos"
PDF = DAT / "sentencias_pdf"
AREAS = {32: "Tribunal Laboral", 96: "1ro Laboral", 97: "2do Laboral"}

def sin_acentos(s):
    return "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")

def limpia(s):
    s = re.sub(r"SIN VALIDEZ OFICIAL", " ", s)
    s = re.sub(r"\s*\n\s*", " ", s)
    s = re.sub(r"[ \t]{2,}", " ", s)
    return re.sub(r"\*[\* ]{2,}", "*** ", s)

def comp(s):
    return re.sub(r"[^a-z0-9$*]", "", sin_acentos(s).lower())

DEFENSAS = {
    "renuncia": r"renuncia",
    "abandono": r"abandon(o|ar)(del|de|su|el)?(empleo|trabajo|labores)|abandonodeempleo|dejodeasistir|dejodepresentarse",
    "negativa_despido": r"(nego|niega|negando|negar|neg[oó])(el|que|haber|la)?(existencia)?(del)?despido|inexistenciadeldespido|nofuedespedid|jamasfuedespedid|nuncafuedespedid|nohubodespido|noexistiodespido",
    "inexistencia_relacion": r"inexistenciadelarelacion|inexistenciadelvinculo|negolarelacion|niegalarelacion|negolaexistenciadelarelacion|niegalaexistenciadelarelacion|negolaexistenciadelvinculo|jamashaexistido|nuncaexistio(relacion|vinculo)|inexistenciadelnexo|nuncatrabajo|negativadelarelacion",
    "ofrecimiento_trabajo": r"ofrec(e|io|imiento|iendo|i)(de)?(el|l)?(a)?(s)?(u)?(trabajo|empleo|reinstal)|ofertadetrabajo|ofertalaboral|ofertadeempleo",
    "prescripcion": r"prescripcion|prescrit",
    "rescision": r"rescindio|rescisionjustificad|justificadarescision|causalderescision|actaadministrativa|investigacionadministrativa|rescindirla|rescisiondelarelacionsinresponsabilidad",
    "contrato_determinado": r"(tiempo|obra)determinad|vencimientodelcontrato|terminodelcontrato|terminaciondelcontrato|periododeprueba|capacitacioninicial",
    "convenio_finiquito": r"finiquito|conveniolaboral|cosajuzgada|convenioante|convenioratificado",
    "pago": r"excepciondepago|excepciondelpago|yafuepagad|acreditoelpago|acreditarelpago",
    "falta_legitimacion": r"legitimacion",
    "obscuridad": r"(obscuridad|oscuridad)|defectolegal",
    "sustitucion_solidaria": r"patronsustitut|sustitucionpatronal|responsabilidadsolidaria|beneficiari[oa]delaobra|subcontrat",
    "confianza": r"trabajadordeconfianza|personadeconfianza|empleadodeconfianza",
}
PRUEBAS = {"confesional": "confesional", "testimonial": "testimonial", "inspeccion": "inspeccion",
           "pericial": "pericial", "documental": "documental", "instrumental": "instrumental"}
TRIG = re.compile(r"contest|opuso|opone|opus|excepcion|defensa|nego|niega|litis|cargadelaprueba|respondio|adujo|arguy")
PATRON = re.compile(r"demandad|patron|empleador|contestacion|excepcion")
NEG_VAL = r"(sinvalor|noselotorgavalor|noseleotorgavalor|noseotorgavalor|carecedevalor|carecendevalor|noledavalor|noseleconcedevalor|nomerecevalor|nomerecenvalor|restarvalor|noesidonea|noresultaidone|noleproduce|nobeneficia|nolebeneficia|noaporta|noesapta)"
POS_VAL = r"(valorprobatorio|valorpleno|plenovalor|merecevalor|seleotorgavalor|seotorgavalor|seconcedevalor|hacepruebaplena|provechaenfavor|lebeneficia|leaprovecha|resultaidone)"

def resolutivos(t):
    """Devuelve (cuerpo, resolutivos) cortando en el último 'R E S U E L V E' con PRIMERO después."""
    c = list(re.finditer(r"R\s*E\s*S\s*U\s*E\s*L\s*V\s*E|PUNTOS RESOLUTIVOS|RESOLUTIVOS|[Ss]e resuelve|[Rr]esuelve\s*:", t))
    for m in reversed(c):
        if re.search(r"P\s*R\s*I\s*M\s*E\s*R\s*O", t[m.end():m.end() + 900]):
            return t[:m.start()], t[m.end():]
    m = None
    for m in re.finditer(r"PRIMERO\s*[\.\-:]", t):
        pass
    if m is not None and m.start() > len(t) * 0.5:
        return t[:m.start()], t[m.start():]
    return t, ""

def corta_res(r):
    for pat in (r"En la lista de acuerdos", r"[Nn]otif[ií]quese", r"Así lo resol", r"Lo prove"):
        m = re.search(pat, r)
        if m and m.start() > 80:
            r = r[:m.start()]
            break
    return r

def resultado(rc):
    """Clasifica con texto comprimido de los resolutivos."""
    abs_ = bool(re.search(r"seabsuelv|seleabsuelv|seabsolvio|absolverys|deabsolver|absueltoa|seabsolver", rc))
    con = bool(re.search(r"secondena|decondenar|procedentecondenar|condenandose|secondeno|condenara", rc))
    if abs_ and not con: return "absuelve_total"
    if con and abs_: return "condena_parcial"
    if con: return "condena_total"
    return "sin_clasificar"

V_ACC = r"(acredit[oa]r?o?n?|prob[oa]r?o?n?|justific[oa]r?o?n?|demostr[oa]r?o?n?)(laprocedenciade|laproced[a-z]*de)?(su|sus|la|las)?(accion|pretension)"

def principal(rc, res):
    """¿Prosperó la acción principal contra algún demandado? si/no/mixto/nd."""
    no = re.search(r"(no|nologro|sinhaber)" + V_ACC + r"|(?<!no)(?<!parcialmente)acredit[oa]r?o?n?(su|sus|la)(s)?excepcion|accion(es)?improcedente|improcedente(s)?laaccion|acreditolaexcepciondeprescripcion|actualizalafigura[a-z]*cosajuzgada", rc)
    si = re.search(r"(?<!no)" + V_ACC + r"|encuentraacreditadalaaccion|procedentelaaccion|procedentesuaccion|esprocedentelaaccion", rc)
    cond = re.search(r"(secondena|decondenar|procedentecondenar|condenara)[^.]{0,700}?(reinstal|indemnizacionconstitucional|indemnizacionde)", rc)
    abs_todo = re.search(r"(seabsuelv|absolverys|deabsolver)[^.]{0,400}?(todasycadauna|todaslasprestaciones|reinstal|indemnizacion)", rc)
    if no and not si:
        return "si" if cond else "no"
    if si and not no:
        return "si"
    if si and no:
        return "si" if cond else "mixto"
    if cond: return "si"
    if res == "absuelve_total" or (abs_todo and res != "condena_total"): return "no"
    if res in ("condena_total", "condena_parcial") and re.search(r"noopus|nodiocontestacion|nohabercomparecido", rc): return "si"
    return "nd"

def juzgador(t):
    cola = t[-6000:]
    pats = [
        r"(?:[Ll]icenciad[oa]|[Ll]ic\.|[Mm]aestr[oa]|[Mm]tr[oa]\.|[Dd]octor[a]?)\s+([A-ZÁÉÍÓÚÑ][\wáéíóúñÁÉÍÓÚÑ\. ]{6,60}?)\s*,?\s*(?:quien\s+)?(?:actúa\s+como\s+)?(Jue[zc]a?\b[^,\.]{0,50})",
        r"(?:LICENCIAD[OA]|LIC\.)\s+([A-ZÁÉÍÓÚÑ][A-ZÁÉÍÓÚÑ\. ]{6,60}?)\s*,?\s*(JUE[ZC]A?\b[^,\.]{0,50})",
    ]
    for p in pats:
        ms = list(re.finditer(p, cola))
        if ms:
            return re.sub(r"\s+", " ", ms[-1].group(1)).strip(" ,."), re.sub(r"\s+", " ", ms[-1].group(2)).strip()
    return "", ""

def oraciones(c_orig):
    return re.split(r"(?<=[\.;:])\s+", c_orig)

def analiza(ruta, meta):
    d = fitz.open(ruta)
    t = limpia("\n".join(p.get_text() for p in d))
    r = dict(meta, paginas=d.page_count, chars=len(t))
    cuerpo, res = resolutivos(t)
    res = corta_res(res)[:7000]
    rc = comp(res)
    bc = comp(cuerpo)
    r["resolutivos"] = res.strip()[:3500]
    r["resultado"] = resultado(rc) if rc else "sin_resolutivos"
    r["accion_principal"] = principal(rc, r["resultado"]) if rc else "nd"
    r["juez"], r["cargo"] = juzgador(t)
    r["periodo"] = "desde_2025_09" if meta["fecha"] >= "2025-09-01" else "antes_2025_09"
    r["rebeldia_res"] = bool(re.search(r"nohabercomparecido|noopus|nodiocontestacion|nohaberdadocontestacion|nohaberdadorespuesta|nocomparecio|rebeldia|nohabersele?s?admiti|nosele?s?admiti|nodarcontestacion|perdidosuderechoparaoponer|nohacercontestacion|hacercontestacion", rc))
    r["rebeldia_cuerpo"] = bool(re.search(r"rebeldia|sentidoafirmativo|nodiocontestacion|nosetuvoporcontestad|nosele?s?admitiolacontestacion|nocontestolademanda", bc))
    r["no_admitida"] = bool(re.search(r"nosele?s?admiti|nohabersele?s?admiti", rc + bc))
    r["ejecutoria"] = bool(re.search(r"ejecutoria|insubsistente|autoridadfederal|concesiondeamparo", rc))
    # Defensas: oraciones del cuerpo con disparador de contestación
    fin_ext = len(cuerpo)
    orig_oras = oraciones(cuerpo[:fin_ext])
    oras = [comp(o) for o in orig_oras]
    for k, pat in DEFENSAS.items():
        hit = 0
        ev = ""
        rx = re.compile(pat)
        for o, orig in zip(oras, orig_oras):
            letras = [c for c in orig if c.isalpha()]
            if letras and sum(c.isupper() for c in letras) / len(letras) > 0.6:
                continue  # Rubro de tesis citado, no alegato de las partes.
            if rx.search(o) and TRIG.search(o) and PATRON.search(o):
                hit += 1
                ev = ev or orig[:420]
        r["def_" + k] = hit > 0
        r["n_" + k] = hit
        r["ev_" + k] = ev
    # Matiz de renuncia
    r["renuncia_escrita"] = bool(re.search(r"renunciaporescrito|renunciaescrita|escritoderenuncia|cartaderenuncia|documentalderenuncia|firmo(su|la)renuncia|renunciafirmada|documentoderenuncia", bc))
    r["renuncia_verbal"] = bool(re.search(r"renunciaverbal|renunciodeformaverbal|renunciodemaneraverbal|verbalmenterenuncio|renunciodeformavoluntaria|renunciavoluntariayverbal|verbalyvoluntaria", bc))
    # Ofrecimiento
    of = [m.start() for m in re.finditer(r"ofrecimientodetrabajo|ofertadetrabajo|ofrecimientodelempleo|ofertalaboral|ofertadeempleo|ofrecimientodeltrabajo", bc)]
    bf = mf = 0
    for i in of:
        w = bc[max(0, i - 500):i + 700]
        mf += bool(re.search(r"malafe", w))
        bf += bool(re.search(r"buenafe", re.sub(r"verdadsabidaybuenafe|verdadsabida,?buenafe|buenafeguardada", "", w)))
    r["oferta_calif"] = "mala_fe" if mf and mf >= bf else ("buena_fe" if bf else ("sin_calif" if of else ""))
    # Excepciones concretas en resolutivos
    for k, pat in {"prescripcion": "prescripcion", "cosa_juzgada": "cosajuzgada", "pago": "excepciondepago"}.items():
        r["exc_res_" + k] = bool(re.search(pat, rc))
    pres = [m.start() for m in re.finditer(r"excepciondeprescripcion|prescripcion", bc)]
    ok = ko = 0
    for i in pres:
        w = bc[i:i + 400]
        ko += bool(re.search(r"improcedente|infundada|nooperala|noprocede|noprospera|desestim|inoperante", w))
        ok += bool(re.search(r"(resulta|es|deviene)(parcialmente)?(procedente|fundada)|operolaprescripcion|estaprescrit|prescribio|queprospera|procedentelaexcepcion", w))
    r["prescripcion_ok"] = ok
    r["prescripcion_ko"] = ko
    # Pruebas
    ora_pr = oras
    for k, s in PRUEBAS.items():
        menc = [o for o in ora_pr if s in o]
        r["pr_" + k] = len(menc)
        r["pr_" + k + "_neg"] = sum(bool(re.search(NEG_VAL, o)) for o in menc)
        r["pr_" + k + "_pos"] = sum(bool(re.search(POS_VAL, o)) for o in menc)
    r["pericial_grafica"] = bool(re.search(r"caligraf|grafoscop|dactiloscop|documentoscop", bc))
    r["objecion_firma"] = bool(re.search(r"objeto(el|la|los)?(documento|firma|contenido)|objecion(de)?(la)?firma|desconoci(o|miento)(de)?(la)?firma|noesfirma|firmaenblanco|enblanco", bc))
    r["art_784"] = "784" in cuerpo
    r["perspectiva_genero"] = bool(re.search(r"perspectivadegenero", bc))
    r["embarazo"] = bool(re.search(r"embaraz", bc))
    r["discriminacion"] = bool(re.search(r"discrimin", bc))
    r["acoso"] = bool(re.search(r"acoso|hostigamiento", bc))
    r["tiempo_extra"] = bool(re.search(r"tiempoextra|horasextra|jornadaextra", bc + rc))
    r["utilidades"] = bool(re.search(r"reparto|utilidades", rc))
    # Citas
    regs = re.findall(r"(?:registro|reg\.)\s*(?:digital|ius|n[uú]mero|no\.?)?\s*(?:n[uú]mero|no\.?|:|de)?\s*:?\s*(\d[\d ]{5,8})", t, re.I)
    regs = sorted({x.replace(" ", "") for x in regs if 6 <= len(x.replace(" ", "")) <= 7})
    r["registros"] = ";".join(regs)
    r["leyenda_prejudicial"] = bool(re.search(r"constanciadenoconciliacion|constanciadenoconciliar", bc))
    return r

def main():
    filas = []
    for a, nom in AREAS.items():
        for e in json.load(open(DAT / "listas_portal" / f"lista_{a}.json"))["Expediente"]:
            for s in e["Sentencias"]:
                ruta = PDF / f"{a}_{e['Consecutivo'].replace('/', '-')}_{s['SentenciaId']}.pdf"
                if not ruta.exists():
                    continue
                meta = dict(tribunal=nom, area=a, exp=e["Consecutivo"], sid=s["SentenciaId"], fecha=s["FechaDeDictado"][:10],
                            juicio=(e.get("Juicio") or {}).get("Nombre"), tramite=(e.get("Tramite") or {}).get("Nombre"),
                            archivo=ruta.name)
                try:
                    filas.append(analiza(ruta, meta))
                except Exception as ex:
                    filas.append(dict(meta, resultado="error", resolutivos=repr(ex)))
    df = pd.DataFrame(filas)
    df.to_csv(DAT / "sentencias.csv", index=False)
    print(len(df))
    return df

if __name__ == "__main__":
    df = main()
    print(df.resultado.value_counts())
    print(df.accion_principal.value_counts())
    print(df.juez.value_counts().head(25))
    print((df.chars < 3000).sum(), "con poco texto")
