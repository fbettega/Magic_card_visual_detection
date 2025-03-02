import re
import os
import cv2
import numpy as np
import xgboost as xgb
from sklearn.model_selection import  RandomizedSearchCV,StratifiedKFold
from sklearn.preprocessing import LabelEncoder
from skimage.feature import hog
from concurrent.futures import  ProcessPoolExecutor
from joblib import dump, load
from sklearn.metrics import accuracy_score
from collections import defaultdict


class CardImageProcessor:
    def __init__(self, images_dir, image_size=(128, 128), orientations=9, pixels_per_cell=(8, 8), cells_per_block=(2, 2)):
        self.images_dir = images_dir
        self.image_size = image_size
        self.orientations = orientations
        self.pixels_per_cell = pixels_per_cell
        self.cells_per_block = cells_per_block

    def process_image(self, card):
        url, image_path, statut = card.get_images()[0]
        img_path = os.path.join(self.images_dir, image_path)
        
        if not os.path.exists(img_path):
            return None  # Ignorer les images inexistantes  
        img = cv2.imread(img_path)
        img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)  # Conversion en niveaux de gris
        img = cv2.resize(img, self.image_size)
        features = hog(img, self.orientations, self.pixels_per_cell, self.cells_per_block)
        
        return features, card.layout, card.set, card.rarity

    def load_images_parallel(self, filtered_cards, target_y, max_per_y=None):
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
            results = list(executor.map(self.process_image, selected_cards))
        
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

    @staticmethod
    def extract_card_id(filename):
        """Extrait l'ID d'une carte depuis le nom du fichier image."""
        match = re.match(r"([a-f0-9-]{36})_", filename) 
        return match.group(1) if match else None

    def train_xgboost(self, X_train, y_train, X_test, y_test, model_name, rerun=True):
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
            xgb.XGBClassifier(tree_method="hist", device="cuda"),  # Activation du GPU
            param_distributions=xgb_params,
            n_iter=10,  # 10 combinaisons aléatoires pour éviter la surcharge
            cv=cv_strategy,
            verbose=10,
            n_jobs=1,  # Attention : XGBoost en GPU doit utiliser `n_jobs=1`
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
    