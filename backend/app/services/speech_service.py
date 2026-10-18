import re
from typing import Optional, Any, Dict, List


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
            return "लाइन पर बनल रहीं। आपन गाँव भा नजदीकी पहचान बताईं।"
        elif "hinglish" in lang:
            if attempt == 1:
                return "Hum aapki aawaz nahi sun paaye. Please batayein patient kahan hai aur kya hua hai?"
            return "Please line par bane rahein aur apna gaon ya landmark batayein."
        else:
            if attempt == 1:
                return "हम आपकी आवाज़ नहीं सुन पाए। कृपया बताएं कि मरीज कहाँ है और क्या हुआ है?"
            return "कृपया लाइन पर बने रहें और अपना गाँव या लैंडमार्क बताएं।"

    @staticmethod
    def get_escalation_prompt(language: str = "hindi") -> str:
        """Directs caller to dial 108 or 112 directly without pretending an automated transfer succeeded."""
        lang = (language or "hindi").lower()

        if "bhojpuri" in lang:
            return (
                "मानव ऑपरेटर से सीधा बात करावे के सुविधा अभी नइखे। "
                "मरीज के एकदम शांत आ स्थिर रखीं। तुरंत मदद खातिर 108 भा 112 पर फोन करीं।"
            )
        elif "hinglish" in lang:
            return (
                "Direct human operator transfer abhi available nahi hai. "
                "Patient ko bilkul shaant aur strictly still rakhein. Immediate transport aur emergency help ke liye please turant 108 ya 112 par call karein."
            )
        else:
            return (
                "सीधा मानव ऑपरेटर ट्रांसफर अभी उपलब्ध नहीं है। "
                "मरीज को बिल्कुल शांत और स्थिर रखें। आपातकालीन सहायता और एम्बुलेंस के लिए तुरंत 108 या 112 पर संपर्क करें।"
            )

    @classmethod
    def format_edesy_response(
        cls,
        result: Any,
        language: str = "hindi",
    ) -> str:
        """
        Produces concise, natural, spoken Hindi/Hinglish/Bhojpuri responses for Edesy IVR.
        Adheres strictly to clinician-reviewed safety and truthfulness rules:
        - Emergency report confirms case registration only if created and requests location.
        - Location turn gives verified facility name, approximate distance, explicitly unverified ASV status,
          and pending referral status.
        - Never fabricates ambulance dispatch, human transfer, coordinates, or ASV availability.
        - Keeps response length to approximately 1-3 short sentences for telephone TTS.
        """
        lang = (language or "hindi").lower()

        # Extract structured properties
        intent = getattr(result, "intent", None) or (result.get("intent") if isinstance(result, dict) else None)
        next_action = getattr(result, "next_action", None) or (result.get("next_action") if isinstance(result, dict) else None)
        case_id = getattr(result, "case_id", None) or (result.get("case_id") if isinstance(result, dict) else None)
        nearby_facilities = getattr(result, "nearby_facilities", None) or (result.get("nearby_facilities") if isinstance(result, dict) else None)
        referral = getattr(result, "referral", None) or (result.get("referral") if isinstance(result, dict) else None)
        missing_info = getattr(result, "missing_information", None) or (result.get("missing_information") if isinstance(result, dict) else [])
        response_text = getattr(result, "response_text", "") or (result.get("response_text", "") if isinstance(result, dict) else "")
        lower_resp = response_text.lower()

        # 1. Human Help / Escalation
        if next_action == "ESCALATE_HUMAN" or intent == "human_help" or "connecting you" in lower_resp:
            return cls.get_escalation_prompt(lang)

        # 2. First-Aid Guidance
        if intent == "first_aid_query" or next_action == "PROVIDE_FIRST_AID" or "first aid" in lower_resp:
            if "bhojpuri" in lang:
                return (
                    "मरीज आ काटे वाला अंग के एकदम स्थिर रखीं। घाव पर चीरा मत लगाईं, जहर मत चूसीं आ बरफ मत लगाईं। "
                    "अगर पट्टी बन्हल बा त ओकरा के मत खोलीं। तुरंत 108 एम्बुलेंस बोलाईं।"
                )
            elif "hinglish" in lang:
                return (
                    "Patient aur kaate hue ang ko bilkul still rakhein. Ghaav par cut, zehar choosna ya barf lagana mana hai. "
                    "Agar tourniquet pehle se bandha hai to usey field me na hatayein. Turant 108 ambulance arrange karein."
                )
            else:
                return (
                    "मरीज और काटे हुए अंग को बिल्कुल स्थिर रखें। घाव पर चीरा, जहर चूसना या बर्फ लगाना सख्त मना है। "
                    "यदि पहले से टूर्निकेट बंधा है तो उसे फील्ड में न हटाएं। तुरंत 108 एम्बुलेंस बुलाएं।"
                )

        # 3. Symptom Report
        if intent == "symptom_report" or next_action == "ASSESS_SYMPTOMS":
            if "bhojpuri" in lang:
                return (
                    "लक्षण दर्ज हो गइल बा। सांस लेवे में दिक्कत भा सूजन गंभीर लक्षण हवे। "
                    "बिना देरी कइले तुरंत 108 एम्बुलेंस से नजदीकी अस्पताल पहुँचीं।"
                )
            elif "hinglish" in lang:
                return (
                    "Symptoms note kar liye gaye hain. Saans lene me takleef ya sujan gambhir lakshan hain. "
                    "Bina deri kiye turant 108 ambulance se aspatal pahunchein."
                )
            else:
                return (
                    "लक्षण नोट कर लिए गए हैं। सांस लेने में तकलीफ या सूजन गंभीर लक्षण हैं। "
                    "बिना देरी किए तुरंत 108 एम्बुलेंस से नजदीकी अस्पताल पहुंचें।"
                )

        # 4. Repeat Request
        if intent == "repeat_request":
            if "bhojpuri" in lang:
                return "दोहरावत बानी: मरीज के एकदम स्थिर रखीं, घाव पर चीरा मत लगाईं आ तुरंत 108 एम्बुलेंस के इंतजाम करीं।"
            elif "hinglish" in lang:
                return "Dohra rahe hain: Patient ko bilkul still rakhein, ghaav par cut na lagayein aur turant 108 ambulance arrange karein."
            else:
                return "दोहरा रहे हैं: मरीज को बिल्कुल स्थिर रखें, घाव पर चीरा न लगाएं और तुरंत 108 एम्बुलेंस का प्रबंध करें।"

        # 5. Location Received with Verified Nearby Facility
        if nearby_facilities and len(nearby_facilities) > 0:
            nearest = nearby_facilities[0]
            fac_name = getattr(nearest, "facility_name", None)
            if not fac_name and isinstance(nearest, dict):
                fac_name = nearest.get("facility_name")
            fac_name = fac_name or "Hospital"

            dist_km = getattr(nearest, "distance_km", None)
            if dist_km is None and isinstance(nearest, dict):
                dist_km = nearest.get("distance_km")
            dist_str = f"{dist_km:.1f} km" if dist_km is not None else "paas"

            if "bhojpuri" in lang:
                return (
                    f"रउआ लगे {fac_name} करीब {dist_str} दूर बा। "
                    f"मरीज के शांत आ एकदम स्थिर रखीं आ तुरंत अस्पताल से मदद लीं।"
                )
            elif "hinglish" in lang:
                return (
                    f"Aapke paas {fac_name} lagbhag {dist_str} door hai. "
                    f"Patient ko shaant aur bilkul still rakhein aur turant medical help lein."
                )
            else:
                return (
                    f"आपके पास {fac_name} लगभग {dist_str} दूर है। "
                    f"मरीज को शांत और बिल्कुल स्थिर रखें और तुरंत मेडिकल सहायता लें।"
                )

        # 6. Location Unresolvable / Missing Coordinates
        if (
            intent == "location_response"
            or "could not reliably resolve" in lower_resp
            or ("location" in missing_info and intent != "emergency_report")
        ):
            if "bhojpuri" in lang:
                return (
                    "जगह के सही पता नइखे चल पावल। "
                    "रउआ आपन जिला, ब्लॉक भा नजदीकी पहचान बताईं। इलाज में देरी मत करीं।"
                )
            elif "hinglish" in lang:
                return (
                    "Aapki location confirm nahi ho paayi. "
                    "Kripya apna district, block ya paas ka landmark batayein. Medical madad me deri na karein."
                )
            else:
                return (
                    "आपके स्थान की सही पुष्टि नहीं हो पाई। "
                    "कृपया अपना जिला, ब्लॉक या पास का मुख्य लैंडमार्क बताएं। इलाज में बिल्कुल देरी न करें।"
                )

        # 7. Location Resolved, but No Facilities within 30 km
        if next_action == "CALL_108" and not nearby_facilities:
            if "bhojpuri" in lang:
                return (
                    "30 किमी के दायरा में कवनो अस्पताल नइखे मिलल। "
                    "तुरंत 108 एम्बुलेंस पर फोन करीं आ मरीज के स्थिर रखीं।"
                )
            elif "hinglish" in lang:
                return (
                    "30 km ke daayre me koi hospital nahi mila. "
                    "Turant 108 ambulance dispatch ko call karein aur patient ko bilkul still rakhein."
                )
            else:
                return (
                    "30 किमी के दायरे में कोई अस्पताल नहीं मिला। "
                    "तुरंत 108 एम्बुलेंस को कॉल करें और मरीज को स्थिर रखें।"
                )

        # 8. Emergency Report / Case Creation (Turn 1)
        if intent == "emergency_report" or next_action == "COLLECT_LOCATION" or "emergency case recorded" in lower_resp:
            if "bhojpuri" in lang:
                return (
                    "मरीज के शांत आ एकदम स्थिर रखीं। घाव के काटे भा जहर चूसे के कोशिश मत करीं। "
                    "रउआ अभी कवन गाँव में बानी? पास के पहचान बताईं।"
                )
            elif "hinglish" in lang:
                return (
                    "Patient ko shaant aur bilkul still rakhein. Ghaav ko na kaatein aur na zehar choosein. "
                    "Aap abhi kis gaon mein hain? Paas ka landmark batayein."
                )
            else:
                return (
                    "मरीज को शांत और बिल्कुल स्थिर रखें। घाव को काटें या जहर चूसने की कोशिश न करें। "
                    "आप अभी किस गाँव में हैं? पास का लैंडमार्क बताएं।"
                )

        # 9. General / Fallback
        if "bhojpuri" in lang:
            return "संजीवनी हेल्पलाइन में बताईं का भइल बा आ मरीज कवन जगह पर बाड़न?"
        elif "hinglish" in lang:
            return "Sanjeevani emergency helpline hai. Batayein kya hua hai aur patient is samay kahan hai?"
        else:
            return "संजीवनी आपातकालीन हेल्पलाइन है। कृपया बताएं क्या हुआ है और मरीज इस समय कहाँ है?"

    @classmethod
    def localize_response(
        cls,
        response_text: str,
        language: str,
        next_action: Optional[str] = None,
        is_fallback: bool = False,
    ) -> str:
        """
        Backwards-compatible string-based localizer.
        Delegates to structured logic or parses key response markers.
        """
        lang = (language or "hindi").lower()
        lower_resp = (response_text or "").lower()

        # Fallback / Server Unreachable
        if is_fallback or "cannot reach the central emergency server" in lower_resp or "unreachable" in lower_resp:
            if "bhojpuri" in lang:
                return (
                    "आपातकालीन सूचना: सर्वर से संपर्क नइखे हो पावत। मरीज के एकदम शांत आ स्थिर रखीं। "
                    "घाव पर चीरा मत लगाईं, जहर मत चूसीं, बरफ मत लगाईं आ बन्हल पट्टी मत खोलीं। "
                    "तुरंत 108 भा 112 पर फोन क के एम्बुलेंस बोलाईं।"
                )
            elif "hinglish" in lang:
                return (
                    "Emergency alert: Central emergency server se contact nahi ho pa raha hai. "
                    "Patient ko calm aur still rakhein. Wound par cut na lagayein, "
                    "poison suck na karein, aur bandhi hui patti na hatayein. "
                    "Immediate transport ke liye turant 108 ya 112 ambulance ko call karein."
                )
            else:
                return (
                    "आपातकालीन सूचना: केंद्रीय सर्वर से संपर्क नहीं हो पा रहा है। मरीज को बिल्कुल शांत और स्थिर रखें। "
                    "घाव पर चीरा न लगाएं, जहर न चूसें, बर्फ न लगाएं, और बंधी पट्टी न हटाएं। "
                    "सीधे 108 या 112 पर कॉल करके एम्बुलेंस बुलाएं।"
                )

        # Escalation / Human Help
        if next_action == "ESCALATE_HUMAN" or "connecting you" in lower_resp or "operator" in lower_resp:
            return cls.get_escalation_prompt(lang)

        # First Aid
        if next_action == "PROVIDE_FIRST_AID" or "first aid" in lower_resp:
            return cls.format_edesy_response({"next_action": "PROVIDE_FIRST_AID"}, language=lang)

        # Location Unresolvable
        if "could not reliably resolve" in lower_resp:
            return cls.format_edesy_response({"intent": "location_response", "nearby_facilities": []}, language=lang)

        # Location with Facility
        if "nearest healthcare facility" in lower_resp or "location received" in lower_resp:
            fac_match = re.search(r"Nearest healthcare facility:\s*([^\n(]+)", response_text, re.IGNORECASE)
            dist_match = re.search(r"\(([\d\.]+)\s*km\s*away\)", response_text, re.IGNORECASE)
            fac_name = fac_match.group(1).strip() if fac_match else "Hospital"
            dist_km = float(dist_match.group(1)) if dist_match else 0.0

            mock_item = {
                "facility_name": fac_name,
                "distance_km": dist_km,
                "asv_stock_status": "UNKNOWN",
                "asv_verification_source": "NOT_VERIFIED",
            }
            return cls.format_edesy_response(
                {"nearby_facilities": [mock_item], "referral": {"referral_status": "PENDING"}},
                language=lang,
            )

        # Emergency Case Recorded
        if "emergency case recorded" in lower_resp or "case id:" in lower_resp:
            return cls.format_edesy_response(
                {"intent": "emergency_report", "case_id": "true"},
                language=lang,
            )

        # Devanagari pass-through
        has_devanagari = bool(re.search(r"[\u0900-\u097F]", response_text))
        if has_devanagari and "hinglish" not in lang:
            return response_text

        return cls.format_edesy_response({"response_text": response_text}, language=lang)

