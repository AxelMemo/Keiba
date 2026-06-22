import cloudscraper
from bs4 import BeautifulSoup
import json
import os
from datetime import datetime, timedelta

# CONFIGURATION
URL = "https://tospo-keiba.jp/news"

def get_keiba_news():
    articles = {}
    jst_now = datetime.utcnow() + timedelta(hours=9)
    date_str = jst_now.strftime("%d/%m/%Y")
    ts_str = jst_now.strftime("%Y-%m-%d %H:%M:%S")

    print(f"--- Tentative avec Cloudscraper sur {URL} ---")
    
    # On crée un scraper qui contourne les protections Cloudflare
    scraper = cloudscraper.create_scraper(
        browser={
            'browser': 'chrome',
            'platform': 'windows',
            'desktop': True
        }
    )

    try:
        response = scraper.get(URL, timeout=20)
        # Si le site renvoie quand même une erreur
        if response.status_code != 200:
            print(f"Erreur du site : {response.status_code}")
            return {}

        soup = BeautifulSoup(response.text, "html.parser")
        
        # On cible les articles. Tospo utilise souvent ces structures :
        # Chaque article est dans un lien qui contient /news/
        items = soup.find_all("a", href=True)
        
        for a in items:
            href = a['href']
            if "/news/" in href and not href.endswith("/news"):
                if href.startswith('/'): href = "https://tospo-keiba.jp" + href
                
                # On cherche le titre dans les classes classiques de Tospo
                title_tag = a.select_one(".p-news-list__title, .c-post-card__title, h3, p")
                
                if title_tag:
                    titre = title_tag.get_text(strip=True)
                    # On évite les textes trop courts (menus, tags)
                    if len(titre) > 15:
                        if href not in articles:
                            articles[href] = {
                                "t": titre,
                                "l": href,
                                "dt": date_str,
                                "ts": ts_str
                            }

    except Exception as e:
        print(f"Erreur Cloudscraper : {e}")
    
    print(f"Articles trouvés : {len(articles)}")
    return articles

def write_html(filename, data):
    jst_now = datetime.utcnow() + timedelta(hours=9)
    now_full = jst_now.strftime("%d/%m %H:%M")
    sorted_articles = sorted(data.values(), key=lambda x: x.get('ts', ''), reverse=True)

    with open(filename, "w", encoding="utf-8") as f:
        f.write("<!DOCTYPE html><html lang='ja'><head><meta charset='UTF-8'><meta name='viewport' content='width=device-width, initial-scale=1.0'><title>🏇 Keiba Cloud</title><style>body{font-family:sans-serif;background:#f0f2f5;padding:15px;margin:0}.header{background:#d32f2f;color:white;padding:15px;border-radius:10px;margin-bottom:15px}.article{background:white;padding:15px;margin-bottom:10px;border-radius:8px;border-left:5px solid #d32f2f;box-shadow:0 2px 4px rgba(0,0,0,0.1)}a{text-decoration:none;color:#333;font-weight:bold;font-size:1.1rem;display:block}.meta{font-size:0.75rem;color:#777;margin-top:8px}</style></head><body>")
        f.write(f"<div class='header'><h1>🏇 Keiba News</h1><p>Dernière mise à jour : {now_full} (JST)</p></div>")
        for a in sorted_articles:
            f.write(f"<div class='article'><a href='{a['l']}' target='_blank'>{a['t']}</a><div class='meta'>{a['dt']}</div></div>")
        f.write("</body></html>")

def main():
    db_file = "data.json"
    all_articles = json.load(open(db_file, "r", encoding="utf-8")) if os.path.exists(db_file) else {}

    new_data = get_keiba_news()
    
    if new_data:
        # Fusionner les nouveaux articles
        for url, info in new_data.items():
            if url not in all_articles:
                all_articles[url] = info
        
        # Garder seulement les 200 plus récents pour le JSON
        all_articles = dict(list(all_articles.items())[-200:])
        
        with open(db_file, "w", encoding="utf-8") as f:
            json.dump(all_articles, f, ensure_ascii=False, indent=2)
            
        write_html("index.html", all_articles)
        print("Mise à jour réussie.")
    else:
        print("Aucun nouvel article trouvé.")

if __name__ == "__main__":
    main()
