import json
import os
from methods.data_parsing_methods import Base_data_method 
from collections import defaultdict
import random
json_dir = os.path.join("data", "scryfall_bulk_data")
images_dir = os.path.join("data", "cards_image_gallery")
label_dir = os.path.join("data", "labels") 
os.makedirs(label_dir, exist_ok=True)

cards = Base_data_method.parse_large_json(os.path.join(json_dir,"all_cards.json"))

# Filtrage des cartes en anglais et regroupement par layout
filtered_cards = defaultdict(list)
for card in cards.values():
    image_exist = card.get_images()
    if card.language == "en" and image_exist:  # Vérifie si la carte a du texte imprimé en anglais
        filtered_cards[card.layout].append(card)

# Sélectionner 100 cartes au maximum par layout
sampled_cards = {}
for layout, layout_cards in filtered_cards.items():
    sampled_cards[layout] = random.sample(layout_cards, min(100, len(layout_cards)))

# Conversion en une liste unique
final_sample = [card for cards_list in sampled_cards.values() for card in cards_list]


# Génération des annotations
for card in final_sample:
    images = card.get_images()
    if not images:
        continue
    
    for url, image_filename, statut in images:
        image_path = os.path.join(images_dir, image_filename)
        label_filename = os.path.join(label_dir, f"{card.id}.txt")
        
        # Vérifier si l'image existe
        if not os.path.exists(image_path):
            continue

        # Gestion des versions imprimées
        if card.language == "en":
            printed_text = card.oracle_text_front or ""
            printed_name = card.name_front or ""
            printed_type_line = card.type_line_front or ""
        else:
            printed_text = card.printed_text or card.oracle_text_front or ""
            printed_name = card.printed_name or card.name_front or ""
            printed_type_line = card.printed_type_line or card.type_line_front or ""

        # Récupération des informations de la carte
        attributes = {
            "0": card.name_front,
            "1": card.mana_cost_front,
            "2": card.artist,
            "3": card.rarity,
            "4": card.collector_number,
            "5": card.language,
            "6": card.flavor_text,
            "7": printed_text,
            "8": printed_name,
            "9": printed_type_line,
        }
        
        # Ajouter les informations de la face arrière si applicable
        if card.layout in {"transform", "modal_dfc", "double_faced_token", "adventure", "split", "flip"}:
            attributes.update({
                "10": card.name_back,
                "11": card.mana_cost_back,
                "12": card.type_line_back,
                "13": ",".join(card.colors_back) if card.colors_back else "",
                "14": card.oracle_text_back or "",
            })

        # Écriture du fichier d’annotation
        with open(label_filename, "w", encoding="utf-8") as f:
            for key, value in attributes.items():
                if value:
                    f.write(f"{key} {value}\n")