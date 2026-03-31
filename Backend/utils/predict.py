import pickle
import os
import math
from typing import Dict, Any

from .nlp_utils import extract_entities, analyze_sentiment
from .term_sheet_validator import validate_term_sheet_structure, combine_ml_and_structure

current_dir = os.path.dirname(os.path.abspath(__file__))
model_dir = os.path.join(os.path.dirname(current_dir), 'model')
model_path = os.path.join(model_dir, 'model.pkl')
vectorizer_path = os.path.join(model_dir, 'vectorizer.pkl')
MAX_AUX_NLP_CHARS = 8_000


class _FallbackModel:
    classes_ = ["invalid", "valid"]

    def predict(self, X):
        return ["invalid"] * X.shape[0]

    def decision_function(self, X):
        return [0.0] * X.shape[0]


# Load model and vectorizer
MODEL_LOADED = False
MODEL_LOAD_ERROR = None
try:
    with open(model_path, 'rb') as f:
        model = pickle.load(f)
    with open(vectorizer_path, 'rb') as f:
        vectorizer = pickle.load(f)
    MODEL_LOADED = True
except Exception as e:
    MODEL_LOAD_ERROR = str(e)
    print(f"Error loading model: {MODEL_LOAD_ERROR}")
    # Safe fallback model/vectorizer for local testing
    from sklearn.feature_extraction.text import TfidfVectorizer

    vectorizer = TfidfVectorizer(max_features=100)
    vectorizer.fit(["sample term sheet text"])
    model = _FallbackModel()


def get_model_status() -> Dict[str, Any]:
    return {
        "model_loaded": MODEL_LOADED,
        "model_path": model_path,
        "vectorizer_path": vectorizer_path,
        "load_error": MODEL_LOAD_ERROR,
    }


def _compute_confidence_details(X_vec, prediction: str) -> Dict[str, Any]:
    details: Dict[str, Any] = {
        "model_confidence": None,
        "confidence_method": None,
        "class_probabilities": None,
    }

    if hasattr(model, "predict_proba"):
        try:
            probabilities = model.predict_proba(X_vec)[0]
            classes = [str(cls) for cls in getattr(model, "classes_", [])]
            class_probs = {
                cls: float(probabilities[idx]) for idx, cls in enumerate(classes)
            }
            details["model_confidence"] = float(max(probabilities))
            details["confidence_method"] = "predict_proba"
            details["class_probabilities"] = class_probs
            return details
        except Exception:
            pass

    if hasattr(model, "decision_function"):
        try:
            decision = model.decision_function(X_vec)
            # Binary margin style score.
            if hasattr(decision, "shape") and len(decision.shape) == 1:
                margin = abs(float(decision[0]))
                details["model_confidence"] = float(1 / (1 + math.exp(-margin)))
                details["confidence_method"] = "decision_margin"
                return details

            # Multiclass decision scores.
            row = decision[0]
            raw_scores = [float(x) for x in row]
            max_score = max(raw_scores)
            exp_scores = [math.exp(score - max_score) for score in raw_scores]
            denom = sum(exp_scores) if exp_scores else 1.0
            softmax_probs = [value / denom for value in exp_scores]
            classes = [str(cls) for cls in getattr(model, "classes_", [])]
            class_probs = {
                cls: float(softmax_probs[idx]) for idx, cls in enumerate(classes)
            }
            details["model_confidence"] = class_probs.get(prediction, max(softmax_probs))
            details["confidence_method"] = "decision_softmax"
            details["class_probabilities"] = class_probs
        except Exception:
            pass

    return details

def predict_text(text):
    """Predict the class of the given text using the trained model"""
    if not isinstance(text, str):
        text = ""

    # Keep feature text aligned with training data representation.
    feature_text = " ".join(text.split())
    
    try:
        X_vec = vectorizer.transform([feature_text])
        prediction = str(model.predict(X_vec)[0])
        confidence_details = _compute_confidence_details(X_vec, prediction)
    except Exception as e:
        print(f"Error during prediction: {e}")
        prediction = "Unable to predict"
        confidence_details = {
            "model_confidence": None,
            "confidence_method": "prediction_error",
            "class_probabilities": None,
        }
    
    # Auxiliary NLP on a short slice to keep response latency stable.
    aux_text = text[:MAX_AUX_NLP_CHARS]
    entities = extract_entities(aux_text)
    sentiment = analyze_sentiment(aux_text)
    structure_validation = validate_term_sheet_structure(text)
    final_assessment = combine_ml_and_structure(prediction, structure_validation)
    
    return {
        'prediction': prediction,
        'model_confidence': confidence_details["model_confidence"],
        'confidence_method': confidence_details["confidence_method"],
        'class_probabilities': confidence_details["class_probabilities"],
        'text_length_raw': len(text),
        'text_length_processed': len(feature_text),
        'entities': list(entities),
        'sentiment': sentiment,
        'structure_validation': structure_validation,
        'final_assessment': final_assessment,
        'model_status': get_model_status(),
    }
