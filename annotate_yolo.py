import json
import os
from methods.data_parsing_methods import Base_data_method 
from collections import defaultdict
import random
import shutil
json_dir = os.path.join("data", "scryfall_bulk_data")
images_dir = os.path.join("data", "cards_image_gallery")
label_dir = os.path.join("data","yolo_anotate", "labels") 
image_label_dir = os.path.join("data","yolo_anotate", "images") 
os.makedirs(label_dir, exist_ok=True)
os.makedirs(image_label_dir, exist_ok=True)
cards = Base_data_method.parse_large_json(os.path.join(json_dir,"all_cards.json"))
cards["018830b2-dff9-45f3-9cc2-dc5b2eec0e54"]
# Filtrage des cartes en anglais et regroupement par layout
filtered_cards = defaultdict(list)
for card in cards.values():
    image_exist = card.get_images()
    if card.language == "en" and image_exist:  # Vérifie si la carte a du texte imprimé en anglais
        filtered_cards[card.layout].append(card)

# Sélectionner 100 cartes au maximum par layout
sampled_cards = {}
for layout, layout_cards in filtered_cards.items():
    sorted_cards = sorted(layout_cards, key=lambda c: c.id)  # Trier par ID ou un autre critère
    sampled_cards[layout] = random.sample(sorted_cards, min(100, len(sorted_cards)))

# Conversion en une liste unique
final_sample = [card for cards_list in sampled_cards.values() for card in cards_list]

# Génération des annotations
for card in final_sample:
    images = card.get_images()
    if not images:
        continue
    for url, image_filename, statut in images:
        image_path = os.path.join(images_dir, image_filename)
        image_dest_path = os.path.join(image_label_dir, image_filename)
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
        # Définition des attributs sous forme de liste
        if "_back.jpg" in image_filename:
            print(card.id)
            print(image_filename)
            attributes = [
                card.name_back,
                card.mana_cost_back,
                card.artist,
                card.rarity,
                card.collector_number,
                card.language,
                card.flavor_text,
                card.oracle_text_back,  # Texte Oracle du dos
                card.type_line_back,  # Type du dos
                card.rarity_letter,
                "",  # Set symbol (vide)
                "",  # Copyright (vide)
                "",   # Cryptogramme (vide)
                ""# Text on card image and collector symbol
            ]
        else:
            attributes = [
                printed_name,
                card.mana_cost_front,
                card.artist,
                card.rarity,
                card.collector_number,
                card.language,
                card.flavor_text,
                printed_text,
                printed_type_line,
                card.rarity_letter,
                "",  # Set symbol (vide)
                "",  # Copyright (vide)
                "",   # Cryptogramme (vide)
                ""# Text on card image and collector symbol
            ]

        # Écriture du fichier d’annotation avec numérotation automatique
        with open(label_filename, "w", encoding="utf-8") as f:
            for idx, value in enumerate(attributes):
                f.write(f"{idx} {value}\n")

        shutil.copy(image_path, image_dest_path)



for card in cards.values():
    images = card.get_images()
    if card.set_name=='Unknown Event':
        print(card.image_uris_front.get("normal"))
    # if not images:
    #     continue
    # for url, image_filename, statut in images:
    #     if "_front.jpg" in image_filename:
    #         print(image_filename)

# from collections import Counter
# set_type_counts = Counter(card.set_type for card in cards.values())
