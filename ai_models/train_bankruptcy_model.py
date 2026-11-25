"""
train_bankruptcy_model.py
--------------------------
Trains a logistic regression model to estimate bankruptcy probability
from six financial ratios (liquidity, profitability, cash flow,
revenue growth, expense control, debt ratio) — the same six ratios
used in the Business Stability Index (see business_stability.py).

This uses SYNTHETIC training data (companies with poor ratios are
labeled higher bankruptcy risk). For a real Final Year Project,
replace generate_synthetic_data() with a labeled dataset such as the
public "Company Bankruptcy Prediction" dataset (Taiwan Economic
Journal, available on Kaggle), keeping the same 6 input features or
re-training the pipeline on the new feature set.

Run manually:
    python ai_models/train_bankruptcy_model.py
"""
import os
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
import joblib

OUTPUT_PATH = os.path.join(os.path.dirname(__file__), 'bankruptcy_model.joblib')


def generate_synthetic_data(n=1000):
    rng = np.random.default_rng(7)

    # Healthy companies: high scores across the board
    healthy = rng.normal(loc=70, scale=15, size=(n, 6))
    # At-risk companies: low scores, especially liquidity/cash flow/debt
    risky = rng.normal(loc=30, scale=15, size=(n // 4, 6))

    X = np.vstack([healthy, risky])
    X = np.clip(X, 0, 100)

    # Label: bankrupt (1) if the average of the 6 scores is below 40
    y = (X.mean(axis=1) < 40).astype(int)

    columns = [
        'liquidity_score', 'profitability_score', 'cash_flow_score',
        'revenue_growth_score', 'expense_control_score', 'debt_ratio_score',
    ]
    df = pd.DataFrame(X, columns=columns)
    df['bankrupt'] = y
    return df


def train(output_path=None):
    output_path = output_path or OUTPUT_PATH
    df = generate_synthetic_data()
    feature_cols = [c for c in df.columns if c != 'bankrupt']
    X = df[feature_cols]
    y = df['bankrupt']

    pipeline = Pipeline([
        ('scaler', StandardScaler()),
        ('clf', LogisticRegression(max_iter=1000)),
    ])
    pipeline.fit(X, y)

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    joblib.dump(pipeline, output_path)
    print(f"Bankruptcy model trained and saved to {output_path}")
    return pipeline


if __name__ == '__main__':
    train()
