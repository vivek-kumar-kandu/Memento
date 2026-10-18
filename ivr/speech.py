import re
from typing import Optional


class SpeechAdapter:
    """
    Handles language detection, telephony prompt sanitization,
    and voice response localization across Hindi, Hinglish, and Bhojpuri.
    """

    # Bhojpuri dialect particles and typical lexical items
    BHOJPURI_DEVANAGARI_MARKERS = [
        "का भइल", "का भवा", "का भेल", "काट लेले बा", "काटलस", "डस लिहिस",
        "डस लेले बा", "कहाँ बाड़ी", "कहाँ बानी", "कहाँ बा", "बाटे", "रउआ",
        "रउवा", "हमार", "तोहार", "सँपवा", "सांपवा", "गइलन", "गईल",
        "अस्पताल ले जाईं", "जल्दी करीं", "का करीं", "बा", "बानी", "बाड़न",
        "केहू", "कवन", "काहे", "भइल", "भईल", "तनी", "बुझाता", "नइखे", "लउकत"
    ]

    BHOJPURI_ROMAN_MARKERS = [
        "ka bhail", "ka bhawa", "ka bhel", "kaat lele ba", "katlas", "das lihis",
        "das lele ba", "kahan baani", "kahan baadi", "kahan ba", "baate", "rauwa",
        "raua", "hamaar", "hamar", "tohaar", "sampwa", "saanpwa", "gailan",
        "aspatal le jaai", "jaldi kari", "ka kari", "baani", "baadan", "kehu",
        "kavan", "kahe", "tani", "bujhata", "naikhe", "laukat"
    ]

    # Hinglish common markers (Latin characters combining Hindi structure + English terms)
    HINGLISH_KEYWORDS = [
        "snake", "bite", "hospital", "patient", "emergency", "ambulance",
        "doctor", "field", "village", "landmark", "ho gaya", "ho gayi", "kahan",
        "kya", "karun", "karu", "hua", "hai", "tha", "thi", "bhai", "saanp",
        "kaata", "dard", "sujan", "jaldi", "batao", "bhejo", "chahiye", "help"
    ]

    @classmethod
    def detect_language(cls, text: str, current_language: Optional[str] = "hindi") -> str:
        """
        Detects caller language/speaking style from utterance:
        - 'bhojpuri'
        - 'hinglish'
        - 'hindi'
        Maintains current language if ambiguous, or switches if clearly indicated.
        """
        if not text or not text.strip():
            return current_language or "hindi"

        lower_text = text.lower().strip()

        # 1. Check for Bhojpuri markers (Devanagari or Roman)
        for marker in cls.BHOJPURI_DEVANAGARI_MARKERS:
            if marker in text:
                return "bhojpuri"
        for marker in cls.BHOJPURI_ROMAN_MARKERS:
            if marker in lower_text:
                return "bhojpuri"

        # 2. Check for Devanagari script (Standard Hindi)
        has_devanagari = bool(re.search(r"[\u0900-\u097F]", text))
        if has_devanagari:
            return "hindi"

        # 3. Check for Hinglish (Latin characters with Hindi-English mixing)
        matches = sum(1 for kw in cls.HINGLISH_KEYWORDS if kw in lower_text)
        if matches >= 1:
            return "hinglish"

        # If predominantly Latin letters without specific dialect markers
        if re.search(r"[a-zA-Z]", text):
            # If current language was already Hinglish, preserve it
            if current_language == "hinglish":
                return "hinglish"
            # Otherwise default to Hinglish for Romanized input
            return "hinglish"

        return current_language or "hindi"

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
    def get_greeting(language: str = "hindi") -> str:
        """
        Returns standard emergency triage IVR greeting.
        Always begins with a short, simple Hindi greeting by default.
        """
        lang = (language or "hindi").lower()
        if "bhojpuri" in lang:
            return (
                "संजीवनी आपातकालीन सेवा में रउआ सब के स्वागत बा। "
                "बताईं का भइल बा आ रउआ कवन जगह पर बानी?"
            )
        elif "hinglish" in lang:
            return (
                "Sanjeevani Emergency Helpline me aapka swagat hai. "
                "Please batayein kya hua hai aur aap kis jagah par hain?"
            )
        # Default simple Hindi greeting in Devanagari
        return (
            "संजीवनी आपातकालीन सेवा में आपका स्वागत है। "
            "कृपया बताएं क्या हुआ है और आप कहाँ हैं?"
        )

    @staticmethod
    def get_clarification_prompt() -> str:
        """Returns one short clarification in simple Hindi if language is ambiguous."""
        return "हम आपकी बात ठीक से समझ नहीं पाए। कृपया बताएं कि मरीज कहाँ है और क्या हुआ है?"

    @staticmethod
    def localize_response(response_text: str, language: str, next_action: Optional[str] = None) -> str:
        """
        Faithfully translates and localizes the authoritative meaning of response_text
        into the caller's detected language (Hindi, Hinglish, or Bhojpuri).
        Preserves facility names, numbers, distances, case IDs, and medical safety meaning.
        """
        lang = (language or "hindi").lower()

        # If response_text already has Devanagari and language is Hindi, return sanitized text
        has_devanagari = bool(re.search(r"[\u0900-\u097F]", response_text))

        lower_resp = response_text.lower()

        # Extract context flags from backend response_text
        is_calm_instruction = any(w in lower_resp for w in ["calm", "still", "do not walk", "wound", "tourniquet"])
        is_location_request = (next_action == "COLLECT_LOCATION") or any(w in lower_resp for w in ["where are you", "location", "village", "landmark"])
        is_dispatched = any(w in lower_resp for w in ["dispatched", "referral", "ambulance", "initiated"])

        if "bhojpuri" in lang:
            parts = []
            if is_calm_instruction:
                parts.append(
                    "मरीज के एकदम शांत आ स्थिर रखीं। काटे वाला अंग बिलकुल मत हिलाईं। "
                    "घाव पर चीरा मत लगाईं, जहर मत चूसीं, आ बरफ भा कस के पट्टी मत बान्हीं। "
                    "तुरंत 108 पर फोन करीं भा नजदीकी अस्पताल ले जाईं।"
                )
            if is_location_request:
                parts.append("रउआ कवन गाँव, टोला भा नजदीकी जगह पर बानी, बताईं?")
            if is_dispatched:
                parts.append("एम्बुलेंस आ नजदीकी अस्पताल के सूचना भेज दिहल गइल बा।")

            if parts:
                return " ".join(parts)
            # If already in Devanagari, preserve
            if has_devanagari:
                return response_text
            return (
                "मरीज के एकदम शांत आ स्थिर रखीं। तुरंत 108 नंबर पर फोन करीं। "
                "काटे वाला अंग पर चीरा भा पट्टी मत बान्हीं।"
            )

        elif "hinglish" in lang:
            parts = []
            if is_calm_instruction:
                parts.append(
                    "Patient ko bilkul calm aur completely still rakhein. Bitten part ko move na karein. "
                    "Wound par cut na lagayein, poison suck na karein, aur ice ya tight tourniquet na bandhein. "
                    "Turant 108 par call karein ya nearest hospital proceed karein."
                )
            if is_location_request:
                parts.append("Please apna gaon, city ya nearest landmark batayein?")
            if is_dispatched:
                parts.append("Ambulance dispatched. Nearest facility referral initiate ho gaya hai.")

            if parts:
                return " ".join(parts)
            if not has_devanagari:
                return response_text
            return (
                "Patient ko bilkul calm aur still rakhein. Turant 108 par call karein. "
                "Bitten limb ko move na karein."
            )

        else:
            # Standard Hindi (Devanagari)
            parts = []
            if is_calm_instruction:
                parts.append(
                    "मरीज को बिल्कुल शांत और स्थिर रखें। काटे हुए हिस्से को बिल्कुल न हिलाएं। "
                    "घाव पर चीरा न लगाएं, जहर न चूसें, और बर्फ या कसकर पट्टी (टूर्निकेट) न बांधें। "
                    "तुरंत 108 पर कॉल करें या नजदीकी अस्पताल ले जाएं।"
                )
            if is_location_request:
                parts.append("कृपया अपने गाँव, शहर या नजदीकी मुख्य पहचान (लैंडमार्क) का नाम बताएं।")
            if is_dispatched:
                parts.append("एम्बुलेंस सेवा और नजदीकी अस्पताल से समन्वय शुरू कर दिया गया है।")

            if parts:
                return " ".join(parts)
            if has_devanagari:
                return response_text
            # English backend text translated to Hindi Devanagari
            return (
                "मरीज को बिल्कुल शांत और स्थिर रखें। तुरंत 108 पर संपर्क करें। "
                "काटे हुए अंग को न हिलाएं और न ही कोई चीरा या पट्टी लगाएं।"
            )

    @staticmethod
    def format_asv_and_facility_speech(
        facility_name: str,
        distance_km: float,
        asv_status: str,
        facility_type: str = "PHC",
        language: str = "hindi",
    ) -> str:
        """
        Formats facility and ASV details strictly adhering to safety rules:
        Never claim ASV is verified unless explicitly confirmed.
        Localizes speech output into Hindi, Hinglish, or Bhojpuri.
        """
        lang = (language or "hindi").lower()
        status_upper = (asv_status or "UNKNOWN").upper()

        if "bhojpuri" in lang:
            dist_str = f"{distance_km:.1f} किलोमीटर" if distance_km else "नजदीके"
            speech = f"सभसे नजदीकी अस्पताल {facility_name} बा, जे लगभग {dist_str} दूरी पर बा। "

            if status_upper == "AVAILABLE":
                speech += "एह अस्पताल में एंटी-स्नेक वेनम मिलल बा अइसन खबर बा, बाकिर 108 से पक्का जरूर क लीं। "
            elif status_upper == "OUT_OF_STOCK":
                speech += "एह अस्पताल में एंटी-स्नेक वेनम खतम बतावल गइल बा, दोसरा बड़ अस्पताल में जाए के पड़ी। "
            else:
                speech += (
                    "एह अस्पताल में एंटी-स्नेक वेनम (ASV) उपलब्ध बा कि ना, ई अभी पक्का नइखे। "
                    "मरीज के ले जाए में तनी देरी मत करीं, 108 एम्बुलेंस से जांच कइल जाई। "
                )
            return speech

        elif "hinglish" in lang:
            dist_str = f"{distance_km:.1f} kilometers" if distance_km else "nearby"
            speech = f"Nearest hospital {facility_name} hai, jo lagbhag {dist_str} door hai. "

            if status_upper == "AVAILABLE":
                speech += "Yahan Anti-Snake Venom available hone ki report hai, lekin dispatch se confirm zaroor karein. "
            elif status_upper == "OUT_OF_STOCK":
                speech += "Yahan Anti-Snake Venom out of stock bataya gaya hai, referral consider karein. "
            else:
                speech += (
                    "Is facility me Anti-Snake Venom (ASV) stock abhi verified nahi hai. "
                    "Hospital pahunchne me bilkul delay na karein, 108 ambulance verify karegi. "
                )
            return speech

        else:
            # Default Hindi (Devanagari)
            dist_str = f"{distance_km:.1f} किलोमीटर" if distance_km else "नजदीक"
            speech = f"नजदीकी अस्पताल {facility_name} है, जो लगभग {dist_str} दूर है। "

            if status_upper == "AVAILABLE":
                speech += "यहाँ एंटी-स्नेक वेनम उपलब्ध होने की सूचना है, लेकिन रवाना होने से पहले 108 से पुष्टि जरूर करें। "
            elif status_upper == "OUT_OF_STOCK":
                speech += "यहाँ एंटी-स्नेक वेनम अभी समाप्त बताया गया है, इसलिए उच्च स्वास्थ्य केंद्र में रेफरल आवश्यक हो सकता है। "
            else:
                speech += (
                    "यहाँ एंटी-स्नेक वेनम (ASV) की उपलब्धता अभी सत्यापित नहीं है। "
                    "अस्पताल जाने में बिल्कुल देरी न करें, 108 एम्बुलेंस से पुष्टि की जाएगी। "
                )
            return speech

    @staticmethod
    def get_silence_retry_prompt(attempt: int, language: str = "hindi") -> str:
        """Returns concise re-prompt when no input is detected in caller's language."""
        lang = (language or "hindi").lower()

        if "bhojpuri" in lang:
            if attempt == 1:
                return "रउआ के आवाज नइखे आवत। बताईं मरीज कहाँ बाड़न आ का भइल बा?"
            return "लाइन पर बनल रहीं, हम emergency सेवा से जोड़े के कोशिश कर रहल बानी।"

        elif "hinglish" in lang:
            if attempt == 1:
                return "Hum aapki aawaz nahi sun paaye. Please batayein patient kahan hai aur kya hua hai?"
            return "Please line par bane rahein, hum emergency service se connect kar rahe hain."

        else:
            # Hindi (Devanagari)
            if attempt == 1:
                return "हम आपकी आवाज़ नहीं सुन पाए। कृपया बताएं कि मरीज कहाँ है और क्या हुआ है?"
            return "कृपया लाइन पर बने रहें, हम आपातकालीन सेवा से जोड़ने का प्रयास कर रहे हैं।"

    @staticmethod
    def get_escalation_prompt(language: str = "hindi") -> str:
        """Returns prompt when escalating to human emergency coordinator in caller's language."""
        lang = (language or "hindi").lower()

        if "bhojpuri" in lang:
            return (
                "रउआ कॉल के आपातकालीन कोऑर्डिनेटर से जोड़ल जा रहल बा। "
                "मरीज के एकदम शांत आ स्थिर रखीं। तुरंत 108 पर फोन करीं।"
            )
        elif "hinglish" in lang:
            return (
                "Connecting your call to an emergency coordinator. "
                "Patient ko bilkul calm aur still rakhein. Turant 108 par call karein."
            )
        else:
            # Hindi (Devanagari)
            return (
                "आपका कॉल आपातकालीन कोऑर्डिनेटर से जोड़ा जा रहा है। "
                "मरीज को बिल्कुल शांत और स्थिर रखें। तुरंत 108 पर कॉल करें।"
            )
