import json
from methods.data_parsing_methods import Base_data_method    

Base_data_method.download_all_cards()

 

with open("data/scryfall_bulk_data/all_cards.json", "r", encoding="utf-8") as f:
    cards = json.load(f)


