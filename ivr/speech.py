import re
from typing import Optional


class SpeechAdapter:
    """Formats and sanitizes speech prompts for telephony TTS synthesis."""

    @staticmethod
    def sanitize_for_tts(text: str) -> str:
        """Removes markdown artifacts, URLs, and formatting unsuitable for phone audio synthesis."""
        if not text:
            return ""

        # Remove URLs
        text = re.sub(r"https?://\S+|www\.\S+", "", text)
        # Remove markdown bold/italics
        text = re.sub(r"[*_~`#]", "", text)
        # Remove bullet points and numbered list markers
        text = re.sub(r"^\s*[-*+]\s+", "", text, flags=re.MULTILINE)
        text = re.sub(r"^\s*\d+\.\s+", "", text, flags=re.MULTILINE)
        # Collapse multiple spaces or newlines into a single space
        text = re.sub(r"\s+", " ", text).strip()

        return text

    @staticmethod
    def format_asv_and_facility_speech(
        facility_name: str,
        distance_km: float,
        asv_status: str,
        facility_type: str = "PHC",
    ) -> str:
        """
        Formats facility and ASV details strictly adhering to safety rules:
        Never claim ASV is verified unless explicitly confirmed.
        """
        dist_str = f"{distance_km:.1f} kilometers" if distance_km else "nearby"
        speech = f"Nearest facility is {facility_name}, approximately {dist_str} away. "

        if asv_status.upper() == "AVAILABLE":
            speech += "Anti-snake venom has been reported available, but dispatch should still confirm. "
        elif asv_status.upper() == "OUT_OF_STOCK":
            speech += "Anti-snake venom is reported out of stock at this center; emergency transport should consider referral. "
        else:
            # Baseline is UNKNOWN / UNVERIFIED
            speech += (
                "Anti-snake venom inventory status is unverified at this location. "
                "Do not delay transport. 108 ambulance dispatch will coordinate verified antivenom. "
            )

        return speech

    @staticmethod
    def get_greeting(language: str = "en") -> str:
        """Returns standard emergency triage IVR greeting."""
        if language.lower().startswith("hi"):
            return (
                "Sanjeevani emergency helpline mein aapka swagat hai. "
                "Kripya aapatkaal ke baare mein batayein. Agar kisi ko saanp ne kaata hai, "
                "toh bataiye kya hua aur aap kis jagah par hain."
            )
        return (
            "Welcome to Sanjeevani Emergency Assistance. "
            "Please describe the emergency. If someone was bitten by a snake, "
            "tell us what happened and your current location."
        )

    @staticmethod
    def get_silence_retry_prompt(attempt: int, language: str = "en") -> str:
        """Returns concise re-prompt when no input is detected."""
        if language.lower().startswith("hi"):
            if attempt == 1:
                return "Hum aapki aawaaz nahi sun paaye. Kripya batayein, patient kahan hai aur kya sthiti hai?"
            return "Kripya line par bane rahein, hum aapko emergency helpline se jodne ka prayas kar rahe hain."

        if attempt == 1:
            return "We could not hear your response. Please describe what happened, or tell us your location."
        return "Please remain on the line while we connect you to emergency support."

    @staticmethod
    def get_escalation_prompt(language: str = "en") -> str:
        """Returns prompt when escalating to human emergency coordinator."""
        if language.lower().startswith("hi"):
            return (
                "Hum aapka call emergency coordinator ko connect kar rahe hain. "
                "Kripya patient ko bilkul shaant aur sthir rakhein. Turant 108 par call karein."
            )
        return (
            "Connecting your call to an emergency coordinator. "
            "Please keep the patient completely calm and still. Dial 108 immediately if transport is needed."
        )
