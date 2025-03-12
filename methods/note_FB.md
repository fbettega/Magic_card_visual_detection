# model token vs cards  
## token / double face token / emblem
## versus cartes normal a définir 

# Model border séparé ?  

# model global layout
## intégrant textless ?
## listé les variables pour déférencier efficacement les grandes classes de layout
# globalement l'idée serait ressemble a une cartes vs autres



# detection cartes anormale : 
import numpy as np
import tensorflow as tf
from tensorflow.keras.layers import Input, Conv2D, Conv2DTranspose, Flatten, Dense, Reshape
from tensorflow.keras.models import Model
import cv2
import os
from sklearn.metrics import mean_squared_error

# 1. Charger et prétraiter les images
def load_images(folder, img_size=(128, 128)):
    images = []
    for filename in os.listdir(folder):
        img = cv2.imread(os.path.join(folder, filename))
        if img is not None:
            img = cv2.resize(img, img_size) / 255.0  # Normalisation
            images.append(img)
    return np.array(images)

normal_cards = load_images("dataset_cartes_normales")
input_shape = normal_cards.shape[1:]

# 2. Construire l'autoencodeur
def build_autoencoder(input_shape):
    input_img = Input(shape=input_shape)

    # Encodeur
    x = Conv2D(32, (3,3), activation='relu', padding='same')(input_img)
    x = Conv2D(64, (3,3), activation='relu', padding='same', strides=2)(x)
    x = Conv2D(128, (3,3), activation='relu', padding='same', strides=2)(x)
    encoded = Flatten()(x)

    # Décodeur
    x = Dense(32*32*128, activation='relu')(encoded)
    x = Reshape((32, 32, 128))(x)
    x = Conv2DTranspose(64, (3,3), activation='relu', padding='same', strides=2)(x)
    x = Conv2DTranspose(32, (3,3), activation='relu', padding='same', strides=2)(x)
    decoded = Conv2D(3, (3,3), activation='sigmoid', padding='same')(x)

    autoencoder = Model(input_img, decoded)
    autoencoder.compile(optimizer='adam', loss='mse')
    
    return autoencoder

autoencoder = build_autoencoder(input_shape)

# 3. Entraîner sur les cartes normales
autoencoder.fit(normal_cards, normal_cards, epochs=20, batch_size=32, validation_split=0.1)

# 4. Détection d’anomalies
def detect_anomalies(model, image_folder, threshold=0.01):
    images = load_images(image_folder)
    reconstructed = model.predict(images)
    
    mse = np.mean((images - reconstructed) ** 2, axis=(1,2,3))  # Erreur MSE
    anomalies = np.where(mse > threshold)[0]  # Indices des images anormales
    
    return anomalies, mse

anomalies, scores = detect_anomalies(autoencoder, "dataset_toutes_cartes")

print(f"Nombre de cartes anormales détectées: {len(anomalies)}")
