import feedparser
import json
import re
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime

# RSS kaynakları — gerçek çalışan feed'ler
FEEDS = [
    {"id": "lifespan",    "name": "Lifespan.io",          "url": "https://www.lifespan.io/feed/",                          "color": "#12e8c4", "cat": "longevity"},
    {"id": "singularity", "name": "Singularity Hub",       "url": "https://singularityhub.com/feed/",                       "color": "#fbbf24", "cat": "ai"},
    {"id": "mit",         "name": "MIT Tech Review",       "url": "https://www.technologyreview.com/feed/",                 "color": "#818cf8", "cat": "ai"},
    {"id": "longevity",   "name": "Longevity.Technology",  "url": "https://longevity.technology/feed/",                     "color": "#12e8c4", "cat": "longevity"},
    {"id": "nature",      "name": "Nature Aging",          "url": "https://www.nature.com/nataging.rss",                    "color": "#818cf8", "cat": "longevity"},
    {"id": "ieee",        "name": "IEEE Spectrum",         "url": "https://spectrum.ieee.org/feeds/feed.rss",               "color": "#34d399", "cat": "bionics"},
    {"id": "webrazzi",    "name": "Webrazzi",              "url": "https://webrazzi.com/feed/",                             "color": "#ef4444", "cat": "tr"},
    {"id": "pubmed",      "name": "PubMed Longevity",      "url": "https://pubmed.ncbi.nlm.nih.gov/rss/search/longevity+aging/?limit=20&format=rss", "color": "#818cf8", "cat": "longevity"},
]

# Viralite skoru hesaplama — anahtar kelime bazlı
VIRAL_KEYWORDS = {
    "neuralink": 20, "crispr": 18, "bci": 15, "brain": 10,
    "aging": 12, "longevity": 12, "lifespan": 10, "cancer": 14,
    "ai": 10, "artificial intelligence": 10, "gene": 12, "stem cell": 13,
    "bionic": 14, "prosthetic": 12, "alzheimer": 13, "parkinson": 11,
    "diabetes": 10, "heart": 9, "vaccine": 11, "drug": 8,
    "trial": 8, "breakthrough": 15, "first": 12, "reversal": 16,
    "türkiye": 15, "turkey": 10, "turkish": 10, "odtü": 18,
    "extend": 10, "reverse": 14, "cure": 16, "treatment": 8,
    "nmn": 12, "rapamycin": 11, "senolytics": 13, "epigenetic": 13,
    "robot": 10, "implant": 12, "chip": 11, "sensor": 8,
    "microbiome": 11, "gut": 9, "dna": 10, "rna": 9,
}

CAT_KEYWORDS = {
    "longevity": ["aging", "longevity", "lifespan", "rapamycin", "nmn", "senolytics", "epigenetic", "senescent", "nad", "metformin", "spermidine", "taurin"],
    "ai":        ["artificial intelligence", "machine learning", "deep learning", "neural network", "gpt", "llm", "alphafold", "algorithm", "ai ", "robot"],
    "bionics":   ["bionic", "prosthetic", "implant", "bci", "brain-computer", "exoskeleton", "neuralink", "neural", "chip", "electrode", "cochlear"],
    "crispr":    ["crispr", "gene editing", "base editing", "prime editing", "gene therapy", "cas9", "cas13"],
    "tr":        ["türkiye", "turkey", "turkish", "odtü", "tubitak", "istanbul", "ankara", "boğaziçi", "hacettepe"],
}

def calc_viral(title, summary):
    text = (title + " " + summary).lower()
    score = 40  # base
    for kw, pts in VIRAL_KEYWORDS.items():
        if kw in text:
            score += pts
    return min(score, 99)

def calc_tiktok(viral):
    if viral >= 90: return "100K-500K"
    if viral >= 80: return "50K-200K"
    if viral >= 70: return "20K-80K"
    if viral >= 60: return "10K-40K"
    return "5K-20K"

def get_cats(title, summary):
    text = (title + " " + summary).lower()
    cats = []
    for cat, keywords in CAT_KEYWORDS.items():
        if any(kw in text for kw in keywords):
            cats.append(cat)
    if not cats:
        cats = ["longevity"]
    return cats

def get_tags(title, summary):
    text = (title + " " + summary).lower()
    tags = []
    tag_map = {
        "CRISPR": "crispr", "AI": "artificial intelligence", "BCI": "brain-computer",
        "neuralink": "neuralink", "longevity": "longevity", "aging": "aging",
        "cancer": "cancer", "alzheimer": "alzheimer", "parkinson": "parkinson",
        "bionic": "bionic", "gene therapy": "gene therapy", "FDA": "fda",
        "NMN": "nmn", "microbiome": "microbiome", "türkiye": "türkiye",
    }
    for tag, kw in tag_map.items():
        if kw in text:
            tags.append(tag)
    return tags[:4] if tags else ["bilim"]

def parse_date(entry):
    try:
        if hasattr(entry, 'published'):
            dt = parsedate_to_datetime(entry.published)
            return dt.astimezone(timezone.utc)
    except:
        pass
    return datetime.now(timezone.utc)

def format_date_tr(dt):
    months = ["", "Oca", "Şub", "Mar", "Nis", "May", "Haz",
              "Tem", "Ağu", "Eyl", "Eki", "Kas", "Ara"]
    return f"{dt.day} {months[dt.month]} {dt.year}"

def clean_text(text):
    if not text:
        return ""
    text = re.sub(r'<[^>]+>', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text[:300]

# Fetch all feeds
all_news = []
seen_urls = set()

for feed_info in FEEDS:
    print(f"Fetching {feed_info['name']}...")
    try:
        feed = feedparser.parse(feed_info["url"])
        entries = feed.entries[:15]  # her kaynaktan max 15
        for i, entry in enumerate(entries):
            url = entry.get("link", "")
            if not url or url in seen_urls:
                continue
            seen_urls.add(url)

            title = clean_text(entry.get("title", ""))
            summary = clean_text(entry.get("summary", entry.get("description", "")))
            if not title:
                continue

            dt = parse_date(entry)
            viral = calc_viral(title, summary)
            cats = get_cats(title, summary)
            tags = get_tags(title, summary)

            news_item = {
                "id": f"{feed_info['id']}_{i}_{abs(hash(url)) % 9999}",
                "source": feed_info["id"],
                "title": title,
                "summary": summary[:250] if summary else title,
                "date": format_date_tr(dt),
                "dv": int(dt.strftime("%Y%m%d")),
                "cat": cats,
                "viral": viral,
                "tiktok": calc_tiktok(viral),
                "factStatus": "verified",
                "tags": tags,
                "url": url,
            }
            all_news.append(news_item)
        print(f"  ✓ {len(entries)} haber alındı")
    except Exception as e:
        print(f"  ✗ Hata: {e}")

# En yeniden eskiye sırala, max 65
all_news.sort(key=lambda x: x["dv"], reverse=True)
all_news = all_news[:65]

# JSON olarak kaydet
output = {
    "updated": datetime.now(timezone.utc).isoformat(),
    "count": len(all_news),
    "news": all_news,
    "sources": FEEDS,
}

with open("news.json", "w", encoding="utf-8") as f:
    json.dump(output, f, ensure_ascii=False, indent=2)

print(f"\n✅ {len(all_news)} haber news.json dosyasına kaydedildi.")
