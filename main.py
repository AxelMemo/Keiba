import requests
from bs4 import BeautifulSoup
import json
import os
from datetime import datetime, timedelta

# CONFIGURATION
URL = "https://tospo-keiba.jp/news"
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

def get_keiba_news():
    articles = {}
    jst_now = datetime.utcnow() + timedelta(hours=9)
    date_str = jst_now.strftime("%d/%m/%Y")
    ts_str = jst_now.strftime("%Y-%m-%d %H:%M:%S")

    print(f"--- Démarrage du scraping sur {URL} ---")
    try:
        r = requests.get(URL, headers=HEADERS, timeout=20)
        r.encoding = 'utf-8' # Force l'encodage japonais
        soup = BeautifulSoup(r.text, "html.parser")
        
        # On cherche tous les liens qui contiennent '/news/' dans l'URL
        linksFound = soup.find_all("a", href=True)
        print(f"Nombre de liens trouvés au total : {len(linksFound)}")

        for a in linksFound:
            href = a['href']
            # On ne garde que les liens vers les articles de news
            if "/news/" in href and not href.endswith("/news"):
                # Nettoyage de l'URL
                if href.startswith('/'): href = "https://tospo-keiba.jp" + href
                
                # Extraction du titre : on prend tout le texte dans le lien
                # et on nettoie les espaces/retours à la ligne
                titre_brut = a.get_text(separator=" ", strip=True)
                
                # Nettoyage : On enlève les préfixes comme "NEW" ou les dates de fin
                titre = titre_brut.replace("NEW", "").strip()
                # On tronque si le titre contient des dates à la fin (ex: 2026/06/22)
                titre = titre.split(' 202')[0] 

                if len(titre) > 15: # Un titre sérieux fait plus de 15 caractères
                    if href not in articles:
                        print(f"Article trouvé : {titre[:50]}...")
                        articles[href] = {
                            "t": titre,
                            "l": href,
                            "dt": date_str,
                            "ts": ts_str
                        }

    except Exception as e:
        print(f"ERREUR CRITIQUE : {e}")
    
    print(f"--- Scraping terminé : {len(articles)} articles valides trouvés ---")
    return articles

def write_html(filename, data):
    jst_now = datetime.utcnow() + timedelta(hours=9)
    now_full = jst_now.strftime("%d/%m %H:%M")
    
    # Tri par date (le plus récent d'abord)
    sorted_articles = sorted(data.values(), key=lambda x: x.get('ts', ''), reverse=True)

    with open(filename, "w", encoding="utf-8") as f:
        f.write("<!DOCTYPE html><html lang='ja'><head><meta charset='UTF-8'>")
        f.write("<meta name='viewport' content='width=device-width, initial-scale=1.0'>")
        f.write("<title>🏇 Keiba Chrono</title>")
        f.write("<style>body{font-family:sans-serif;background:#f0f2f5;padding:15px;margin:0} .header{background:#1b5e20;color:white;padding:20px;border-radius:12px;margin-bottom:20px;box-shadow:0 4px 6px rgba(0,0,0,0.1)} .article{background:white;padding:18px;margin-bottom:12px;border-radius:10px;border-left:6px solid #ffc107;box-shadow:0 2px 4px rgba(0,0,0,0.05)} a{text-decoration:none;color:#1b5e20;font-weight:bold;font-size:1.15rem;line-height:1.4;display:block} .meta{font-size:0.8rem;color:#777;margin-top:10px}</style></head><body>")
        f.write(f"<div class='header'><h1>🏇 Tospo Keiba News</h1><p>Dernière mise à jour : {now_full} (JST)</p></div>")
        
        for a in sorted_articles:
            f.write(f"<div class='article'><a href='{a['l']}' target='_blank'>{a['t']}</a><div class='meta'>Publié le {a['dt']}</div></div>")
        
        f.write("</body></html>")

def main():
    db_file = "data.json"
    
    # 1. Charger l'existant
    if os.path.exists(db_file):
        try:
            with open(db_file, "r", encoding="utf-8") as f:
                all_articles = json.load(f)
        except: all_articles = {}
    else:
        all_articles = {}

    # 2. Récupérer le neuf
    new_data = get_keiba_news()
    
    # 3. Fusionner si on a trouvé quelque chose (sécurité anti-vidage)
    if new_data:
        for url, info in new_data.items():
            if url not in all_articles:
                all_articles[url] = info
        
        # 4. Sauvegarder
        with open(db_file, "w", encoding="utf-8") as f:
            json.dump(all_articles, f, ensure_ascii=False, indent=2)
            
        # 5. Créer l'index
        write_html("index.html", all_articles)
        print("Fichiers mis à jour avec succès.")
    else:
        print("ALERTE : Aucun article trouvé. On ne touche à rien pour éviter d'effacer la base.")

if __name__ == "__main__":
    main()
