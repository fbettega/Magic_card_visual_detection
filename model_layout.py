import os
import cv2
import numpy as np
from sklearn.svm import SVC
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from skimage.feature import hog
from sklearn.preprocessing import LabelEncoder
from joblib import dump
import re

from methods.data_parsing_methods import Base_data_method    


json_dir = os.path.join("data", "scryfall_bulk_data")
images_dir = os.path.join("data", "cards_image_gallery")

cards = Base_data_method.parse_large_json(os.path.join(json_dir,"all_cards.json"))
# Chemin du dossier des images


# Récupération des fichiers images présents dans le dossier
image_files = set(f for f in os.listdir(images_dir) if f.endswith(('.jpg', '.png')))

def extract_card_id(filename):
    """Extrait l'ID d'une carte depuis le nom du fichier image."""
    match = re.match(r"([\w-]+)_", filename)
    return match.group(1) if match else None

# Extraire les IDs des cartes présentes dans le dossier
image_card_ids = {extract_card_id(f) for f in image_files if extract_card_id(f)}

# Filtrer les cartes qui ont une image
filtered_cards = {card_id: card for card_id, card in cards.items() if card_id in image_card_ids}

# Paramètres
image_size = (128, 128)  # Taille fixe pour homogénéiser les images
orientations = 9  # Paramètres HOG
pixels_per_cell = (8, 8)
cells_per_block = (2, 2)

# Charger les images et extraire les caractéristiques
X, y = [], []
for card_id, card in filtered_cards.items():
    url, image_path,statut = card.get_images()[0]
    img_path = os.path.join(images_dir, image_path)
    if os.path.exists(img_path):
        img = cv2.imread(img_path, cv2.IMREAD_GRAYSCALE)  # Lecture en niveaux de gris
        img = cv2.resize(img, image_size)  # Redimensionnement
        features = hog(img, orientations, pixels_per_cell, cells_per_block)  # Extraction HOG
        X.append(features)
        y.append(card.layout)

X = np.array(X)
y = np.array(y)

# Encoder les labels (layout)
label_encoder = LabelEncoder()
y = label_encoder.fit_transform(y)

# Séparer les données
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Entraînement du modèle Random Forest
model = RandomForestClassifier(n_estimators=100, n_jobs=-1, verbose=1)
model.fit(X_train, y_train)

