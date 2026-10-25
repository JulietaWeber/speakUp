# Morfología del español con tablas y reglas (nada aprendido). La usan el
# corrector, para dar otra forma de la MISMA palabra, y los scripts que
# generan el corpus, así las dos etapas siguen las mismas reglas.
import unicodedata

PERSONAS = ("1s", "2s", "2v", "3s", "1p", "3p")   # 2v = voseo ("vos querés")
TIEMPOS = ("pres", "pret", "imp", "fut", "cond", "subj")

# ── Tildes ────────────────────────────────────────────────────────────────────

_SIN_TILDE = str.maketrans("áéíóúüÁÉÍÓÚÜ", "aeiouuAEIOUU")
_CON_TILDE = {"a": "á", "e": "é", "i": "í", "o": "ó", "u": "ú"}
VOCALES = set("aeiouáéíóúü")
_FUERTES = set("aeoáéó")


def quitar_tildes(texto):
    """'mamá' -> 'mama' (la ñ se conserva)."""
    return texto.translate(_SIN_TILDE)


def tiene_tilde(texto):
    return any(c in "áéíóú" for c in texto)


def _grupos_vocalicos(palabra):
    """Posiciones (inicio, fin) de cada grupo de vocales (núcleos silábicos
    aproximados: diptongos juntos, 'ue' de 'gue/que' incluido)."""
    grupos, i = [], 0
    while i < len(palabra):
        if palabra[i] in VOCALES:
            j = i
            while j + 1 < len(palabra) and palabra[j + 1] in VOCALES:
                j += 1
            grupos.append((i, j))
            i = j + 1
        else:
            i += 1
    return grupos


def _acentuar_grupo(palabra, grupo):
    """Pone tilde en la vocal fuerte del grupo (o en la última si son débiles)."""
    ini, fin = grupo
    pos = next((k for k in range(ini, fin + 1) if palabra[k] in _FUERTES), fin)
    return palabra[:pos] + _CON_TILDE.get(palabra[pos], palabra[pos]) + palabra[pos + 1:]


def pluralizar(palabra):
    """Plural de un sustantivo o adjetivo: 'perro' -> 'perros', 'lápiz' ->
    'lápices', 'camión' -> 'camiones', 'joven' -> 'jóvenes'."""
    p = palabra
    if not p:
        return p
    u = p[-1]
    if u in "aeiou":
        return p + "s"
    if u in "áéó":
        return p + "s"                       # mamá -> mamás, café -> cafés
    if u in "íú":
        return p + "s"                       # menú -> menús
    if u == "z":
        return p[:-1] + "ces"
    grupos = _grupos_vocalicos(p)
    if u in "sx":
        if len(grupos) <= 1:
            return p + "es"                  # mes -> meses, gas -> gases
        ini = grupos[-1][0]
        if tiene_tilde(p[ini:]):
            return p[:ini] + quitar_tildes(p[ini:]) + "es"   # inglés -> ingleses
        return p                             # lunes, crisis
    if u == "y":
        return p + "es"                      # rey -> reyes
    # consonante: +es con ajuste de tilde
    if grupos and tiene_tilde(p[grupos[-1][0]:]):
        ini = grupos[-1][0]
        return p[:ini] + quitar_tildes(p[ini:]) + "es"     # camión -> camiones
    if u == "n" and len(grupos) >= 2 and not tiene_tilde(p):
        return _acentuar_grupo(p, grupos[-2]) + "es"        # joven -> jóvenes
    return p + "es"


# ── Determinantes ─────────────────────────────────────────────────────────────
# Cada familia en orden (masc. sing., fem. sing., masc. pl., fem. pl.).

_FAMILIAS_DET = [
    ("el", "la", "los", "las"),
    ("un", "una", "unos", "unas"),
    ("este", "esta", "estos", "estas"),
    ("ese", "esa", "esos", "esas"),
    ("aquel", "aquella", "aquellos", "aquellas"),
    ("mucho", "mucha", "muchos", "muchas"),
    ("poco", "poca", "pocos", "pocas"),
    ("otro", "otra", "otros", "otras"),
    ("todo", "toda", "todos", "todas"),
    ("tanto", "tanta", "tantos", "tantas"),
    ("algún", "alguna", "algunos", "algunas"),
    ("ningún", "ninguna", "ningunos", "ningunas"),
    ("nuestro", "nuestra", "nuestros", "nuestras"),
    ("mi", "mi", "mis", "mis"),
    ("tu", "tu", "tus", "tus"),
    ("su", "su", "sus", "sus"),
]
_IDX = {("m", "s"): 0, ("f", "s"): 1, ("m", "p"): 2, ("f", "p"): 3}
_RASGOS = {v: k for k, v in _IDX.items()}

DETERMINANTES = {}
for _fam in _FAMILIAS_DET:
    for _i, _forma in enumerate(_fam):
        DETERMINANTES.setdefault(_forma, (_fam, _i))
DETERMINANTES["al"] = (("al", "a la", "a los", "a las"), 0)
DETERMINANTES["del"] = (("del", "de la", "de los", "de las"), 0)

# Femeninos que llevan "el"/"un" en singular por empezar con a tónica.
FEMENINAS_A_TONICA = {
    "agua", "águila", "alma", "área", "hacha", "arma", "ala", "hada", "hambre",
    "aula", "ave", "ancla", "arpa", "asma", "haba",
}


def rasgos_determinante(det):
    """(género, número) de un determinante, o None si no es uno flexionable.
    'mi'/'tu'/'su' no tienen género propio: se devuelve (None, número)."""
    if det not in DETERMINANTES:
        return None
    fam, i = DETERMINANTES[det]
    g, n = _RASGOS[i]
    if fam[0] == fam[1]:
        g = None
    return g, n


def flexionar_determinante(det, genero, numero, siguiente=None):
    """'el' -> 'la', 'un' -> 'unas', 'al' -> 'a la'. Respeta 'el agua',
    'un águila'. Devuelve None si `det` no es un determinante flexionable."""
    if det not in DETERMINANTES:
        return None
    fam, _ = DETERMINANTES[det]
    forma = fam[_IDX[(genero, numero)]]
    if genero == "f" and numero == "s" and siguiente in FEMENINAS_A_TONICA:
        forma = {"la": "el", "una": "un", "a la": "al", "de la": "del"}.get(forma, forma)
    return forma


# ── Adjetivos ─────────────────────────────────────────────────────────────────
# Género y número: "cansado" -> "cansada", "feliz" -> "felices".

ADJ_INVARIABLES_GENERO = {
    "rosa", "lila", "naranja", "violeta", "fucsia", "turquesa", "marrón",
    "mejor", "peor", "mayor", "menor", "superior", "inferior", "exterior",
    "interior", "anterior", "posterior", "cortés", "idiota", "hipócrita",
    "agrícola", "maya", "persa", "belga",
}


def _es_vocal_final(p):
    return p[-1:] in VOCALES


def base_adjetivo(forma, es_palabra=None):
    """Forma base (masc. sing.) de un adjetivo flexionado: 'rojas' -> 'rojo',
    'felices' -> 'feliz', 'grandes' -> 'grande'. `es_palabra` (opcional) se
    usa para elegir entre candidatos ambiguos ('verdes' -> 'verde' vs
    'azules' -> 'azul')."""
    f = forma
    if f in ADJ_INVARIABLES_GENERO:
        return f
    if f[:-1] in ADJ_INVARIABLES_GENERO or f[:-2] in ADJ_INVARIABLES_GENERO:
        return f[:-1] if f[:-1] in ADJ_INVARIABLES_GENERO else f[:-2]
    cands = []
    if f.endswith("os"):
        cands = [f[:-1]]
    elif f.endswith("as"):
        cands = [f[:-2] + "o", f[:-1]]
    elif f.endswith("a"):
        cands = [f[:-1] + "o", f]
    elif f.endswith("es") and len(f) > 3:
        raiz = f[:-2]
        cands = [f[:-1]]                                    # grandes -> grande
        if raiz.endswith("c"):
            cands.insert(0, raiz[:-1] + "z")                # felices -> feliz
        grupos = _grupos_vocalicos(raiz)
        if tiene_tilde(raiz) and len(grupos) >= 2:
            cands.append(quitar_tildes(raiz))               # jóvenes -> joven
        if raiz[-1:] in "ns" and len(grupos) >= 2 and not tiene_tilde(raiz):
            cands.append(_acentuar_grupo(raiz, grupos[-1]))  # comunes -> común
        cands.append(raiz)                                  # azules -> azul
    else:
        cands = [f]
    if es_palabra:
        for c in cands:
            if c != f and es_palabra(c):
                return c
        if f.endswith("es") and es_palabra(f[:-1]):
            return f[:-1]
    if f.endswith("es") and len(f) > 3:
        raiz = f[:-2]
        if raiz.endswith("c"):
            return raiz[:-1] + "z"
        if raiz[-1:] in "lrnsdjy" and not raiz.endswith(("nt", "rd", "rt", "st")):
            return cands[-1]
        return f[:-1]
    return cands[0]


def formas_adjetivo(base):
    """{(g, n): forma} para un adjetivo en forma base."""
    b = base
    if b in ADJ_INVARIABLES_GENERO or b.endswith("ista"):
        pl = pluralizar(b)
        return {("m", "s"): b, ("f", "s"): b, ("m", "p"): pl, ("f", "p"): pl}
    if b.endswith("o"):
        r = b[:-1]
        return {("m", "s"): b, ("f", "s"): r + "a", ("m", "p"): r + "os", ("f", "p"): r + "as"}
    if b.endswith("or") or b.endswith("ón") or b.endswith("án") or b.endswith("és"):
        fem = quitar_tildes(b[:-2]) + quitar_tildes(b[-2]) + b[-1] + "a" if tiene_tilde(b[-2:]) else b + "a"
        return {("m", "s"): b, ("f", "s"): fem, ("m", "p"): pluralizar(b), ("f", "p"): fem + "s"}
    pl = pluralizar(b)
    return {("m", "s"): b, ("f", "s"): b, ("m", "p"): pl, ("f", "p"): pl}


def rasgos_adjetivo(forma):
    """(género o None, número) aproximado de un adjetivo por su terminación."""
    if forma.endswith("os"):
        return "m", "p"
    if forma.endswith("as"):
        return "f", "p"
    if forma.endswith("o"):
        return "m", "s"
    if forma.endswith("a"):
        return "f", "s"
    if forma.endswith("es") and len(forma) > 3:
        return None, "p"
    return None, "s"


def flexionar_adjetivo(forma, genero, numero, es_palabra=None):
    return formas_adjetivo(base_adjetivo(forma, es_palabra))[(genero, numero)]


# ── Verbos ────────────────────────────────────────────────────────────────────
# 6 tiempos (presente, pretérito, imperfecto, futuro, condicional, subjuntivo)
# y 6 personas, con voseo rioplatense ("vos querés", "vos sos").

_TERM_PRES = {
    "ar": ("o", "as", "ás", "a", "amos", "an"),
    "er": ("o", "es", "és", "e", "emos", "en"),
    "ir": ("o", "es", "ís", "e", "imos", "en"),
}
_TERM_PRET = {
    "ar": ("é", "aste", "aste", "ó", "amos", "aron"),
    "er": ("í", "iste", "iste", "ió", "imos", "ieron"),
    "ir": ("í", "iste", "iste", "ió", "imos", "ieron"),
}
_TERM_IMP = {
    "ar": ("aba", "abas", "abas", "aba", "ábamos", "aban"),
    "er": ("ía", "ías", "ías", "ía", "íamos", "ían"),
    "ir": ("ía", "ías", "ías", "ía", "íamos", "ían"),
}
_TERM_FUT = ("é", "ás", "ás", "á", "emos", "án")
_TERM_COND = ("ía", "ías", "ías", "ía", "íamos", "ían")
_TERM_PRET_FUERTE = ("e", "iste", "iste", "o", "imos", "ieron")

# Tablas completas para los verbos más irregulares.
_IRREGULARES = {
    "ser": {
        "pres": ("soy", "eres", "sos", "es", "somos", "son"),
        "pret": ("fui", "fuiste", "fuiste", "fue", "fuimos", "fueron"),
        "imp": ("era", "eras", "eras", "era", "éramos", "eran"),
        "subj": ("sea", "seas", "seas", "sea", "seamos", "sean"),
    },
    "ir": {
        "pres": ("voy", "vas", "vas", "va", "vamos", "van"),
        "pret": ("fui", "fuiste", "fuiste", "fue", "fuimos", "fueron"),
        "imp": ("iba", "ibas", "ibas", "iba", "íbamos", "iban"),
        "subj": ("vaya", "vayas", "vayas", "vaya", "vayamos", "vayan"),
    },
    "estar": {
        "pres": ("estoy", "estás", "estás", "está", "estamos", "están"),
        "subj": ("esté", "estés", "estés", "esté", "estemos", "estén"),
    },
    "haber": {
        "pres": ("he", "has", "has", "ha", "hemos", "han"),
        "subj": ("haya", "hayas", "hayas", "haya", "hayamos", "hayan"),
    },
    "dar": {
        "pres": ("doy", "das", "das", "da", "damos", "dan"),
        "pret": ("di", "diste", "diste", "dio", "dimos", "dieron"),
        "subj": ("dé", "des", "des", "dé", "demos", "den"),
    },
    "ver": {
        "pres": ("veo", "ves", "ves", "ve", "vemos", "ven"),
        "pret": ("vi", "viste", "viste", "vio", "vimos", "vieron"),
        "imp": ("veía", "veías", "veías", "veía", "veíamos", "veían"),
        "subj": ("vea", "veas", "veas", "vea", "veamos", "vean"),
    },
    "saber": {
        "pres": ("sé", "sabes", "sabés", "sabe", "sabemos", "saben"),
        "subj": ("sepa", "sepas", "sepas", "sepa", "sepamos", "sepan"),
    },
    "caber": {
        "pres": ("quepo", "cabes", "cabés", "cabe", "cabemos", "caben"),
        "subj": ("quepa", "quepas", "quepas", "quepa", "quepamos", "quepan"),
    },
    "oír": {
        "pres": ("oigo", "oyes", "oís", "oye", "oímos", "oyen"),
        "pret": ("oí", "oíste", "oíste", "oyó", "oímos", "oyeron"),
        "imp": ("oía", "oías", "oías", "oía", "oíamos", "oían"),
        "subj": ("oiga", "oigas", "oigas", "oiga", "oigamos", "oigan"),
    },
    "reír": {
        "pres": ("río", "ríes", "reís", "ríe", "reímos", "ríen"),
        "pret": ("reí", "reíste", "reíste", "rio", "reímos", "rieron"),
        "imp": ("reía", "reías", "reías", "reía", "reíamos", "reían"),
        "subj": ("ría", "rías", "rías", "ría", "riamos", "rían"),
    },
    "sonreír": {
        "pres": ("sonrío", "sonríes", "sonreís", "sonríe", "sonreímos", "sonríen"),
        "pret": ("sonreí", "sonreíste", "sonreíste", "sonrió", "sonreímos", "sonrieron"),
        "imp": ("sonreía", "sonreías", "sonreías", "sonreía", "sonreíamos", "sonreían"),
        "subj": ("sonría", "sonrías", "sonrías", "sonría", "sonriamos", "sonrían"),
    },
    "oler": {
        "pres": ("huelo", "hueles", "olés", "huele", "olemos", "huelen"),
        "subj": ("huela", "huelas", "huelas", "huela", "olamos", "huelan"),
    },
}

# Presente con 1ª persona irregular (el resto se arma con la regla general).
_YO_IRREGULAR = {
    "tener": "tengo", "venir": "vengo", "decir": "digo", "hacer": "hago",
    "poner": "pongo", "salir": "salgo", "traer": "traigo", "caer": "caigo",
    "valer": "valgo",
}
# Verbos base con irregularidades que heredan los derivados (mantener,
# componer, deshacer, prevenir, atraer...).
_BASES_DERIVABLES = ("tener", "poner", "venir", "hacer", "decir", "traer", "salir", "caer")

_E_IE = {
    "querer", "pensar", "empezar", "comenzar", "cerrar", "despertar", "entender",
    "perder", "sentir", "preferir", "merendar", "sentar", "mentir", "encender",
    "defender", "divertir", "convertir", "nevar", "calentar", "recomendar",
    "tener", "venir", "atender", "extender", "advertir", "herir", "sugerir",
    "negar", "regar", "fregar", "temblar", "gobernar", "confesar", "apretar",
    "tropezar", "atravesar", "invertir", "hervir", "consentir",
}
_O_UE = {
    "poder", "dormir", "volver", "encontrar", "recordar", "contar", "morir",
    "mostrar", "almorzar", "mover", "soñar", "probar", "acostar", "devolver",
    "doler", "costar", "acordar", "colgar", "llover", "resolver", "volar",
    "rogar", "sonar", "torcer", "morder", "soltar", "aprobar", "comprobar",
    "demostrar", "envolver", "promover", "renovar", "tostar", "forzar",
}
_U_UE = {"jugar"}
_E_I = {
    "pedir", "seguir", "repetir", "servir", "vestir", "elegir", "corregir",
    "medir", "despedir", "conseguir", "competir", "impedir", "decir",
    "perseguir", "freír", "gemir", "rendir", "teñir", "reñir",
}
# Pretérito fuerte (raíz + e/iste/o/imos/ieron).
_PRET_FUERTE = {
    "tener": "tuv", "estar": "estuv", "andar": "anduv", "poder": "pud",
    "poner": "pus", "saber": "sup", "querer": "quis", "venir": "vin",
    "hacer": "hic", "decir": "dij", "traer": "traj", "haber": "hub",
    "caber": "cup", "conducir": "conduj", "producir": "produj",
    "traducir": "traduj", "reducir": "reduj", "introducir": "introduj",
}
_FUT_IRREG = {
    "tener": "tendr", "venir": "vendr", "poner": "pondr", "salir": "saldr",
    "valer": "valdr", "poder": "podr", "saber": "sabr", "haber": "habr",
    "querer": "querr", "caber": "cabr", "decir": "dir", "hacer": "har",
}
_ZCO_EXCEPCIONES = {"hacer", "cocer", "mecer", "decir"}
# Verbos que acentúan la i / u de la raíz en las formas fuertes: envío, actúo.
_ACENTUA_I = {"enviar", "confiar", "enfriar", "guiar", "criar", "vaciar", "esquiar",
              "desafiar", "ampliar", "resfriar", "variar", "espiar", "fotografiar"}
_ACENTUA_U = {"actuar", "continuar", "graduar", "evaluar", "situar", "reunir", "acentuar"}


def es_infinitivo(palabra):
    p = palabra.lower()
    return len(p) >= 2 and (p.endswith(("ar", "er", "ir", "ír")))


def _terminacion(v):
    fin = v[-2:]
    return "ir" if fin == "ír" else fin


def _base_derivada(v):
    """'mantener' -> ('man', 'tener'); None si no deriva de un irregular."""
    for base in _BASES_DERIVABLES:
        if v.endswith(base) and v != base and len(v) - len(base) <= 5:
            return v[: -len(base)], base
    return None


def _cambiar_ultima_vocal(raiz, de, a):
    pos = raiz.rfind(de)
    if pos < 0:
        return raiz
    return raiz[:pos] + a + raiz[pos + 1:]


def _raiz_diptongada(v):
    """Raíz con cambio vocálico de presente (quier-, pued-, jueg-, pid-)."""
    raiz = v[:-2]
    if v in _E_IE:
        return _cambiar_ultima_vocal(raiz, "e", "ie")
    if v in _O_UE:
        r = _cambiar_ultima_vocal(raiz, "o", "ue")
        return "h" + r if r.startswith("ue") else r
    if v in _U_UE:
        return _cambiar_ultima_vocal(raiz, "u", "ue")
    if v in _E_I:
        return _cambiar_ultima_vocal(raiz, "e", "i")
    if v in _ACENTUA_I:
        return _cambiar_ultima_vocal(raiz, "i", "í")
    if v in _ACENTUA_U:
        return _cambiar_ultima_vocal(raiz, "u", "ú")
    return raiz


def _ajuste_ortografico(raiz, vocal):
    """Ajusta la consonante final de la raíz para conservar el sonido ante
    `vocal`: busc+e -> busqu+e, jug+e -> jugu+e, empez+e -> empec+e,
    escog+o -> escoj+o, segu+o -> sig+o, conoc+o -> conozc+o."""
    if vocal in "eé":
        if raiz.endswith("c"):
            return raiz[:-1] + "qu"
        if raiz.endswith("gu") and not raiz.endswith("güe"):
            return raiz[:-1] + "ü"
        if raiz.endswith("g"):
            return raiz + "u"
        if raiz.endswith("z"):
            return raiz[:-1] + "c"
    return raiz


def _ajuste_ao(v, raiz):
    """Cambios de la raíz ante a/o en verbos -er/-ir (escojo, sigo, conozco,
    venzo, construyo)."""
    fin = _terminacion(v)
    if fin == "ar":
        return raiz
    if raiz.endswith("gu") and v.endswith("guir"):
        return raiz[:-1]
    if raiz.endswith("g"):
        return raiz[:-1] + "j"
    if raiz.endswith("c"):
        if v in _ZCO_EXCEPCIONES:
            return raiz
        if len(raiz) > 1 and raiz[-2] in VOCALES:
            return raiz[:-1] + "zc"
        return raiz[:-1] + "z"
    if v.endswith("uir") and not v.endswith("guir"):
        return raiz + "y"
    return raiz


def _presente(v):
    fin = _terminacion(v)
    t = _TERM_PRES[fin]
    raiz = v[:-2]
    dipt = _raiz_diptongada(v)
    formas = []
    for i, term in enumerate(t):
        persona = PERSONAS[i]
        r = raiz if persona in ("2v", "1p") else dipt
        if persona == "1s":
            r = _ajuste_ao(v, r)
        elif v.endswith("uir") and not v.endswith("guir") and persona in ("2s", "3s", "3p"):
            r = r + "y"
        formas.append(r + term)
    if v in _YO_IRREGULAR:
        formas[0] = _YO_IRREGULAR[v]
    if v == "decir":
        formas[2] = "decís"
    return tuple(formas)


def _preterito(v):
    fin = _terminacion(v)
    raiz = v[:-2]
    if v in _PRET_FUERTE:
        r = _PRET_FUERTE[v]
        t = list(_TERM_PRET_FUERTE)
        if r.endswith("j"):
            t[5] = "eron"
        formas = [r + x for x in t]
        if v == "hacer":
            formas[3] = "hizo"
        return tuple(formas)
    t = _TERM_PRET[fin]
    formas = []
    for i, term in enumerate(t):
        r = raiz
        if i == 0 and fin == "ar":
            r = _ajuste_ortografico(raiz, "é")
        if fin == "ir" and i in (3, 5):
            if v in _E_IE or v in _E_I:
                r = _cambiar_ultima_vocal(raiz, "e", "i")
            elif v in ("dormir", "morir"):
                r = _cambiar_ultima_vocal(raiz, "o", "u")
        formas.append(r + term)
    # leer, creer, caer, construir: -yó/-yeron y tildes en leíste, leímos
    if fin in ("er", "ir") and raiz[-1:] in VOCALES and not v.endswith("guir"):
        formas[3] = raiz + "yó"
        formas[5] = raiz + "yeron"
        if not v.endswith("uir"):
            formas[0] = raiz + "í"
            formas[1] = formas[2] = raiz + "íste"
            formas[4] = raiz + "ímos"
    return tuple(formas)


def _imperfecto(v):
    fin = _terminacion(v)
    return tuple(v[:-2] + t for t in _TERM_IMP[fin])


def _futuro(v, condicional=False):
    raiz = _FUT_IRREG.get(v, v.replace("ír", "ir") if v.endswith("ír") else v)
    t = _TERM_COND if condicional else _TERM_FUT
    return tuple(raiz + x for x in t)


def _subjuntivo(v):
    fin = _terminacion(v)
    vocal = "e" if fin == "ar" else "a"
    yo = _presente(v)[0]
    raiz_yo = yo[:-1] if yo.endswith("o") else v[:-2]
    raiz_1p = raiz_yo
    if v in _ACENTUA_I or v in _ACENTUA_U:
        raiz_1p = v[:-2]
    if v in _E_IE or v in _O_UE or v in _U_UE or v in _E_I:
        raiz_1p = v[:-2]
        if fin == "ir":
            if v in _E_IE or v in _E_I:
                raiz_1p = _cambiar_ultima_vocal(raiz_1p, "e", "i")
            elif v in _O_UE:
                raiz_1p = _cambiar_ultima_vocal(raiz_1p, "o", "u")
        raiz_1p = _ajuste_ao(v, raiz_1p) if fin != "ar" else raiz_1p
    if v in _YO_IRREGULAR:
        raiz_1p = raiz_yo
    formas = []
    for i, term in enumerate(("", "s", "s", "", "mos", "n")):
        r = raiz_1p if PERSONAS[i] == "1p" else raiz_yo
        if fin == "ar":
            r = _ajuste_ortografico(r, "e")
        formas.append(r + vocal + term)
    return tuple(formas)


_cache_paradigmas = {}


def paradigma(infinitivo):
    """{tiempo: (formas en el orden de PERSONAS)} de un infinitivo."""
    v = infinitivo.lower()
    if v in _cache_paradigmas:
        return _cache_paradigmas[v]
    if not es_infinitivo(v):
        return {}
    derivado = _base_derivada(v) if v not in _IRREGULARES else None
    if derivado:
        prefijo, base = derivado
        res = {t: tuple(prefijo + f for f in fs) for t, fs in paradigma(base).items()}
        _cache_paradigmas[v] = res
        return res
    res = {
        "pres": _presente(v),
        "pret": _preterito(v),
        "imp": _imperfecto(v),
        "fut": _futuro(v),
        "cond": _futuro(v, condicional=True),
        "subj": _subjuntivo(v),
    }
    if v in _IRREGULARES:
        res.update(_IRREGULARES[v])
    _cache_paradigmas[v] = res
    return res


def conjugar(infinitivo, tiempo, persona):
    """'querer', 'pres', '1s' -> 'quiero'. None si no es un infinitivo."""
    par = paradigma(infinitivo)
    if tiempo not in par:
        return None
    return par[tiempo][PERSONAS.index(persona)]


def gerundio(infinitivo):
    v = infinitivo.lower()
    fin = _terminacion(v)
    raiz = v[:-2]
    especiales = {"ir": "yendo", "poder": "pudiendo", "decir": "diciendo", "venir": "viniendo",
                  "dormir": "durmiendo", "morir": "muriendo", "reír": "riendo", "oír": "oyendo",
                  "leer": "leyendo", "creer": "creyendo", "caer": "cayendo", "traer": "trayendo"}
    if v in especiales:
        return especiales[v]
    if fin == "ar":
        return raiz + "ando"
    if fin == "ir" and (v in _E_IE or v in _E_I):
        raiz = _cambiar_ultima_vocal(raiz, "e", "i")
    if v.endswith("uir") and not v.endswith("guir"):
        return raiz + "yendo"
    return raiz + "iendo"


def participio(infinitivo):
    v = infinitivo.lower()
    especiales = {"hacer": "hecho", "decir": "dicho", "ver": "visto", "poner": "puesto",
                  "escribir": "escrito", "romper": "roto", "volver": "vuelto", "abrir": "abierto",
                  "morir": "muerto", "devolver": "devuelto", "resolver": "resuelto",
                  "cubrir": "cubierto", "freír": "frito", "leer": "leído", "traer": "traído",
                  "caer": "caído", "oír": "oído", "reír": "reído", "creer": "creído"}
    if v in especiales:
        return especiales[v]
    fin = _terminacion(v)
    return v[:-2] + ("ado" if fin == "ar" else "ido")


# Análisis inverso: permite cambiar la persona sin cambiar el verbo ni el
# tiempo ("yo quiere" -> "yo quiero").
class IndiceVerbal:
    """Índice inverso forma conjugada -> [(infinitivo, tiempo, persona)] para
    un conjunto de infinitivos conocidos."""

    # Formas que no se tocan nunca aunque coincidan con una conjugación: "hay"
    # (impersonal) y monosílabos ambiguos con otras palabras o imperativos.
    NO_ANALIZAR = {"hay", "ve", "sé", "di", "vi", "da", "dé", "ha", "he"}

    def __init__(self, infinitivos):
        self.infinitivos = sorted(set(i.lower() for i in infinitivos if es_infinitivo(i)))
        self.indice = {}
        for v in self.infinitivos:
            for tiempo, formas in paradigma(v).items():
                for persona, forma in zip(PERSONAS, formas):
                    self.indice.setdefault(forma, []).append((v, tiempo, persona))

    def analizar(self, forma):
        f = forma.lower()
        if f in self.NO_ANALIZAR:
            return []
        return self.indice.get(f, [])

    def cambiar_persona(self, forma, persona, tiempo_preferido=None):
        """'quiere' + '1s' -> 'quiero' (mismo verbo y tiempo). None si la
        forma no es una conjugación conocida."""
        analisis = self.analizar(forma)
        if not analisis:
            return None
        orden = list(TIEMPOS)
        if tiempo_preferido in orden:
            orden.remove(tiempo_preferido)
            orden.insert(0, tiempo_preferido)
        analisis = sorted(analisis, key=lambda a: orden.index(a[1]))
        v, tiempo, _ = analisis[0]
        return conjugar(v, tiempo, persona)

    def formas(self):
        return self.indice.keys()
