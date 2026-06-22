import cloudscraper
from bs4 import BeautifulSoup
import json
import os
from datetime import datetime, timedelta

def main():
    url = "https://tospo-keiba.jp/news"
    db_file = "data.json"
    
    # 1. Charger la base de données existante
    articles = {}
    if os.path.exists(db_file) and os.path.getsize(db_file) > 4:
        with open(db_file, "r", encoding="utf-8") as f:
            articles = json.load(f)

    # 2. Récupérer les news
    scraper = cloudscraper.create_scraper()
    try:
        r = scraper.get(url, timeout=20)
        soup = BeautifulSoup(r.text, "html.parser")
        
        jst_now = datetime.utcnow() + timedelta(hours=9)
        date_str = jst_now.strftime("%d/%m/%Y")
        ts_str = jst_now.strftime("%Y-%m-%d %H:%M:%S")

        for a in soup.select("a[href*='/news/']"):
            href = a['href']
            if href.startswith('/'): href = "https://tospo-keiba.jp" + href
            
            # On prend le texte du lien ou de la balise titre
            titre = a.get_text(strip=True)
            if len(titre) > 20 and href not in articles:
                articles[href] = {"t": titre, "l": href, "dt": date_str, "ts": ts_str}
                print(f"Trouvé : {titre[:30]}")

    except Exception as e:
        print(f"Erreur : {e}")

    # 3. Sauvegarder (Top 100)
    sorted_items = sorted(articles.values(), key=lambda x: x.get('ts', ''), reverse=True)[:100]
    final_data = {i['l']: i for i in sorted_items}
    
    with open(db_file, "w", encoding="utf-8") as f:
        json.dump(final_data, f, ensure_ascii=False, indent=2)

    # 4. Générer l'HTML
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(f"<html><head><meta charset='UTF-8'><title>Keiba</title></head><body style='font-family:sans-serif;padding:20px;'>")
        f.write(f"<h1>🏇 Keiba News</h1>")
        for a in sorted_items:
            f.write(f"<div style='margin-bottom:15px;'><a href='{a['l']}' style='font-weight:bold;'>{a['t']}</a><br><small>{a['dt']}</small></div>")
        f.write("</body></html>")

if __name__ == "__main__":
    main()
