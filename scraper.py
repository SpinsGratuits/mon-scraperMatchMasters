import json
import os
from datetime import datetime, date
import cloudscraper
from bs4 import BeautifulSoup
import re

# 1. URL du site cible et nom de votre fichier JSON
url = "https://mosttechs.com/match-masters-free-boosters/"
filename = "scrapmatchmasters.json"

# --- CHARGEMENT DE L'HISTORIQUE PRÉCÉDENT ---
anciens_liens = {}
if os.path.exists(filename):
    try:
        with open(filename, mode="r", encoding="utf-8") as json_file:
            data_chargee = json.load(json_file)
            if isinstance(data_chargee, list):
                for item in data_chargee:
                    if "lienurl" in item:
                        anciens_liens[item["lienurl"]] = item
    except Exception as e:
        print(f"Impossible de lire le fichier JSON précédent (il sera recréé) : {e}")

scraper = cloudscraper.create_scraper(browser={'browser': 'chrome', 'platform': 'windows', 'mobile': False})

try:
    response = scraper.get(url)
    status_code = response.status_code
    html_text = response.text
except Exception as e:
    status_code = 500
    html_text = ""
    print(f"Erreur lors du contournement du blocage : {e}")

if status_code == 200:
    soup = BeautifulSoup(html_text, "html.parser")
    
    now = datetime.now()
    date_now_str = now.strftime("%d/%m/%Y à %H:%M")
    date_du_jour_str = now.strftime("%d/%m/%Y")
    heure_actuelle_str = now.strftime("%H:%M")
    
    json_data = []
    
    all_links = soup.find_all("a", href=True)
    
    for link in all_links:
        href = link["href"]
        
        if "://matchmasters.com" in href:
            if any(item["lienurl"] == href for item in json_data):
                continue
                
            # --- AJOUT : LIMITATION À 20 LIENS MAXIMUM ---
            if len(json_data) >= 20:
                break
                
            parent_text = link.find_parent().get_text(separator=" ").strip() if link.find_parent() else ""
            if len(parent_text) < 15 and link.find_parent().find_parent():
                parent_text = link.find_parent().find_parent().get_text(separator=" ").strip()
            
            clean_text = " ".join(parent_text.split())
            recompense_match = re.search(r'\d+[\s\w]*(?:tours|spins|pieces|coins|tours\s*&\s*pièces)', clean_text, re.IGNORECASE)
            type_recompense = recompense_match.group(0).strip() if recompense_match else "Tours / Pièces"
            type_recompense = re.sub(r'^(?:Cliquez ici pour recevoir|Récupérer)\s*', '', type_recompense, flags=re.IGNORECASE)
            
            if href in anciens_liens:
                json_data.append({
                    "date_scraping": anciens_liens[href].get("date_scraping", date_now_str), 
                    "date": anciens_liens[href].get("date", date_du_jour_str), 
                    "heure": anciens_liens[href].get("heure", "00:00"),
                    "recompense": type_recompense, 
                    "lienurl": href,
                    "badge": ""  
                })
            else:
                json_data.append({
                    "date_scraping": date_now_str, 
                    "date": date_du_jour_str, 
                    "heure": heure_actuelle_str,
                    "recompense": type_recompense, 
                    "lienurl": href,
                    "badge": "NEW"  
                })

    if not json_data:
        json_data.append({
            "date_scraping": date_now_str,
            "statut": "VIDE",
            "message": "Aucun lien trouvé sur la page. Vérifiez manuellement le site."
        })
        print("Aucun lien extrait.")
    else:
        print(f"Succès total ! {len(json_data)} liens traités (Anciens préservés + Nouveaux ajoutés).")

    with open(filename, mode="w", encoding="utf-8") as json_file:
        json.dump(json_data, json_file, indent=4, ensure_ascii=False)
            
else:
    print(f"Erreur d'accès réseau (Code {status_code}). Le site blocks toujours.")
