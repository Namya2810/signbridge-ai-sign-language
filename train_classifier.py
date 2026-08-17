"""
train_classifier.py — Landmark data pe Random Forest train karo
----------------------------------------------------------------
Input:  landmark_data/landmarks.csv
Output: landmark_classifier.pkl + landmark_encoder.pkl
"""

import pandas as pd
import numpy as np
import pickle
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report

print("Data load ho raha hai...")
df = pd.read_csv("landmark_data/landmarks.csv")
print(f"Total samples: {len(df)}")
print(f"Classes: {sorted(df['label'].unique())}")
print(f"Samples per class:\n{df['label'].value_counts().sort_index()}")

# ─── Features aur labels ─────────────────────────────────────────────────────
X = df.drop("label", axis=1).values
y = df["label"].values

le = LabelEncoder()
y_encoded = le.fit_transform(y)

# ─── Train/test split ─────────────────────────────────────────────────────────
X_train, X_test, y_train, y_test = train_test_split(
    X, y_encoded, test_size=0.2, stratify=y_encoded, random_state=42
)
print(f"\nTrain: {len(X_train)} | Test: {len(X_test)}")

# ─── Random Forest train ──────────────────────────────────────────────────────
print("\nRandom Forest train ho raha hai...")
clf = RandomForestClassifier(
    n_estimators = 200,
    max_depth    = None,
    random_state = 42,
    n_jobs       = -1    # all CPU cores use karo
)
clf.fit(X_train, y_train)

# ─── Evaluate ─────────────────────────────────────────────────────────────────
y_pred = clf.predict(X_test)
acc    = accuracy_score(y_test, y_pred)
print(f"\nTest Accuracy: {acc*100:.2f}%")
print("\nPer-class report:")
print(classification_report(y_test, y_pred, target_names=le.classes_))

# ─── Save ─────────────────────────────────────────────────────────────────────
with open("landmark_classifier.pkl", "wb") as f:
    pickle.dump(clf, f)
with open("landmark_encoder.pkl", "wb") as f:
    pickle.dump(le, f)

print("\n✓ Saved: landmark_classifier.pkl + landmark_encoder.pkl")
print("Ab backend.py restart karo — naya classifier automatically pick ho jayega!")
