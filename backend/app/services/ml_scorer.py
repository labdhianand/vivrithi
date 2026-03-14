from __future__ import annotations

import json
import logging
from decimal import Decimal
from pathlib import Path

import joblib
import numpy as np
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import roc_auc_score

from ..config import get_settings

logger = logging.getLogger(__name__)

FEATURE_NAMES = [
    "character_score",
    "capacity_score",
    "capital_score",
    "collateral_score",
    "conditions_score",
    "promoter_holding_pct",
    "gnpa_pct",
    "nnpa_pct",
    "crar_pct",
    "debt_equity_ratio",
    "net_profit_margin_pct",
    "lcr_pct",
    "loan_to_turnover_ratio",
    "shares_pledged_pct",
    "negative_news_count",
    "legal_findings_count",
    "rating_notch",  # AAA=7, AA=6, A=5, BBB=4, BB=3, B=2, C=1, D=0
]

RATING_NOTCH_MAP = {
    "AAA": 7, "AA+": 6.5, "AA": 6, "AA-": 5.5,
    "A+": 5.5, "A": 5, "A-": 4.5,
    "BBB+": 4.5, "BBB": 4, "BBB-": 3.5,
    "BB+": 3.5, "BB": 3, "BB-": 2.5,
    "B+": 2.5, "B": 2, "B-": 1.5,
    "C": 1, "D": 0,
}


def _generate_synthetic_data(n_samples: int = 2000) -> tuple[np.ndarray, np.ndarray]:
    """Generate realistic synthetic Indian corporate credit data."""
    rng = np.random.RandomState(42)
    X = np.zeros((n_samples, len(FEATURE_NAMES)))

    # Generate correlated features that represent realistic credit profiles
    # Good credits (60% of data)
    n_good = int(n_samples * 0.6)
    n_stressed = int(n_samples * 0.25)
    n_default = n_samples - n_good - n_stressed

    for i in range(n_samples):
        if i < n_good:
            # Good credit profile
            base_quality = rng.uniform(0.6, 1.0)
            X[i] = [
                rng.uniform(65, 95),  # character
                rng.uniform(60, 90),  # capacity
                rng.uniform(60, 90),  # capital
                rng.uniform(55, 85),  # collateral
                rng.uniform(60, 85),  # conditions
                rng.uniform(40, 75),  # promoter_holding
                rng.uniform(0.5, 3.0),  # gnpa
                rng.uniform(0.1, 1.5),  # nnpa
                rng.uniform(18, 35),  # crar
                rng.uniform(2, 6),  # debt_equity
                rng.uniform(10, 30),  # net_profit_margin
                rng.uniform(110, 250),  # lcr
                rng.uniform(0.05, 0.4),  # loan_to_turnover
                rng.uniform(0, 10),  # shares_pledged
                rng.randint(0, 2),  # neg_news
                rng.randint(0, 1),  # legal
                rng.uniform(4, 7),  # rating
            ]
        elif i < n_good + n_stressed:
            # Stressed profile
            X[i] = [
                rng.uniform(35, 65),
                rng.uniform(35, 60),
                rng.uniform(35, 60),
                rng.uniform(30, 55),
                rng.uniform(35, 60),
                rng.uniform(15, 50),
                rng.uniform(3, 8),
                rng.uniform(1.5, 5),
                rng.uniform(12, 20),
                rng.uniform(5, 10),
                rng.uniform(2, 12),
                rng.uniform(80, 120),
                rng.uniform(0.3, 0.7),
                rng.uniform(10, 40),
                rng.randint(2, 5),
                rng.randint(1, 3),
                rng.uniform(2, 4),
            ]
        else:
            # Default-prone profile
            X[i] = [
                rng.uniform(15, 45),
                rng.uniform(15, 40),
                rng.uniform(15, 40),
                rng.uniform(10, 35),
                rng.uniform(15, 40),
                rng.uniform(5, 30),
                rng.uniform(6, 20),
                rng.uniform(4, 12),
                rng.uniform(8, 15),
                rng.uniform(8, 15),
                rng.uniform(-5, 5),
                rng.uniform(40, 90),
                rng.uniform(0.5, 1.2),
                rng.uniform(30, 80),
                rng.randint(3, 8),
                rng.randint(2, 6),
                rng.uniform(0, 2),
            ]

    # Labels: 0 = no default, 1 = default
    y = np.zeros(n_samples)
    y[n_good:n_good + n_stressed] = (rng.random(n_stressed) < 0.3).astype(float)
    y[n_good + n_stressed:] = (rng.random(n_default) < 0.85).astype(float)
    # Add noise to good credits
    y[:n_good] = (rng.random(n_good) < 0.03).astype(float)

    return X, y


def _get_model_path() -> Path:
    settings = get_settings()
    path = Path(settings.storage_root).parent.parent / "data" / "checkpoints"
    path.mkdir(parents=True, exist_ok=True)
    return path / "risk_model.joblib"


def _train_model() -> GradientBoostingClassifier:
    """Train the risk model on synthetic data."""
    logger.info("Training ML risk model on synthetic credit data...")
    X, y = _generate_synthetic_data(2000)
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

    model = GradientBoostingClassifier(
        n_estimators=200,
        max_depth=4,
        learning_rate=0.1,
        min_samples_split=10,
        min_samples_leaf=5,
        subsample=0.8,
        random_state=42,
    )
    model.fit(X_train, y_train)

    # Log performance
    y_pred_proba = model.predict_proba(X_test)[:, 1]
    auc = roc_auc_score(y_test, y_pred_proba)
    logger.info(f"ML risk model trained — AUC: {auc:.4f}")

    # Save model
    model_path = _get_model_path()
    joblib.dump({"model": model, "feature_names": FEATURE_NAMES, "auc": auc}, model_path)
    logger.info(f"Model saved to {model_path}")

    return model


def _load_or_train_model() -> GradientBoostingClassifier:
    model_path = _get_model_path()
    if model_path.exists():
        try:
            bundle = joblib.load(model_path)
            if isinstance(bundle, dict) and "model" in bundle:
                return bundle["model"]
            return bundle
        except Exception:
            logger.warning("Failed to load saved model, retraining...")
    return _train_model()


_cached_model: GradientBoostingClassifier | None = None


def get_model() -> GradientBoostingClassifier:
    global _cached_model
    if _cached_model is None:
        _cached_model = _load_or_train_model()
    return _cached_model


def _parse_rating_notch(rating_str: str | None) -> float:
    if not rating_str:
        return 3.0  # default to BBB-ish
    cleaned = rating_str.strip().upper().replace("CRISIL ", "").replace("ICRA ", "").replace("CARE ", "").replace("IND ", "")
    for key, val in RATING_NOTCH_MAP.items():
        if cleaned.startswith(key):
            return val
    return 3.0


def build_feature_vector(
    five_cs: dict,
    extraction_map: dict[str, any],
    research_items: list,
    case: any,
) -> np.ndarray:
    """Build feature vector from Five Cs scores and extracted data."""
    from .utils import parse_decimal

    def _num(key: str, default: float = 0.0) -> float:
        val = extraction_map.get(key)
        if val is None:
            return default
        if isinstance(val, (int, float)):
            return float(val)
        if isinstance(val, Decimal):
            return float(val)
        parsed = parse_decimal(str(val))
        return float(parsed) if parsed is not None else default

    turnover = float(case.turnover_crore or 0) if case.turnover_crore else 0
    loan_amt = float(case.loan_amount_crore or 0) if case.loan_amount_crore else 0
    loan_to_turnover = (loan_amt / turnover) if turnover > 0 else 0.5

    neg_news = sum(1 for item in research_items if getattr(item, 'sentiment', '') == 'negative')
    legal_count = sum(1 for item in research_items if getattr(item, 'category', '') == 'legal')

    rating_str = extraction_map.get("long_term_rating", "")

    features = [
        five_cs["character"].score,
        five_cs["capacity"].score,
        five_cs["capital"].score,
        five_cs["collateral"].score,
        five_cs["conditions"].score,
        _num("promoter_holding_percent", 50.0),
        _num("gnpa_percent", 2.0),
        _num("nnpa_percent", 1.0),
        _num("crar_percent", 20.0),
        _num("debt_equity_ratio", 5.0),
        _num("net_profit_margin", 10.0),
        _num("lcr_ratio", _num("lcr_percent", 120.0)),
        loan_to_turnover,
        _num("shares_pledged_percent", 5.0),
        float(neg_news),
        float(legal_count),
        _parse_rating_notch(str(rating_str) if rating_str else None),
    ]

    return np.array(features).reshape(1, -1)


def predict_default_probability(
    five_cs: dict,
    extraction_map: dict,
    research_items: list,
    case: any,
) -> dict:
    """Predict probability of default and provide explainable output."""
    model = get_model()
    X = build_feature_vector(five_cs, extraction_map, research_items, case)

    pd_probability = float(model.predict_proba(X)[0, 1])

    # Feature importance for this prediction
    importances = model.feature_importances_
    feature_impacts = []
    for i, (name, importance) in enumerate(zip(FEATURE_NAMES, importances)):
        if importance > 0.02:  # Only show meaningful features
            value = float(X[0, i])
            direction = "increases" if importance > 0.05 else "influences"
            feature_impacts.append({
                "feature": name.replace("_", " ").title(),
                "importance": round(float(importance) * 100, 1),
                "value": round(value, 2),
                "direction": direction,
            })

    feature_impacts.sort(key=lambda x: x["importance"], reverse=True)

    # ML-based risk grade
    if pd_probability < 0.05:
        ml_grade = "AAA"
    elif pd_probability < 0.08:
        ml_grade = "AA"
    elif pd_probability < 0.12:
        ml_grade = "A"
    elif pd_probability < 0.18:
        ml_grade = "BBB"
    elif pd_probability < 0.28:
        ml_grade = "BB"
    elif pd_probability < 0.45:
        ml_grade = "B"
    elif pd_probability < 0.65:
        ml_grade = "C"
    else:
        ml_grade = "D"

    settings = get_settings()
    approve_threshold = float(getattr(settings, 'pd_approve_threshold', 0.08) or 0.08)
    conditional_threshold = float(getattr(settings, 'pd_conditional_threshold', 0.16) or 0.16)

    if pd_probability <= approve_threshold:
        ml_decision = "approve"
    elif pd_probability <= conditional_threshold:
        ml_decision = "conditional_approve"
    else:
        ml_decision = "reject"

    return {
        "pd_probability": round(pd_probability, 4),
        "pd_percentage": round(pd_probability * 100, 2),
        "ml_grade": ml_grade,
        "ml_decision": ml_decision,
        "feature_impacts": feature_impacts[:10],
        "model_confidence": round(1.0 - abs(pd_probability - 0.5) * 2, 2) if pd_probability > 0.5 else round(1.0 - pd_probability, 2),
        "approve_threshold": approve_threshold,
        "conditional_threshold": conditional_threshold,
    }
