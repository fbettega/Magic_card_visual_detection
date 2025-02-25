import json
from methods.data_parsing_methods import Base_data_method    
import os
if False:
    Base_data_method.download_all_cards()

cards = Base_data_method.parse_large_json("data/scryfall_bulk_data/all_cards.json")

# Warning need more than one run to DL all cards ?
Base_data_method().download_card_images(cards,"data/cards_image_gallery")


cards['0001a521-655c-432f-9f52-1c199b792f68']