import json
from methods.data_parsing_methods import Base_data_method    
import os
if False:
    Base_data_method.download_all_cards()

cards = Base_data_method.parse_large_json("data/scryfall_bulk_data/all_cards.json")

Base_data_method().download_card_images(cards,"data/cards_image_gallery")




for card in cards[:200]:  
        existing_files = set(os.listdir("data/cards_image_gallery"))  
        images = card.get_images()
        for url, filename in images:
            if filename in existing_files:
                 print(url)
# a prevoir ocr pour enlever le place holder "Localized Not Available" 