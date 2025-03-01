xgb_random = RandomizedSearchCV(
    xgb.XGBClassifier(tree_method="gpu_hist", device="cuda"),  # Activation du GPU
    param_distributions=xgb_params,
    n_iter=10,  # 10 combinaisons aléatoires pour éviter la surcharge
    cv=3,
    verbose=1,
    n_jobs=1  # Attention : XGBoost en GPU doit utiliser `n_jobs=1`
)

# ======= Utilisation de ResNet50 =======
X_resnet, y_resnet = load_images_parallel(filtered_cards, method="resnet", num_workers=8)
# Séparation des données pour ResNet50
X_train_resnet, X_test_resnet, _, _ = train_test_split(X_resnet, y, test_size=0.2, random_state=42)


# Entraînement XGBoost avec ResNet50
best_xgb.fit(X_train_resnet, y_train)
accuracy_xgb_resnet = best_xgb.score(X_test_resnet, y_test)
print(f"Précision XGBoost avec ResNet50 : {accuracy_xgb_resnet:.2f}")