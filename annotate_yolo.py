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
    # remove scret lair in this version to remove strange non magic cards
    if not images or card.set_name =='Secret Lair Drop':
        continue
    for url, image_filename, statut in images:
        image_path = os.path.join(images_dir, image_filename)
        image_dest_path = os.path.join(image_label_dir, image_filename)
        label_filename = os.path.join(label_dir, f"{card.id}.txt")
        # Vérifier si l'image existe
        if not os.path.exists(image_path):
            continue

        is_back = "_back.jpg" in image_filename

        # Déterminer le suffixe en fonction de la face de la carte
        side = "back" if is_back else "front"

        # Récupérer les valeurs dynamiquement
        mana_cost = getattr(card, f"mana_cost_{side}", "") or ""
        watermark = getattr(card, f"watermark_{side}", "") or ""

        power = getattr(card, f"power_{side}", "") or ""
        toughness = getattr(card, f"toughness_{side}", "") or ""
        loyalty = getattr(card, f"loyalty_{side}", "") or "" 

        # Détermination de carac_result
        if power and toughness and loyalty:
            print(f"⚠️ WARNING: Card {printed_name} with power/toughness and loyalty.")

        if power and toughness:
            carac_result = f"{power}/{toughness}"
        elif loyalty:
            carac_result = loyalty
        else:
            carac_result = ""

        if card.language == "en":
            printed_text = getattr(card, f"oracle_text_{side}", "") or ""
            printed_name = getattr(card, f"name_{side}", "") or ""
            printed_type_line = getattr(card, f"type_line_{side}", "") or ""
        else:
            printed_text = getattr(card, f"printed_text_{side}", "") or ""
            printed_name = getattr(card, f"printed_name_{side}", "") or ""
            printed_type_line = getattr(card, f"printed_type_line_{side}", "") or ""

        # manque les stat loyalty force et endu
        attributes = [
            printed_name,
            mana_cost,
            card.artist,
            card.rarity,
            card.collector_number,
            card.language,
            card.flavor_text,
            carac_result,
            # to add card stat loyalty or pwoer / endu
            printed_text,  # Texte Oracle du dos
            printed_type_line,  # Type du dos
            card.rarity_letter,
            "",  # Set symbol (vide)
            "",  # Copyright (vide)
            card.security_stamp,   # Cryptogramme (vide)
            watermark # Text on card image and collector symbol
        ]

        # Écriture du fichier d’annotation avec numérotation automatique
        with open(label_filename, "w", encoding="utf-8") as f:
            for idx, value in enumerate(attributes):
                _ = f.write(f"{idx} {value}\n")
        _ = shutil.copy(image_path, image_dest_path)

##############################################################################################################
# debug
# Filtrage des cartes en anglais et regroupement par layout

debug_filtered_cards = defaultdict()
for card in cards.values():
    if not card.token:  # Vérifie si la carte a du texte imprimé en anglais
        debug_filtered_cards[card.id] = card

len(debug_filtered_cards)
from collections import Counter
set_type_counts = Counter(card.token for card in cards.values())
promo_type_counts = Counter(promo for card in debug_filtered_cards.values() for promo in card.promo_types)


max_count = 100
count = 0
for card in cards.values():
    images = card.get_images()
    if card.set_name=='Unknown Event':
        count += 1
        print(card.image_uris_front.get("normal"))
    if count > max_count:
        break
max_count = 100
count = 0

for card in debug_filtered_cards.values():
    if 'schinesealtart' in card.promo_types:
        count += 1
        print(card.image_uris_front.get("normal"))
    if count > max_count:
        break

debug_images_dir = os.path.join("data", "debug_image")   
os.makedirs(debug_images_dir, exist_ok=True)
max_count = 100
count = 0
for card in debug_filtered_cards.values():
    if 'playerrewards' in card.promo_types:
        images = card.get_images()
        if not images:
            continue
        count += 1
        image_path = os.path.join(images_dir, image_filename)
        for url, image_filename, statut in images:
            if not os.path.exists(image_path):
                continue
            image_dest_path = os.path.join(debug_images_dir, image_filename)
            
            _ = shutil.copy(image_path, image_dest_path)
    if count > max_count:
        break


# remove scret lair in this version to remove strange non magic cards

# >>> promo_type_counts
# Counter({'boosterfun': 36737, 'prerelease': 3707, 'datestamped': 3640, 
#          'promopack': 2727, 'mediainsert': 2310, 
#         'stamped': 2123, 'setpromo': 2081, 'surgefoil': 1538, 'ripplefoil': 1337,
#         'starterdeck': 1133, 'boxtopper': 1090, 'startercollection': 838,
#         'beginnerbox': 774, 'firstplacefoil': 772, 'bundle': 494, 'buyabox': 369,
#         'silverfoil': 369,  
#          'textured': 295, 'serialized': 294,
#         'doublerainbow': 287,  'magnified': 240, 'fnm': 227,
#         'halofoil': 211, 'thick': 200, 'judgegift': 174, 'rainbowfoil': 166,
#         'instore': 161,  'vault': 155, 
#         'ravnicacity': 135,  'release': 110, 'imagine': 108, 'doubleexposure': 107,
#         'embossed': 99, 'arenaleague': 84, 'gameday': 84,  'stepandcompleat': 76,
#         'raisedfoil': 72,   'wizardsplaynetwork': 64, 'manafoil': 60,
#         'convention': 56, 'premiereshop': 51, 'resale': 48, 'gilded': 48, 'storechampionship': 41,
#         'intropack': 40, 'fracturefoil': 40, 'concept': 37, 'oilslick': 25, 'brawldeck': 24, 'event': 24,
#         'neonink': 20, 'giftbox': 16, 'invisibleink': 14, 'duels': 14,
#         'glossy': 7, 
#         })
# playtest
# godzillaseries vault  draculaseries ravnicacity wizardsplaynetwork imagine

#  poster

# Card 
# 'jpwalker': 72,'scroll': 359,'schinesealtart': 72,
# 'upsidedown': 1, 'upsidedownback': 1
# 'draculaseries': 148,'godzillaseries': 160,'themepack': 333,'planeswalkerdeck': 2236, 'moonlitland': 5,'league': 6, 'bringafriend': 6, 
#         'commanderparty': 11, 'galaxyfoil': 10,'playpromo': 9,
#  'setextension': 9,'portrait': 280,'draftweekend': 9, 'alchemy': 7, 'confettifoil': 20, 
# Card with strange typo 
# 'dossier': 350, 
# some times not a cards 
# 'sldbonus': 336,'tourney': 296,'playerrewards': 53, 
# not cards
# 'poster': 80,'playtest': 123,
# end debug
##############################################################################################################

# suite

# from paddleocr import PaddleOCR
# import cv2

# ocr = PaddleOCR(use_angle_cls=True, lang="en")  # OCR en anglais

# def detect_text_regions(image_path):
#     """ Détecte les zones de texte et renvoie leurs coordonnées. """
#     image = cv2.imread(image_path)
#     results = ocr.ocr(image, cls=True)
    
#     annotations = []
    
#     for res in results:
#         for line in res:
#             bbox, text, confidence = line
#             x_min, y_min = int(bbox[0][0]), int(bbox[0][1])
#             x_max, y_max = int(bbox[2][0]), int(bbox[2][1])
#             annotations.append((x_min, y_min, x_max, y_max, text))
    
#     return annotations

# # Exemple sur une carte
# image_path = "dataset/images/12345678.jpg"
# annotations = detect_text_regions(image_path)

# for ann in annotations:
#     print(f"Texte: {ann[4]}, BBox: {ann[:4]}")

# import os

# class_mapping = {
#     "Nom": 0,
#     "Mana_Cost": 1,
#     "Artiste": 2,
#     "Rareté": 3,
#     "Numéro": 4,
#     "Langue": 5
# }

# def convert_to_yolo_format(image_path, annotations):
#     img = cv2.imread(image_path)
#     height, width, _ = img.shape

#     yolo_annotations = []
    
#     for x_min, y_min, x_max, y_max, text in annotations:
#         x_center = (x_min + x_max) / 2.0 / width
#         y_center = (y_min + y_max) / 2.0 / height
#         bbox_width = (x_max - x_min) / width
#         bbox_height = (y_max - y_min) / height

#         class_id = class_mapping.get(text, -1)  # Associer le texte à une classe
#         if class_id != -1:
#             yolo_annotations.append(f"{class_id} {x_center:.6f} {y_center:.6f} {bbox_width:.6f} {bbox_height:.6f}")
    
#     return yolo_annotations

# # Générer les annotations pour une image
# image_path = "dataset/images/12345678.jpg"
# annotations = detect_text_regions(image_path)
# yolo_annotations = convert_to_yolo_format(image_path, annotations)

# # Sauvegarde du fichier d’annotation YOLO
# label_path = "dataset/labels/12345678.txt"
# with open(label_path, "w") as f:
#     f.write("\n".join(yolo_annotations))

# print(f"Annotations YOLO enregistrées pour {image_path}.")