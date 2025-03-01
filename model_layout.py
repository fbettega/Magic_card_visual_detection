import re
import os
import cv2
import numpy as np
import xgboost as xgb
import tensorflow as tf
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split, RandomizedSearchCV
from tensorflow.keras.applications import ResNet50
from tensorflow.keras.applications.resnet50 import preprocess_input
from tensorflow.keras.preprocessing.image import img_to_array
from tensorflow.keras.models import Model
from sklearn.preprocessing import LabelEncoder
from skimage.feature import hog
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
from joblib import dump
import cupy as cp 

from methods.data_parsing_methods import Base_data_method    


# Paramètres HOG
image_size = (128, 128)  
orientations = 9
pixels_per_cell = (8, 8)
cells_per_block = (2, 2)

# Chargement du modèle ResNet50 si nécessaire
base_model = None
feature_extractor = None

def initialize_resnet():
    global base_model, feature_extractor
    base_model = ResNet50(weights="imagenet", include_top=False, input_shape=(224, 224, 3))
    feature_extractor = Model(inputs=base_model.input, outputs=base_model.output)

# Fonction de traitement d'une seule image
def process_image(card, method="hog"):
    url, image_path, statut = card.get_images()[0]
    img_path = os.path.join(images_dir, image_path)
    
    if not os.path.exists(img_path):
        return None  # Ignorer les images inexistantes
    
    img = cv2.imread(img_path)
    
    if method == "hog":
        img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)  # Conversion en niveaux de gris
        img = cv2.resize(img, image_size)
        features = hog(img, orientations, pixels_per_cell, cells_per_block)
    
    elif method == "resnet":
        img = cv2.resize(img, (224, 224))
        img = img_to_array(img)
        img = preprocess_input(img)
        features = feature_extractor.predict(np.expand_dims(img, axis=0)).flatten()
    else:
        raise ValueError("Méthode d'extraction inconnue")

    return features, card.layout

# Chargement parallèle des images
def load_images_parallel(filtered_cards, method="hog", num_workers=8):
    if method == "resnet":
        initialize_resnet()  # Initialisation du modèle si nécessaire

    X, y = [], []
    # with ThreadPoolExecutor(max_workers=num_workers) as executor:
    with ThreadPoolExecutor() as executor:
        results = list(executor.map(lambda card: process_image(card, method), filtered_cards.values()))

    for res in results:
        if res is not None:
            X.append(res[0])
            y.append(res[1])
    # Encodage des labels
    y = np.array(y)
    label_encoder = LabelEncoder()
    y = label_encoder.fit_transform(y)
    return np.array(X), y
# Exemple d'utilisation


def extract_card_id(filename):
    """Extrait l'ID d'une carte depuis le nom du fichier image."""
    match = re.match(r"([\w-]+)_", filename)
    return match.group(1) if match else None



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

X_hog, y = load_images_parallel(filtered_cards, method="hog", num_workers=16)



X_train_hog, X_test_hog, y_train, y_test = train_test_split(X_hog, y, test_size=0.2, random_state=42)

###########################################################
# Conversion des données en GPU avec `cupy`
X_train_hog_gpu = cp.asarray(X_train_hog)
# y_train_gpu = cp.asarray(y_train)

# Optimisation XGBoost
xgb_params = {
    'n_estimators': [100, 300, 500],
    'max_depth': [3, 6, 9],
    'learning_rate': [0.01, 0.1, 0.2]
}

xgb_random = RandomizedSearchCV(
    xgb.XGBClassifier(tree_method="gpu_hist", device="cuda"),  # Activation du GPU
    param_distributions=xgb_params,
    n_iter=10,  # 10 combinaisons aléatoires pour éviter la surcharge
    cv=3,
    verbose=1,
    n_jobs=1  # Attention : XGBoost en GPU doit utiliser `n_jobs=1`
)

xgb_random.fit(X_train_hog_gpu, y_train)
best_xgb = xgb_random.best_estimator_

# Évaluation XGBoost optimisé
accuracy_xgb = best_xgb.score(X_test_hog, y_test)
print(f"Précision XGBoost optimisé : {accuracy_xgb:.2f}")
dump(best_xgb, "data/model/layout/layout_predictor_xgb_optimized.joblib")

