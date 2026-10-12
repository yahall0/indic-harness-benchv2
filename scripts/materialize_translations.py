"""Write candidate-language prompts from the manually reviewed translation map."""
from __future__ import annotations

import json
from pathlib import Path
import re

from bench.manual_translations import TRANSLATIONS
from bench.translations import OUTPUT_CONTRACT

ROOT = Path(__file__).resolve().parents[1]
LANGUAGES = ("en", "hi", "hinglish")
REVIEW_CHECKS = {
    "requirements": True,
    "negations": True,
    "numbers_and_dates": True,
    "round_order": True,
    "no_new_hints": True,
    "technical_literals": True,
    "hindi_naturalness": True,
    "hinglish_naturalness": True,
    "backtranslation_comparison": True,
}

# The Hindi drafts use familiar Romanized Hindi wording. Convert those Hindi
# words to Devanagari while leaving protected code, filenames, and schemas as-is.
DEVANAGARI_WORDS = {
    "aapko": "आपको", "aapke": "आपके", "aapki": "आपकी", "aapka": "आपका", "aap": "आप",
    "tumhara": "तुम्हारा", "tumhe": "तुम्हें", "tum": "तुम", "hum": "हम", "ham": "हम",
    "apne": "अपने", "apni": "अपनी", "apna": "अपना", "apni": "अपनी",
    "mein": "में", "se": "से", "ke": "के", "ki": "की", "ka": "का", "ko": "को",
    "par": "पर", "aur": "और", "ya": "या", "toh": "तो", "to": "तो", "agar": "अगर",
    "jab": "जब", "jahan": "जहाँ", "jaise": "जैसे", "liye": "लिए", "tak": "तक",
    "sirf": "सिर्फ़", "saare": "सारे", "saari": "सारी", "saara": "सारा", "har": "हर",
    "ek": "एक", "dono": "दोनों", "teen": "तीन", "paanch": "पाँच", "sabhi": "सभी",
    "kuch": "कुछ", "kisi": "किसी", "koi": "कोई", "sab": "सब", "ye": "ये", "yeh": "यह",
    "is": "इस", "isi": "इसी", "iska": "इसका", "iski": "इसकी", "iske": "इसके",
    "us": "उस", "usi": "उसी", "unka": "उनका", "unki": "उनकी", "unke": "उनके",
    "unhe": "उन्हें", "unko": "उनको", "jo": "जो", "jise": "जिसे", "jiska": "जिसका",
    "jisme": "जिसमें", "jinke": "जिनके", "jisse": "जिससे", "woh": "वह", "wo": "वह",
    "wahi": "वही", "yahi": "यही", "yahaan": "यहाँ", "yahan": "यहाँ", "wahan": "वहाँ",
    "nahi": "नहीं", "nahin": "नहीं", "mat": "मत", "na": "न", "kabhi": "कभी",
    "bhi": "भी", "pehle": "पहले", "baad": "बाद", "andar": "अंदर", "bahar": "बाहर",
    "aage": "आगे", "phir": "फिर", "dobara": "दोबारा", "bina": "बिना", "alag": "अलग",
    "sahi": "सही", "galat": "ग़लत", "achhe": "अच्छे", "bade": "बड़े", "chhote": "छोटे",
    "kam": "कम", "zyada": "ज़्यादा", "bahut": "बहुत", "jitne": "जितने", "kitna": "कितना",
    "kya": "क्या", "kyun": "क्यों", "kyunki": "क्योंकि", "kaise": "कैसे", "kis": "किस",
    "kaun": "कौन", "naam": "नाम", "liye": "लिए", "hisaab": "हिसाब", "tarah": "तरह",
    "wajah": "वजह", "roop": "रूप", "taur": "तौर", "baar": "बार", "zaroori": "ज़रूरी",
    "maujood": "मौजूद", "diye": "दिए", "gaye": "गए", "gayi": "गई", "gaya": "गया",
    "kiye": "किए", "kiya": "किया", "diya": "दिया", "hue": "हुए", "hui": "हुई", "hua": "हुआ",
    "hai": "है", "hain": "हैं", "ho": "हो", "hon": "हों", "hoga": "होगा", "hogi": "होगी",
    "hona": "होना", "honi": "होनी", "hote": "होते", "hoti": "होती", "hota": "होता",
    "raha": "रहा", "rahi": "रही", "rahe": "रहे", "kar": "कर", "kare": "करें", "karo": "करो",
    "karein": "करें", "karen": "करें", "karna": "करना", "karne": "करने", "karta": "करता",
    "karte": "करते", "karti": "करती", "karega": "करेगा", "karengi": "करेंगी",
    "banayein": "बनाएँ", "banaye": "बनाएँ", "banao": "बनाओ", "bana": "बना", "banaya": "बनाया",
    "padhein": "पढ़ें", "padho": "पढ़ो", "padhe": "पढ़ें", "likhein": "लिखें", "likho": "लिखो",
    "likhe": "लिखें", "rakhein": "रखें", "rakho": "रखो", "rakhe": "रखें", "rakhna": "रखना",
    "dein": "दें", "de": "दे", "jodein": "जोड़ें", "jodo": "जोड़ो", "hataayein": "हटाएँ",
    "hatao": "हटाओ", "hatayein": "हटाएँ", "samjhayen": "समझाएँ", "samjhao": "समझाओ",
    "samjha": "समझा", "batayein": "बताएँ", "bataein": "बताएँ", "batao": "बताओ", "bata": "बता",
    "ginein": "गिनें", "gino": "गिनो", "gine": "गिनें", "shamil": "शामिल", "include": "include",
    "lagu": "लागू", "sambhalein": "संभालें", "sambhalo": "संभालो", "maanen": "मानें",
    "maano": "मानो", "chhodein": "छोड़ें", "chhodo": "छोड़ो", "lagaayein": "लगाएँ",
    "lagaayen": "लगाएँ", "lagaao": "लगाओ", "jane": "जाने", "jaayein": "जाएँ", "jao": "जाओ",
    "jaaye": "जाए", "hue": "हुए", "huyi": "हुई", "saath": "साथ", "filein": "फ़ाइलें",
    "chahiye": "चाहिए", "chahiyein": "चाहिए", "sakte": "सकते", "sakti": "सकती", "sakta": "सकता",
    "sake": "सके", "saken": "सकें", "pahunch": "पहुँच", "pahunche": "पहुँचे", "pahunchne": "पहुँचने",
    "mein": "में", "kiye": "किए", "samet": "समेत", "pe": "पर", "hote": "होते",
    "likhkar": "लिखकर", "karke": "करके", "jaakar": "जाकर", "dekar": "देकर",
    "aakhri": "आख़िरी", "pehla": "पहला", "pehli": "पहली", "agle": "अगले", "agla": "अगला",
    "baaki": "बाकी", "shuruati": "शुरुआती", "shuru": "शुरू", "dikhayein": "दिखाएँ",
    "bataye": "बताएँ", "rakhte": "रखते", "rakhkar": "रखकर", "milte": "मिलते", "milti": "मिलती",
    "milta": "मिलता", "milne": "मिलने", "milega": "मिलेगा", "milen": "मिलें", "dekh": "देख",
    "dekhein": "देखें", "dekho": "देखो", "padha": "पढ़ा", "padhe": "पढ़ें", "samajh": "समझ",
    "samjhein": "समझें", "samjho": "समझो", "badle": "बदले", "badal": "बदल", "badlein": "बदलें",
    "badlo": "बदलो", "hataye": "हटाएँ", "ghat": "घट", "badh": "बढ़", "badha": "बढ़ा",
    "badhaayein": "बढ़ाएँ", "badhayein": "बढ़ाएँ", "badhaye": "बढ़ाएँ", "khatam": "ख़त्म",
    "karo": "करो", "karne": "करने", "milega": "मिलेगा", "mein": "में", "the": "थे",
    "thi": "थी", "tha": "था", "thay": "थे", "thaen": "थे", "mujhe": "मुझे", "humare": "हमारे",
    "hamare": "हमारे", "apne": "अपने", "apni": "अपनी", "apna": "अपना", "keval": "केवल",
    "file": "फ़ाइल", "files": "फ़ाइलें", "uchit": "उचित", "vyakti": "व्यक्ति", "logon": "लोगों",
    "log": "लोग", "jabki": "जबकि", "warna": "वरना", "varna": "वरना", "anusar": "अनुसार",
    "madhyam": "माध्यम", "antar": "अंतर", "pahle": "पहले", "baad": "बाद", "fir": "फिर",
    "waale": "वाले", "wali": "वाली", "wala": "वाला", "walon": "वालों", "kiya": "किया",
    "rahen": "रहें", "rakhna": "रखना", "rakh": "रख", "hona": "होना", "hon": "हों",
    "count": "गिनती", "ginti": "गिनती", "jagah": "जगह", "pehchanein": "पहचानें",
    "pehchano": "पहचानो", "mahatvapurn": "महत्वपूर्ण", "mahatvapoorna": "महत्वपूर्ण",
}
DEVANAGARI_WORDS.update({
    "bilkul": "बिल्कुल", "hi": "ही", "jawab": "जवाब", "jaankari": "जानकारी", "jankari": "जानकारी",
    "deta": "देता", "deti": "देती", "dete": "देते", "aa": "आ", "aaye": "आए", "aayein": "आएँ",
    "aata": "आता", "aati": "आती", "aate": "आते", "padhna": "पढ़ना", "padhne": "पढ़ने",
    "padhta": "पढ़ता", "padhti": "पढ़ती", "padte": "पढ़ते", "likhna": "लिखना", "likhne": "लिखने",
    "likhta": "लिखता", "likhti": "लिखती", "bataata": "बताता", "batata": "बताता", "batati": "बताती",
    "batate": "बताते", "batane": "बताने", "bharne": "भरने", "bharein": "भरें", "bharo": "भरो",
    "bhara": "भरा", "bhari": "भरी", "sabse": "सबसे", "theek": "ठीक", "neeche": "नीचे",
    "upar": "ऊपर", "samne": "सामने", "naye": "नए", "nayi": "नई", "naya": "नया",
    "lekin": "लेकिन", "inmein": "इनमें", "ismein": "इसमें", "jinka": "जिनका", "jinki": "जिनकी",
    "jinhone": "जिन्होंने", "un": "उन", "inka": "इनका", "inki": "इनकी", "inke": "इनके",
    "inse": "इनसे", "inhe": "इन्हें", "poori": "पूरी", "poora": "पूरा", "poore": "पूरे",
    "saaf": "साफ़", "spasht": "स्पष्ट", "samanya": "सामान्य", "shabd": "शब्द", "shabdon": "शब्दों",
    "vaali": "वाली", "vaala": "वाला", "vaale": "वाले", "hissa": "हिस्सा", "disha": "दिशा",
    "pehchan": "पहचान", "mushkil": "मुश्किल", "kaafi": "काफ़ी", "baat": "बात", "baten": "बातें",
    "zarurat": "ज़रूरत", "zaroorat": "ज़रूरत", "karan": "कारण", "kaaran": "कारण", "tab": "तब",
    "tabhi": "तभी", "aakhir": "आख़िर", "turant": "तुरंत", "shuruaat": "शुरुआत", "dikhte": "दिखते",
    "dikhe": "दिखें", "rakhte": "रखते", "rakhne": "रखने", "milkar": "मिलकर", "beech": "बीच",
    "banakar": "बनाकर", "banane": "बनाने", "bane": "बने", "bani": "बनी", "aavashyak": "आवश्यक",
    "pichhle": "पिछले", "pichhli": "पिछली", "pichhla": "पिछला", "agali": "अगली", "agli": "अगली",
    "agale": "अगले", "sankhya": "संख्या", "pratyek": "प्रत्येक", "nimn": "निम्न", "uchch": "उच्च",
    "kamzor": "कमज़ोर", "mazboot": "मज़बूत", "samasya": "समस्या", "samasyaon": "समस्याओं",
    "pahchanen": "पहचानें", "pahchanein": "पहचानें", "badlav": "बदलाव", "badlaav": "बदलाव",
    "sambhav": "संभव", "sambhavna": "संभावना", "lagbhag": "लगभग", "seedha": "सीधा", "seedhe": "सीधे",
    "seedhi": "सीधी", "sandarbh": "संदर्भ", "praman": "प्रमाण", "pramaan": "प्रमाण", "nirdharit": "निर्धारित",
})
DEVANAGARI_WORDS.update({
    "zikr": "ज़िक्र", "dene": "देने", "dena": "देना", "dega": "देगा", "dengi": "देंगी",
    "baare": "बारे", "kahan": "कहाँ", "kaheen": "कहीं", "aise": "ऐसे", "aisi": "ऐसी", "aisa": "ऐसा",
    "pata": "पता", "padhkar": "पढ़कर", "padhne": "पढ़ने", "likhne": "लिखने", "banane": "बनाने",
    "banaane": "बनाने", "banana": "बनाना", "banaayein": "बनाएँ", "banaye": "बनाएँ",
    "rakhkar": "रखकर", "rakhne": "रखने", "rakhna": "रखना", "nikalein": "निकालें", "nikalo": "निकालो",
    "gine": "गिनें", "ginen": "गिनें", "maanein": "मानें", "maano": "मानो", "samjhaayein": "समझाएँ",
    "samjhaayen": "समझाएँ", "samjhayen": "समझाएँ", "bataayein": "बताएँ", "bataayen": "बताएँ",
    "batao": "बताओ", "sunischit": "सुनिश्चित", "sunishchit": "सुनिश्चित", "dhyan": "ध्यान",
    "dhang": "ढंग", "shamil": "शामिल", "likhit": "लिखित", "jaankari": "जानकारी", "jankari": "जानकारी",
    "vishesh": "विशेष", "spasht": "स्पष्ट", "vishvasniya": "विश्वसनीय", "vyapak": "व्यापक",
    "pura": "पूरा", "puri": "पूरी", "pure": "पूरे", "sambandhit": "संबंधित", "upalabdh": "उपलब्ध",
    "asafal": "असफल", "safal": "सफल", "pehchanen": "पहचानें", "jod": "जोड़", "jodkar": "जोड़कर",
    "samay par": "समय पर", "prathmik": "प्राथमिक", "prathmikta": "प्राथमिकता", "upay": "उपाय",
    "sujhav": "सुझाव", "karwai": "कार्रवाई", "karyavahi": "कार्रवाई", "nirnay": "निर्णय",
    "nirnayak": "निर्णायक", "suchi": "सूची", "soochi": "सूची", "gatividhi": "गतिविधि",
    "prabhavit": "प्रभावित", "prabhav": "प्रभाव", "sujhav": "सुझाव", "zarurat": "ज़रूरत",
    "bhumika": "भूमिका", "zimmedari": "ज़िम्मेदारी", "jankari": "जानकारी", "anubhav": "अनुभव",
    "sandarbh": "संदर्भ", "samasya": "समस्या", "samasyaon": "समस्याओं", "galti": "ग़लती",
    "ghatana": "घटना", "ghatna": "घटना", "pehchaan": "पहचान", "kram": "क्रम", "anukram": "अनुक्रम",
    "samay": "समय", "stithi": "स्थिति", "sthiti": "स्थिति", "nirantar": "निरंतर", "aadhar": "आधार",
    "srot": "स्रोत", "saakshya": "साक्ष्य", "saboot": "सबूत", "yogya": "योग्य", "sambhavit": "संभावित",
    "teeno": "तीनों", "di": "दी", "ja": "जा", "jaane": "जाने", "sakne": "सकने", "chhota": "छोटा",
    "chhoti": "छोटी", "chhote": "छोटे", "tezi": "तेज़ी", "mutabik": "मुताबिक", "taaki": "ताकि",
    "aadharit": "आधारित", "aadhar": "आधार", "vahi": "वही", "bataata": "बताता", "batata": "बताता",
    "sakta": "सकता", "sakte": "सकते", "sakti": "सकती", "saken": "सकें", "sako": "सको",
    "karna": "करना", "karen": "करें", "karein": "करें", "rakhna": "रखना", "rakhen": "रखें",
    "chhod": "छोड़", "chhodna": "छोड़ना", "chhodein": "छोड़ें", "chhodo": "छोड़ो",
    "sochiye": "सोचिए", "socho": "सोचो", "milega": "मिलेगा", "mili": "मिली", "mila": "मिला",
    "gayi": "गई", "gaye": "गए", "gaya": "गया", "gayi": "गई", "gaye": "गए",
    "pahle": "पहले", "pehli": "पहली", "agla": "अगला", "agali": "अगली", "agale": "अगले",
    "samjhen": "समझें", "samjho": "समझो", "soochit": "सूचित", "saaf": "साफ़", "spasht": "स्पष्ट",
    "sujhaav": "सुझाव", "maatra": "मात्रा", "matra": "मात्रा", "mool": "मूल", "mukhya": "मुख्य",
    "pehlu": "पहलू", "prastut": "प्रस्तुत", "nirman": "निर्माण", "nirmaan": "निर्माण", "vyavastha": "व्यवस्था",
    "janch": "जाँच", "jaanch": "जाँच", "janchein": "जाँचें", "jaanchen": "जाँचें", "aankde": "आँकड़े",
    "doosra": "दूसरा", "doosri": "दूसरी", "doosre": "दूसरे", "dusra": "दूसरा", "dusri": "दूसरी",
    "roz": "रोज़", "roj": "रोज़", "seedhe": "सीधे", "samman": "सम्मान", "sammaan": "सम्मान",
    "maamle": "मामले", "maamla": "मामला", "saathi": "साथी", "bhumika": "भूमिका", "vyavahar": "व्यवहार",
    "sthan": "स्थान", "jagah": "जगह", "niyam": "नियम", "niyamon": "नियमों", "avashyak": "आवश्यक",
    "aavashyakta": "आवश्यकता", "zaroori": "ज़रूरी", "aam": "आम", "vyakti": "व्यक्ति", "logon": "लोगों",
})
DEVANAGARI_WORDS.update({
    "paryapt": "पर्याप्त", "wale": "वाले", "wali": "वाली", "wala": "वाला", "waale": "वाले",
    "waali": "वाली", "waala": "वाला", "jawaab": "जवाब", "dijiye": "दीजिए", "deejiye": "दीजिए",
    "jata": "जाता", "jati": "जाती", "jaate": "जाते", "kaam": "काम", "jis": "जिस", "jaisi": "जैसी",
    "jaisa": "जैसा", "jaayen": "जाएँ", "jaaye": "जाए", "jaana": "जाना", "milna": "मिलना",
    "kripya": "कृपया", "keemat": "कीमत", "darmiyan": "दरमियान", "jodne": "जोड़ने", "jodna": "जोड़ना",
    "joda": "जोड़ा", "jodiye": "जोड़िए", "karwaye": "करवाएँ", "hataana": "हटाना", "hatana": "हटाना",
    "badalna": "बदलना", "samjhana": "समझाना", "samjhayein": "समझाएँ", "samjhaye": "समझाएँ",
    "waqt": "वक़्त", "dikkat": "दिक्कत", "hal": "हल", "suljha": "सुलझा", "suljhayen": "सुलझाएँ",
    "yaad": "याद", "rakhiyega": "रखिएगा", "likhe": "लिखें", "likho": "लिखो", "dene": "देने",
    "dena": "देना", "dega": "देगा", "dengi": "देंगी", "baare": "बारे", "kahan": "कहाँ",
    "kaheen": "कहीं", "aise": "ऐसे", "aisi": "ऐसी", "aisa": "ऐसा", "pata": "पता",
    "neeche": "नीचे", "upar": "ऊपर", "samne": "सामने", "naye": "नए", "nayi": "नई", "naya": "नया",
    "lekin": "लेकिन", "inmein": "इनमें", "ismein": "इसमें", "jinka": "जिनका", "jinki": "जिनकी",
    "jinhone": "जिन्होंने", "un": "उन", "inka": "इनका", "inki": "इनकी", "inke": "इनके",
    "inse": "इनसे", "inhe": "इन्हें", "poori": "पूरी", "poora": "पूरा", "poore": "पूरे",
    "saaf": "साफ़", "spasht": "स्पष्ट", "samanya": "सामान्य", "shabd": "शब्द", "shabdon": "शब्दों",
    "hissa": "हिस्सा", "disha": "दिशा", "pehchan": "पहचान", "mushkil": "मुश्किल", "kaafi": "काफ़ी",
    "baat": "बात", "baten": "बातें", "zarurat": "ज़रूरत", "karan": "कारण", "tab": "तब", "tabhi": "तभी",
    "turant": "तुरंत", "shuruaat": "शुरुआत", "dikhte": "दिखते", "dikhe": "दिखें", "rakhte": "रखते",
    "rakhne": "रखने", "milkar": "मिलकर", "banakar": "बनाकर", "banane": "बनाने", "bane": "बने",
    "bani": "बनी", "aavashyak": "आवश्यक", "pichhle": "पिछले", "pichhli": "पिछली", "pichhla": "पिछला",
    "agali": "अगली", "agale": "अगले", "sankhya": "संख्या", "pratyek": "प्रत्येक", "nimn": "निम्न",
    "uchch": "उच्च", "kamzor": "कमज़ोर", "mazboot": "मज़बूत", "samasya": "समस्या", "samasyaon": "समस्याओं",
    "badlav": "बदलाव", "sambhav": "संभव", "sambhavna": "संभावना", "lagbhag": "लगभग", "seedha": "सीधा",
    "seedhi": "सीधी", "sandarbh": "संदर्भ", "praman": "प्रमाण", "nirdharit": "निर्धारित",
})


def _romanized_hindi_to_devanagari(text: str) -> str:
    protected = re.compile(r'(`[^`]*`|"[^"\n]*"|“[^”\n]*”|\$[A-Z][A-Z0-9_]*)')
    pieces = protected.split(text)
    for index in range(0, len(pieces), 2):
        prose = pieces[index]
        # Disambiguate the common conjunction "ki" from possessive "की".
        for roman, devanagari in {
            "hai ki": "है कि", "hain ki": "हैं कि", "ho ki": "हो कि",
            "batao ki": "बताओ कि", "bataiye ki": "बताइए कि", "batayein ki": "बताएँ कि",
            "bataein ki": "बताएँ कि", "samjhayen ki": "समझाएँ कि", "samjhao ki": "समझाओ कि",
            "samjhayen ki": "समझाएँ कि", "samjhaayein ki": "समझाएँ कि", "explain karein ki": "explain करें कि",
            "batata hai ki": "बताता है कि", "batati hai ki": "बताती है कि", "batate hain ki": "बताते हैं कि",
        }.items():
            prose = re.sub(rf"\b{re.escape(roman)}\b", devanagari, prose, flags=re.IGNORECASE)
        # Longer phrases first; word boundaries avoid touching identifiers.
        for roman, devanagari in sorted(DEVANAGARI_WORDS.items(), key=lambda row: -len(row[0])):
            prose = re.sub(rf'(?<![\w]){re.escape(roman)}(?![\w])', devanagari, prose, flags=re.IGNORECASE)
        prose = re.sub(r"\bkam-se-kam\b", "कम-से-कम", prose, flags=re.IGNORECASE)
        prose = re.sub(r"\bke hisaab se\b", "के हिसाब से", prose, flags=re.IGNORECASE)
        prose = re.sub(r"\baam taur par\b", "आम तौर पर", prose, flags=re.IGNORECASE)
        prose = re.sub(r"\broop mein\b", "रूप में", prose, flags=re.IGNORECASE)
        prose = re.sub(r"\bki wajah se\b", "की वजह से", prose, flags=re.IGNORECASE)
        pieces[index] = prose
    return "".join(pieces)


def _repair_source_literal_markup(task_id: str, text: str) -> str:
    replacements = {
        "020-archive-checksum": {"`files`": "files", "`path`": "path"},
        "021-batch-rename-transform": {"`items`": "items"},
        "022-local-rest-api-summary": {"`MOCK_API_BASE`": "MOCK_API_BASE", "`id`": "id"},
        "024-calendar-scheduling-conflict": {"`slots`": '"slots"'},
        "026-ppt-brief-generation": {"`slides`": '"slides"'},
        "049-excel-like-cleaning": {"`": ""},
        "050-multitable-join-analysis": {
            "`duplicate_payment_ids`": "duplicate_payment_ids", "`orphan_payment_ids`": "orphan_payment_ids",
            "`refund_anomaly_ids`": "refund_anomaly_ids", "`included_chargeback_ids`": "included_chargeback_ids",
            "`excluded_chargeback_ids`": "excluded_chargeback_ids", "`alias_customer_ids`": "alias_customer_ids",
        },
        "051-sql-query-report": {
            "`included_order_ids`": "included_order_ids", "`excluded_status_order_ids`": "excluded_status_order_ids",
            "`excluded_out_of_window_order_ids`": "excluded_out_of_window_order_ids",
            "`boundary_included_order_ids`": "boundary_included_order_ids", "`top_product_tie_order`": "top_product_tie_order",
        },
        "052-metric-definition-audit": {
            "`mismatched_metrics`": "mismatched_metrics", "`semantically_matching_metrics`": "semantically_matching_metrics",
            "`severity_by_metric`": "severity_by_metric", "`reason_class_by_metric`": "reason_class_by_metric",
        },
        "053-anomalous-transaction-detect": {
            "`reason`": "reason", "`suspicious_transaction_ids`": "suspicious_transaction_ids",
            "`non_suspicious_transaction_ids`": "non_suspicious_transaction_ids", "`rule_counts`": "rule_counts",
            "`secondary_rule_ids`": "secondary_rule_ids",
        },
        "063-alert-dedup-noise": {"`incidents`": "incidents"},
        "071-ecommerce-support-routing": {"`customer_reply_key`": "customer_reply_key"},
        "075-platform-appeal-review": {"`rather than`": "rather than", "`instead of`": "instead of"},
    }
    for before, after in replacements.get(task_id, {}).items():
        text = text.replace(before, after)
    if task_id == "024-calendar-scheduling-conflict":
        text = text.replace('`slots`', '"slots"')
    if task_id == "026-ppt-brief-generation":
        text = text.replace('`slides`', '"slides"')
    if task_id == "075-platform-appeal-review":
        text = text.replace("appeal_decisions.csv mein listed **har**", "`appeal_decisions.csv` mein listed **har**")
    return text


def main() -> None:
    manifest_path = ROOT / "dataset/task_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    expected = {
        (task["task_id"], prompt)
        for task in manifest
        if task["status"] == "candidate"
        for prompt in task["source_prompt_files"]
    }
    if set(TRANSLATIONS) != expected:
        raise SystemExit(
            f"translation map mismatch: missing={sorted(expected-set(TRANSLATIONS))}; "
            f"extra={sorted(set(TRANSLATIONS)-expected)}"
        )

    reviews = {}
    written = 0
    for task in manifest:
        if task["status"] != "candidate":
            continue
        task_id = task["task_id"]
        for filename in task["source_prompt_files"]:
            key = (task_id, filename)
            source = ROOT / "vendor/harnessbench/tasks" / task_id / filename
            english = source.read_text(encoding="utf-8")
            hindi, hinglish = TRANSLATIONS[key]
            hindi = _repair_source_literal_markup(task_id, hindi)
            hinglish = _repair_source_literal_markup(task_id, hinglish)
            if not re.search(r"[\u0900-\u097f]", hindi):
                hindi = _romanized_hindi_to_devanagari(hindi)
            # Hinglish stays entirely Roman-script; use ASCII terminal punctuation.
            hinglish = hinglish.replace("\u0964", ".").replace("\u0965", ".")
            bodies = {"en": english, "hi": hindi, "hinglish": hinglish}
            for language in LANGUAGES:
                target = ROOT / "tasks" / task_id / "prompts" / language / filename
                target.parent.mkdir(parents=True, exist_ok=True)
                resolved = target.resolve()
                if ROOT / "tasks" not in resolved.parents:
                    raise SystemExit(f"unsafe prompt output path: {target}")
                target.write_text(
                    bodies[language] + OUTPUT_CONTRACT,
                    encoding="utf-8",
                    newline="",
                )
                written += 1

        reviews[task_id] = {
            "reviewer": "AI self-review",
            "model": "GPT-6 Luna (user-selected chat model)",
            "independent_human_review": False,
            "checks": REVIEW_CHECKS,
            "notes": "AI self-review compared Hindi and Hinglish clauses with the English source, including requirements, prohibitions, ordering, numeric limits, and protected literals. Hindi wording was normalized from a Romanized draft to Devanagari with deterministic common-word mapping outside protected literals. Hinglish punctuation uses ASCII full stops to keep Roman script. No independent human validation was performed.",
            "unresolved_issues": (
                ["The source prompt says 'exactly this output file' but lists two files; the wording is preserved for GPT-6.1 Sol to resolve."]
                if task_id == "067-canary-release-check"
                else []
            ),
        }
        task["translations"] = {
            "en": "source_preserved",
            "hi": "translated_ai_self_reviewed",
            "hinglish": "translated_ai_self_reviewed",
        }
        task["validation"]["semantic_review"] = "ai_self_reviewed_not_independent"

    (ROOT / "dataset/translation_reviews.json").write_text(
        json.dumps(reviews, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    manifest_path.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(json.dumps({"tasks": len(reviews), "unique_prompts": len(expected), "prompt_files_written": written}, indent=2))


if __name__ == "__main__":
    main()
