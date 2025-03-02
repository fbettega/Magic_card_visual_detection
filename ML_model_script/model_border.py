import re
import os
import cv2
import numpy as np
import xgboost as xgb
import tensorflow as tf
from sklearn.model_selection import StratifiedShuffleSplit, RandomizedSearchCV,StratifiedKFold
from sklearn.metrics import accuracy_score
import cupy as cp 
from collections import Counter,defaultdict
from methods.data_parsing_methods import Base_data_method    
from methods.XGB_training import CardImageProcessor

# explore train test split
def test_y_rep(cards,y_train,y_test,var_name):
    rarity_counts = Counter(getattr(card, var_name) for card in cards.values())
    # Afficher les résultats
    for rarity, count in rarity_counts.items():
        print(f"{rarity}: {count}")
# Vérifier si une classe manque dans y_rarity_test
    missing_classes = set(y_train) - set(y_test)
    if missing_classes:
        print(f"Classes manquantes dans y_rarity_test : {missing_classes}")
    return rarity_counts,missing_classes
#################################################################################################################################################################################
json_dir = os.path.join("data", "scryfall_bulk_data")
images_dir = os.path.join("data", "cards_image_gallery")

cards = Base_data_method.parse_large_json(os.path.join(json_dir,"all_cards.json"))
# Chemin du dossier des images
# Récupération des fichiers images présents dans le dossier
image_files = set(f for f in os.listdir(images_dir) if f.endswith(('.jpg', '.png')))
# Extraire les IDs des cartes présentes dans le dossier
image_card_ids = {CardImageProcessor.extract_card_id(f) for f in image_files if CardImageProcessor.extract_card_id(f)}
# Types et layouts à exclure
excluded_set_types = {"token", "memorabilia"}  # Tokens, emblèmes, cartes promotionnelles, etc.
excluded_layouts = {"token", "emblem", "double_faced_token", "art_series", "vanguard"}
# Filtrer les cartes valides (pas token, emblème, etc.)
filtered_cards = {
    card_id: card for card_id, card in cards.items()
    if card_id in image_card_ids 
    # and card.set_type not in excluded_set_types
    # and card.layout not in excluded_layouts
}




X_hog, y_layout,label_encoder = CardImageProcessor(images_dir = images_dir).load_images_parallel(filtered_cards, target_y="layout", max_per_y=5000)
#################################################################################################################################################################################

# Séparation unique des données pour les trois cibles
sss = StratifiedShuffleSplit(n_splits=1, test_size=0.2)
for train_idx, test_idx in sss.split(X_hog, y_layout):  # Stratification sur y_rarity
    X_train_hog, X_test_hog = X_hog[train_idx], X_hog[test_idx]
    y_layout_train, y_layout_test = y_layout[train_idx], y_layout[test_idx]
    # y_set_train, y_set_test = y_set[train_idx], y_set[test_idx]
    # y_rarity_train, y_rarity_test = y_rarity[train_idx], y_rarity[test_idx]


###########################################################
len(filtered_cards)
len(cards)
len(image_card_ids)
print("The memory size of numpy array arr is:",X_hog.itemsize*X_hog.size,"bytes")
test_y_rep(filtered_cards,y_layout_train,y_layout_test,"layout")
###########################################################


# Séparation des données pour chaque cible (layout, set, rarity)

# Conversion des données en GPU avec `cupy`
# add in order to prevent first execution fail
# del X_train_hog
# X_train_hog_gpu = cp.asarray(X_train_hog).astype(cp.float32)
# # del X_train_hog
# X_test_hog_gpu = cp.asarray(X_test_hog).astype(cp.float32)
# del X_test_hog

retrain_model = True
# Entraînement du modèle pour le layout
best_xgb_layout, accuracy_xgb_layout = CardImageProcessor(images_dir = images_dir).train_xgboost(X_train_hog, y_layout_train, X_test_hog, y_layout_test, "layout",rerun=retrain_model)


# border
# # Entraînement du modèle pour le set
# best_xgb_set, accuracy_xgb_set = train_xgboost(X_train_hog_gpu, y_set_train, X_test_hog_gpu, y_set_test, "set",rerun=retrain_model)

# # Entraînement du modèle pour la rareté
# best_xgb_rarity, accuracy_xgb_rarity = train_xgboost(X_train_hog_gpu, y_rarity_train, X_test_hog_gpu, y_rarity_test, "rarity",rerun=retrain_model)



