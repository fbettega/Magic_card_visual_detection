import os
from sklearn.model_selection import StratifiedShuffleSplit
from methods.data_parsing_methods import Base_data_method    
from methods.XGB_training import CardImageProcessor
#################################################################################################################################################################################
retrain_model = False
json_dir = os.path.join("data", "scryfall_bulk_data")
images_dir = os.path.join("data", "cards_image_gallery")
#################################################################################################################################################################################
def process_target(images_dir:str, filtered_cards, target_y:str, retrain_model:bool, max_per_y=5000, test_size=0.2):
    """
    Charge les images, effectue la séparation train/test et entraîne un modèle XGBoost.

    Args:
        images_dir (str): Répertoire contenant les images.
        filtered_cards (list): Liste des cartes filtrées à utiliser.
        target_y (str): La cible à prédire (ex: "layout", "border_color").
        retrain_model (bool): Si True, entraîne un nouveau modèle.
        max_per_y (int, optional): Nombre max d'images par catégorie. Default 5000.
        test_size (float, optional): Fraction de test. Default 0.2.

    Returns:
        tuple: (Meilleur modèle entraîné, précision)
    """

    processor = CardImageProcessor(images_dir=images_dir)
    # Chargement des images et extraction des features
    X_hog, y, label_encoder = processor.load_images_parallel(
        filtered_cards, target_y=target_y, max_per_y=max_per_y
    )

    # Séparation train/test avec stratification
    sss = StratifiedShuffleSplit(n_splits=1, test_size=test_size)
    for train_idx, test_idx in sss.split(X_hog, y):
        X_train, X_test = X_hog[train_idx], X_hog[test_idx]
        y_train, y_test = y[train_idx], y[test_idx]

    # Entraînement du modèle
    best_model, accuracy = processor.train_xgboost(
        X_train, y_train, X_test, y_test, target_y, rerun=retrain_model
    )

    return (X_hog,y, label_encoder),best_model, accuracy
#################################################################################################################################################################################



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


# Exécution pour "layout"
data_layout,best_xgb_layout, accuracy_xgb_layout = process_target(
    images_dir, filtered_cards, "layout", retrain_model=retrain_model
)

# Exécution pour "border_color"
data_border,best_xgb_border, accuracy_xgb_border = process_target(
    images_dir, filtered_cards, "border_color", retrain_model=retrain_model
)




