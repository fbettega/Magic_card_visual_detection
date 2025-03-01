import re
import os
import cv2
import numpy as np
import xgboost as xgb
import tensorflow as tf
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split, RandomizedSearchCV,StratifiedKFold
from tensorflow.keras.applications import ResNet50
from tensorflow.keras.applications.resnet50 import preprocess_input
from tensorflow.keras.preprocessing.image import img_to_array
from tensorflow.keras.models import Model
from sklearn.preprocessing import LabelEncoder
from skimage.feature import hog
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
from joblib import dump, load
from sklearn.metrics import accuracy_score
import cupy as cp 

from methods.data_parsing_methods import Base_data_method    


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

    return features, card.layout,card.set, card.rarity


# Chargement parallèle des images
def load_images_parallel(filtered_cards):
    X, y_layout, y_extension, y_rarity = [], [], [], []
    num_workers = os.cpu_count() 
    with ProcessPoolExecutor(max_workers=num_workers) as executor:
        results = list(executor.map(process_image, [card for card in filtered_cards.values()]))
    for res in results:
        if res is not None:
            X.append(res[0])
            y_layout.append(res[1])
            y_extension.append(res[2])
            y_rarity.append(res[3])

    # Encodage des labels
    le_layout = LabelEncoder()
    le_extension = LabelEncoder()
    le_rarity = LabelEncoder()

    y_layout = le_layout.fit_transform(y_layout)
    y_extension = le_extension.fit_transform(y_extension)
    y_rarity = le_rarity.fit_transform(y_rarity)

    return np.array(X), np.array(y_layout),np.array(y_extension),np.array(y_rarity) 


def extract_card_id(filename):
    """Extrait l'ID d'une carte depuis le nom du fichier image."""
    match = re.match(r"([\w-]+)_", filename)
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
        'learning_rate': [0.01, 0.1, 0.2]
    }
    cv_strategy = StratifiedKFold(n_splits=3, shuffle=True, random_state=42)
    xgb_random = RandomizedSearchCV(
        # xgb.XGBClassifier(tree_method="gpu_hist", device="cuda"),  
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

# Filtrer les cartes qui ont une image
filtered_cards = {card_id: card for card_id, card in cards.items() if card_id in image_card_ids}
del cards  # Libération mémoire

X_hog, y_layout,y_set, y_rarity = load_images_parallel(filtered_cards)
del filtered_cards  # Libération mémoire
#################################################################################################################################################################################

# Séparation unique des données pour les trois cibles
X_train_hog, X_test_hog, y_layout_train, y_layout_test, y_set_train, y_set_test, y_rarity_train, y_rarity_test = train_test_split(
    X_hog, y_layout, y_set, y_rarity, test_size=0.2, random_state=42)
del X_hog, y_layout, y_set, y_rarity 
###########################################################

# Séparation des données pour chaque cible (layout, set, rarity)

# Conversion des données en GPU avec `cupy`
# add in order to prevent first execution fail
cp._default_memory_pool.free_all_blocks()
cp._default_pinned_memory_pool.free_all_blocks()
X_train_hog_gpu = cp.asarray(X_train_hog)
del X_train_hog
X_test_hog_gpu = cp.asarray(X_test_hog)
del X_test_hog

retrain_model = True
# Entraînement du modèle pour le layout
best_xgb_layout, accuracy_xgb_layout = train_xgboost(X_train_hog_gpu, y_layout_train, X_test_hog_gpu, y_layout_test, "layout",rerun=retrain_model)

# Entraînement du modèle pour le set
best_xgb_set, accuracy_xgb_set = train_xgboost(X_train_hog_gpu, y_set_train, X_test_hog_gpu, y_set_test, "set",rerun=retrain_model)

# Entraînement du modèle pour la rareté
best_xgb_rarity, accuracy_xgb_rarity = train_xgboost(X_train_hog_gpu, y_rarity_train, X_test_hog_gpu, y_rarity_test, "rarity",rerun=retrain_model)


