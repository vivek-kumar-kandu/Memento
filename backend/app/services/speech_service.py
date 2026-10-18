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
        "kaata", "dard", "sujan", "jaldi", "batao", "bhejo", "chahiye", "help",
        "madad", "nearest"
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
    def get_silence_retry_prompt(attempt: int, language: str = "hindi") -> str:
        """Returns concise re-prompt when no input is detected in caller's language."""
        lang = (language or "hindi").lower()

        if "bhojpuri" in lang:
            if attempt == 1:
                return "रउआ के आवाज नइखे आवत। बताईं मरीज कहाँ बाड़न आ का भइल बा?"
            return "लाइन पर बनल रहीं, हम emergency सहायता जोड़े के कोशिश कर रहल बानी।"
        elif "hinglish" in lang:
            if attempt == 1:
                return "Hum aapki aawaz nahi sun paaye. Please batayein patient kahan hai aur kya hua hai?"
            return "Please line par bane rahein, hum emergency help connect karne ki koshish kar rahe hain."
        else:
            if attempt == 1:
                return "हम आपकी आवाज़ नहीं सुन पाए। कृपया बताएं कि मरीज कहाँ है और क्या हुआ है?"
            return "कृपया लाइन पर बने रहें, हम आपातकालीन सहायता से जोड़ने का प्रयास कर रहे हैं।"

    @staticmethod
    def get_escalation_prompt(language: str = "hindi") -> str:
        """Directs caller to dial 108 or 112 directly."""
        lang = (language or "hindi").lower()

        if "bhojpuri" in lang:
            return (
                "मानव ऑपरेटर से सीधा बात करावे के सुविधा अभी नइखे। "
                "मरीज के एकदम शांत आ स्थिर रखीं। तुरंत मदद भा एम्बुलेंस खातिर 108 नंबर पर फोन करीं।"
            )
        elif "hinglish" in lang:
            return (
                "Direct human operator transfer abhi available nahi hai. "
                "Patient ko bilkul calm aur strictly still rakhein. Immediate transport aur emergency help ke liye please turant 108 ya 112 par call karein."
            )
        else:
            return (
                "मानव ऑपरेटर का सीधा ट्रांसफर अभी उपलब्ध नहीं है। "
                "मरीज को बिल्कुल शांत और स्थिर रखें। आपातकालीन सहायता या एम्बुलेंस के लिए तुरंत 108 या 112 पर संपर्क करें।"
            )

    @staticmethod
    def localize_response(
        response_text: str,
        language: str,
        next_action: Optional[str] = None,
        is_fallback: bool = False,
    ) -> str:
        lang = (language or "hindi").lower()
        lower_resp = (response_text or "").lower()

        # 1. Fallback / Server Unreachable Handling
        if is_fallback or "cannot reach the central emergency server" in lower_resp or "unreachable" in lower_resp:
            if "bhojpuri" in lang:
                return (
                    "आपातकालीन सूचना: सर्वर से संपर्क नइखे हो पावत। मरीज के एकदम शांत आ स्थिर रखीं। "
                    "घाव पर चीरा मत लगाईं, जहर मत चूसीं, बरफ मत लगाईं आ बन्हल पट्टी मत खोलीं। "
                    "तुरंत 108 भा 112 पर फोन क के एम्बुलेंस बोलाईं।"
                )
            elif "hinglish" in lang:
                return (
                    "Emergency alert: Central emergency server se abhi contact nahi ho pa raha hai. "
                    "Patient ko bilkul calm aur strictly still rakhein. Wound par cut na lagayein, "
                    "poison suck na karein, aur bandhi hui patti na hatayein. "
                    "Immediate transport ke liye please turant 108 ya 112 ambulance ko call karein."
                )
            else:
                return (
                    "आपातकालीन सूचना: केंद्रीय सर्वर से अभी संपर्क नहीं हो पा रहा है। मरीज को बिल्कुल शांत और स्थिर रखें। "
                    "घाव पर चीरा न लगाएं, जहर न चूसें, बर्फ न लगाएं, और बंधी पट्टी न हटाएं। "
                    "सीधे 108 या 112 पर कॉल करके एम्बुलेंस बुलाएं।"
                )

        # 2. Check for Case ID in response
        case_match = re.search(r"Case ID:\s*([A-Za-z0-9\-]+)", response_text, re.IGNORECASE)
        cid_str = case_match.group(1) if case_match else None

        if cid_str or "emergency case recorded" in lower_resp:
            cid_display = f" (Case ID: {cid_str})" if cid_str else ""
            if "bhojpuri" in lang:
                return (
                    f"आपातकालीन केस दर्ज हो गइल बा{cid_display}। मरीज के एकदम शांत आ स्थिर रखीं। "
                    f"घाव पर चीरा मत लगाईं आ जहर मत चूसीं। अगर पट्टी बन्हल बा त ओकरा के मत खोलीं। "
                    f"रउआ कवन गाँव भा नजदीकी जगह पर बानी, बताईं?"
                )
            elif "hinglish" in lang:
                return (
                    f"Emergency case record ho gaya hai{cid_display}. Patient ko bilkul calm aur strictly still rakhein. "
                    f"Bite wound par cut ya suck na karein. Agar tourniquet pehle se bandha hai, to use remove na karein. "
                    f"Please apna current village, landmark ya location batayein taaki nearest hospital route kiya ja sake."
                )
            else:
                return (
                    f"आपातकालीन केस दर्ज कर लिया गया है{cid_display}। मरीज को बिल्कुल शांत और स्थिर रखें। "
                    f"काटे हुए घाव पर चीरा न लगाएं और जहर न चूसें। यदि पहले से पट्टी बंधी है, तो उसे बिल्कुल न हटाएं। "
                    f"कृपया अपना गाँव, शहर या नजदीकी मुख्य पहचान बताएं ताकि नजदीकी अस्पताल का रास्ता बताया जा सके।"
                )

        # 3. Location / Facility referral turn
        if "location received" in lower_resp or "nearest healthcare facility" in lower_resp:
            fac_match = re.search(r"Nearest healthcare facility:\s*([^\n(]+)", response_text, re.IGNORECASE)
            dist_match = re.search(r"\(([\d\.]+)\s*km\s*away\)", response_text, re.IGNORECASE)

            fac_name = fac_match.group(1).strip() if fac_match else "Nearest PHC"
            dist_str = f"{dist_match.group(1)} km" if dist_match else "nearby"

            ref_status = "PENDING"
            if "status confirmed" in lower_resp:
                ref_status = "CONFIRMED"

            if "bhojpuri" in lang:
                return (
                    f"जगह के जानकारी मिल गइल। सभसे नजदीकी अस्पताल: {fac_name} ({dist_str})। "
                    f"रेफरल स्थिति: {ref_status}। 108 एम्बुलेंस से तुरंत अस्पताल जाए के इंतजाम करीं। "
                    f"काटे वाला अंग के एकदम स्थिर रखीं।"
                )
            elif "hinglish" in lang:
                return (
                    f"Location receive ho gaya hai. Nearest healthcare facility: {fac_name} ({dist_str}). "
                    f"Referral status: {ref_status}. Please 108 ambulance se immediate transport arrange karein. "
                    f"Bitten limb ko strictly immobilized aur still rakhein."
                )
            else:
                return (
                    f"स्थान प्राप्त हुआ। नजदीकी स्वास्थ्य केंद्र: {fac_name} ({dist_str})। "
                    f"रेफरल स्थिति: {ref_status}। कृपया 108 एम्बुलेंस द्वारा तुरंत मरीज को अस्पताल ले जाने की व्यवस्था करें। "
                    f"काटे हुए अंग को स्थिर रखें।"
                )

        # 3b. Location clarification turn (unresolved or ambiguous location)
        if "could not reliably resolve" in lower_resp or (next_action == "COLLECT_LOCATION" and "case recorded" not in lower_resp):
            if "bhojpuri" in lang:
                return (
                    "जगह साफ नइखे बुझात। रउआ नजदीकी ब्लॉक, तहसील भा प्रमुख शहर/कस्बा के नाम बताईं "
                    "ताकि नजदीकी अस्पताल खोजल जा सके। मरीज के शांत राखीं आ तुरंत 108 एम्बुलेंस बोलाईं।"
                )
            elif "hinglish" in lang:
                return (
                    "Location confirm nahi ho paayi. Kripya apna nazdeeki block, tehsil, ya bada shahar/landmark "
                    "batayein taaki nazdeeki hospital khoja ja sake. Patient ko bilkul sthir rakhein aur 108 ambulance ko call karein."
                )
            else:
                return (
                    "स्थान स्पष्ट रूप से नहीं मिल सका। कृपया अपना नजदीकी ब्लॉक, तहसील या प्रमुख शहर/कस्बा बताएं "
                    "ताकि नजदीकी अस्पताल खोजा जा सके। मरीज को बिल्कुल स्थिर रखें और 108 एम्बुलेंस से संपर्क करें।"
                )

        # 4. Devanagari pass-through
        has_devanagari = bool(re.search(r"[\u0900-\u097F]", response_text))
        if has_devanagari and "hinglish" not in lang:
            return response_text

        # 5. Default safe guidance
        if "bhojpuri" in lang:
            return (
                "मरीज के एकदम शांत आ स्थिर रखीं। तुरंत 108 नंबर पर फोन करीं। "
                "काटे वाला अंग पर चीरा भा बरफ मत लगाईं।"
            )
        elif "hinglish" in lang:
            return (
                "Patient ko bilkul calm aur strictly still rakhein. Turant 108 ambulance par call karein. "
                "Bitten limb ko bilkul move na karein."
            )
        else:
            return (
                "मरीज को बिल्कुल शांत और स्थिर रखें। तुरंत 108 पर संपर्क करें। "
                "काटे हुए अंग को न हिलाएं और न ही कोई चीरा या बर्फ लगाएं।"
            )
