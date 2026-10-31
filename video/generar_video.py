"""Video animado de Ratio: voz de Gemini (video/voz/N.wav) + animación con Pillow + ffmpeg.
Uso: generar_video.py preview | final"""
import glob, math, pathlib, random, subprocess, sys, wave
import fitz
import imageio_ffmpeg
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

RAIZ = pathlib.Path(__file__).resolve().parent
TMP = pathlib.Path(sys.argv[2])
TMP.mkdir(exist_ok=True)
FF = imageio_ffmpeg.get_ffmpeg_exe()
W, H, FPS, SR = 1920, 1080, 30, 44100

TINTA, PAPEL, AMBAR, GRIS, TEAL = (14, 26, 36), (243, 239, 230), (217, 164, 65), (138, 152, 165), (79, 163, 165)
SUP = "/System/Library/Fonts/Supplemental/"
_f = {}
def serif(s, b=False, i=False):
    n = "Georgia Bold.ttf" if b else ("Georgia Italic.ttf" if i else "Georgia.ttf")
    return _f.setdefault((n, s), ImageFont.truetype(SUP + n, s))
def sans(s, b=False):
    k = ("av", s, b)
    if k not in _f:
        _f[k] = ImageFont.truetype("/System/Library/Fonts/Avenir Next.ttc", s, index=2 if b else 7)
    return _f[k]

VOZ = "Eddy (Español (México))"
VOZ2 = "Paulina"
ESC = [
    ("gancho", VOZ2, "Licenciado, ¿qué posibilidades tengo de ganar?", 0.5, 1.0),
    ("conflicto", VOZ, "Todos hemos respondido esa pregunta con experiencia e intuición. Pero desde el primero de septiembre de dos mil veinticinco, el tribunal cambió: llegaron los jueces electos. ¿Cuánto de lo que sabíamos sigue aplicando?", 0.4, 0.8),
    ("giro", VOZ, "La respuesta está en lo que el propio tribunal ya resolvió. El problema es que nadie alcanza a leerlo todo.", 0.3, 0.5),
    ("marca", VOZ, "Por eso existe Ratio.", 0.4, 0.9),
    ("solucion", VOZ, "En materia laboral, Ratio analiza más de seis mil ochocientos juicios ordinarios, más de sesenta y tres mil acuerdos publicados desde julio de dos mil veintidós y setecientas sesenta y una sentencias públicas de los tribunales locales de la ciudad de Aguascalientes, México. Además, mil quinientos cuarenta y nueve criterios de la Suprema Corte de Justicia de la Nación. Y separa lo resuelto antes y después del cambio de jueces, para que compares tu asunto con los datos del tribunal.", 0.3, 0.6),
    ("honesto", VOZ, "Ratio no te dice cómo terminará tu juicio. Te da un análisis estimado: un resultado probable, no uno real. Y puede cambiar en cualquier momento, según las circunstancias de cada juicio y su desarrollo probatorio.", 0.3, 0.8),
    ("criterio", VOZ, "El criterio sigue siendo tuyo. Ahora lo respaldas con datos.", 0.3, 0.8),
    ("cierre", VOZ, "Ratio: la razón detrás de cada sentencia. Conócelo en una demostración.", 0.3, 5.0),
]

def voces():
    pistas, t = [], 0.0
    for i, (nom, voz, txt, pre, pos) in enumerate(ESC):
        a, b = RAIZ / "voz" / f"{i + 1}.wav", TMP / f"gemini_{i}.wav"
        if not b.exists():
            subprocess.run([FF, "-y", "-loglevel", "error", "-i", str(a), "-af", "loudnorm=I=-16:TP=-1.5:LRA=11", "-ar", str(SR), "-ac", "1", "-sample_fmt", "s16", str(b)], check=True)
        with wave.open(str(b)) as w:
            x = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16)
        dur = len(x) / SR
        pistas.append(dict(nom=nom, ini=t, voz_ini=t + pre, voz_fin=t + pre + dur, fin=t + pre + dur + pos, x=x, txt=txt))
        t += pre + dur + pos
    return pistas, t

def clamp(x, a=0.0, b=1.0): return max(a, min(b, x))
def ease(x):
    x = clamp(x)
    return 1 - (1 - x) ** 3
def mix(c1, c2, a):
    return tuple(int(c1[i] + (c2[i] - c1[i]) * clamp(a)) for i in range(3))
def centro(d, y, txt, f, col, x=W // 2):
    if col == TINTA:
        return  # Texto aún invisible: dibujarlo borraría lo que ya está debajo.
    b = d.textbbox((0, 0), txt, font=f)
    d.text((x - (b[2] - b[0]) / 2, y), txt, font=f, fill=col)
def parrafo(txt, f, ancho, d):
    ls, l = [], ""
    for p in txt.split():
        n = (l + " " + p).strip()
        if d.textlength(n, font=f) > ancho and l:
            ls.append(l); l = p
        else:
            l = n
    return ls + [l]
def aparece(t, t0, d=0.6, sal=None, ds=0.5):
    a = ease((t - t0) / d)
    if sal is not None:
        a *= 1 - ease((t - sal) / ds)
    return a

# Páginas reales de versiones públicas: solo primera hoja y desenfocadas, para que nada sea legible.
def miniaturas(n=24):
    salida = []
    fs = sorted(glob.glob(str(RAIZ.parent / "datos" / "sentencias_pdf" / "*.pdf")))
    random.Random(4).shuffle(fs)
    for f in fs[:n]:
        d = fitz.open(f)
        px = d[0].get_pixmap(dpi=40)
        im = Image.frombytes("RGB", (px.width, px.height), px.samples).filter(ImageFilter.GaussianBlur(1.6))
        salida.append(im.resize((150, 194)))
    return salida

R = random.Random(11)
NODOS = []
for _ in range(130):
    x, y = R.uniform(90, 1040), R.uniform(170, 860)
    NODOS.append((x, y))
NODOS.sort()
n_post = round(len(NODOS) * 108 / 761)
AR = []
for i, a in enumerate(NODOS):
    cerca = sorted(range(len(NODOS)), key=lambda j: (NODOS[j][0] - a[0]) ** 2 + (NODOS[j][1] - a[1]) ** 2)[1:4]
    AR += [(i, j) for j in cerca if i < j]

CIFRAS = [("primero de septiembre de dos mil veinticinco", "1 de septiembre de 2025"), ("seis mil ochocientos", "6,800"), ("sesenta y tres mil", "63 mil"),
          ("dos mil veintidós", "2022"), ("setecientas sesenta y una", "761"), ("mil quinientos cuarenta y nueve", "1,549")]

def rotulos(pistas):
    """Subtítulos por frases, repartidos según su longitud."""
    out = []
    for p in pistas:
        if p["nom"] in ("gancho", "marca", "criterio"):
            continue
        partes, act = [], ""
        texto = p["txt"]
        for a, b in CIFRAS:
            texto = texto.replace(a, b)
        for w in texto.split():
            act = (act + " " + w).strip()
            if len(act) > 62 or (w[-1] in ".:?" and len(act) > 20):
                partes.append(act); act = ""
        if act: partes.append(act)
        tot, t = sum(map(len, partes)), p["voz_ini"]
        for s in partes:
            d = (p["voz_fin"] - p["voz_ini"]) * len(s) / tot
            out.append((t, t + d, s)); t += d
    return out

def subt(d, t, subs):
    for a, b, s in subs:
        if a <= t < b:
            f = sans(34)
            w = d.textlength(s, font=f)
            d.rounded_rectangle((W / 2 - w / 2 - 22, 972, W / 2 + w / 2 + 22, 1032), 10, fill=(8, 15, 21))
            d.text((W / 2 - w / 2, 980), s, font=f, fill=PAPEL)

def s_gancho(im, d, t, p):
    a = aparece(t, 0.2, 0.9)
    txt = "“Licenciado, ¿qué posibilidades"
    centro(d, 410, txt, serif(76, i=True), mix(TINTA, PAPEL, a))
    centro(d, 510, "tengo de ganar?”", serif(76, i=True), mix(TINTA, PAPEL, aparece(t, 0.9, 0.9)))
    centro(d, 650, "— tu cliente", sans(32), mix(TINTA, GRIS, aparece(t, 1.8)))

def s_conflicto(im, d, t, p):
    D = p["fin"] - p["ini"]
    a1 = aparece(t, 0.2, 0.7, sal=D * 0.34)
    centro(d, 390, "Experiencia.", serif(84), mix(TINTA, PAPEL, a1))
    centro(d, 500, "Intuición.", serif(84), mix(TINTA, GRIS, aparece(t, 1.5, 0.7, sal=D * 0.34)))
    a2 = aparece(t, D * 0.38, 0.8, sal=D * 0.70)
    centro(d, 345, "1 de septiembre de 2025", serif(92, b=True), mix(TINTA, AMBAR, a2))
    centro(d, 480, "El tribunal cambió: llegaron los jueces electos.", sans(46), mix(TINTA, PAPEL, a2))
    l = ease((t - D * 0.42) / 1.2)
    y = 610
    d.line((W / 2 - 500 * l, y, W / 2 + 500 * l, y), fill=mix(TINTA, GRIS, a2), width=4)
    d.line((W / 2, y - 26, W / 2, y + 26), fill=mix(TINTA, AMBAR, a2), width=6)
    centro(d, 640, "antes", sans(34), mix(TINTA, GRIS, a2), W // 2 - 280)
    centro(d, 640, "después", sans(34), mix(TINTA, AMBAR, a2), W // 2 + 280)
    a3 = aparece(t, D * 0.74, 0.8)
    centro(d, 380, "¿Cuánto de lo que sabíamos", serif(76, i=True), mix(TINTA, PAPEL, a3))
    centro(d, 485, "sigue aplicando?", serif(76, i=True), mix(TINTA, PAPEL, a3))

def s_giro(im, d, t, p, th):
    D = p["fin"] - p["ini"]
    n = int(ease(t / (D * 0.8)) * 66)
    r = random.Random(3)
    for i in range(n):
        x, y = 40 + (i % 11) * 170, 30 + (i // 11) * 182
        m = th[i % len(th)]
        k = clamp((t - i * D * 0.8 / 66) / 0.5) * 0.42
        bg = Image.new("RGB", m.size, TINTA)
        im.paste(Image.blend(bg, m, k), (x + r.randint(-6, 6), y + r.randint(-6, 6)))
    v = Image.new("RGB", (W, 330), TINTA)
    a = aparece(t, 0.2, 0.8)
    im.paste(Image.blend(im.crop((0, 300, W, 630)), v, 0.82 * a), (0, 300))
    centro(d, 345, "La respuesta está en lo que", serif(66), mix(TINTA, PAPEL, a))
    centro(d, 435, "el propio tribunal ya resolvió.", serif(66, b=True), mix(TINTA, AMBAR, a))
    centro(d, 545, "Nadie alcanza a leerlo todo.", sans(38), mix(TINTA, PAPEL, aparece(t, D * 0.55)))

def logo(d, y, a, tam=170):
    f = serif(tam, b=True)
    w = d.textlength("Ratio", font=f)
    d.text((W / 2 - w / 2, y), "Ratio", font=f, fill=mix(TINTA, PAPEL, a))
    d.ellipse((W / 2 + w / 2 + 14, y + tam * 1.02, W / 2 + w / 2 + 14 + tam * .14, y + tam * 1.16), fill=mix(TINTA, AMBAR, a))

def s_marca(im, d, t, p):
    centro(d, 300, "Por eso existe", sans(46), mix(TINTA, GRIS, aparece(t, 0.2)))
    logo(d, 380, aparece(t, 0.7, 0.9))

def s_solucion(im, d, t, p):
    D = p["fin"] - p["ini"]
    S = 2
    capa = Image.new("RGB", (1120 * S, 960 * S), TINTA)
    g = ImageDraw.Draw(capa)
    prog = ease(t / (D * 0.75))
    mostrar = int(prog * len(NODOS))
    for i, j in AR:
        if i < mostrar and j < mostrar:
            c = mix(TINTA, AMBAR if j >= len(NODOS) - n_post else GRIS, 0.35)
            g.line((NODOS[i][0] * S, NODOS[i][1] * S, NODOS[j][0] * S, NODOS[j][1] * S), fill=c, width=2 * S // 2)
    for i in range(mostrar):
        x, y = NODOS[i]
        post = i >= len(NODOS) - n_post
        r = (9 if post else 6) * S
        g.ellipse((x * S - r, y * S - r, x * S + r, y * S + r), fill=AMBAR if post else GRIS)
    im.paste(capa.resize((1120, 960), Image.LANCZOS), (0, 0))
    xc = NODOS[len(NODOS) - n_post][0] - 8
    ad = aparece(t, D * 0.68, 0.8)
    for y in range(120, 900, 22):
        d.line((xc, y, xc, y + 10), fill=mix(TINTA, PAPEL, ad), width=2)
    d.text((xc - 262, 75), "Antes de 09/2025", font=sans(30), fill=mix(TINTA, GRIS, ad))
    d.text((xc + 16, 75), "Desde 09/2025", font=sans(30), fill=mix(TINTA, AMBAR, ad))
    centro(d, 22, "Materia laboral  ·  Juicios ordinarios  ·  Ciudad de Aguascalientes, México", sans(32, True), mix(TINTA, AMBAR, aparece(t, 0.2)))
    filas = [("+6,800", "juicios ordinarios", 0.08), ("+63 mil", "acuerdos desde julio de 2022", 0.17),
             ("761", "sentencias públicas", 0.30), ("1,549", "criterios de la SCJN (nacionales)", 0.55)]
    for k, (c, e, f) in enumerate(filas):
        a = aparece(t, D * f, 0.7)
        y = 120 + k * 195
        d.text((1180, y), c, font=serif(82, b=True), fill=mix(TINTA, PAPEL, a))
        d.text((1182, y + 100), e, font=sans(34), fill=mix(TINTA, GRIS, a))
    d.text((90, 905), "Representación ilustrativa", font=sans(22), fill=mix(TINTA, GRIS, aparece(t, 1)))

ETAPAS = [("Demanda", 50), ("Contestación", 61), ("Réplica", 54), ("Contrarréplica", 58), ("Audiencia Preliminar", 52), ("Audiencia de Juicio", 63), ("Sentencia", 63)]
def s_honesto(im, d, t, p):
    D = p["fin"] - p["ini"]
    a0 = aparece(t, 0.2, 0.6, sal=D * 0.22)
    centro(d, 390, "Ratio no te dice", serif(80), mix(TINTA, PAPEL, a0))
    centro(d, 495, "cómo terminará tu juicio.", serif(80, b=True), mix(TINTA, PAPEL, a0))
    a = aparece(t, D * 0.26, 0.7)
    if a <= 0:
        return
    centro(d, 95, "Análisis estimado: un resultado probable, no uno real.", serif(50), mix(TINTA, PAPEL, a))
    x0, x1, y = 260, 1660, 450
    S = 2
    d.rounded_rectangle((x0, y - 14, x1, y + 14), 14, fill=mix(TINTA, (50, 66, 80), a))
    tt = clamp((t - D * 0.42) / (D * 0.55))
    pos = tt * (len(ETAPAS) - 1)
    i = int(pos); fr = ease((pos - i) * 2.2)
    v = ETAPAS[i][1] if i == len(ETAPAS) - 1 else ETAPAS[i][1] + (ETAPAS[i + 1][1] - ETAPAS[i][1]) * fr
    xv = x0 + (x1 - x0) * v / 100
    ban = 9 * (x1 - x0) / 100
    d.rounded_rectangle((xv - ban, y - 14, xv + ban, y + 14), 14, fill=mix(TINTA, TEAL, a))
    d.ellipse((xv - 24, y - 24, xv + 24, y + 24), fill=mix(TINTA, AMBAR, a))
    centro(d, y - 130, f"{round(v)}%", serif(80, b=True), mix(TINTA, AMBAR, a), int(xv))
    d.text((x0, y + 34), "menos probable", font=sans(28), fill=mix(TINTA, GRIS, a))
    tx = "más probable"
    d.text((x1 - d.textlength(tx, font=sans(28)), y + 34), tx, font=sans(28), fill=mix(TINTA, GRIS, a))
    for k, (e, _) in enumerate(ETAPAS):
        xe = x0 + 70 + k * (x1 - x0 - 140) / (len(ETAPAS) - 1)
        act = k <= pos + 0.25
        d.ellipse((xe - 11, 625, xe + 11, 647), fill=mix(TINTA, AMBAR if act else (50, 66, 80), a))
        if k:
            xp = x0 + 70 + (k - 1) * (x1 - x0 - 140) / (len(ETAPAS) - 1)
            d.line((xp + 14, 636, xe - 14, 636), fill=mix(TINTA, GRIS if act else (50, 66, 80), a), width=3)
        lineas = e.split(" ", 1) if e.startswith("Audiencia") else [e]
        for n, l in enumerate(lineas):
            centro(d, 662 + n * 36, l, sans(28, b=act), mix(TINTA, PAPEL if act else GRIS, a), int(xe))
    centro(d, 790, "Puede cambiar según las circunstancias de cada juicio y su desarrollo probatorio.", sans(36), mix(TINTA, PAPEL, aparece(t, D * 0.62)))
    centro(d, 862, "Cifras ilustrativas", sans(28, b=True), mix(TINTA, AMBAR, a))

def s_criterio(im, d, t, p):
    centro(d, 390, "El criterio sigue siendo tuyo.", serif(80), mix(TINTA, PAPEL, aparece(t, 0.2, 0.8)))
    centro(d, 510, "Ahora lo respaldas con datos.", serif(80, b=True), mix(TINTA, AMBAR, aparece(t, 1.8, 0.8)))

AVISO = ("Análisis estimado con base en datos públicos de juicios ordinarios laborales de los tribunales locales de la ciudad de Aguascalientes, México. No constituye un resultado real ni garantiza el sentido de una resolución. "
         "La estimación puede modificarse en cualquier momento según las circunstancias de cada juicio y su desarrollo probatorio. No sustituye el criterio del abogado responsable.")
def s_cierre(im, d, t, p):
    logo(d, 170, aparece(t, 0.2, 0.8), 150)
    centro(d, 385, "La razón detrás de cada sentencia.", serif(52, i=True), mix(TINTA, PAPEL, aparece(t, 0.7, 0.8)))
    a = aparece(t, 2.6, 0.7)
    w = d.textlength("Solicita una demostración", font=sans(36, True))
    d.rounded_rectangle((W / 2 - w / 2 - 34, 495, W / 2 + w / 2 + 34, 570), 12, outline=mix(TINTA, AMBAR, a), width=3)
    centro(d, 509, "Solicita una demostración", sans(36, True), mix(TINTA, AMBAR, a))
    a2 = aparece(t, 3.2, 0.8)
    y = 660
    for l in parrafo(AVISO, sans(30), 1400, d):
        centro(d, y, l, sans(30), mix(TINTA, PAPEL, a2)); y += 44

def cuadro(t, pistas, subs, th):
    im = Image.new("RGB", (W, H), TINTA)
    p = next((x for x in pistas if x["ini"] <= t < x["fin"]), pistas[-1])
    tl = t - p["ini"]
    if p["nom"] == "solucion":
        pass
    d = ImageDraw.Draw(im)
    f = {"gancho": s_gancho, "conflicto": s_conflicto, "marca": s_marca, "solucion": s_solucion,
         "honesto": s_honesto, "criterio": s_criterio, "cierre": s_cierre}
    if p["nom"] == "giro":
        s_giro(im, d, tl, p, th)
    else:
        f[p["nom"]](im, d, tl, p)
    d = ImageDraw.Draw(im)
    if p["nom"] != "cierre":
        subt(d, t, subs)
    # Fundido en cortes de escena
    fade = min(clamp(tl / 0.25), clamp((p["fin"] - t) / 0.25))
    if p is pistas[-1]:
        fade = clamp(tl / 0.25) * clamp((p["fin"] - t) / 0.6)
    if fade < 1:
        im = Image.blend(Image.new("RGB", (W, H), TINTA), im, fade)
    return im

def main():
    modo = sys.argv[1]
    pistas, total = voces()
    subs = rotulos(pistas)
    th = miniaturas()
    print("duracion", round(total, 1), [(p["nom"], round(p["fin"] - p["ini"], 1)) for p in pistas], flush=True)
    if modo == "preview":
        ts = []
        for p in pistas:
            D = p["fin"] - p["ini"]
            ts += [p["ini"] + D * q for q in (0.3, 0.6, 0.9)]
        ims = [cuadro(t, pistas, subs, th).resize((640, 360)) for t in ts]
        col = 4
        fil = math.ceil(len(ims) / col)
        hoja = Image.new("RGB", (col * 640, fil * 360), (60, 60, 60))
        for i, m in enumerate(ims):
            hoja.paste(m, ((i % col) * 640, (i // col) * 360))
        hoja.save(TMP / "hoja.jpg", quality=80)
        return
    audio = np.zeros(int((total + 0.5) * SR), dtype=np.int16)
    for p in pistas:
        i = int(p["voz_ini"] * SR)
        audio[i:i + len(p["x"])] = p["x"]
    aw = TMP / "audio.wav"
    with wave.open(str(aw), "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes(audio.tobytes())
    sal = RAIZ / "Ratio_video_v4.mp4"
    ff = subprocess.Popen([FF, "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                           "-i", str(aw), "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p",
                           "-c:a", "aac", "-b:a", "160k", "-shortest", "-movflags", "+faststart", str(sal)], stdin=subprocess.PIPE)
    n = int(total * FPS)
    for k in range(n):
        ff.stdin.write(cuadro(k / FPS, pistas, subs, th).tobytes())
        if k % 600 == 0:
            print(k, n, flush=True)
    ff.stdin.close(); ff.wait()
    print("LISTO", sal, ff.returncode)

main()
