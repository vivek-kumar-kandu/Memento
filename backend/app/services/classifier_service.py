import re
from pathlib import Path
from typing import Tuple, Dict, Any
import joblib

from app.core.logging import logger

MODEL_PATH = Path(__file__).resolve().parent.parent / "ml" / "intent_classifier.joblib"

# Clinician-safety and emergency override triggers (Hinglish, Hindi, English)
EMERGENCY_KEYWORDS = [
    "snake",
    "saanp",
    "sanp",
    "saap",
    "bite",
    "bitten",
    "kaat",
    "kat",
    "das",
    "zehar",
    "zahar",
    "poison",
    "venom",
    "cobra",
    "krait",
    "viper",
    "सांप",
    "डस",
    "काटा",
    "काट",
    "जहर",
    "इमरजेंसी",
    "आपातकाल",
]

HUMAN_HELP_KEYWORDS = [
    "human",
    "doctor",
    "operator",
    "agent",
    "officer",
    "insaan",
    "aadmi",
    "person",
    "बात कराओ",
    "बात करवाइए",
    "इंसान",
    "डॉक्टर",
    "ऑपरेटर",
    "अधिकारी",
    "talk to",
    "speak to",
]


class ClassifierService:
    def __init__(self, model_path: Path = MODEL_PATH):
        self.model_path = model_path
        self._pipeline = None
        self._load_model()

    def _load_model(self) -> None:
        try:
            if self.model_path.exists():
                self._pipeline = joblib.load(self.model_path)
                logger.info(f"Loaded intent classification pipeline from {self.model_path}")
            else:
                logger.warning(f"Intent model file not found at {self.model_path}. Will use heuristic fallback.")
        except Exception as e:
            logger.error(f"Failed to load intent model: {e}", exc_info=True)
            self._pipeline = None

    def check_safety_overrides(self, text: str) -> Tuple[bool, bool]:
        """Independent safety rules: identify emergency or human escalation without model dependency."""
        lowered = text.lower()

        is_emergency = any(kw in lowered for kw in EMERGENCY_KEYWORDS)
        is_human = any(kw in lowered for kw in HUMAN_HELP_KEYWORDS)

        return is_emergency, is_human

    def predict_intent(self, text: str) -> Dict[str, Any]:
        """
        Predict intent with confidence, respecting deterministic safety and escalation overrides.
        Returns dict with: intent, confidence, safety_override (None, 'emergency_report', 'human_help').
        """
        if not text or not text.strip():
            return {
                "intent": "unknown",
                "confidence": 1.0,
                "safety_override": None,
                "is_emergency": False,
                "is_human_escalation": False,
            }

        is_emergency, is_human = self.check_safety_overrides(text)

        # 1. Human help override: highest priority for live escalation
        if is_human and not is_emergency:
            return {
                "intent": "human_help",
                "confidence": 1.0,
                "safety_override": "human_help",
                "is_emergency": False,
                "is_human_escalation": True,
            }

        # 2. Model inference
        predicted_intent = "unknown"
        confidence = 0.5

        if self._pipeline is not None:
            try:
                probs = self._pipeline.predict_proba([text])[0]
                classes = self._pipeline.classes_
                best_idx = probs.argmax()
                predicted_intent = classes[best_idx]
                confidence = float(probs[best_idx])

                # Safe fallback if classifier uncertainty is high
                if confidence < 0.35 and predicted_intent != "emergency_report":
                    predicted_intent = "unknown"
            except Exception as e:
                logger.error(f"Inference error: {e}", exc_info=True)
                predicted_intent = "unknown"
                confidence = 0.0

        # 3. Emergency safety override: If emergency keywords are present, NEVER let low model confidence drop an emergency
        if is_emergency and predicted_intent not in ["emergency_report", "symptom_report", "first_aid_query"]:
            logger.warning(
                f"Emergency keyword detected in utterance '{text}' but model predicted '{predicted_intent}' ({confidence:.2f}). "
                "Overriding to emergency_report for patient safety."
            )
            predicted_intent = "emergency_report"
            confidence = max(confidence, 0.95)
            override = "emergency_report"
        else:
            override = None

        return {
            "intent": predicted_intent,
            "confidence": round(confidence, 4),
            "safety_override": override,
            "is_emergency": is_emergency or predicted_intent == "emergency_report",
            "is_human_escalation": is_human or predicted_intent == "human_help",
        }


classifier_service = ClassifierService()
