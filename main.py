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

    print(f"--- Tentative de scraping : {URL} ---")
    
    # Simulation d'un navigateur réel
    scraper = cloudscraper.create_scraper(
        browser={
            'browser': 'chrome',
            'platform': 'windows',
            'desktop': True
        }
    )

    try:
        response = scraper.get(URL, timeout=30)
        if response.status_code != 200:
            print(f"Erreur HTTP : {response.status_code}")
            return {}

        soup = BeautifulSoup(response.text, "html.parser")
        
        # On cherche tous les liens de news
        found_links = soup.select("a[href*='/news/']")
        print(f"Liens potentiels trouvés : {len(found_links)}")

        for a in found_links:
            href = a['href']
            if href.startswith('/'): href = "https://tospo-keiba.jp" + href
            
            # On cherche le titre le plus propre possible
            # On regarde d'abord dans les classes connues, sinon on prend le texte du lien
            title_tag = a.select_one(".p-news-list__title, .c-post-card__title, h3, p, span")
            titre = title_tag.get_text(strip=True) if title_tag else a.get_text(strip=True)

            if len(titre) > 15 and "/news/" in href and not href.endswith("/news"):
                if href not in articles:
                    articles[href] = {
                        "t": titre,
                        "l": href,
                        "dt": date_str,
                        "ts": ts_str
                    }
    except Exception as e:
        print(f"Erreur pendant le scraping : {e}")
    
    print(f"Articles valides extraits : {len(articles)}")
    return articles

def main():
    db_file = "data.json"
    all_articles = {}

    # --- SÉCURITÉ CHARGEMENT JSON ---
    if os.path.exists(db_file) and os.path.getsize(db_file) > 0:
        try:
            with open(db_file, "r", encoding="utf-8") as f:
                all_articles = json.load(f)
        except Exception as e:
            print(f"Note: Impossible de lire le JSON existant ({e}). On repart à zéro.")
            all_articles = {}

    # --- RÉCUPÉRATION ---
    new_data = get_keiba_news()
    
    if new_data:
        # Fusion
        for url, info in new_data.items():
            if url not in all_articles:
                all_articles[url] = info
        
        # Tri et limitation aux 100 derniers
        sorted_keys = sorted(all_articles.keys(), key=lambda x: all_articles[x].get('ts', ''), reverse=True)
        final_db = {k: all_articles[k] for k in sorted_keys[:100]}
        
        # Sauvegarde JSON
        with open(db_file, "w", encoding="utf-8") as f:
            json.dump(final_db, f, ensure_ascii=False, indent=2)

        # Génération HTML simple
        jst_now = datetime.utcnow() + timedelta(hours=9)
        now_f = jst_now.strftime("%d/%m %H:%M")
        
        with open("index.html", "w", encoding="utf-8") as f:
            f.write(f"<html><head><meta charset='UTF-8'><meta name='viewport' content='width=device-width, initial-scale=1.0'><title>Keiba</title><style>body{{font-family:sans-serif;padding:15px;background:#f9f9f9}} .art{{background:white;padding:15px;margin-bottom:10px;border-radius:8px;box-shadow:0 1px 3px rgba(0,0,0,0.1)}} a{{color:#1b5e20;text-decoration:none;font-weight:bold}} .meta{{font-size:0.8rem;color:#777;margin-top:5px}}</style></head><body>")
            f.write(f"<h2 style='color:#1b5e20'>🏇 Keiba News ({now_f})</h2>")
            for url in sorted_keys[:100]:
                a = all_articles[url]
                f.write(f"<div class='art'><a href='{a['l']}' target='_blank'>{a['t']}</a><div class='meta'>{a['dt']}</div></div>")
            f.write("</body></html>")
            
        print("Mise à jour effectuée avec succès.")
    else:
        print("ÉCHEC : Aucun article n'a pu être récupéré.")

if __name__ == "__main__":
    main()
