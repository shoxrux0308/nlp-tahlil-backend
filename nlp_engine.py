import re
from typing import Dict, List
from collections import Counter

POS_DICT = {
    "til":"Ot","tili":"Ot","tillar":"Ot","tillardan":"Ot","dunyo":"Ot","dunyoda":"Ot","dunyodagi":"Ot",
    "grammatik":"Sifat","tuzilish":"Ot","tuzilishi":"Ot","matn":"Ot","matnlar":"Ot",
    "inson":"Ot","kitob":"Ot","maktab":"Ot","uy":"Ot","shahar":"Ot","vaqt":"Ot",
    "hayot":"Ot","fan":"Ot","ilm":"Ot","bilim":"Ot","biri":"Ot",
    "uzbek":"Sifat","katta":"Sifat","kichik":"Sifat","yaxshi":"Sifat","yomon":"Sifat",
    "boy":"Sifat","murakkab":"Sifat","oson":"Sifat","yangi":"Sifat","eski":"Sifat",
    "xos":"Sifat","chiroyli":"Sifat","baland":"Sifat","past":"Sifat",
    "bordi":"Fel","keldi":"Fel","qildi":"Fel","boldi":"Fel","boladi":"Fel",
    "bolib":"Fel","oqudi":"Fel","yozdi":"Fel","ishladi":"Fel","xosdir":"Fel","hisoblanadi":"Fel",
    "eng":"Ravish","juda":"Ravish","ham":"Ravish","yana":"Ravish","tez":"Ravish","sekin":"Ravish",
    "men":"Olmosh","sen":"Olmosh","u":"Olmosh","biz":"Olmosh","siz":"Olmosh","ular":"Olmosh",
    "bu":"Olmosh","shu":"Olmosh",
    "va":"Boglovchi","yoki":"Boglovchi","lekin":"Boglovchi","ammo":"Boglovchi","chunki":"Boglovchi",
    "bilan":"Komakchi","uchun":"Komakchi","haqida":"Komakchi","kabi":"Komakchi",
}

SUFFIXES = [
    ("lardan","koplik+dan",6),("larda","koplik+da",5),("larni","koplik+ni",5),
    ("larga","koplik+ga",5),("lar","koplik",3),("ning","qaratqich",4),
    ("dagi","orin+sifat",4),("dan","chiqish",3),("da","orin-payt",2),
    ("ni","tushum",2),("ga","jonalish",2),("lik","ot yasovchi",3),
    ("chi","ot yasovchi",3),("ish","harakat nomi",3),("di","otgan zamon",2),
    ("adi","hozirgi zamon",3),("moq","infinitiv",3),("ib","ravishdosh",2),
]

STOPWORDS = {"va","yoki","bu","shu","u","biz","siz","men","sen","ular","ham","esa","bir","kop","hech"}

class NLPEngine:
    def analyze(self, text, analysis_type, options):
        text = text.strip()
        tokens = self._tokenize(text)
        words = [t for t in tokens if t["type"]=="word"]
        result = {"text":text,"token_count":len(tokens),"word_count":len(words),"sentence_count":len(re.split(r"[.!?]+",text))}
        if analysis_type in ("morphological","full"): result["morphological"] = self._morph(words)
        if analysis_type in ("semantic","full"): result["semantic"] = self._semantic(words,text)
        if analysis_type in ("lexical","full"): result["lexical"] = self._lexical(words)
        if analysis_type == "full": result["summary"] = self._summary(result)
        return result

    def _tokenize(self, text):
        tokens = []
        for m in re.finditer(r"[a-zA-ZЀ-ӿȀ-ɏ'`]+|[0-9]+|[^\s]", text):
            w = m.group()
            if re.match(r"[a-zA-ZЀ-ӿȀ-ɏ]",w): tokens.append({"text":w,"type":"word","start":m.start(),"end":m.end()})
            elif re.match(r"[0-9]",w): tokens.append({"text":w,"type":"number","start":m.start(),"end":m.end()})
            elif w in ".!?": tokens.append({"text":w,"type":"sentence_end","start":m.start(),"end":m.end()})
        return tokens

    def _analyze_word(self, word):
        wl = word.lower()
        if wl in POS_DICT: return {"root":wl,"pos":POS_DICT[wl],"suffix":"","suffix_name":"—","confidence":0.97}
        for suffix,sname,length in SUFFIXES:
            if wl.endswith(suffix) and len(wl)>length+1:
                root = wl[:-length]
                if root in POS_DICT: return {"root":root,"pos":POS_DICT[root],"suffix":suffix,"suffix_name":sname,"confidence":0.91}
        pos = "Fel" if wl.endswith(("di","adi","moq","ib")) else "Ot" if wl.endswith(("lik","chi","lar")) else "Sifat" if wl.endswith(("li","siz","gi")) else "Ot"
        return {"root":wl,"pos":pos,"suffix":"","suffix_name":"—","confidence":0.55}

    def _morph(self, words):
        analyzed = [{"word":w["text"],**self._analyze_word(w["text"])} for w in words]
        pos_counts = Counter(a["pos"] for a in analyzed)
        return {"words":analyzed,"pos_distribution":dict(pos_counts),"pos_stats":[{"pos":p,"count":c,"percent":round(c/max(len(words),1)*100,1)} for p,c in pos_counts.most_common()]}

    def _semantic(self, words, text):
        wl = [w["text"].lower() for w in words if w["text"].lower() not in STOPWORDS and len(w["text"])>2]
        freq = Counter(wl)
        kws = [{"word":w,"frequency":c,"weight":round(c/max(len(wl),1),3)} for w,c in freq.most_common(10)]
        pos_w = {"yaxshi","chiroyli","ajoyib","zor","katta","boy","baxt","sevgi"}
        neg_w = {"yomon","qiyin","murakkab","ogir","qorqinchli","past"}
        ps = sum(1 for w in wl if w in pos_w); ns = sum(1 for w in wl if w in neg_w)
        sent = "Ijobiy" if ps>ns else ("Salbiy" if ns>ps else "Neytral")
        topics = {"Talim":{"maktab","talaba","kitob","fan","bilim","ilm"},"Texnologiya":{"kompyuter","dastur","internet","texnologiya","suniy","intellekt"},"Tabiat":{"tabiat","ormon","daryo","tog","kol","havo","suv"},"Madaniyat":{"til","madaniyat","sanat","musiqa","adabiyot"}}
        ws = set(wl); scores = {t:len(ws&k) for t,k in topics.items()}; best = max(scores,key=scores.get)
        return {"keywords":kws,"sentiment":{"label":sent,"positive":round(ps/max(ps+ns,1),2),"negative":round(ns/max(ps+ns,1),2),"neutral":round(1-(ps+ns)/max(len(wl),1),2)},"topic":best if scores[best]>0 else "Umumiy","unique_words":len(set(wl)),"lexical_diversity":round(len(set(wl))/max(len(wl),1),3)}

    def _lexical(self, words):
        aw = [w["text"].lower() for w in words]
        return {"word_frequency":[{"word":w,"count":c} for w,c in Counter(aw).most_common(15)],"avg_word_length":round(sum(len(w) for w in aw)/max(len(aw),1),2),"unique_ratio":round(len(set(aw))/max(len(aw),1),3),"long_words":[w for w in set(aw) if len(w)>=8]}

    def _summary(self, result):
        morph = result.get("morphological",{}); sem = result.get("semantic",{})
        pd = morph.get("pos_distribution",{}); dp = max(pd,key=pd.get) if pd else "—"
        return {"dominant_pos":dp,"topic":sem.get("topic","—"),"sentiment":sem.get("sentiment",{}).get("label","—"),"top_keyword":(sem.get("keywords",[{}])[0].get("word","—") if sem.get("keywords") else "—")}
