import os
import shutil
from PIL import Image
import numpy as np
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
        
        forbidden_patterns = {"missing", "placeholder", "en/normal/back", "default_back"}
        return not any(pattern in url for pattern in forbidden_patterns) 

    # Fonction pour télécharger une image
    def download_card_images(self,cards: dict[str, Card], output_dir: str, bad_image_dir: str, max_workers=8):
        """Télécharge les images de toutes les cartes fournies."""
        os.makedirs(output_dir, exist_ok=True)
        os.makedirs(bad_image_dir, exist_ok=True)
        existing_files = set(os.listdir(output_dir)) | set(os.listdir(bad_image_dir))  # Set de noms de fichiers uniquement

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
        for card in cards.values():  # Correction : itérer sur les valeurs
            images.extend(card.get_images())

        # Téléchargement en parallèle
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [executor.submit(download_image, url, filename, image_status) for url, filename , image_status in images]
            for future in futures:
                future.result()

    ########################################################
    # download Data and parse json
    # Fonction pour parser un gros JSON et stocker les cartes dans une liste
    def parse_large_json(file_path:str) -> dict[str, Card]:
        cards_dict = {}
        # remove minigame and funny set_tyupe
        bad_set_type = {"minigame",'funny'}
        # remove token emblem art series planar minigame custom cards ('Unknown Event')
        exclude_layout = {'token','art_series','emblem','planar'}
        with open(file_path, 'r', encoding='utf-8') as f:
            for item in ijson.items(f, "item"):
                card_name = item.get("name", "")
                set_type = item.get("set_type", "")
                set_code = item.get("set", "")
                set_name = item.get("set_name", "")
                # remove token in first place 
                if item.get("digital", False) or set_type in bad_set_type or item.get("layout", "") in exclude_layout or set_name == 'Unknown Event': 
                    continue
                elif set_name.startswith("World Championship") and set_code.startswith("wc") and (card_name.endswith(" Bio") or card_name.endswith(" Decklist")):
                    continue
                else:
                    cards_dict[item["id"]] = Card(item)
        return cards_dict


    def download_all_cards(output_dir:str):
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
    #######################################################################
    def is_card_back(image_path: str, back_card_reference: str, threshold=0.95) -> bool:
        """Compare une image avec une référence du dos de carte et retourne True si c'est un dos de carte."""
        try:
        # Vérifie si c'est bien un fichier image
            if not os.path.isfile(image_path):
                print(f"⚠️ Fichier ignoré (non valide) : {image_path}")
                return False

            img = Image.open(image_path).convert("L").resize((100, 100))  # Grayscale + Resize
            ref = Image.open(back_card_reference).convert("L").resize((100, 100))

            hist_img = np.array(img.histogram())
            hist_ref = np.array(ref.histogram())

            # Similarité cosinus entre les histogrammes
            similarity = np.dot(hist_img, hist_ref) / (np.linalg.norm(hist_img) * np.linalg.norm(hist_ref))
            return similarity > threshold
        except Exception as e:
            print(f"Erreur lors de la vérification de {image_path} : {e}")
            return False

    def detect_and_move_back(self,image_entry, back_reference, bad_images_dir):
        """Détecte si l'image est un dos de carte et la déplace si nécessaire."""
        if image_entry.name == ".gitignore":
            return None  # Ignorer .gitignore
        image_path = image_entry.path
        if Base_data_method.is_card_back(image_path, back_reference):
            new_path = os.path.join(bad_images_dir, image_entry.name)
            shutil.move(image_path, new_path)  # Déplacement
            return image_entry.name  # Retourne le nom des fichiers déplacés
        return None

    def move_card_backs_parallel(self,images_dir, back_reference, bad_images_dir, max_workers=8):
        """Parallélise la détection et le déplacement des dos de cartes."""
        os.makedirs(bad_images_dir, exist_ok=True)
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Scan rapide des fichiers (sans précharger la liste en mémoire)
            with os.scandir(images_dir) as entries:
                futures = [executor.submit(self.detect_and_move_back, entry, back_reference, bad_images_dir)
                        for entry in entries if entry.is_file()]

            # Récupération des fichiers déplacés
            moved_files = [future.result() for future in futures if future.result()]

        print(f"✅ {len(moved_files)} dos de cartes déplacés vers {bad_images_dir}.")
