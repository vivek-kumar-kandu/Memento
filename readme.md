# 🐍 Dhwani-Sanjeevani (ध्वनि-संजीवनी)
### *Universal Voice-First Emergency Response & Antivenom Infrastructure Engine*

[![Backend Deployment](https://img.shields.io/badge/Render-Live%20Backend-00e5a3?logo=render&logoColor=white)](https://sanjeevini-ai.onrender.com)
[![Swagger API Docs](https://img.shields.io/badge/FastAPI-Swagger%20Docs-009688?logo=fastapi&logoColor=white)](https://sanjeevini-ai.onrender.com/docs)
[![Flutter Build](https://img.shields.io/badge/Flutter-Android%20Release%20APK-02569B?logo=flutter&logoColor=white)](https://drive.google.com/file/d/1GTCP2EI9LIxLLUlbGp2zgEsoHBjdjCfE/view?usp=sharing)
[![Vercel Showcase](https://img.shields.io/badge/Vercel-Interactive%20Showcase-black?logo=vercel&logoColor=white)](https://memento-intro-page.vercel.app)
[![Compliance](https://img.shields.io/badge/NAPSE-Clinical%20Protocol%20Compliant-red)](#-strict-clinical-safety--napse-protocols)
[![Facilities](https://img.shields.io/badge/Facilities%20Indexed-34%2C936%20PHCs%2FCHCs-blue)](#-geospatial-infrastructure)

---

## 📖 Executive Overview

In rural India, snakebite envenomation claims **over 58,000 lives annually**—more than anywhere else in the world. The primary cause of mortality is not the unavailability of Anti-Snake Venom (ASV), but the **fatal delay during the "Golden Hour"** caused by digital inequality, panic, and misinformation.

**Dhwani-Sanjeevani** eliminates this delay through a **Unified Tri-Channel Emergency Ecosystem** backed by an ultra-fast FastAPI geospatial engine indexed with **34,936 verified government healthcare facilities (PHCs, CHCs, DHs)** across all 28 states and 8 union territories.

Whether a victim possesses a 4G smartphone, an illiterate villager dials from a 2G keypad phone, or a family member sends a WhatsApp pin, Sanjeevini immediately initiates emergency dispatch, localizes nearest ASV-stocked facilities in sub-milliseconds, and guides strict clinician-approved first-aid protocols.

---

## ⚡ Unified Multi-Channel Architecture

```
                                  ┌────────────────────────┐
                                  │   Caller / Patient /   │
                                  │   ASHA Field Worker    │
                                  └───────────┬────────────┘
                                              │
               ┌──────────────────────────────┼──────────────────────────────┐
               ▼                              ▼                              ▼
     [ 📱 Channel 01 ]              [ 📞 Channel 02 ]              [ 💬 Channel 03 ]
      Flutter Mobile App              Edesy IVR Telephony            WhatsApp Cloud Bot
     • GPS Proximity                • 2G Feature Phones            • Meta Cloud API
     • Turn-by-Turn Nav             • Speech-to-Text (ASR)         • 1-Tap Location Pin
     • ASHA Stock Audits            • Text-to-Speech (TTS)         • Rich Hospital Cards
     • Offline Protocol Cache       • SIP Transfer to 108          • Regional Language Chat
               │                              │                              │
               └──────────────────────────────┼──────────────────────────────┘
                                              │ HTTP JSON
                                              ▼
                             ┌──────────────────────────────────┐
                             │  FastAPI Production Engine       │
                             │  (https://sanjeevini-ai.onrender)│
                             ├──────────────────────────────────┤
                             │ • BallTree Geospatial (<2ms)     │
                             │ • ML Intent Classifier (Joblib)  │
                             │ • Async SQLite Session Engine    │
                             │ • Clinician Safety Triage Filter │
                             └────────────────┬─────────────────┘
                                              │
                      ┌───────────────────────┴───────────────────────┐
                      ▼                                               ▼
      ┌───────────────────────────────┐               ┌───────────────────────────────┐
      │   34,936 Geo-Indexed PHCs/CHCs│               │   108 National Emergency SIP  │
      │   Database & ASV Status Cache │               │   Dispatch & Ambulance Alert  │
      └───────────────────────────────┘               └───────────────────────────────┘
```

---

## 🚀 The Three Integrated Channels

### 1. 📱 Channel 01: Flutter Mobile App & ASHA Portal
- **Target Audience:** Patients, rural families, and Accredited Social Health Activists (ASHA).
- **Core Capabilities:**
  - **Live GPS Lock:** High-precision device coordinates with automatic fallback to manual village/landmark search.
  - **Hospital Discovery:** Ranked nearest facilities with exact distance, contact numbers, and turn-by-turn Google Maps launch.
  - **ASHA Worker Portal:** Role-based authenticated interface allowing community health workers to perform real-time ASV inventory audits.
  - **Emergency 108 SOS Bar:** Persistent, single-tap dialer for ambulance dispatch.
  - **Download Release APK:** [Google Drive Hosted APK](https://drive.google.com/file/d/1GTCP2EI9LIxLLUlbGp2zgEsoHBjdjCfE/view?usp=sharing)

### 2. 📞 Channel 02: Edesy IVR Voice Telephony (`/ivr`)
- **Target Audience:** Rural farmers, illiterate villagers, or callers in extreme shock holding 2G keypad feature phones.
- **Core Capabilities:**
  - **Zero App Required:** Runs over standard GSM voice calls via the **Edesy Telephony Platform**.
  - **Bidirectional Voice AI:** Converts inbound caller speech to text (ASR), routes through backend triage, and speaks clinician-approved instructions (TTS) in regional languages.
  - **Resilient Fallback:** If cloud backend is temporarily unreachable, local IVR fallback guarantees immediate first-aid guidance without delay.
  - **Emergency SIP Bridge:** Automatically executes SIP call transfer to 108 emergency queue on detected severe systemic envenomation (`ESCALATE_HUMAN`).

### 3. 💬 Channel 03: WhatsApp Business Cloud Bot (`/whatsapp_bot`)
- **Target Audience:** Family members and bystanders with instant messaging on basic smartphones.
- **Core Capabilities:**
  - **Native Location Pin:** Users tap the WhatsApp paperclip icon, drop their location pin, and receive immediate structured hospital cards.
  - **Zero Learning Curve:** Natural language triage and regional dialect understanding.

### 4. 🌐 Interactive Showcase Terminal (`/intro-page`)
- Neo-Brutalist interactive landing page, real-time live channel simulator, developer API contract inspector, and direct APK download portal deployed on Vercel.

---

## 🏥 Strict Clinical Safety & NAPSE Protocols

Dhwani-Sanjeevani strictly enforces clinician-reviewed protocols based on the **National Action Plan for Prevention and Control of Snakebite Envenoming (NAPSE)**:

| ❌ Dangerous Traditional Myth | ✅ Sanjeevani Clinical Enforcement |
|:---|:---|
| **Applying tight arterial tourniquets** | ⛔ **Strict Warning:** Tourniquets cause limb ischemia and gangrene. If already tied, **DO NOT REMOVE in field** (sudden systemic venom release). Allow doctors to release under IV line control. |
| **Cutting or incising the bite site** | ⛔ **Strict Warning:** Causes severe bleeding, infection, and tissue destruction. |
| **Sucking venom (by mouth or vacuum pump)** | ⛔ **Strict Warning:** Ineffective, introduces bacteria, and risks poisoning rescuer. |
| **Applying ice packs, herbs, or cow dung** | ⛔ **Strict Warning:** Aggravates local tissue necrosis. |
| **Delaying transport for local remedies** | ✅ **Immediate Action:** Keep patient calm and completely still. Immobilize limb with a splint. Transport immediately to nearest ASV-capable centre. |

---

## 🗺️ Geospatial Infrastructure & Dataset

- **Facility Dataset:** 34,936 verified government primary and community health centres (`phc_chc_facilities_clean.csv`).
- **Spatial Indexing:** High-dimensional **Scikit-Learn `BallTree`** using Haversine metric (radian-converted coordinates) allowing **sub-2ms lookup** times even under concurrent load.
- **Data Quarantine Engine:** 186 invalid or malformed coordinates automatically isolated into quarantine logs during engine boot, ensuring zero zero-coordinate false referrals.

---

## 📁 Repository Structure

```
├── backend
│   ├── app
│   │   ├── api
│   │   │   ├── v1
│   │   │   │   ├── endpoints
│   │   │   │   │   ├── __init__.py
│   │   │   │   │   ├── assistant.py
│   │   │   │   │   ├── cases.py
│   │   │   │   │   ├── facilities.py
│   │   │   │   └── health.py
│   │   │   │   ├── __init__.py
│   │   │   │   └── router.py
│   │   │   └── __init__.py
│   │   ├── core
│   │   │   ├── __init__.py
│   │   ├── config.py
│   │   └── logging.py
│   ├── db
│   │   ├── models
│   │   │   ├── __init__.py
│   │   │   ├── case.py
│   │   │   ├── conversation.py
│   │   │   └── facility.py
│   │   ├── __init__.py
│   │   ├── base.py
│   │   └── session.py
│   ├── ml
│   │   ├── dataset.py
│   │   ├── evaluation_report.json
│   │   ├── intent_classifier.joblib
│   │   └── train_classifier.py
│   ├── schemas
│   │   ├── __init__.py
│   │   ├── assistant.py
│   │   ├── case.py
│   │   ├── common.py
│   │   └── facility.py
│   ├── services
│   │   ├── __init__.py
│   │   ├── assistant_service.py
│   │   ├── case_service.py
│   │   ├── classifier_service.py
│   │   ├── facility_service.py
│   │   └── geo_service.py
│   ├── __init__.py
│   └── main.py
├── examples
│   └── quickstart_test.py
├── tests
│   ├── conftest.py
│   ├── test_assistant.py
│   ├── test_cases.py
│   ├── test_facilities.py
│   └── test_health.py
├── INTEGRATION_CONTRACT.md
└── requirements.txt
├── Data
│   ├── Dhwani_Sanjeevani_Facility_Data_Bundle
│   │   ├── asv_inventory_template.csv
│   │   ├── DATA_AUDIT_README.txt
│   │   ├── phc_chc_coordinate_review.csv
│   │   ├── phc_chc_facilities_clean.csv
│   │   ├── phc_chc_facilities_for_nearby_search.geojson
│   │   ├── phc_chc_facilities_for_nearby_search.json
│   │   └── state_summary.csv
│   ├── asv_inventory_template.csv
│   ├── Dhwani_Sanjeevani_Facility_Data_Bundle.zip
│   ├── geocode_health_centre.csv
│   ├── hospital_directory.csv
│   ├── NATIONAL-ACTION-PLAN-FOR-PREVENTION-AND-CONTROL-OF-SNAKEBITE-ENVENOMING-NAPSE.pdf
│   ├── Operational Guidelines_FDSI.pdf
│   ├── phc_chc_facilities_clean.csv
│   └── phc_chc_facilities_for_nearby_search.json
├── flutter
│   ├── android
│   │   ├── app
│   │   │   ├── src
│   │   │   │   ├── debug
│   │   │   │   │   └── AndroidManifest.xml
│   │   │   │   ├── main
│   │   │   │   │   ├── java
│   │   │   │   │   ├── kotlin
│   │   │   │   │   ├── res
│   │   │   │   │   └── AndroidManifest.xml
│   │   │   │   └── profile
│   │   │   │       └── AndroidManifest.xml
│   │   │   └── build.gradle.kts
│   │   ├── gradle
│   │   │   └── wrapper
│   │   │       ├── gradle-wrapper.jar
│   │   │       └── gradle-wrapper.properties
│   │   ├── build.gradle.kts
│   │   ├── gradle.properties
│   │   ├── gradlew
│   │   ├── gradlew.bat
│   │   ├── local.properties
│   │   └── settings.gradle.kts
│   ├── ios
│   │   ├── Flutter
│   │   │   ├── ephemeral
│   │   │   │   ├── Packages
│   │   │   │   │   └── FlutterGeneratedPluginSwiftPackage
│   │   │   │   ├── flutter_lldb_helper.py
│   │   │   │   ├── flutter_lldbinit
│   │   │   │   └── flutter_native_integration.env
│   │   │   ├── AppFrameworkInfo.plist
│   │   │   ├── Debug.xcconfig
│   │   │   ├── flutter_export_environment.sh
│   │   │   ├── Generated.xcconfig
│   │   │   └── Release.xcconfig
│   │   ├── Runner
│   │   │   ├── Assets.xcassets
│   │   │   │   ├── AppIcon.appiconset
│   │   │   │   │   ├── Contents.json
│   │   │   │   │   ├── Icon-App-1024x1024@1x.png
│   │   │   │   │   ├── Icon-App-20x20@1x.png
│   │   │   │   │   ├── Icon-App-20x20@2x.png
│   │   │   │   │   ├── Icon-App-20x20@3x.png
│   │   │   │   │   ├── Icon-App-29x29@1x.png
│   │   │   │   │   ├── Icon-App-29x29@2x.png
│   │   │   │   │   ├── Icon-App-29x29@3x.png
│   │   │   │   │   ├── Icon-App-40x40@1x.png
│   │   │   │   │   ├── Icon-App-40x40@2x.png
│   │   │   │   │   ├── Icon-App-40x40@3x.png
│   │   │   │   │   ├── Icon-App-60x60@2x.png
│   │   │   │   │   ├── Icon-App-60x60@3x.png
│   │   │   │   │   ├── Icon-App-76x76@1x.png
│   │   │   │   │   ├── Icon-App-76x76@2x.png
│   │   │   │   │   └── Icon-App-83.5x83.5@2x.png
│   │   │   │   └── LaunchImage.imageset
│   │   │   │       ├── Contents.json
│   │   │   │       ├── LaunchImage.png
│   │   │   │       ├── LaunchImage@2x.png
│   │   │   │       ├── LaunchImage@3x.png
│   │   │   │       └── README.md
│   │   │   ├── Base.lproj
│   │   │   │   ├── LaunchScreen.storyboard
│   │   │   │   └── Main.storyboard
│   │   │   ├── AppDelegate.swift
│   │   │   ├── GeneratedPluginRegistrant.h
│   │   │   ├── GeneratedPluginRegistrant.m
│   │   │   ├── Info.plist
│   │   │   ├── Runner-Bridging-Header.h
│   │   │   └── SceneDelegate.swift
│   │   ├── Runner.xcodeproj
│   │   │   ├── project.xcworkspace
│   │   │   │   ├── xcshareddata
│   │   │   │   │   ├── IDEWorkspaceChecks.plist
│   │   │   │   │   └── WorkspaceSettings.xcsettings
│   │   │   │   └── contents.xcworkspacedata
│   │   │   ├── xcshareddata
│   │   │   │   └── xcschemes
│   │   │   │       └── Runner.xcscheme
│   │   │   └── project.pbxproj
│   │   ├── Runner.xcworkspace
│   │   │   ├── xcshareddata
│   │   │   │   ├── IDEWorkspaceChecks.plist
│   │   │   │   └── WorkspaceSettings.xcsettings
│   │   │   └── contents.xcworkspacedata
│   │   └── RunnerTests
│   │       └── RunnerTests.swift
│   ├── lib
│   │   ├── core
│   │   │   ├── constants
│   │   │   │   └── api_constants.dart
│   │   │   └── theme
│   │   │       └── app_theme.dart
│   │   ├── data
│   │   │   └── safety_product_repository.dart
│   │   ├── models
│   │   │   ├── assistant_message_model.dart
│   │   │   ├── facility_model.dart
│   │   │   └── safety_product.dart
│   │   ├── providers
│   │   │   └── facility_provider.dart
│   │   ├── screens
│   │   │   ├── asha_dashboard_screen.dart
│   │   │   ├── asha_login_screen.dart
│   │   │   ├── facility_detail_screen.dart
│   │   │   ├── first_aid_screen.dart
│   │   │   ├── home_screen.dart
│   │   │   ├── patient_home_screen.dart
│   │   │   ├── safety_product_details_screen.dart
│   │   │   ├── safety_products_screen.dart
│   │   │   └── sanjeevini_landing_screen.dart
│   │   ├── services
│   │   │   ├── api_service.dart
│   │   │   └── location_service.dart
│   │   ├── widgets
│   │   │   ├── asv_badge.dart
│   │   │   ├── facility_card.dart
│   │   │   ├── role_option_card.dart
│   │   │   ├── safety_product_card.dart
│   │   │   └── sanjeevini_logo.dart
│   │   └── main.dart
│   ├── linux
│   │   ├── flutter
│   │   │   ├── ephemeral
│   │   │   ├── CMakeLists.txt
│   │   │   ├── generated_plugin_registrant.cc
│   │   │   ├── generated_plugin_registrant.h
│   │   │   └── generated_plugins.cmake
│   │   ├── runner
│   │   │   ├── CMakeLists.txt
│   │   │   ├── main.cc
│   │   │   ├── my_application.cc
│   │   │   └── my_application.h
│   │   └── CMakeLists.txt
│   ├── macos
│   │   ├── Flutter
│   │   │   ├── ephemeral
│   │   │   │   ├── Packages
│   │   │   │   │   └── FlutterGeneratedPluginSwiftPackage
│   │   │   │   ├── flutter_export_environment.sh
│   │   │   │   ├── flutter_native_integration.env
│   │   │   │   └── Flutter-Generated.xcconfig
│   │   │   ├── Flutter-Debug.xcconfig
│   │   │   ├── Flutter-Release.xcconfig
│   │   │   └── GeneratedPluginRegistrant.swift
│   │   ├── Runner
│   │   │   ├── Assets.xcassets
│   │   │   │   └── AppIcon.appiconset
│   │   │   │       ├── app_icon_1024.png
│   │   │   │       ├── app_icon_128.png
│   │   │   │       ├── app_icon_16.png
│   │   │   │       ├── app_icon_256.png
│   │   │   │       ├── app_icon_32.png
│   │   │   │       ├── app_icon_512.png
│   │   │   │       ├── app_icon_64.png
│   │   │   │       └── Contents.json
│   │   │   ├── Base.lproj
│   │   │   │   └── MainMenu.xib
│   │   │   ├── Configs
│   │   │   │   ├── AppInfo.xcconfig
│   │   │   │   ├── Debug.xcconfig
│   │   │   │   ├── Release.xcconfig
│   │   │   │   └── Warnings.xcconfig
│   │   │   ├── AppDelegate.swift
│   │   │   ├── DebugProfile.entitlements
│   │   │   ├── Info.plist
│   │   │   ├── MainFlutterWindow.swift
│   │   │   └── Release.entitlements
│   │   ├── Runner.xcodeproj
│   │   │   ├── project.xcworkspace
│   │   │   │   └── xcshareddata
│   │   │   │       └── IDEWorkspaceChecks.plist
│   │   │   ├── xcshareddata
│   │   │   │   └── xcschemes
│   │   │   │       └── Runner.xcscheme
│   │   │   └── project.pbxproj
│   │   ├── Runner.xcworkspace
│   │   │   ├── xcshareddata
│   │   │   │   └── IDEWorkspaceChecks.plist
│   │   │   └── contents.xcworkspacedata
│   │   └── RunnerTests
│   │       └── RunnerTests.swift
│   ├── test
│   │   └── widget_test.dart
│   ├── web
│   │   ├── icons
│   │   │   ├── Icon-192.png
│   │   │   ├── Icon-512.png
│   │   │   ├── Icon-maskable-192.png
│   │   │   └── Icon-maskable-512.png
│   │   ├── favicon.png
│   │   ├── index.html
│   │   └── manifest.json
│   ├── windows
│   │   ├── flutter
│   │   │   ├── ephemeral
│   │   │   ├── CMakeLists.txt
│   │   │   ├── generated_plugin_registrant.cc
│   │   │   ├── generated_plugin_registrant.h
│   │   │   └── generated_plugins.cmake
│   │   ├── runner
│   │   │   ├── resources
│   │   │   │   └── app_icon.ico
│   │   │   ├── CMakeLists.txt
│   │   │   ├── flutter_window.cpp
│   │   │   ├── flutter_window.h
│   │   │   ├── main.cpp
│   │   │   ├── resource.h
│   │   │   ├── runner.exe.manifest
│   │   │   ├── Runner.rc
│   │   │   ├── utils.cpp
│   │   │   ├── utils.h
│   │   │   ├── win32_window.cpp
│   │   │   └── win32_window.h
│   │   └── CMakeLists.txt
│   ├── analysis_options.yaml
│   ├── pubspec.lock
│   ├── pubspec.yaml
│   └── readme.md
├── intro-page
│   ├── app.js
│   ├── index.html
│   ├── styles.css
│   └── vercel.json
├── ivr
│   ├── tests
│   │   ├── __init__.py
│   │   ├── test_conversation_flow.py
│   │   ├── test_edesy_adapter.py
│   │   └── test_health.py
│   ├── backend_client.py
│   ├── config.py
│   ├── conversation.py
│   ├── edesy_adapter.py
│   ├── main.py
│   ├── readme.md
│   ├── requirements.txt
│   └── speech.py
├── whatsapp_bot
│   ├── readme.md
│   └── rrreadme.md
└── readme.md
```

---

## 🛠️ Quickstart & Local Setup Guide

### 1. Prerequisites
- **Python 3.11+**
- **Flutter 3.24+** & **Dart 3.5+**
- **Android SDK Platform 34/35** (for APK generation)
- **Node.js 20+** (for optional local static hosting)

---

### 2. Backend (FastAPI Service)
```bash
# Navigate to backend directory
cd backend

# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies including greenlet for SQLAlchemy asyncio
pip install -r requirements.txt greenlet

# Run database migrations and start server
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```
- Interactive Swagger UI: `http://localhost:8000/docs`
- Health check: `http://localhost:8000/health`

---

### 3. IVR Voice Telephony Adapter (Edesy Interface)
```bash
# Navigate to IVR directory
cd ivr

# Copy environment configuration
cp .env.example .env
# Ensure BACKEND_BASE_URL points to your backend:
# BACKEND_BASE_URL=https://sanjeevini-ai.onrender.com

# Run IVR Adapter server on port 8001
python main.py

# Run test suite
pytest tests
```

---

### 4. Flutter Mobile App (Android APK / Web)
```bash
# Navigate to Flutter directory
cd flutter

# Install dependencies
flutter pub get

# Run on Chrome
flutter run -d chrome

# Build Production Release APK pointing to live Render backend
flutter build apk --release --dart-define=BACKEND_BASE_URL=https://sanjeevini-ai.onrender.com
```
*Output APK located at:* `flutter/build/app/outputs/flutter-apk/app-release.apk`

---

### 5. Intro Showcase Page (Vercel)
```bash
cd intro-page
# Test locally
npx serve .
# Or deploy to Vercel via CLI
npx vercel
```

---

## 📡 Core API Contract Specifications

### 1. Proximity Health Facility Lookup
`POST /api/v1/facilities/nearby`
```json
{
  "latitude": 26.8467,
  "longitude": 80.9462,
  "limit": 3
}
```
**Response (200 OK):**
```json
{
  "facilities": [
    {
      "facility_id": "UP-LKO-0012",
      "facility_name": "CHC Mohanlalganj",
      "facility_type": "Community Health Centre",
      "state_name": "Uttar Pradesh",
      "district_name": "Lucknow",
      "distance_km": 4.12,
      "asv_stock_status": "AVAILABLE",
      "safety_disclaimer": "Call ahead to confirm emergency medical officer on duty."
    }
  ]
}
```

### 2. Conversational Voice & Text Triage (Universal Assistant)
`POST /api/v1/assistant/message`
```json
{
  "message": "Snake bit my brother in foot, bleeding profusely",
  "channel": "IVR",
  "caller_phone": "+919876543210",
  "language": "en"
}
```
**Response (200 OK):**
```json
{
  "response_text": "Emergency recorded. Do NOT apply tourniquet or cut wound. Immobilize limb with a splint. Proceed immediately to nearest CHC Mohanlalganj (4.1 km away). Ambulance 108 notified.",
  "next_action": "DISPATCH_OR_TRANSPORT",
  "conversation_id": "conv-8841-992",
  "case_id": "DS-2026-A109F"
}
```

---

## 👥 Contributors & Collaboration

Developed with passion for India's emergency healthcare frontier by the **Dhwani-Sanjeevani Team**:
- **Backend & Geospatial Core:** FastAPI, BallTree, Scikit-learn, SQLite Async
- **Telephony & Voice AI:** Edesy ASR/TTS Adapter & SIP 108 Bridge
- **Mobile & Front-End:** Flutter Native (Android/Web), Neo-Brutalist Web Showcase
- **Clinical Alignment:** NAPSE National Guidelines & WHO Snakebite Prevention Strategy

---

## 📜 License
This project is open-source under the [MIT License](LICENSE). Emergency clinical advice conforms to Ministry of Health & Family Welfare (MoHFW) emergency first-aid protocols.