import re
import unicodedata
from typing import Dict, List, Tuple, Optional
from collections import Counter


# ============================================================
# NORMALIZATION
# Uzbek Latin uses oʻ (U+02BB), gʻ, but users often type o', o`, o', g`.
# All variants are unified to the canonical oʻ/gʻ form before lookup.
# ============================================================
_APOS = "['`‘’ʼʹʻʺ]"
_APOS_RE = re.compile(f"([oOgG]){_APOS}")


def normalize(text: str) -> str:
    text = unicodedata.normalize("NFC", text)
    text = _APOS_RE.sub(lambda m: m.group(1) + "ʻ", text)
    return text


def norm_word(word: str) -> str:
    return normalize(word).lower()


# ============================================================
# POS DICTIONARY
# ============================================================
_RAW_POS = {
    "Ot": [
        "odam", "inson", "bola", "qiz", "oʻgʻil", "ota", "ona", "aka", "uka",
        "opa", "singil", "bobo", "buvi", "amaki", "xola", "amma", "togʻa",
        "oila", "doʻst", "dushman", "oʻrtoq", "qoʻshni", "qarindosh",
        "sinf", "maktab", "dars", "oʻqituvchi", "muallim", "talaba",
        "oʻquvchi", "universitet", "institut", "fakultet", "kafedra", "kurs",
        "imtihon", "baho", "darslik", "kitob", "daftar", "qalam", "ruchka",
        "doska", "stol", "stul", "xona", "uy", "hovli", "bogʻ", "dala",
        "togʻ", "daryo", "koʻl", "dengiz", "koʻprik", "koʻcha", "mahalla",
        "shahar", "qishloq", "tuman", "viloyat", "davlat", "mamlakat",
        "vatan", "xalq", "millat", "poytaxt",
        "til", "nutq", "soʻz", "jumla", "matn", "gap", "bob", "bet", "satr",
        "grammatika", "morfologiya", "sintaksis", "semantika", "leksika",
        "fonetika", "imlo", "tuzilish", "tuzilishi",
        "fan", "ilm", "bilim", "tadqiqot", "tajriba", "kashfiyot",
        "adabiyot", "sheʼr", "doston", "hikoya", "roman", "asar", "muallif",
        "yozuvchi", "shoir", "sanʼat", "musiqa", "qoʻshiq", "raqs", "rasm",
        "teatr", "kino", "film", "madaniyat", "urf", "odat", "anʼana",
        "ish", "mehnat", "kasb", "hunar", "lavozim", "vazifa", "muhandis",
        "shifokor", "vrach", "bemor", "dori", "kasalxona", "shifoxona",
        "dorixona", "bozor", "doʻkon", "oshxona", "restoran", "mehmonxona",
        "transport", "avtobus", "mashina", "poyezd", "samolyot", "velosiped",
        "yoʻl", "xiyobon",
        "vaqt", "soat", "daqiqa", "soniya", "kun", "hafta", "oy", "yil",
        "asr", "davr", "zamon", "oʻtmish", "kelajak",
        "bahor", "yoz", "kuz", "qish", "fasl", "iqlim", "havo", "ob-havo",
        "quyosh", "yulduz", "osmon", "bulut", "yomgʻir", "qor", "muz",
        "shamol", "suv", "olov", "oʻt", "yer", "zamin", "tabiat", "oʻrmon",
        "oʻsimlik", "daraxt", "gul", "meva", "sabzavot", "olma", "nok",
        "uzum", "tarvuz", "qovun",
        "hayvon", "mushuk", "it", "sigir", "qoʻy", "echki", "tovuq", "qush",
        "baliq",
        "bosh", "yuz", "koʻz", "burun", "ogʻiz", "tish", "quloq", "qoʻl",
        "oyoq", "yurak", "qon", "ovoz", "kuch",
        "imkoniyat", "sabab", "natija", "foyda", "zarar", "haqiqat",
        "yolgʻon", "adolat", "dunyo", "hayot", "baxt", "sevgi", "muhabbat",
        "doʻstlik", "tinchlik", "urush", "erkinlik", "mustaqillik",
        "oʻzbekiston", "toshkent", "samarqand", "buxoro", "xiva", "fargʻona",
        "andijon", "namangan", "navoiy", "qashqadaryo", "surxondaryo",
        "xorazm", "jizzax", "sirdaryo",
        "kompyuter", "dastur", "internet", "texnologiya", "telefon",
        "tarmoq", "sayt", "ilova", "maʼlumot", "xabar", "yangilik",
        "tarix", "geografiya", "matematika", "fizika", "kimyo", "biologiya",
        "astronomiya", "psixologiya", "falsafa", "iqtisodiyot", "siyosat",
        "sport", "futbol", "basketbol", "voleybol", "boks", "kurash",
        "olimpiada", "musobaqa", "gʻolib", "jamoa",
        "pul", "soʻm", "dollar", "bank", "kredit", "sarmoya", "biznes",
        "tadbirkor", "korxona", "savdo", "narx",
        "prezident", "hukumat", "parlament", "vazir", "vazirlik", "saylov",
        "qonun", "konstitutsiya", "elchi",
        "biri", "nomi", "soʻnggi",
    ],
    "Sifat": [
        "katta", "kichik", "baland", "past", "uzun", "qisqa", "keng", "tor",
        "yaxshi", "yomon", "chiroyli", "xunuk", "goʻzal", "boy", "kambagʻal",
        "yosh", "qari", "keksa", "yangi", "eski", "oson", "qiyin",
        "murakkab", "sodda", "issiq", "sovuq", "iliq", "salqin", "shirin",
        "achchiq", "nordon", "shoʻr", "tez", "sekin", "ogʻir", "yengil",
        "qimmat", "arzon", "toza", "iflos", "qora", "oq", "qizil", "koʻk",
        "yashil", "sariq", "jigarrang", "kulrang", "quvnoq", "xafa",
        "baxtli", "baxtsiz", "aqlli", "ahmoq", "dono", "jasur", "qoʻrqoq",
        "kuchli", "zaif", "sogʻlom", "muhim", "zarur", "kerakli", "foydali",
        "zararli", "ajoyib", "gʻaroyib", "odatiy", "oddiy", "maxsus",
        "haqiqiy", "toʻgʻri", "notoʻgʻri", "xos", "milliy", "xalqaro",
        "zamonaviy", "grammatik", "lugʻaviy", "adabiy", "ilmiy", "badiiy",
        "rasmiy", "norasmiy", "erkin", "mustaqil", "barqaror", "ishonchli",
        "qiziqarli", "zerikarli",
    ],
    "Fel": [
        # infinitives
        "bormoq", "kelmoq", "qilmoq", "boʻlmoq", "koʻrmoq", "eshitmoq",
        "gapirmoq", "yozmoq", "oʻqimoq", "ishlamoq", "olmoq", "bermoq",
        "yemoq", "ichmoq", "uxlamoq", "turmoq", "oʻtirmoq", "yurmoq",
        "yugurmoq", "sakramoq", "oʻylamoq", "bilmoq", "tushunmoq", "sevmoq",
        "istamoq", "xohlamoq", "boshlamoq", "tugatmoq", "topmoq",
        "yoʻqotmoq", "sotmoq", "ochmoq", "yopmoq", "yasamoq", "yaratmoq",
        "oʻrganmoq", "oʻrgatmoq", "tekshirmoq", "tahlil qilmoq",
        # past tense (3rd person)
        "bordi", "keldi", "qildi", "boʻldi", "koʻrdi", "eshitdi", "gapirdi",
        "yozdi", "oʻqidi", "ishladi", "oldi", "berdi", "yedi", "ichdi",
        "uxladi", "turdi", "oʻtirdi", "yurdi", "yugurdi", "oʻyladi",
        "bildi", "tushundi", "sevdi", "boshladi", "tugatdi", "topdi",
        "sotdi", "ochdi", "yopdi", "yaratdi", "oʻrgandi", "tekshirdi",
        # present tense (3rd person)
        "boradi", "keladi", "qiladi", "boʻladi", "koʻradi", "eshitadi",
        "gapiradi", "yozadi", "oʻqiydi", "ishlaydi", "oladi", "beradi",
        "yeydi", "ichadi", "uxlaydi", "turadi", "oʻtiradi",
        # copular / auxiliary
        "hisoblanadi", "sanaladi", "xosdir", "ekan", "edi",
    ],
    "Ravish": [
        "eng", "juda", "ham", "yana", "tez", "sekin", "asta", "darhol",
        "birdan", "hozir", "hamisha", "doim", "goho", "baʼzan", "bugun",
        "kecha", "ertaga", "indinga", "yaxshilab", "ancha", "sal",
        "toʻliq", "qisman", "albatta", "ehtimol", "shubhasiz", "tabiiy",
        "aniq", "chindan", "rostdan", "aslida", "odatda", "koʻpincha",
    ],
    "Olmosh": [
        "men", "sen", "u", "biz", "siz", "ular", "bu", "shu", "oʻsha",
        "mening", "sening", "uning", "bizning", "sizning", "ularning",
        "nima", "kim", "qaysi", "qancha", "qayer", "qachon", "qanday",
        "nega", "nechta", "hech", "har", "allakim", "allanima", "oʻz",
        "oʻzim", "oʻzing", "oʻzi", "oʻzimiz", "oʻzingiz", "oʻzlari",
    ],
    "Bogʻlovchi": [
        "va", "yoki", "lekin", "ammo", "biroq", "chunki", "agar", "zero",
        "yaʼni", "shuningdek", "qachonki", "garchi", "holbuki", "hamda",
        "balki", "goh",
    ],
    "Koʻmakchi": [
        "bilan", "uchun", "haqida", "kabi", "singari", "orqali", "tomon",
        "tomonidan", "tarafidan", "sari", "tufayli", "osha", "qadar",
        "boshqa", "boshqacha",
    ],
    "Yuklama": [
        "faqat", "hatto", "axir", "naqd", "xuddi", "xolos", "goʻyo",
    ],
    "Undov": [
        "oh", "voy", "ey", "vo", "hay", "salom", "xayr", "ura", "barakalla",
    ],
    "Son": [
        "bir", "ikki", "uch", "toʻrt", "besh", "olti", "yetti", "sakkiz",
        "toʻqqiz", "oʻn", "yigirma", "oʻttiz", "qirq", "ellik", "oltmish",
        "yetmish", "sakson", "toʻqson", "yuz", "ming", "million", "milliard",
        "birinchi", "ikkinchi", "uchinchi", "toʻrtinchi", "beshinchi",
    ],
}

POS_DICT: Dict[str, str] = {}
for _pos, _words in _RAW_POS.items():
    for _w in _words:
        POS_DICT[norm_word(_w)] = _pos


# ============================================================
# SUFFIXES — ordered longest first for greedy match.
# (suffix_form, suffix_name, min_root_length)
# ============================================================
SUFFIXES: List[Tuple[str, str, int]] = [
    # plural + case (compound)
    ("lardan", "koʻplik+chiqish", 3),
    ("larda", "koʻplik+oʻrin", 3),
    ("larga", "koʻplik+joʻnalish", 3),
    ("larni", "koʻplik+tushum", 3),
    ("larning", "koʻplik+qaratqich", 3),
    ("lari", "koʻplik+egalik", 3),
    ("larim", "koʻplik+egalik(1)", 3),
    ("laring", "koʻplik+egalik(2)", 3),
    # plural
    ("lar", "koʻplik", 2),
    # cases
    ("ning", "qaratqich", 3),
    ("dan", "chiqish", 2),
    ("ga", "joʻnalish", 2),
    ("ka", "joʻnalish", 2),
    ("qa", "joʻnalish", 2),
    ("ni", "tushum", 2),
    ("dagi", "oʻrin-sifat", 3),
    ("da", "oʻrin-payt", 2),
    # possessive
    ("imiz", "egalik(1koʻp)", 3),
    ("ingiz", "egalik(2koʻp)", 3),
    ("im", "egalik(1)", 2),
    ("ing", "egalik(2)", 2),
    ("si", "egalik(3)", 3),
    # derivational (word-forming)
    ("chilik", "ot yasovchi", 4),
    ("iston", "joy nomi", 4),
    ("xona", "joy nomi", 3),
    ("dosh", "ot yasovchi", 3),
    ("lik", "ot yasovchi", 3),
    ("chi", "ot yasovchi", 3),
    ("zor", "ot yasovchi", 3),
    # adjective-forming
    ("siz", "sifat yasovchi (-siz)", 3),
    ("cha", "sifat/ravish yasovchi", 3),
    ("dek", "oʻxshash", 3),
    ("gi", "sifat yasovchi", 3),
    ("ki", "sifat yasovchi", 3),
    ("li", "sifat yasovchi", 3),
    # verb forms
    ("moqchi", "niyat (kelasi)", 4),
    ("yapti", "hozirgi-davom", 4),
    ("yotgan", "hozirgi-sifatdosh", 4),
    ("ajak", "kelasi zamon", 3),
    ("gan", "oʻtgan-sifatdosh", 3),
    ("kan", "oʻtgan-sifatdosh", 3),
    ("qan", "oʻtgan-sifatdosh", 3),
    ("ydi", "hozirgi zamon", 3),
    ("adi", "hozirgi zamon", 3),
    ("moq", "infinitiv", 3),
    ("ish", "harakat nomi", 3),
    ("ib", "ravishdosh", 2),
    ("sa", "shart", 2),
    ("ar", "kelasi zamon", 2),
    ("di", "oʻtgan zamon", 2),
    ("ti", "oʻtgan zamon", 2),
]


# ============================================================
# SENTIMENT LEXICONS
# ============================================================
POSITIVE = {norm_word(w) for w in [
    "yaxshi", "ajoyib", "goʻzal", "chiroyli", "zoʻr", "aʼlo", "oliy",
    "baxtli", "xursand", "quvnoq", "shod", "sevinch", "muvaffaqiyat",
    "gʻalaba", "yutuq", "taraqqiyot", "rivojlanish", "oʻsish", "sevgi",
    "muhabbat", "doʻstlik", "tinchlik", "erkinlik", "mustaqillik", "baxt",
    "omad", "foydali", "samarali", "natijali", "muhim", "qimmatli",
    "aqlli", "dono", "jasur", "kuchli", "sogʻlom", "qobiliyatli",
    "iqtidorli", "mehribon", "saxiy", "halol", "adolatli", "oliyjanob",
    "mard", "botir", "yoqimli", "hayratomuz", "ustun", "yetakchi",
    "qahramon", "qadrli", "aziz", "muqaddas", "pok", "gullab-yashnagan",
    "baraka", "saodat",
]}

NEGATIVE = {norm_word(w) for w in [
    "yomon", "xunuk", "qoʻpol", "dahshatli", "qoʻrqinchli", "xafa",
    "gʻamgin", "baxtsiz", "magʻlub", "magʻlubiyat", "yoʻqotish",
    "muvaffaqiyatsiz", "zararli", "xavfli", "xatarli", "ogʻir", "qiyin",
    "murakkab", "azob", "iztirob", "alam", "qaygʻu", "dard", "kasal",
    "zaif", "ojiz", "ahmoq", "nodon", "tentak", "yolgʻon", "firibgar",
    "xoin", "dushman", "tashvish", "xavf", "urush", "janjal", "mojaro",
    "fojea", "ofat", "balo", "halokat", "oʻlim", "aybdor", "gunohkar",
    "noxush", "achinarli", "fojiali", "noqulay", "mushkul", "qoʻrqoq",
    "nomard", "yomonlik", "yovuzlik", "kamchilik", "nuqson", "ayb",
    "gʻam", "kulfat", "chorasiz",
]}


# ============================================================
# TOPIC LEXICONS
# ============================================================
_TOPICS_RAW = {
    "Taʼlim": [
        "maktab", "talaba", "oʻquvchi", "oʻqituvchi", "muallim", "kitob",
        "daftar", "dars", "imtihon", "baho", "fan", "ilm", "bilim",
        "universitet", "institut", "fakultet", "kafedra", "kurs", "semestr",
        "oʻqish", "oʻrganish", "taʼlim", "tarbiya", "pedagog", "darslik",
        "lektsiya", "seminar", "amaliyot", "diplom", "sertifikat", "oʻqituv",
    ],
    "Texnologiya": [
        "kompyuter", "dastur", "internet", "texnologiya", "sunʼiy",
        "intellekt", "robot", "algoritm", "tarmoq", "sayt", "ilova",
        "telefon", "smartfon", "planshet", "dasturchi", "muhandis",
        "kod", "maʼlumot", "baza", "server", "bulut", "xavfsizlik",
        "raqamli", "virtual", "elektron", "avtomatlashtirish",
    ],
    "Tabiat": [
        "tabiat", "oʻrmon", "daryo", "togʻ", "koʻl", "dengiz", "havo",
        "suv", "quyosh", "oy", "yulduz", "osmon", "bulut", "yomgʻir",
        "qor", "shamol", "yer", "olov", "daraxt", "gul", "oʻsimlik",
        "hayvon", "qush", "baliq", "fasl", "bahor", "yoz", "kuz", "qish",
        "iqlim", "ekologiya",
    ],
    "Madaniyat": [
        "til", "madaniyat", "sanʼat", "musiqa", "adabiyot", "sheʼr",
        "doston", "hikoya", "roman", "yozuvchi", "shoir", "muallif",
        "teatr", "kino", "film", "rassom", "rasm", "haykaltaroshlik",
        "anʼana", "urf", "odat", "bayram", "milliylik", "folklor",
        "raqs", "qoʻshiq",
    ],
    "Tibbiyot": [
        "shifokor", "vrach", "bemor", "kasal", "dori", "kasalxona",
        "shifoxona", "dorixona", "tabobat", "salomatlik", "sogʻliq",
        "davolash", "operatsiya", "tashxis", "virus", "bakteriya",
        "emlash", "dorivor", "terapiya",
    ],
    "Iqtisodiyot": [
        "iqtisod", "iqtisodiyot", "pul", "soʻm", "dollar", "yevro", "bank",
        "kredit", "sarmoya", "investitsiya", "biznes", "tadbirkor",
        "kompaniya", "firma", "korxona", "bozor", "savdo", "sotuv", "xarid",
        "narx", "foyda", "zarar", "soliq", "byudjet",
    ],
    "Sport": [
        "sport", "futbol", "basketbol", "voleybol", "kurash", "boks",
        "yugurish", "suzish", "olimpiada", "musobaqa", "gʻolib", "chempion",
        "jamoa", "oʻyinchi", "stadion", "maydon", "medal", "kubok",
        "trenirovka", "mashq",
    ],
    "Siyosat": [
        "prezident", "hukumat", "parlament", "vazirlik", "vazir", "deputat",
        "saylov", "kandidat", "siyosat", "siyosiy", "davlat", "hokimiyat",
        "qonun", "konstitutsiya", "diplomat", "elchi", "xalqaro", "qaror",
    ],
    "Oila va hayot": [
        "oila", "ota", "ona", "bola", "aka", "uka", "opa", "singil",
        "bobo", "buvi", "amaki", "xola", "nikoh", "toʻy", "uy", "hovli",
        "qarindosh", "doʻst", "doʻstlik", "sevgi", "muhabbat",
    ],
}

TOPICS: Dict[str, set] = {
    name: {norm_word(w) for w in words} for name, words in _TOPICS_RAW.items()
}


STOPWORDS = {norm_word(w) for w in [
    "va", "yoki", "bu", "shu", "u", "biz", "siz", "men", "sen", "ular",
    "ham", "esa", "bir", "koʻp", "hech", "har", "yaʼni", "agar", "chunki",
    "lekin", "ammo", "biroq", "bilan", "uchun", "kabi", "haqida", "orqali",
    "qachon", "qanday", "qancha", "nima", "kim", "qayer", "nega", "eng",
    "juda", "yana", "edi", "ekan", "boʻlib", "boʻlgan", "boʻlsa",
]}


# ============================================================
# LANGUAGE DETECTION
# ============================================================
_RU_LETTERS = set("ёйцукенгшщзхъфывапролджэячсмитьбю")
_EN_LETTERS = set("abcdefghijklmnopqrstuvwxyz")
_UZ_COMMON = {"va", "bu", "shu", "uchun", "bilan", "kabi", "haqida", "ham",
              "lekin", "ammo", "chunki", "hozir", "boʻlib", "boʻlgan",
              "oʻz", "eng", "juda", "yana", "emas", "edi", "ekan"}
_UZ_SUFFIXES = ("lar", "ning", "dan", "ga", "da", "ni", "lik", "chi",
                "moq", "adi", "gan", "ydi", "ish", "miz", "ingiz")


def detect_language(text: str) -> str:
    text = normalize(text).lower()
    words = re.findall(r"[a-zʻʼЀ-ӿ'`]+", text)
    if not words:
        return "unknown"
    uz = ru = en = 0
    for w in words:
        if any(c in _RU_LETTERS for c in w):
            ru += 2
            continue
        if "oʻ" in w or "gʻ" in w:
            uz += 3
            continue
        if w in _UZ_COMMON:
            uz += 2
            continue
        if w.endswith(_UZ_SUFFIXES):
            uz += 1
            continue
        if all(c in _EN_LETTERS for c in w):
            en += 1
    top = max(uz, ru, en)
    if top == 0:
        return "unknown"
    if uz == top:
        return "uzbek"
    if ru == top:
        return "russian"
    return "english"


# ============================================================
# CORE ANALYSIS
# ============================================================
class NLPEngine:
    def analyze(self, text: str, analysis_type: str, options: dict):
        text = text.strip()
        tokens = self._tokenize(text)
        words = [t for t in tokens if t["type"] == "word"]
        sentences = [s for s in re.split(r"[.!?]+", text) if s.strip()]
        result = {
            "text": text,
            "token_count": len(tokens),
            "word_count": len(words),
            "sentence_count": max(len(sentences), 1),
            "language": detect_language(text),
        }
        if analysis_type in ("morphological", "full"):
            result["morphological"] = self._morph(words)
        if analysis_type in ("semantic", "full"):
            result["semantic"] = self._semantic(words, text)
        if analysis_type in ("lexical", "full"):
            result["lexical"] = self._lexical(words)
        if analysis_type == "full":
            result["summary"] = self._summary(result)
        return result

    # ----- tokenization -----
    def _tokenize(self, text: str):
        text = normalize(text)
        tokens = []
        pattern = r"[A-Za-zʻʼЀ-ӿ'`]+|[0-9]+(?:[.,][0-9]+)?|[^\s]"
        for m in re.finditer(pattern, text):
            w = m.group()
            kind = "word" if re.match(r"[A-Za-zʻʼЀ-ӿ]", w) else (
                "number" if w[0].isdigit() else (
                    "sentence_end" if w in ".!?" else "punct"))
            tokens.append({"text": w, "type": kind,
                           "start": m.start(), "end": m.end()})
        return tokens

    # ----- morphology -----
    def _strip_suffixes(self, word: str) -> Tuple[str, List[dict]]:
        """Iteratively strip suffixes; return (root, stripped_list)."""
        stripped = []
        cur = word
        changed = True
        while changed and len(cur) > 2:
            changed = False
            if cur in POS_DICT:
                break
            for suf, name, min_root in SUFFIXES:
                if cur.endswith(suf) and len(cur) - len(suf) >= min_root:
                    root = cur[:-len(suf)]
                    # stop if removing would destroy a dictionary form
                    if root in POS_DICT or len(root) >= 3:
                        stripped.append({"suffix": suf, "name": name})
                        cur = root
                        changed = True
                        break
        return cur, stripped

    def _guess_pos(self, word: str) -> str:
        if word.endswith(("di", "adi", "ydi", "moq", "ib", "gan", "kan",
                          "qan", "yapti", "yotgan", "ajak")):
            return "Fel"
        if word.endswith(("lik", "chi", "chilik", "lar", "xona", "iston",
                          "dosh")):
            return "Ot"
        if word.endswith(("li", "siz", "gi", "ki", "cha", "dek")):
            return "Sifat"
        if word.isdigit():
            return "Son"
        return "Ot"

    def _analyze_word(self, word: str) -> dict:
        wl = norm_word(word)
        if wl in POS_DICT:
            return {"root": wl, "pos": POS_DICT[wl], "suffixes": [],
                    "suffix_name": "—", "confidence": 0.97}
        root, stripped = self._strip_suffixes(wl)
        if root in POS_DICT:
            names = "+".join(s["name"] for s in reversed(stripped)) or "—"
            sufs = "".join(s["suffix"] for s in reversed(stripped))
            return {"root": root, "pos": POS_DICT[root],
                    "suffix": sufs, "suffix_name": names,
                    "suffixes": list(reversed(stripped)),
                    "confidence": round(0.93 - 0.03 * len(stripped), 2)}
        # Fallback: guess by ending
        pos = self._guess_pos(root)
        if stripped:
            names = "+".join(s["name"] for s in reversed(stripped))
            sufs = "".join(s["suffix"] for s in reversed(stripped))
            return {"root": root, "pos": pos, "suffix": sufs,
                    "suffix_name": names,
                    "suffixes": list(reversed(stripped)),
                    "confidence": 0.62}
        return {"root": wl, "pos": pos, "suffix": "", "suffix_name": "—",
                "suffixes": [], "confidence": 0.5}

    def _morph(self, words):
        analyzed = [{"word": w["text"], **self._analyze_word(w["text"])}
                    for w in words]
        pos_counts = Counter(a["pos"] for a in analyzed)
        total = max(len(words), 1)
        return {
            "words": analyzed,
            "pos_distribution": dict(pos_counts),
            "pos_stats": [{"pos": p, "count": c,
                           "percent": round(c / total * 100, 1)}
                          for p, c in pos_counts.most_common()],
            "avg_confidence": round(
                sum(a["confidence"] for a in analyzed) / total, 3),
        }

    # ----- semantic -----
    def _semantic(self, words, text):
        tokens = []
        for w in words:
            wl = norm_word(w["text"])
            if wl in STOPWORDS or len(wl) <= 2:
                continue
            # reduce to root for better keyword aggregation
            info = self._analyze_word(w["text"])
            tokens.append(info["root"] or wl)
        freq = Counter(tokens)
        kws = [{"word": w, "frequency": c,
                "weight": round(c / max(len(tokens), 1), 3)}
               for w, c in freq.most_common(10)]

        ps = sum(1 for w in tokens if w in POSITIVE)
        ns = sum(1 for w in tokens if w in NEGATIVE)
        total_sent = ps + ns
        if total_sent == 0:
            label, pos_r, neg_r, neu_r = "Neytral", 0.0, 0.0, 1.0
        else:
            pos_r = round(ps / total_sent, 2)
            neg_r = round(ns / total_sent, 2)
            neu_r = round(
                max(0.0, 1 - total_sent / max(len(tokens), 1)), 2)
            label = ("Ijobiy" if ps > ns
                     else "Salbiy" if ns > ps else "Neytral")

        tokset = set(tokens)
        scores = {name: len(tokset & kws_set)
                  for name, kws_set in TOPICS.items()}
        best, best_score = max(scores.items(), key=lambda x: x[1])
        top3 = [{"topic": t, "score": s}
                for t, s in sorted(scores.items(), key=lambda x: -x[1])
                if s > 0][:3]

        return {
            "keywords": kws,
            "sentiment": {"label": label, "positive": pos_r,
                          "negative": neg_r, "neutral": neu_r,
                          "positive_count": ps, "negative_count": ns},
            "topic": best if best_score > 0 else "Umumiy",
            "topic_scores": top3,
            "unique_words": len(set(tokens)),
            "lexical_diversity": round(
                len(set(tokens)) / max(len(tokens), 1), 3),
        }

    # ----- lexical -----
    def _lexical(self, words):
        aw = [norm_word(w["text"]) for w in words]
        uniq = set(aw)
        return {
            "word_frequency": [{"word": w, "count": c}
                               for w, c in Counter(aw).most_common(15)],
            "avg_word_length": round(
                sum(len(w) for w in aw) / max(len(aw), 1), 2),
            "unique_ratio": round(len(uniq) / max(len(aw), 1), 3),
            "long_words": sorted([w for w in uniq if len(w) >= 8]),
            "hapax_legomena": sorted(
                [w for w, c in Counter(aw).items() if c == 1])[:20],
        }

    # ----- summary -----
    def _summary(self, result):
        morph = result.get("morphological", {})
        sem = result.get("semantic", {})
        pd = morph.get("pos_distribution", {})
        dominant = max(pd, key=pd.get) if pd else "—"
        kws = sem.get("keywords", [])
        return {
            "dominant_pos": dominant,
            "topic": sem.get("topic", "—"),
            "sentiment": sem.get("sentiment", {}).get("label", "—"),
            "top_keyword": kws[0]["word"] if kws else "—",
            "language": result.get("language", "unknown"),
            "lexical_diversity": sem.get("lexical_diversity", 0),
        }
