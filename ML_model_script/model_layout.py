import os
from sklearn.model_selection import StratifiedShuffleSplit
from methods.data_parsing_methods import Base_data_method    
from methods.XGB_training import CardImageProcessor

#################################################################################################################################################################################
json_dir = os.path.join("data", "scryfall_bulk_data")
images_dir = os.path.join("data", "cards_image_gallery")

cards = Base_data_method.parse_large_json(os.path.join(json_dir,"all_cards.json"))
# Chemin du dossier des images
# Récupération des fichiers images présents dans le dossier
image_files = set(f for f in os.listdir(images_dir) if f.endswith(('.jpg', '.png')))
# Extraire les IDs des cartes présentes dans le dossier
image_card_ids = {CardImageProcessor.extract_card_id(f) for f in image_files if CardImageProcessor.extract_card_id(f)}
# Filtrer les cartes valides (pas token, emblème, etc.)
filtered_cards = {
    card_id: card for card_id, card in cards.items()
    if card_id in image_card_ids 
}

X_hog, y_layout,label_encoder = CardImageProcessor(images_dir = images_dir).load_images_parallel(filtered_cards, target_y="layout", max_per_y=5000)
#################################################################################################################################################################################
# Séparation unique des données pour les trois cibles
sss = StratifiedShuffleSplit(n_splits=1, test_size=0.2)
for train_idx, test_idx in sss.split(X_hog, y_layout):  # Stratification sur y_rarity
    X_train_hog, X_test_hog = X_hog[train_idx], X_hog[test_idx]
    y_layout_train, y_layout_test = y_layout[train_idx], y_layout[test_idx]


retrain_model = False
best_xgb_layout, accuracy_xgb_layout = CardImageProcessor(images_dir = images_dir).train_xgboost(X_train_hog, y_layout_train, X_test_hog, y_layout_test, "layout",rerun=retrain_model)


