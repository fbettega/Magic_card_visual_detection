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
        # manque les stat loyalty force et endu
        if "_back.jpg" in image_filename:
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
                card.security_stamp,   # Cryptogramme (vide)
                card.watermark_back # Text on card image and collector symbol
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
                card.security_stamp,   # Cryptogramme (vide)
                card.watermark_front# Text on card image and collector symbol
            ]

        # Écriture du fichier d’annotation avec numérotation automatique
        with open(label_filename, "w", encoding="utf-8") as f:
            for idx, value in enumerate(attributes):
                _ = f.write(f"{idx} {value}\n")
        _ = shutil.copy(image_path, image_dest_path)


cards['8bcf942f-5afd-414e-a50d-00d884fe59da']
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
# set_type_counts = Counter(card.layout for card in cards.values())

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