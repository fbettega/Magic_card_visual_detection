from methods.data_parsing_methods import Base_data_method    
import os
Rerun_alll = False
json_dir = os.path.join("data", "scryfall_bulk_data")
images_dir = os.path.join("data", "cards_image_gallery")
bad_images_dir = os.path.join("data", "bad_image")
back_reference = os.path.join("data", "other_file", "default_back.jpg")


if Rerun_alll:
    Base_data_method.download_all_cards(json_dir)

cards = Base_data_method.parse_large_json(os.path.join(json_dir,"all_cards.json"))

# Warning need more than one run to DL all cards ?
for i in [0,1]:
    Base_data_method().download_card_images(cards,images_dir,bad_images_dir)

# Example of problamatic cards need to be handle : cards['0001a521-655c-432f-9f52-1c199b792f68']
# new example cards['000cb74e-2ebf-4c31-a334-4dbad1486ead']
# Détection et déplacement des dos de cartes
# Exemple d'utilisation

Base_data_method().move_card_backs_parallel(images_dir, back_reference, bad_images_dir)





