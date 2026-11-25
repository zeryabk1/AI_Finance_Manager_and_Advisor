"""
train_fraud_model.py
---------------------
Trains a simple fraud-detection model on journal entry data
(amount, frequency of that debit/credit account pair, hour of day)
and saves it with joblib so Django views can load and reuse it.

Run manually:
    python ai_models/train_fraud_model.py

This is a STARTER model — for a real Final Year Project you should
replace the synthetic training data below with your exported
JournalEntry data (see accounting/models.py) once you have enough
real transactions to train on.
"""
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
import joblib
import os

OUTPUT_PATH = os.path.join(os.path.dirname(__file__), 'fraud_model.joblib')


def generate_synthetic_data(n=500):
    """Simulate 'normal' journal entries plus a few fraud-like outliers."""
    rng = np.random.default_rng(42)
    normal_amounts = rng.normal(loc=5000, scale=1500, size=n)
    normal_freq = rng.integers(1, 30, size=n)

    # Inject some obvious anomalies: huge one-off amounts, rare pairs
    fraud_amounts = rng.normal(loc=50000, scale=15000, size=20)
    fraud_freq = rng.integers(1, 3, size=20)

    amounts = np.concatenate([normal_amounts, fraud_amounts])
    freq = np.concatenate([normal_freq, fraud_freq])

    df = pd.DataFrame({'amount': amounts, 'frequency': freq})
    df['amount'] = df['amount'].clip(lower=100)
    return df


def train(output_path=None):
    output_path = output_path or OUTPUT_PATH
    df = generate_synthetic_data()
    X = df[['amount', 'frequency']]

    model = IsolationForest(contamination=0.05, random_state=42)
    model.fit(X)

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    joblib.dump(model, output_path)
    print(f"Model trained and saved to {output_path}")
    return model


if __name__ == '__main__':
    train()
