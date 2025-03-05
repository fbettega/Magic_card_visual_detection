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




for card in final_sample:
    card_id = card.id
    url, image_path, statut = card.get_images()[0]
    image_filename = os.path.join(images_dir, "cards_image_gallery")
    label_filename = os.path.join(label_dir, f"{card_id}.txt")
    
    # Vérifier si l'image existe
    if not os.path.exists(os.path.join(images_dir, image_filename)):
        continue  # Passer si l'image est absente

    # Récupérer les informations
    name = card.name
    mana_cost = card.mana_cost
    artist = card.artist
    rarity = card.rarity
    collector_number = card.collector_number
    language = card.language
    flavor_text = card.flavor_text 
    printed_text = card.printed_text 
    printed_name = card.printed_name 
    printed_type_line = card.printed_type_line 

    # Générer un fichier d’annotation YOLO
    with open(label_filename, "w", encoding="utf-8") as f:
        f.write(f"0 {name}\n")  # Classe "Nom de la carte"
        f.write(f"1 {mana_cost}\n")  # Classe "Coût en mana"
        f.write(f"2 {artist}\n")  # Classe "Artiste"
        f.write(f"3 {rarity}\n")  # Classe "Rareté"
        f.write(f"4 {collector_number}\n")  # Classe "Numéro de la carte"
        f.write(f"5 {language}\n")  # Classe "Langue"