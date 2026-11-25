"""
predict.py
----------
Loads the trained IsolationForest model and scores a journal entry
for fraud probability / risk. Import this from a Django view, e.g.:

    from ai_models.predict import score_journal_entry
    result = score_journal_entry(amount=52000, frequency=1)
"""
import os
import joblib

try:
    from django.conf import settings
    _CACHE_DIR = os.path.join(str(settings.DATA_DIR), 'ai_models_cache')
except Exception:
    # Fallback for standalone use outside Django (e.g. manual testing)
    _CACHE_DIR = os.path.dirname(__file__)

MODEL_PATH = os.path.join(_CACHE_DIR, 'fraud_model.joblib')
_model = None


def _load_model():
    global _model
    if _model is None:
        if not os.path.exists(MODEL_PATH):
            # First time this runs on this machine: train automatically
            # instead of requiring someone to run a script by hand.
            from ai_models.train_fraud_model import train
            _model = train(output_path=MODEL_PATH)
        else:
            _model = joblib.load(MODEL_PATH)
    return _model


def score_journal_entry(amount, frequency):
    """
    Returns a dict: {is_anomaly, risk_score (0-100), recommendation}
    -1 from IsolationForest.predict() means anomaly (potential fraud).
    """
    model = _load_model()
    prediction = model.predict([[amount, frequency]])[0]
    anomaly_score = model.decision_function([[amount, frequency]])[0]

    # decision_function: lower (more negative) = more anomalous.
    # Normalize roughly to a 0-100 risk score for display purposes.
    risk_score = max(0, min(100, round((0.5 - anomaly_score) * 100)))

    is_anomaly = prediction == -1
    if is_anomaly:
        recommendation = 'Flag for manual review — unusual amount/frequency pattern detected.'
    else:
        recommendation = 'No unusual pattern detected.'

    return {
        'is_anomaly': bool(is_anomaly),
        'risk_score': risk_score,
        'recommendation': recommendation,
    }
