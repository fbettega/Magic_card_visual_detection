import os
import ijson
import requests
from common_class.Cards import Card
import json

class Base_data_method:
    ########################################################
    # download image from cards class
    def is_valid_image(self, url: str) -> bool:
        """Checks if the image URL is valid, avoiding placeholder images."""
        if not url:
            return False
        
        forbidden_patterns = {"missing", "placeholder", "en/normal/back"}
        return not any(pattern in url for pattern in forbidden_patterns)

    # Fonction pour télécharger une image
    def download_card_image(self,cards:Card,output_dir:str):
        """Télécharge les images valides en évitant les placeholders."""
        os.makedirs(output_dir, exist_ok=True)
        images = cards.get_images()
        existing_files = set(os.listdir(output_dir))
        for url, filename in images:
            if filename in existing_files:
                continue  # Skip already downloaded files
            
            if not self.is_valid_image(url):
                continue  # Skip invalid images
            
            file_path = os.path.join(self.output_dir, filename)
            try:
                response = requests.get(url, stream=True, timeout=10)
                if response.status_code == 200:
                    with open(file_path, "wb") as file:
                        for chunk in response.iter_content(1024):
                            file.write(chunk)
                    existing_files.add(filename)  # Update cache
                else:
                    print(f"❌ Failed to download: {url} (HTTP {response.status_code})")
            except requests.RequestException as e:
                print(f"❌ Failed to download {url}: {e}")

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

 

