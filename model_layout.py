import re
import os
import cv2
import numpy as np
import xgboost as xgb
import tensorflow as tf
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import StratifiedShuffleSplit, RandomizedSearchCV,StratifiedKFold
from sklearn.preprocessing import LabelEncoder
from skimage.feature import hog
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
from joblib import dump, load
from sklearn.metrics import accuracy_score
import cupy as cp 
from collections import Counter,defaultdict
from methods.data_parsing_methods import Base_data_method    




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


# Paramètres HOG
image_size = (128, 128)  
orientations = 9
pixels_per_cell = (8, 8)
cells_per_block = (2, 2)
# Fonction de traitement d'une seule image
def process_image(card):
    url, image_path, statut = card.get_images()[0]
    img_path = os.path.join(images_dir, image_path)
    
    if not os.path.exists(img_path):
        return None  # Ignorer les images inexistantes  
    img = cv2.imread(img_path)
    
    img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)  # Conversion en niveaux de gris
    img = cv2.resize(img, image_size)
    features = hog(img, orientations, pixels_per_cell, cells_per_block)
    
    return features, card.layout, card.set, card.rarity

def load_images_parallel(filtered_cards, target_y, max_per_y=None):
    X, y = [], []
    count_per_y = defaultdict(int)
    selected_cards = []
    
    # Pré-filtrage des cartes avant chargement des images
    for card in filtered_cards.values():
        target_value = {"layout": card.layout, "extension": card.set, "rarity": card.rarity}[target_y]
        
        if max_per_y is not None and count_per_y[target_value] >= max_per_y:
            continue
        
        count_per_y[target_value] += 1
        selected_cards.append(card)
    
    num_workers = os.cpu_count()
    with ProcessPoolExecutor(max_workers=num_workers) as executor:
        results = list(executor.map(process_image, selected_cards))
    
    for res in results:
        if res is None:
            continue
        
        features, layout, extension, rarity = res
        target_value = {"layout": layout, "extension": extension, "rarity": rarity}[target_y]
        
        X.append(features)
        y.append(target_value)
    
    # Encodage des labels
    le = LabelEncoder()
    y = le.fit_transform(y)
    
    return np.array(X), np.array(y), le



def extract_card_id(filename):
    """Extrait l'ID d'une carte depuis le nom du fichier image."""
    match = re.match(r"([a-f0-9-]{36})_", filename) 
    return match.group(1) if match else None

# Fonction pour entraîner ou charger un modèle XGBoost
def train_xgboost(X_train, y_train, X_test, y_test, model_name, rerun=True):
    model_path = f"data/model/{model_name}"
    model_file = f"{model_path}/{model_name}_predictor_xgb_optimized.joblib"

    # Vérifie si le modèle existe déjà
    if not rerun and os.path.exists(model_file):
        print(f"Chargement du modèle existant : {model_file}")
        best_xgb = load(model_file)
        y_pred = best_xgb.predict(X_test)
        accuracy_xgb = accuracy_score(y_test, y_pred)
        print(f"Précision {model_name} XGBoost chargé : {accuracy_xgb:.2f}")
        return best_xgb, accuracy_xgb

    # Création du dossier si nécessaire
    os.makedirs(model_path, exist_ok=True)

    xgb_params = {
        'n_estimators': [100, 300, 500],
        'max_depth': [3, 6, 9],
        'learning_rate': [0.01,0.1, 0.2]
    }
    cv_strategy = StratifiedKFold(n_splits=3, shuffle=True, random_state=42)
    xgb_random = RandomizedSearchCV(
        xgb.XGBClassifier(tree_method = "hist", device = "cuda"), 
        # Activation du GPU
        param_distributions=xgb_params,
        n_iter=10,  # 10 combinaisons aléatoires pour éviter la surcharge
        cv=cv_strategy,
        verbose=10,
        n_jobs=1 , # Attention : XGBoost en GPU doit utiliser `n_jobs=1`
        error_score="raise"
    )

    xgb_random.fit(X_train, y_train)
    best_xgb = xgb_random.best_estimator_

    # Évaluation du modèle
    y_pred = best_xgb.predict(X_test)
    accuracy_xgb = accuracy_score(y_test, y_pred)
    print(f"Précision {model_name} XGBoost optimisé : {accuracy_xgb:.2f}")

    # Sauvegarde du modèle
    dump(best_xgb, model_file)

    return best_xgb, accuracy_xgb

#################################################################################################################################################################################


json_dir = os.path.join("data", "scryfall_bulk_data")
images_dir = os.path.join("data", "cards_image_gallery")

cards = Base_data_method.parse_large_json(os.path.join(json_dir,"all_cards.json"))
# Chemin du dossier des images


# Récupération des fichiers images présents dans le dossier
image_files = set(f for f in os.listdir(images_dir) if f.endswith(('.jpg', '.png')))

# Extraire les IDs des cartes présentes dans le dossier
image_card_ids = {extract_card_id(f) for f in image_files if extract_card_id(f)}
# Types et layouts à exclure
excluded_set_types = {"token", "memorabilia"}  # Tokens, emblèmes, cartes promotionnelles, etc.
excluded_layouts = {"token", "emblem", "double_faced_token", "art_series", "vanguard"}

# Filtrer les cartes valides (pas token, emblème, etc.)
filtered_cards = {
    card_id: card for card_id, card in cards.items()
    if card_id in image_card_ids 
    and card.set_type not in excluded_set_types
    and card.layout not in excluded_layouts
}



X_hog, y_layout,label_encoder = load_images_parallel(filtered_cards, target_y="layout", max_per_y=5000)
#################################################################################################################################################################################



# Séparation unique des données pour les trois cibles
sss = StratifiedShuffleSplit(n_splits=1, test_size=0.2)
for train_idx, test_idx in sss.split(X_hog, y_layout):  # Stratification sur y_rarity
    X_train_hog, X_test_hog = X_hog[train_idx], X_hog[test_idx]
    y_layout_train, y_layout_test = y_layout[train_idx], y_layout[test_idx]
    # y_set_train, y_set_test = y_set[train_idx], y_set[test_idx]
    # y_rarity_train, y_rarity_test = y_rarity[train_idx], y_rarity[test_idx]


###########################################################
# len(filtered_cards)
# len(cards)
# len(image_card_ids)
# print("The memory size of numpy array arr is:",X_hog.itemsize*X_hog.size,"bytes")
# test_y_rep(filtered_cards,y_layout_train,y_layout_test,"layout")
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
best_xgb_layout, accuracy_xgb_layout = train_xgboost(X_train_hog, y_layout_train, X_test_hog, y_layout_test, "layout",rerun=retrain_model)

# # Entraînement du modèle pour le set
# best_xgb_set, accuracy_xgb_set = train_xgboost(X_train_hog_gpu, y_set_train, X_test_hog_gpu, y_set_test, "set",rerun=retrain_model)

# # Entraînement du modèle pour la rareté
# best_xgb_rarity, accuracy_xgb_rarity = train_xgboost(X_train_hog_gpu, y_rarity_train, X_test_hog_gpu, y_rarity_test, "rarity",rerun=retrain_model)



