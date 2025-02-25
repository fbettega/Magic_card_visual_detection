import json
from methods.data_parsing_methods import Base_data_method    
import os
if False:
    Base_data_method.download_all_cards()

cards = Base_data_method.parse_large_json("data/scryfall_bulk_data/all_cards.json")

Base_data_method().download_card_images(cards,"data/cards_image_gallery")


