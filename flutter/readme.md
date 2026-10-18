# Dhwani-Sanjeevani — Flutter Emergency Mobile App

A life-saving, voice & location-first mobile client for **Dhwani-Sanjeevani**, built to assist victims and emergency responders during snakebite incidents across India.

---

## 📱 Features

1. **One-Tap Emergency 108 Dispatch:**
   - Direct dialer integration for the National 108 ambulance service.
2. **Nearest PHC/CHC Healthcare Locator:**
   - Detects live device GPS coordinates via `geolocator`.
   - Queries the backend spatial index to find verified health facilities sorted by direct distance in kilometres.
3. **ASV (Anti-Snake Venom) Inventory Status:**
   - Displays clear stock status badges (`AVAILABLE`, `OUT_OF_STOCK`, `UNVERIFIED`).
   - Includes mandatory medical safety disclaimers to prevent fatal delays.
4. **Turn-by-Turn Navigation:**
   - One-tap Google Maps directions to the selected facility.
5. **Official NAPSE Snakebite First Aid Guide:**
   - Implements the Indian government's **R.I.G.H.T.** protocol.
   - Highlights critical warnings (Strictly NO tourniquets, NO cutting, NO suction).

---

## 🏗️ Architecture & Directory Structure

```text
flutter/
├── android/               # Android native configuration & location permissions
├── ios/                   # iOS native configuration
├── lib/
│   ├── core/
│   │   ├── constants/
│   │   │   └── api_constants.dart    # FastAPI backend URLs & emergency numbers
│   │   └── theme/
│   │       └── app_theme.dart        # Emergency Crimson & Medical Teal theme
│   ├── models/
│   │   └── facility_model.dart       # Facility & nearby query data models
│   ├── providers/
│   │   └── facility_provider.dart    # Provider state management for location & search
│   ├── screens/
│   │   ├── home_screen.dart          # Main emergency dashboard & facility feed
│   │   ├── facility_detail_screen.dart # In-depth facility info & directions
│   │   └── first_aid_screen.dart     # Official NAPSE First Aid Do's & Don'ts
│   ├── services/
│   │   ├── api_service.dart          # HTTP client for FastAPI endpoints
│   │   └── location_service.dart     # Device GPS positioning & permission handling
│   ├── widgets/
│   │   ├── asv_badge.dart            # Visual status indicator for ASV stock
│   │   └── facility_card.dart        # Facility proximity card with direct navigation
│   └── main.dart                     # App entry point
├── test/
│   └── widget_test.dart              # Smoke test suite
└── pubspec.yaml                      # Dependencies (provider, geolocator, http, url_launcher)
```

---

## 🚀 Getting Started

### 1. Ensure Backend is Running
The app connects to the Dhwani-Sanjeevani FastAPI backend:
```bash
cd ../backend
uvicorn app.main:app --reload
```

> **Note on Device/Emulator Connections:**
> - **Web / Desktop (Windows):** Defaults to `http://localhost:8000`
> - **Android Emulator:** Set `baseUrl = 'http://10.0.2.2:8000'` in `lib/core/constants/api_constants.dart`
> - **Physical Mobile Device:** Set `baseUrl = 'http://<YOUR_LAN_IP>:8000'`

### 2. Run the App
```bash
flutter pub get
flutter run
```

### 3. Run Analysis & Tests
```bash
flutter analyze
flutter test
```
