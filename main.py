import json
from methods.data_parsing_methods import Base_data_method    
import os

json_dir = os.path.join("data", "scryfall_bulk_data")
images_dir = os.path.join("data", "cards_image_gallery")
bad_images_dir = os.path.join("data", "bad_image")
back_reference = os.path.join("data", "other_file", "default_back.jpg")


if False:
    Base_data_method.download_all_cards(json_dir)

cards = Base_data_method.parse_large_json(json_dir)

# Warning need more than one run to DL all cards ?
Base_data_method().download_card_images(cards,images_dir,bad_images_dir)

# Example of problamatic cards need to be handle : cards['0001a521-655c-432f-9f52-1c199b792f68']
# Détection et déplacement des dos de cartes
# Exemple d'utilisation
Base_data_method().move_card_backs_parallel(images_dir, back_reference, bad_images_dir)