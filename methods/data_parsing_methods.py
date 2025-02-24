import os
import ijson
import requests
from common_class.Cards import Card
import json

class Base_data_method:
    # Fonction pour parser un gros JSON et stocker les cartes dans une liste
    def parse_large_json(file_path):
        cards_list = []
        with open(file_path, 'r', encoding='utf-8') as f:
            for item in ijson.items(f, "item"):
                cards_list.append(Card(item))
        return cards_list

    # Fonction pour télécharger une image
    def download_card_image(url,file_name,output_dir):
        if not url:
            return

        file_name = file_name.replace(" ", "_").replace("/", "_")  # Nettoyer le nom
        file_path = os.path.join(output_dir, file_name)

        if os.path.exists(file_path):
            # print(f"Image déjà téléchargée : {file_name}")
            return

        try:
            response = requests.get(url, stream=True)
            if response.status_code == 200:
                with open(file_path, "wb") as file:
                    for chunk in response.iter_content(1024):
                        file.write(chunk)
                # print(f"Téléchargé : {file_name}")
            else:
                print(f"Échec du téléchargement : {file_name}")
        except requests.RequestException as e:
            print(f"Erreur de téléchargement : {e}")


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

 

