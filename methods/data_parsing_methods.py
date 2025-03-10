import os
import shutil
from PIL import Image
import numpy as np
import ijson
import requests
from common_class.Cards import Card
import os
import shutil
import numpy as np
import cv2
from concurrent.futures import ProcessPoolExecutor

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
        bad_set_type = {
            "minigame",'funny','archenemy'
                        }
        # remove token emblem art series planar minigame custom cards ('Unknown Event')
        exclude_layout = {'vanguard','scheme',
                          'art_series','planar'}
        with open(file_path, 'r', encoding='utf-8') as f:
            for item in ijson.items(f, "item"):
                card_name = item.get("name", "")
                set_type = item.get("set_type", "")
                set_code = item.get("set", "")
                set_name = item.get("set_name", "")
                # remove token in first place 

                if item.get("oversized", False) or item.get("digital", False) or set_type in bad_set_type or item.get("layout", "") in exclude_layout:  #  or set_name == 'Unknown Event'
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
    def is_card_back(image_path, reference_histograms, threshold=0.90):
        """Vérifie si une image correspond à l'un des dos de carte de référence."""
        try:
            if not os.path.isfile(image_path):
                return False

            img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
            if img is None:
                return False  # Image non lisible

            img = cv2.resize(img, (100, 100))
            hist_img = cv2.calcHist([img], [0], None, [256], [0, 256]).flatten()
            hist_img /= np.linalg.norm(hist_img)  # Normalisation

            # Vérification avec les références
            return any(np.dot(hist_img, hist_ref) > threshold for hist_ref in reference_histograms)
        except Exception as e:
            print(f"Erreur lors de la vérification de {image_path} : {e}")
            return False


    def load_reference_histograms(back_card_references):
        """Charge une seule fois les histogrammes des dos de carte."""
        reference_histograms = []
        for ref_path in back_card_references:
            ref = cv2.imread(ref_path, cv2.IMREAD_GRAYSCALE)
            if ref is None:
                print(f"⚠️ Impossible de charger l'image de référence : {ref_path}")
                continue

            ref = cv2.resize(ref, (100, 100))
            hist_ref = cv2.calcHist([ref], [0], None, [256], [0, 256]).flatten()
            hist_ref /= np.linalg.norm(hist_ref)  # Normalisation
            reference_histograms.append(hist_ref)
        
        if not reference_histograms:
            raise ValueError("Aucune image de référence valide n'a été chargée.")
        
        return reference_histograms


    def detect_and_move_back(image_path, reference_histograms, bad_images_dir):
        """Détecte si une image est un dos de carte et la déplace si nécessaire."""
        if Base_data_method.is_card_back(image_path, reference_histograms):
            new_path = os.path.join(bad_images_dir, os.path.basename(image_path))
            shutil.move(image_path, new_path)  # Déplacement
            return image_path
        return None

    @staticmethod
    def move_card_backs_parallel(images_dir, back_references, bad_images_dir, max_workers=8):
        """Parallélise la détection et le déplacement des dos de cartes."""
        os.makedirs(bad_images_dir, exist_ok=True)

        # Charger les histogrammes des dos de carte une seule fois
        reference_histograms = Base_data_method.load_reference_histograms(back_references)

        # Liste des fichiers
        image_paths = [entry.path for entry in os.scandir(images_dir) if entry.is_file()]

        # ProcessPoolExecutor pour le multi-processing
        with ProcessPoolExecutor(max_workers=max_workers) as executor:
            results = executor.map(
                Base_data_method.detect_and_move_back,
                image_paths,  # Fichiers images
                [reference_histograms] * len(image_paths),  # Références partagées
                [bad_images_dir] * len(image_paths)  # Dossier de destination
            )

        # Récupération des fichiers déplacés
        moved_files = [res for res in results if res]

        print(f"✅ {len(moved_files)} dos de cartes déplacés vers {bad_images_dir}.")
