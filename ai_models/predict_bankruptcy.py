"""
predict_bankruptcy.py
----------------------
Loads the trained bankruptcy model and scores a company's six ratio
scores (from business_stability.calculate_stability_index) for
bankruptcy probability.

Usage:
    from ai_models.predict_bankruptcy import predict_bankruptcy
    result = predict_bankruptcy(stability_result)
"""
import os
import joblib

try:
    from django.conf import settings
    _CACHE_DIR = os.path.join(str(settings.DATA_DIR), 'ai_models_cache')
except Exception:
    _CACHE_DIR = os.path.dirname(__file__)

MODEL_PATH = os.path.join(_CACHE_DIR, 'bankruptcy_model.joblib')
_model = None


def _load_model():
    global _model
    if _model is None:
        if not os.path.exists(MODEL_PATH):
            from ai_models.train_bankruptcy_model import train
            _model = train(output_path=MODEL_PATH)
        else:
            _model = joblib.load(MODEL_PATH)
    return _model


def predict_bankruptcy(stability_result):
    """
    stability_result: the dict returned by business_stability.calculate_stability_index()
    Returns: {probability (0-100), risk_level, recommendation}
    """
    model = _load_model()
    features = [[
        stability_result['liquidity_score'],
        stability_result['profitability_score'],
        stability_result['cash_flow_score'],
        stability_result['revenue_growth_score'],
        stability_result['expense_control_score'],
        stability_result['debt_ratio_score'],
    ]]
    probability = model.predict_proba(features)[0][1] * 100
    probability = round(probability, 1)

    if probability >= 60:
        risk_level = 'High'
        recommendation = 'Immediate attention needed — review liquidity and reduce liabilities.'
    elif probability >= 30:
        risk_level = 'Medium'
        recommendation = 'Monitor cash flow closely and control expenses.'
    else:
        risk_level = 'Low'
        recommendation = 'Financial position looks stable — maintain current practices.'

    return {
        'probability': probability,
        'risk_level': risk_level,
        'recommendation': recommendation,
    }
