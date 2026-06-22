import requests
from bs4 import BeautifulSoup
import json
import os
from datetime import datetime, timedelta

# On se fait passer pour Googlebot, le seul robot que les sites ne bloquent jamais
HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)"
}

# L'URL du Sitemap qui contient les derniers articles
SITEMAP_URL = "https://tospo-keiba.jp/sitemap-posts-1.xml"

def get_keiba_from_xml():
    articles = {}
    jst_now = datetime.utcnow() + timedelta(hours=9)
    date_str = jst_now.strftime("%d/%m/%Y")
    ts_str = jst_now.strftime("%Y-%m-%d %H:%M:%S")

    print(f"--- Lecture du Sitemap : {SITEMAP_URL} ---")
    try:
        r = requests.get(SITEMAP_URL, headers=HEADERS, timeout=20)
        # On utilise le parseur XML
        soup = BeautifulSoup(r.text, "xml")
        
        # Dans un sitemap, chaque article est dans une balise <url>
        items = soup.find_all("url")
        print(f"Nombre d'entrées trouvées dans le Sitemap : {len(items)}")

        for item in items:
            link = item.find("loc").text if item.find("loc") else ""
            
            # On ne garde que les liens qui contiennent '/news/'
            if "/news/" in link:
                # Dans un sitemap, le titre n'est pas écrit. 
                # On va le générer proprement à partir de l'URL pour le moment
                # Exemple : /news/2024-une-course-incroyable -> "2024 une course incroyable"
                slug = link.split("/")[-1]
                titre = slug.replace("-", " ").capitalize()

                if link not in articles:
                    articles[link] = {
                        "t": titre,
                        "l": link,
                        "dt": date_str,
                        "ts": ts_str
                    }
        
        # Si on a des liens, on essaie d'aller chercher le VRAI titre sur la page de l'article 
        # (Seulement pour les 5 derniers pour ne pas être bloqué)
        for url in list(articles.keys())[:5]:
            try:
                res = requests.get(url, headers=HEADERS, timeout=5)
                s = BeautifulSoup(res.text, "html.parser")
                real_title = s.find("h1").get_text(strip=True) if s.find("h1") else None
                if real_title:
                    articles[url]["t"] = real_title
                    print(f"Titre récupéré : {real_title[:40]}...")
            except:
                continue

    except Exception as e:
        print(f"ERREUR : {e}")
    
    return articles

def write_html(filename, data):
    jst_now = datetime.utcnow() + timedelta(hours=9)
    now_full = jst_now.strftime("%d/%m %H:%M")
    sorted_articles = sorted(data.values(), key=lambda x: x.get('ts', ''), reverse=True)

    with open(filename, "w", encoding="utf-8") as f:
        f.write("<!DOCTYPE html><html lang='ja'><head><meta charset='UTF-8'><meta name='viewport' content='width=device-width, initial-scale=1.0'><title>🏇 Keiba XML</title><style>body{font-family:sans-serif;background:#f0f2f5;padding:15px;margin:0}.header{background:#1b5e20;color:white;padding:15px;border-radius:10px;margin-bottom:15px}.article{background:white;padding:15px;margin-bottom:10px;border-radius:8px;border-left:5px solid #ffc107;box-shadow:0 2px 4px rgba(0,0,0,0.1)}a{text-decoration:none;color:#1b5e20;font-weight:bold;font-size:1.1rem;display:block}.meta{font-size:0.75rem;color:#777;margin-top:8px}</style></head><body>")
        f.write(f"<div class='header'><h1>🏇 Keiba News (Sitemap)</h1><p>Dernière mise à jour : {now_full} (JST)</p></div>")
        for a in sorted_articles:
            f.write(f"<div class='article'><a href='{a['l']}' target='_blank'>{a['t']}</a><div class='meta'>{a['dt']}</div></div>")
        f.write("</body></html>")

def main():
    db_file = "data.json"
    all_articles = json.load(open(db_file, "r", encoding="utf-8")) if os.path.exists(db_file) else {}

    new_data = get_keiba_from_xml()
    
    if new_data:
        for url, info in new_data.items():
            if url not in all_articles:
                all_articles[url] = info
        
        with open(db_file, "w", encoding="utf-8") as f:
            json.dump(all_articles, f, ensure_ascii=False, indent=2)
        write_html("index.html", all_articles)
        print(f"Succès : {len(all_articles)} articles au total.")
    else:
        print("Échec : Aucun article trouvé dans le Sitemap.")

if __name__ == "__main__":
    main()
