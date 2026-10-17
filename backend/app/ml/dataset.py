"""Labelled dataset for Dhwani-Sanjeevani emergency intent classification.

Includes representative utterances in English, Hindi (Devanagari), and Roman Hindi/Hinglish.
Each record has:
- text: The utterance string.
- intent: Target intent class (one of 7).
- group_id: Cluster/family identifier to prevent data leakage during train/test splits.
"""

INTENT_CLASSES = [
    "emergency_report",
    "location_response",
    "symptom_report",
    "first_aid_query",
    "repeat_request",
    "human_help",
    "unknown",
]

DATASET = [
    # --- emergency_report ---
    # English
    {"text": "A snake bit my brother, please help us immediately", "intent": "emergency_report", "group_id": "em_en_1"},
    {"text": "Snake bite emergency, my brother was bitten by a snake", "intent": "emergency_report", "group_id": "em_en_1"},
    {"text": "Emergency! Someone here has been bitten by a snake", "intent": "emergency_report", "group_id": "em_en_2"},
    {"text": "Urgent snakebite incident, need ambulance immediately", "intent": "emergency_report", "group_id": "em_en_2"},
    {"text": "A farmer in our field just got bitten by a cobra", "intent": "emergency_report", "group_id": "em_en_3"},
    {"text": "Snake attacked my father in the farm, emergency", "intent": "emergency_report", "group_id": "em_en_3"},
    {"text": "We need emergency snakebite treatment right now", "intent": "emergency_report", "group_id": "em_en_4"},
    {"text": "Snake bite case, send help as soon as possible", "intent": "emergency_report", "group_id": "em_en_4"},
    {"text": "A venomous snake has bitten a child, please help", "intent": "emergency_report", "group_id": "em_en_5"},
    {"text": "Child bitten by snake in house, urgent assistance needed", "intent": "emergency_report", "group_id": "em_en_5"},
    {"text": "My mother was bitten by a snake while sleeping", "intent": "emergency_report", "group_id": "em_en_6"},

    # Hinglish / Roman Hindi
    {"text": "Bhai ko saanp ne kaat liya hai jaldi aao", "intent": "emergency_report", "group_id": "em_hi_rom_1"},
    {"text": "Mere bhai ko snake ne kaat liya hai emergency hai", "intent": "emergency_report", "group_id": "em_hi_rom_1"},
    {"text": "Saanp kaat liya hai emergency hai madad bhejo", "intent": "emergency_report", "group_id": "em_hi_rom_2"},
    {"text": "Jaldi ambulance bhejiye saanp ne kaat liya", "intent": "emergency_report", "group_id": "em_hi_rom_2"},
    {"text": "Khet me pitaji ko saap ne das liya hai", "intent": "emergency_report", "group_id": "em_hi_rom_3"},
    {"text": "Khet me sanp ne kaat khaya hai jaldi madad chahiye", "intent": "emergency_report", "group_id": "em_hi_rom_3"},
    {"text": "Ghar me bache ko saanp ne kaat liya bacha lijiye", "intent": "emergency_report", "group_id": "em_hi_rom_4"},
    {"text": "Snake bite hua hai khoon beh raha hai bahut emergency hai", "intent": "emergency_report", "group_id": "em_hi_rom_5"},
    {"text": "Saap kaat liya hai patient behosh ho raha hai", "intent": "emergency_report", "group_id": "em_hi_rom_6"},

    # Hindi (Devanagari)
    {"text": "सांप ने काट लिया है जल्दी मदद भेजिए", "intent": "emergency_report", "group_id": "em_hi_dev_1"},
    {"text": "मेरे भाई को सांप ने डस लिया है जल्दी आइए", "intent": "emergency_report", "group_id": "em_hi_dev_1"},
    {"text": "खेत में सांप ने काट लिया बहुत बड़ी इमरजेंसी है", "intent": "emergency_report", "group_id": "em_hi_dev_2"},
    {"text": "सांप का काटा हुआ मरीज है तुरंत एम्बुलेंस भेजो", "intent": "emergency_report", "group_id": "em_hi_dev_2"},
    {"text": "बच्चे को जहरीले सांप ने काट लिया है बचाइए", "intent": "emergency_report", "group_id": "em_hi_dev_3"},
    {"text": "सांप ने डस लिया है मरीज की हालत खराब हो रही है", "intent": "emergency_report", "group_id": "em_hi_dev_4"},

    # --- location_response ---
    # English
    {"text": "We are near Bakshi Ka Talab in Lucknow", "intent": "location_response", "group_id": "loc_en_1"},
    {"text": "Location is Bakshi Ka Talab, near railway crossing", "intent": "location_response", "group_id": "loc_en_1"},
    {"text": "Our village is Mohanlalganj, Lucknow district", "intent": "location_response", "group_id": "loc_en_2"},
    {"text": "We are situated in Mohanlalganj near the main market", "intent": "location_response", "group_id": "loc_en_2"},
    {"text": "We are at latitude 26.8467 and longitude 80.9462", "intent": "location_response", "group_id": "loc_en_3"},
    {"text": "Coordinates are 26.90 degrees north 80.95 degrees east", "intent": "location_response", "group_id": "loc_en_3"},
    {"text": "Near Rampur primary school, village Rampur", "intent": "location_response", "group_id": "loc_en_4"},
    {"text": "We are 5 kilometers away from Sitapur highway toll plaza", "intent": "location_response", "group_id": "loc_en_5"},
    {"text": "Malihabad mango orchard sector 4", "intent": "location_response", "group_id": "loc_en_6"},

    # Hinglish / Roman Hindi
    {"text": "Hum log Bakshi Ka Talab ke paas khade hain", "intent": "location_response", "group_id": "loc_hi_rom_1"},
    {"text": "Location BKT block Lucknow hai", "intent": "location_response", "group_id": "loc_hi_rom_1"},
    {"text": "Humara gaon Mohanlalganj me hai mandir ke samne", "intent": "location_response", "group_id": "loc_hi_rom_2"},
    {"text": "Mohanlalganj tehsil ke paas hain hum", "intent": "location_response", "group_id": "loc_hi_rom_2"},
    {"text": "Rampur gaon me hain primary school ke paas", "intent": "location_response", "group_id": "loc_hi_rom_3"},
    {"text": "Sitapur road toll plaza ke nazdeek hain", "intent": "location_response", "group_id": "loc_hi_rom_4"},
    {"text": "Malihabad road par petrol pump ke samne", "intent": "location_response", "group_id": "loc_hi_rom_5"},

    # Hindi (Devanagari)
    {"text": "हम बक्शी का तालाब लखनऊ के पास हैं", "intent": "location_response", "group_id": "loc_hi_dev_1"},
    {"text": "हमारी लोकेशन बक्शी का तालाब है रेलवे क्रॉसिंग के पास", "intent": "location_response", "group_id": "loc_hi_dev_1"},
    {"text": "हमारा गांव मोहनलालगंज है मंदिर के पास", "intent": "location_response", "group_id": "loc_hi_dev_2"},
    {"text": "हम रामपुर प्राथमिक विद्यालय के सामने खड़े हैं", "intent": "location_response", "group_id": "loc_hi_dev_3"},
    {"text": "सीतापुर रोड टोल प्लाजा के पास हैं हम लोग", "intent": "location_response", "group_id": "loc_hi_dev_4"},

    # --- symptom_report ---
    # English
    {"text": "Severe swelling on the right foot and intense burning pain", "intent": "symptom_report", "group_id": "sym_en_1"},
    {"text": "His leg is swelling rapidly and it hurts very badly", "intent": "symptom_report", "group_id": "sym_en_1"},
    {"text": "His eyelids are drooping and having difficulty breathing", "intent": "symptom_report", "group_id": "sym_en_2"},
    {"text": "Patient is having shortness of breath and cannot open eyes", "intent": "symptom_report", "group_id": "sym_en_2"},
    {"text": "Two puncture fang marks bleeding continuously", "intent": "symptom_report", "group_id": "sym_en_3"},
    {"text": "Blood is oozing from the bite wound on his hand", "intent": "symptom_report", "group_id": "sym_en_3"},
    {"text": "He is vomiting, sweating, and feels dizzy", "intent": "symptom_report", "group_id": "sym_en_4"},
    {"text": "Bite area is turning black and numb", "intent": "symptom_report", "group_id": "sym_en_5"},

    # Hinglish / Roman Hindi
    {"text": "Pair me bahut tez sujan aur dard ho raha hai", "intent": "symptom_report", "group_id": "sym_hi_rom_1"},
    {"text": "Kaatne ki jagah fool gayi hai aur dard bahut hai", "intent": "symptom_report", "group_id": "sym_hi_rom_1"},
    {"text": "Aankhein band ho rahi hain aur saans lene me takleef hai", "intent": "symptom_report", "group_id": "sym_hi_rom_2"},
    {"text": "Saans phool rahi hai aur behoshi jaisa lag raha hai", "intent": "symptom_report", "group_id": "sym_hi_rom_2"},
    {"text": "Do daant ke nishan hain aur khoon nikal raha hai", "intent": "symptom_report", "group_id": "sym_hi_rom_3"},
    {"text": "Ulti ho rahi hai chakkar aa rahe hain patient ko", "intent": "symptom_report", "group_id": "sym_hi_rom_4"},
    {"text": "Ghav kala pad raha hai aur thanda ho gaya hai", "intent": "symptom_report", "group_id": "sym_hi_rom_5"},

    # Hindi (Devanagari)
    {"text": "पैर में बहुत तेज सूजन है और असहनीय दर्द हो रहा है", "intent": "symptom_report", "group_id": "sym_hi_dev_1"},
    {"text": "काटने की जगह फूल गई है और जल रही है", "intent": "symptom_report", "group_id": "sym_hi_dev_1"},
    {"text": "पलकें गिर रही हैं और सांस लेने में भारी तकलीफ है", "intent": "symptom_report", "group_id": "sym_hi_dev_2"},
    {"text": "मरीज को सांस नहीं आ रही और मुंह से झाग निकल रहा है", "intent": "symptom_report", "group_id": "sym_hi_dev_2"},
    {"text": "घाव से लगातार खून बह रहा है और दो दांत के निशान हैं", "intent": "symptom_report", "group_id": "sym_hi_dev_3"},
    {"text": "मरीज को उल्टी और चक्कर आ रहे हैं", "intent": "symptom_report", "group_id": "sym_hi_dev_4"},

    # --- first_aid_query ---
    # English
    {"text": "What first aid should we do right now?", "intent": "first_aid_query", "group_id": "fa_en_1"},
    {"text": "How can we give emergency first aid immediately?", "intent": "first_aid_query", "group_id": "fa_en_1"},
    {"text": "Should we tie a tight tourniquet or cloth above the bite?", "intent": "first_aid_query", "group_id": "fa_en_2"},
    {"text": "Can we use a rope or tourniquet to stop the poison?", "intent": "first_aid_query", "group_id": "fa_en_2"},
    {"text": "Should we cut the wound and suck the venom out?", "intent": "first_aid_query", "group_id": "fa_en_3"},
    {"text": "Is it okay to cut the skin to remove poison?", "intent": "first_aid_query", "group_id": "fa_en_3"},
    {"text": "Can we apply ice or turmeric on the snake bite?", "intent": "first_aid_query", "group_id": "fa_en_4"},
    {"text": "What should we do while the ambulance arrives?", "intent": "first_aid_query", "group_id": "fa_en_5"},

    # Hinglish / Roman Hindi
    {"text": "Abhi gharelu ilaaj ya first aid kya karein?", "intent": "first_aid_query", "group_id": "fa_hi_rom_1"},
    {"text": "Ghar pe kya prathmik upchar karein batayein", "intent": "first_aid_query", "group_id": "fa_hi_rom_1"},
    {"text": "Kya rassi ya kapda kas ke baandh de pair me?", "intent": "first_aid_query", "group_id": "fa_hi_rom_2"},
    {"text": "Tourniquet baandhna sahi hai ya nahi?", "intent": "first_aid_query", "group_id": "fa_hi_rom_2"},
    {"text": "Kya ghav pe blade maar ke khoon nikalna chahiye?", "intent": "first_aid_query", "group_id": "fa_hi_rom_3"},
    {"text": "Munh se zehar kheench sakte hain kya?", "intent": "first_aid_query", "group_id": "fa_hi_rom_3"},
    {"text": "Baraf ya haldi lagayein kya kaatne par?", "intent": "first_aid_query", "group_id": "fa_hi_rom_4"},
    {"text": "Gadi aane tak mareez ke sath kya karein?", "intent": "first_aid_query", "group_id": "fa_hi_rom_5"},

    # Hindi (Devanagari)
    {"text": "अभी तुरंत प्राथमिक उपचार क्या करना चाहिए?", "intent": "first_aid_query", "group_id": "fa_hi_dev_1"},
    {"text": "हम घर पर क्या इलाज कर सकते हैं?", "intent": "first_aid_query", "group_id": "fa_hi_dev_1"},
    {"text": "क्या रस्सी या कपड़ा कसकर बांध दें जहर रोकने के लिए?", "intent": "first_aid_query", "group_id": "fa_hi_dev_2"},
    {"text": "क्या पट्टी जोर से बांधनी चाहिए?", "intent": "first_aid_query", "group_id": "fa_hi_dev_2"},
    {"text": "क्या घाव पर चीरा लगाकर जहर चूसना चाहिए?", "intent": "first_aid_query", "group_id": "fa_hi_dev_3"},
    {"text": "घाव पर बर्फ या जड़ी-बूटी लगाना ठीक है क्या?", "intent": "first_aid_query", "group_id": "fa_hi_dev_4"},

    # --- repeat_request ---
    # English
    {"text": "Can you please repeat what you just said?", "intent": "repeat_request", "group_id": "rep_en_1"},
    {"text": "Please repeat the last instructions", "intent": "repeat_request", "group_id": "rep_en_1"},
    {"text": "I could not hear properly, say it again", "intent": "repeat_request", "group_id": "rep_en_2"},
    {"text": "Pardon me, please say that once more", "intent": "repeat_request", "group_id": "rep_en_2"},
    {"text": "What was the hospital name again?", "intent": "repeat_request", "group_id": "rep_en_3"},
    {"text": "Can you say the address one more time?", "intent": "repeat_request", "group_id": "rep_en_3"},

    # Hinglish / Roman Hindi
    {"text": "Ek baar dobara bataiye kya bola", "intent": "repeat_request", "group_id": "rep_hi_rom_1"},
    {"text": "Aapki awaaz nahi aayi fir se boliye", "intent": "repeat_request", "group_id": "rep_hi_rom_1"},
    {"text": "Hospital ka naam repeat kijiye please", "intent": "repeat_request", "group_id": "rep_hi_rom_2"},
    {"text": "Samajh nahi aaya dobara kaho", "intent": "repeat_request", "group_id": "rep_hi_rom_3"},
    {"text": "Fir se sunao kya karna hai", "intent": "repeat_request", "group_id": "rep_hi_rom_4"},

    # Hindi (Devanagari)
    {"text": "कृपया एक बार फिर से दोहराएं", "intent": "repeat_request", "group_id": "rep_hi_dev_1"},
    {"text": "आवाज साफ नहीं आई दोबारा बोलिए", "intent": "repeat_request", "group_id": "rep_hi_dev_1"},
    {"text": "अस्पताल का नाम दोबारा बताइए", "intent": "repeat_request", "group_id": "rep_hi_dev_2"},
    {"text": "आपने क्या निर्देश दिया फिर से कहिए", "intent": "repeat_request", "group_id": "rep_hi_dev_3"},

    # --- human_help ---
    # English
    {"text": "Connect me to a real person immediately", "intent": "human_help", "group_id": "hum_en_1"},
    {"text": "I want to speak with a human agent, not a computer", "intent": "human_help", "group_id": "hum_en_1"},
    {"text": "Please connect me to a doctor right away", "intent": "human_help", "group_id": "hum_en_2"},
    {"text": "Transfer this call to an emergency doctor", "intent": "human_help", "group_id": "hum_en_2"},
    {"text": "Put me through to the 108 ambulance operator", "intent": "human_help", "group_id": "hum_en_3"},
    {"text": "I want to talk to an ambulance driver or officer", "intent": "human_help", "group_id": "hum_en_3"},
    {"text": "Speak to representative, give me a human", "intent": "human_help", "group_id": "hum_en_4"},
    {"text": "Connect to medical officer immediately", "intent": "human_help", "group_id": "hum_en_5"},
    {"text": "Talk to human agent right now", "intent": "human_help", "group_id": "hum_en_6"},

    # Hinglish / Roman Hindi
    {"text": "Kisi insaan se baat karwao turant", "intent": "human_help", "group_id": "hum_hi_rom_1"},
    {"text": "Doctor se baat karni hai line connect karo", "intent": "human_help", "group_id": "hum_hi_rom_1"},
    {"text": "Operator ko call transfer kijiye please", "intent": "human_help", "group_id": "hum_hi_rom_2"},
    {"text": "Helpline officer se baat karao jaldi", "intent": "human_help", "group_id": "hum_hi_rom_2"},
    {"text": "Machine se nahi kisi aadmi se baat karni hai", "intent": "human_help", "group_id": "hum_hi_rom_3"},
    {"text": "Kisi doctor se baat kara do emergency hai", "intent": "human_help", "group_id": "hum_hi_rom_4"},
    {"text": "Mujhe operator se baat karni hai jaldi", "intent": "human_help", "group_id": "hum_hi_rom_5"},

    # Hindi (Devanagari)
    {"text": "किसी इंसान या डॉक्टर से बात करवाइए", "intent": "human_help", "group_id": "hum_hi_dev_1"},
    {"text": "मुझे डॉक्टर से बात करनी है तुरंत फोन लगाओ", "intent": "human_help", "group_id": "hum_hi_dev_1"},
    {"text": "ऑपरेटर से बात कराओ कंप्यूटर से नहीं", "intent": "human_help", "group_id": "hum_hi_dev_2"},
    {"text": "कॉल को 108 हेल्पलाइन अधिकारी को ट्रांसफर करें", "intent": "human_help", "group_id": "hum_hi_dev_3"},
    {"text": "डॉक्टर से बात करवाइए तुरंत", "intent": "human_help", "group_id": "hum_hi_dev_4"},
    {"text": "किसी अधिकारी से बात करनी है लाइन जोड़िए", "intent": "human_help", "group_id": "hum_hi_dev_5"},


    # --- unknown ---
    # English
    {"text": "What is the weather like today?", "intent": "unknown", "group_id": "unk_en_1"},
    {"text": "Will it rain tomorrow afternoon?", "intent": "unknown", "group_id": "unk_en_1"},
    {"text": "Can you tell me a good joke?", "intent": "unknown", "group_id": "unk_en_2"},
    {"text": "Where is the nearest railway station or metro?", "intent": "unknown", "group_id": "unk_en_3"},
    {"text": "I want to recharge my mobile balance", "intent": "unknown", "group_id": "unk_en_4"},
    {"text": "Hello hello testing mic 1 2 3", "intent": "unknown", "group_id": "unk_en_5"},

    # Hinglish / Roman Hindi
    {"text": "Aaj mausam kaisa rahega Lucknow me", "intent": "unknown", "group_id": "unk_hi_rom_1"},
    {"text": "Mobile recharge kaise karein", "intent": "unknown", "group_id": "unk_hi_rom_2"},
    {"text": "Koi achha gana sunao please", "intent": "unknown", "group_id": "unk_hi_rom_3"},
    {"text": "Hello kaun bol raha hai samne", "intent": "unknown", "group_id": "unk_hi_rom_4"},
    {"text": "Bas aisi hi call lagaya tha", "intent": "unknown", "group_id": "unk_hi_rom_5"},

    # Hindi (Devanagari)
    {"text": "आज का मौसम कैसा रहेगा?", "intent": "unknown", "group_id": "unk_hi_dev_1"},
    {"text": "मेरा फोन रिचार्ज कर दीजिए", "intent": "unknown", "group_id": "unk_hi_dev_2"},
    {"text": "आप कौन बोल रहे हैं?", "intent": "unknown", "group_id": "unk_hi_dev_3"},
    {"text": "रेलवे स्टेशन कितनी दूर है यहां से?", "intent": "unknown", "group_id": "unk_hi_dev_4"},
]
