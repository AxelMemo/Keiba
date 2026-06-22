import requests
from bs4 import BeautifulSoup
import json
import os
from datetime import datetime, timedelta

URL = "https://tospo-keiba.jp/news"
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

def get_keiba_news():
    articles = {}
    try:
        r = requests.get(URL, headers=HEADERS, timeout=15)
        soup = BeautifulSoup(r.text, "html.parser")
        # Sur Tospo Keiba, les articles sont souvent dans des balises 'a' avec une classe spécifique
        for item in soup.select("a[href*='/news/']"):
            title_tag = item.select_one(".p-news-list__title, h3, p")
            if title_tag:
                tit = title_tag.get_text().strip()
                link = item['href']
                if not link.startswith('http'):
                    link = "https://tospo-keiba.jp" + link
                
                if len(tit) > 10:
                    # On utilise l'URL comme clé unique pour éviter les doublons
                    articles[link] = {
                        "t": tit, 
                        "l": link, 
                        "ts": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    }
    except Exception as e:
        print(f"Erreur lors du scraping: {e}")
    return articles

def write_html(data):
    now = (datetime.utcnow() + timedelta(hours=9)).strftime("%d/%m %H:%M")
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(f"""
        <!DOCTYPE html>
        <html lang="ja">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Keiba News Chrono</title>
            <style>
                body {{ font-family: sans-serif; background: #eceff1; padding: 15px; }}
                .header {{ background: #1b5e20; color: white; padding: 15px; border-radius: 10px; margin-bottom: 20px; }}
                .article {{ background: white; padding: 15px; margin-bottom: 10px; border-radius: 8px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }}
                a {{ text-decoration: none; color: #1b5e20; font-weight: bold; font-size: 1.1rem; }}
                .time {{ font-size: 0.7rem; color: #666; margin-top: 5px; }}
            </style>
        </head>
        <body>
            <div class="header"><h1>🏇 Tospo Keiba News</h1><p>Dernière mise à jour (JST): {now}</p></div>
            <div id="news-list">
        """)
        for url, info in data.items():
            f.write(f"""
                <div class="article">
                    <a href="{info['l']}" target="_blank">{info['t']}</a>
                    <div class="time">Détecté le : {info['ts']}</div>
                </div>
            """)
        f.write("</div></body></html>")

def main():
    # Charger l'historique
    db_file = "data.json"
    if os.path.exists(db_file):
        with open(db_file, "r", encoding="utf-8") as f:
            all_articles = json.load(f)
    else:
        all_articles = {}

    # Récupérer les nouvelles news
    new_ones = get_keiba_news()
    
    # Fusionner (les nouveaux en premier)
    updated_db = {**new_ones, **all_articles}
    
    # Limiter à 200 articles pour ne pas alourdir
    final_db = dict(list(updated_db.items())[:200])

    # Sauvegarder et générer l'HTML
    with open(db_file, "w", encoding="utf-8") as f:
        json.dump(final_db, f, ensure_ascii=False, indent=2)
    
    write_html(final_db)

if __name__ == "__main__":
    main()
