import os
import ijson
import requests
from common_class.Cards import Card
import json
from concurrent.futures import ThreadPoolExecutor

class Base_data_method:
    ########################################################
    # download image from cards class
    def is_valid_image(self, url: str,image_status: str) -> bool:
        """Checks if the image URL is valid, avoiding placeholder images."""
        if not url or image_status in {"missing", "placeholder"}:
            return False
        
        forbidden_patterns = {"missing", "placeholder", "en/normal/back"}

        return not any(pattern in url for pattern in forbidden_patterns) 

    # Fonction pour télécharger une image
    def download_card_images(self,cards, output_dir, max_workers=8):
        """Télécharge les images de toutes les cartes fournies."""
        os.makedirs(output_dir, exist_ok=True)
        existing_files = set(os.listdir(output_dir))  # Set de noms de fichiers uniquement

        def download_image(url, filename,image_status):
            if filename in existing_files:  # Vérification rapide
                return
            
            if not self.is_valid_image(url,image_status):
                return
            
            try:
                response = requests.get(url, timeout=5)
                if response.status_code == 200:
                    file_path = os.path.join(output_dir, filename)
                    with open(file_path, "wb") as file:
                        file.write(response.content)
                    existing_files.add(filename)  # Mise à jour du cache local
                else:
                    print(f"❌ Failed to download: {url} (HTTP {response.status_code})")
            except requests.RequestException as e:
                print(f"❌ Failed to download {url}: {e}")

        images = []
        for card in cards:
            for url, filename in card.get_images():
                images.append((url, filename, card.image_status))

        # Téléchargement en parallèle
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            executor.map(lambda img: download_image(*img), images)

    ########################################################
    # download Data and parse json
    # Fonction pour parser un gros JSON et stocker les cartes dans une liste
    def parse_large_json(file_path):
        cards_list = []
        with open(file_path, 'r', encoding='utf-8') as f:
            for item in ijson.items(f, "item"):
                cards_list.append(Card(item))
        return cards_list


    def download_all_cards(output_dir="data/scryfall_bulk_data"):
        url = "https://api.scryfall.com/bulk-data"
        response = requests.get(url)

        if response.status_code != 200:

            print(f"Error retrieving data: {response.status_code}")

            return    

        data = response.json()

        os.makedirs(output_dir, exist_ok=True)
        all_cards = next((item for item in data["data"] if item["type"] == "all_cards"), None)

        if all_cards:
            name = all_cards["type"]
            download_url = all_cards["download_uri"]
            file_path = os.path.join(output_dir, f"{name}.json")

            print(f"Downloading {name}...")

            file_response = requests.get(download_url)

            if file_response.status_code == 200:
                with open(file_path, "wb") as f:
                    f.write(file_response.content)
                print(f"✅ {name} successfully downloaded!")
            else:
                print(f"❌ Failed to download {name}")

        else:

            print("❌ 'All Cards' not found in Scryfall data")

 

