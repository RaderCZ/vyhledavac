import streamlit as st
import feedparser
import re
from collections import Counter

# Nastavení vzhledu stránky
st.set_page_config(page_title="Gaming Topic Radar", page_icon="🎮", layout="wide")

# Maskování hlavičky pro servery
feedparser.USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

# --- 50 RSS FEEDŮ ---
RSS_FEEDS = [
    "http://www.gameinformer.com/feeds/thefeedrss.aspx",
    "http://www.psxextreme.com/rss/",
    "https://www.bluesnews.com/news/bn.rdf",
    "https://cogconnected.com/feed/",
    "https://www.dsogaming.com/feed/",
    "https://www.dualshockers.com/feed/",
    "https://www.engadget.com/gaming/rss.xml",
    "https://www.eurogamer.net/feed/news",
    "https://www.gamedeveloper.com/rss.xml",
    "https://www.gamereactor.eu/rss/rss.php",
    "https://venturebeat.com/category/games/feed/",
    "https://www.gamesindustry.biz/feed/news",
    "https://www.gamespot.com/feeds/news/",
    "https://www.gamesradar.com/news/rss/",
    "https://www.gamewatcher.com/news/rss",
    "https://arstechnica.com/gaming/feed/",
    "https://www.gematsu.com/feed",
    "https://hardcoregamer.com/feed/",
    "https://feeds.feedburner.com/IgnAll",
    "https://insider-gaming.com/feed/",
    "https://n4g.com/rss/news",
    "https://www.videogameschronicle.com/feed/",
    "https://nintendoeverything.com/feed/",
    "https://www.nintendolife.com/feeds/latest",
    "https://www.pcgamer.com/rss/",
    "https://www.pcgamesn.com/mainrss.xml",
    "https://www.playstationlifestyle.net/feed/",
    "https://blog.playstation.com/feed/",
    "https://www.polygon.com/rss/index.xml",
    "https://press-start.com.au/feed/",
    "https://www.psnation.com/feed/",
    "https://www.pushsquare.com/feeds/latest",
    "https://www.rockpapershotgun.com/feed/news",
    "https://www.siliconera.com/feed/",
    "https://rss.slashdot.org/Slashdot/slashdotMain",
    "https://www.escapistmagazine.com/feed/",
    "https://www.thesixthaxis.com/feed/",
    "https://twinfinite.net/feed/",
    "https://www.vg247.com/feed/news",
    "https://vgleaks.com/feed/",
    "https://gamingbolt.com/feed",
    "https://wccftech.com/category/games/feed/",
    "https://news.xbox.com/en-us/feed/",
    "https://www.destructoid.com/feed/",
    "https://www.forbes.com/sites/erikkain/feed/",
    "https://gamerant.com/feed/",
    "https://gamezone.com/feed/",
    "https://www.giantbomb.com/feeds/news/",
    "https://kotaku.com/rss",
    "https://www.pcinvasion.com/feed/"
]

OBECNA_SLOVA = ["game", "games", "gaming", "news", "new", "release", "released", "video", "trailer"]

def ocisti_text(text):
    text = text.lower()
    words = re.findall(r'\w+', text)
    return [w for w in words if len(w) > 3 and w not in OBECNA_SLOVA]

# Cache na 15 minut pro hladký chod na cloudu
@st.cache_data(ttl=900)
def stahni_vsechny_clanky():
    clanky = []
    vsechna_slova = []
    
    for url in RSS_FEEDS:
        try:
            feed = feedparser.parse(url)
            source_name = url.split('/')[2].replace("www.", "").replace("feeds.feedburner.com", "IGN").replace("rss.slashdot.org", "Slashdot")
            if "gameinformer" in url: source_name = "Game Informer"
            elif "psxextreme" in url: source_name = "PSX Extreme"
            
            for entry in feed.entries[:15]:
                title = entry.get('title', '')
                summary = entry.get('summary', '') or entry.get('description', '')
                link = entry.get('link', '')
                
                slova_nadpisu = ocisti_text(title)
                vsechna_slova.extend(slova_nadpisu)
                
                clanky.append({
                    'title': title,
                    'source': source_name,
                    'link': link,
                    'summary': summary,
                    'slova': slova_nadpisu
                })
        except:
            pass
            
    cetnost = Counter(vsechna_slova)
    
    for c in clanky:
        score = 30
        body_za_trend = sum([cetnost[slovo] for slovo in c['slova'] if cetnost[slovo] > 1])
        score += body_za_trend * 1.2
        delka = len(c['summary']) if c['summary'] else 0
        if delka > 600: score += 20
        c['base_score'] = int(score)
        
    return clanky

# --- UI STRÁNKY ---
st.title("🎯 Gaming Topic Radar & Aggregator")
st.write("Scan global gaming media for specific topics.")

# Boční panel s informacemi a tlačítkem na promazání cache
with st.sidebar:
    st.header("Controls")
    st.write(f"Monitoring **{len(RSS_FEEDS)}** global feeds.")
    if st.button("🔄 Force Refresh Feeds"):
        st.cache_data.clear()
        st.success("Cache cleared! Next search will fetch fresh data.")

# Vyhledávací pole
hledane_tema = st.text_input("Type a game title, studio or console (e.g. Witcher, Xbox, Kojima):", "").strip()

if hledane_tema:
    with st.spinner("Scanning global feeds..."):
        vsechny_clanky = stahni_vsechny_clanky()
    
    hledane_lower = hledane_tema.lower()
    nalezeno = []
    
    for c in vsechny_clanky:
        obsah_text = (c['title'] + " " + (c['summary'] or "")).lower()
        if hledane_lower in obsah_text:
            final_score = c['base_score']
            if hledane_lower in c['title'].lower():
                final_score += 30 # Extra bonus za shodu přímo v nadpisu
            
            nalezeno.append({
                'title': c['title'],
                'source': c['source'],
                'link': c['link'],
                'score': final_score,
                'summary': c['summary']
            })
            
    nalezeno.sort(key=lambda x: x['score'], reverse=True)
    
    st.success(f"Found {len(nalezeno)} articles for **'{hledane_tema}'**")
    st.write("---")
    
    for c in nalezeno:
        col1, col2 = st.columns([6, 1])
        with col1:
            st.markdown(f"### [{c['title']}]({c['link']})")
            st.caption(f"**Source:** {c['source']}")
            if c['summary']:
                cistotext = re.sub('<[^<]+?>', '', c['summary'])[:250]
                st.write(f"{cistotext}...")
        with col2:
            st.metric(label="Relevance", value=f"{c['score']} pts")
        st.write("---")
else:
    st.info("Enter a keyword above to start searching.")
