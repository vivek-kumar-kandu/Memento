import 'dart:async';
import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:geolocator/geolocator.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:provider/provider.dart';

import 'package:dhwani_sanjeevani/main.dart';
import 'package:dhwani_sanjeevani/models/facility_model.dart';
import 'package:dhwani_sanjeevani/models/safety_product.dart';
import 'package:dhwani_sanjeevani/providers/facility_provider.dart';
import 'package:dhwani_sanjeevani/screens/home_screen.dart';
import 'package:dhwani_sanjeevani/screens/safety_product_details_screen.dart';
import 'package:dhwani_sanjeevani/services/api_service.dart';
import 'package:dhwani_sanjeevani/services/location_service.dart';

void main() {
  group('Original Sanjeevini Flow Tests', () {
    testWidgets('Sanjeevini landing screen renders all key sections',
        (WidgetTester tester) async {
      await tester.pumpWidget(const DhwaniSanjeevaniApp());
      await tester.pumpAndSettle();

      expect(find.text('Sanjeevini'), findsWidgets);
      expect(find.text('Snakebite emergency assistance'), findsOneWidget);
      expect(find.text('How can we help?'), findsOneWidget);
      expect(find.text('Continue as Patient'), findsOneWidget);
      expect(find.text('ASHA Worker Login'), findsOneWidget);
    });

    testWidgets(
        'Patient / Family navigates directly to Patient Home screen without login',
        (WidgetTester tester) async {
      await tester.pumpWidget(const DhwaniSanjeevaniApp());
      await tester.pumpAndSettle();

      final patientBtn = find.text('Continue as Patient');
      expect(patientBtn, findsOneWidget);
      await tester.tap(patientBtn);
      await tester.pumpAndSettle();

      expect(find.text('Patient Emergency Care'), findsOneWidget);
      expect(find.text('Call 108 Ambulance'), findsOneWidget);
      expect(find.text('Official First Aid Guidelines'), findsOneWidget);
      expect(find.text('Nearby Healthcare Facilities'), findsOneWidget);

      final backBtn = find.byType(BackButton);
      expect(backBtn, findsOneWidget);
      await tester.tap(backBtn);
      await tester.pumpAndSettle();

      expect(find.text('How can we help?'), findsOneWidget);
    });

    testWidgets(
        'ASHA Worker opens login screen and enforces validation before dashboard',
        (WidgetTester tester) async {
      await tester.pumpWidget(const DhwaniSanjeevaniApp());
      await tester.pumpAndSettle();

      final ashaBtn = find.text('ASHA Worker Login');
      expect(ashaBtn, findsOneWidget);
      await tester.ensureVisible(ashaBtn);
      await tester.pumpAndSettle();
      await tester.tap(ashaBtn);
      await tester.pumpAndSettle();

      expect(find.text('Field Coordination Login'), findsOneWidget);

      final loginBtn = find.text('Login to Dashboard');
      await tester.ensureVisible(loginBtn);
      await tester.pumpAndSettle();
      await tester.tap(loginBtn);
      await tester.pumpAndSettle();

      expect(find.text('Please enter your ASHA ID or registered mobile number.'),
          findsOneWidget);

      await tester.enterText(find.byType(TextFormField).first, 'ASHA-88214');
      await tester.enterText(find.byType(TextFormField).last, '1234');
      await tester.pumpAndSettle();

      await tester.tap(loginBtn);
      await tester.pump();
      await tester.pump(const Duration(milliseconds: 700));
      await tester.pumpAndSettle();

      expect(find.text('ASHA Field Dashboard'), findsOneWidget);
      expect(find.text('Worker ID: ASHA-88214'), findsOneWidget);
    });

    testWidgets(
        'Screen renders cleanly on small mobile screen (320x480) without overflow',
        (WidgetTester tester) async {
      tester.view.physicalSize = const Size(320, 480);
      tester.view.devicePixelRatio = 1.0;
      addTearDown(() {
        tester.view.resetPhysicalSize();
        tester.view.resetDevicePixelRatio();
      });

      await tester.pumpWidget(const DhwaniSanjeevaniApp());
      await tester.pumpAndSettle();

      expect(find.text('How can we help?'), findsOneWidget);
      await tester.drag(find.byType(SingleChildScrollView), const Offset(0, -500));
      await tester.pumpAndSettle();

      expect(tester.takeException(), isNull);
    });

    testWidgets(
        'Patient Home navigates to Prevention & Safety Products screen',
        (WidgetTester tester) async {
      await tester.pumpWidget(const DhwaniSanjeevaniApp());
      await tester.pumpAndSettle();

      await tester.tap(find.text('Continue as Patient'));
      await tester.pumpAndSettle();

      expect(find.text('Prevention & Safety Products'), findsOneWidget);

      final browseBtn = find.text('Browse Safety Products');
      await tester.ensureVisible(browseBtn);
      await tester.pumpAndSettle();
      await tester.tap(browseBtn);
      await tester.pumpAndSettle();

      expect(find.text('Prevention & Safety Products'), findsWidgets);
      expect(find.text('High-Beam Rechargeable LED Torch'), findsOneWidget);
    });

    testWidgets(
        'Safety products screen displays seller buttons (Buy on Amazon, Search on Flipkart)',
        (WidgetTester tester) async {
      await tester.pumpWidget(const DhwaniSanjeevaniApp());
      await tester.pumpAndSettle();

      await tester.tap(find.text('Continue as Patient'));
      await tester.pumpAndSettle();

      final browseBtn = find.text('Browse Safety Products');
      await tester.ensureVisible(browseBtn);
      await tester.pumpAndSettle();
      await tester.tap(browseBtn);
      await tester.pumpAndSettle();

      final lightingChip = find.widgetWithText(ChoiceChip, 'Lighting');
      await tester.tap(lightingChip);
      await tester.pumpAndSettle();

      await tester.tap(find.text('High-Beam Rechargeable LED Torch'));
      await tester.pumpAndSettle();

      expect(find.text('Product Details'), findsOneWidget);
      expect(find.text('Buy on Amazon'), findsOneWidget);
      expect(find.text('Search on Flipkart'), findsOneWidget);
    });

    testWidgets(
        'Handles invalid URL launch gracefully with user notification',
        (WidgetTester tester) async {
      const invalidProduct = SafetyProduct(
        id: 'test-invalid-url',
        name: 'Testing Malformed Link Product',
        category: 'Preparedness',
        description: 'Test description',
        amazonDirectUrl: 'ftp://invalid-protocol.com/item',
        enableMarketplaceSearchFallback: false,
        intendedUse: 'Testing error resilience',
        safetyNotes: 'Test safety notes',
      );

      await tester.pumpWidget(
        const MaterialApp(
          home: SafetyProductDetailsScreen(product: invalidProduct),
        ),
      );
      await tester.pumpAndSettle();

      final amazonBtn = find.text('Buy on Amazon');
      expect(amazonBtn, findsOneWidget);
      await tester.ensureVisible(amazonBtn);
      await tester.pumpAndSettle();
      await tester.tap(amazonBtn);
      await tester.pumpAndSettle();

      expect(find.text('Invalid link format for Amazon.'), findsOneWidget);
    });

    test(
        'SafetyProduct model unit test: validates direct vs search fallback URLs',
        () {
      const productWithDirect = SafetyProduct(
        id: 'p1',
        name: 'Safety Torch',
        category: 'Lighting',
        description: 'Desc',
        amazonDirectUrl: 'https://www.amazon.in/dp/B001',
        flipkartDirectUrl: 'https://www.flipkart.com/p/item1',
        intendedUse: 'Lighting',
        safetyNotes: 'Notes',
      );

      final directLinks = productWithDirect.sellerLinks;
      expect(directLinks.length, 2);
      expect(directLinks[0].buttonLabel, 'Buy on Amazon');
      expect(directLinks[0].isDirect, isTrue);
    });
  });

  group('GPS & Backend Integration Tests (Step 7)', () {
    // 1. Successful location retrieval using a mocked location service
    test('1. Successful location retrieval using mocked LocationService',
        () async {
      final mockLocationService = LocationService(
        serviceEnabledChecker: () async => true,
        permissionChecker: () async => LocationPermission.always,
        positionRetriever: ({locationSettings}) async => Position(
          latitude: 26.8467,
          longitude: 80.9462,
          timestamp: DateTime.now(),
          accuracy: 14.5,
          altitude: 0.0,
          altitudeAccuracy: 0.0,
          heading: 0.0,
          headingAccuracy: 0.0,
          speed: 0.0,
          speedAccuracy: 0.0,
        ),
      );

      final result = await mockLocationService.getCurrentLocation();
      expect(result.isSuccess, isTrue);
      expect(result.latitude, 26.8467);
      expect(result.longitude, 80.9462);
      expect(result.accuracy, 14.5);
    });

    // 2. Permission denied and permission permanently denied
    test('2. Permission denied and permission permanently denied', () async {
      final deniedService = LocationService(
        serviceEnabledChecker: () async => true,
        permissionChecker: () async => LocationPermission.denied,
        permissionRequester: () async => LocationPermission.denied,
      );

      final deniedResult = await deniedService.getCurrentLocation();
      expect(deniedResult.isSuccess, isFalse);
      expect(deniedResult.status, LocationStatus.permissionDenied);
      expect(deniedResult.message, contains('Location permission was denied'));

      final foreverDeniedService = LocationService(
        serviceEnabledChecker: () async => true,
        permissionChecker: () async => LocationPermission.deniedForever,
      );

      final foreverResult = await foreverDeniedService.getCurrentLocation();
      expect(foreverResult.isSuccess, isFalse);
      expect(foreverResult.status, LocationStatus.permissionDeniedForever);
      expect(foreverResult.message, contains('permanently denied'));
    });

    // 3. Location services disabled or timeout
    test('3. Location services disabled or timeout', () async {
      final disabledService = LocationService(
        serviceEnabledChecker: () async => false,
      );

      final disabledResult = await disabledService.getCurrentLocation();
      expect(disabledResult.isSuccess, isFalse);
      expect(disabledResult.status, LocationStatus.serviceDisabled);

      final timeoutService = LocationService(
        serviceEnabledChecker: () async => true,
        permissionChecker: () async => LocationPermission.always,
        positionRetriever: ({locationSettings}) async {
          throw TimeoutException('GPS timed out');
        },
      );

      final timeoutResult = await timeoutService.getCurrentLocation();
      expect(timeoutResult.isSuccess, isFalse);
      expect(timeoutResult.status, LocationStatus.timeout);
      expect(timeoutResult.message, contains('timed out'));
    });

    // 4. Correct request payload sent to the actual backend contract
    test('4. Correct request payload sent to POST /api/v1/facilities/nearby',
        () async {
      late Map<String, dynamic> capturedBody;
      late String capturedPath;

      final mockClient = MockClient((request) async {
        capturedPath = request.url.path;
        capturedBody = jsonDecode(request.body);
        return http.Response(
          jsonEncode({
            'query_latitude': 26.8467,
            'query_longitude': 80.9462,
            'search_radius_km': 30.0,
            'total_found': 1,
            'facilities': [
              {
                'facility_id': 'HCF-018470',
                'facility_name': 'Tala PHC',
                'facility_type': 'PHC',
                'state_name': 'Uttar Pradesh',
                'district_name': 'Lucknow',
                'latitude': 27.0543,
                'longitude': 80.9321,
                'distance_km': 4.2,
                'asv_stock_status': 'UNKNOWN',
                'asv_data_mode': 'REAL',
                'asv_verification_source': 'NOT_VERIFIED',
              }
            ],
            'safety_disclaimer': 'ASV is unverified.',
          }),
          200,
          headers: {'content-type': 'application/json'},
        );
      });

      final apiService = ApiService(client: mockClient);
      final response = await apiService.fetchNearbyFacilities(
        latitude: 26.8467,
        longitude: 80.9462,
        radiusKm: 30.0,
        limit: 10,
        facilityType: 'PHC',
      );

      expect(capturedPath, '/api/v1/facilities/nearby');
      expect(capturedBody['latitude'], 26.8467);
      expect(capturedBody['longitude'], 80.9462);
      expect(capturedBody['radius_km'], 30.0);
      expect(capturedBody['limit'], 10);
      expect(capturedBody['facility_type'], 'PHC');
      expect(response.facilities.length, 1);
      expect(response.facilities.first.facilityName, 'Tala PHC');
    });

    // 5. Successful nearby-facility response parsing
    test('5. Successful nearby-facility response parsing', () {
      final json = {
        'query_latitude': 26.8467,
        'query_longitude': 80.9462,
        'search_radius_km': 30.0,
        'total_found': 2,
        'facilities': [
          {
            'facility_id': 'HCF-001',
            'facility_name': 'Bakshi Ka Talab CHC',
            'facility_type': 'CHC',
            'state_name': 'Uttar Pradesh',
            'district_name': 'Lucknow',
            'subdistrict_name': 'Bakshi Ka Talab',
            'latitude': 27.0123,
            'longitude': 80.9234,
            'distance_km': 2.5,
            'asv_stock_status': 'UNKNOWN',
            'asv_quantity_vials': null,
            'asv_data_mode': 'REAL',
            'asv_verification_source': 'NOT_VERIFIED',
            'asv_notes': 'Stock pending inspection',
          },
          {
            'facility_id': 'HCF-002',
            'facility_name': 'Itaunja PHC',
            'facility_type': 'PHC',
            'state_name': 'Uttar Pradesh',
            'district_name': 'Lucknow',
            'latitude': 27.0891,
            'longitude': 80.9123,
            'distance_km': 8.7,
            'asv_stock_status': 'AVAILABLE',
            'asv_quantity_vials': 10,
            'asv_data_mode': 'REAL',
            'asv_verification_source': 'OPERATIONAL_REPORT',
          }
        ],
        'safety_disclaimer': 'Always verify through 108 dispatch.',
      };

      final parsed = NearbySearchResponse.fromJson(json);
      expect(parsed.totalFound, 2);
      expect(parsed.facilities.length, 2);

      final chc = parsed.facilities[0];
      expect(chc.facilityId, 'HCF-001');
      expect(chc.facilityName, 'Bakshi Ka Talab CHC');
      expect(chc.facilityType, 'CHC');
      expect(chc.distanceKm, 2.5);
      expect(chc.asvStockStatus, 'UNKNOWN');
      expect(chc.asvQuantityVials, isNull);

      final phc = parsed.facilities[1];
      expect(phc.facilityName, 'Itaunja PHC');
      expect(phc.asvStockStatus, 'AVAILABLE');
      expect(phc.asvQuantityVials, 10);
    });

    // 6. Empty facility results
    test('6. Empty facility results handled cleanly', () async {
      final mockClient = MockClient((request) async {
        return http.Response(
          jsonEncode({
            'query_latitude': 26.8467,
            'query_longitude': 80.9462,
            'search_radius_km': 15.0,
            'total_found': 0,
            'facilities': [],
            'safety_disclaimer': 'No facilities found.',
          }),
          200,
          headers: {'content-type': 'application/json'},
        );
      });

      final mockLocationService = LocationService(
        serviceEnabledChecker: () async => true,
        permissionChecker: () async => LocationPermission.always,
        positionRetriever: ({locationSettings}) async => Position(
          latitude: 26.8467,
          longitude: 80.9462,
          timestamp: DateTime.now(),
          accuracy: 10.0,
          altitude: 0.0,
          altitudeAccuracy: 0.0,
          heading: 0.0,
          headingAccuracy: 0.0,
          speed: 0.0,
          speedAccuracy: 0.0,
        ),
      );

      final provider = FacilityProvider(
        apiService: ApiService(client: mockClient),
        locationService: mockLocationService,
      );

      await provider.useCurrentLocationAndSearch();
      expect(provider.status, FacilitySearchStatus.noResults);
      expect(provider.facilities.isEmpty, isTrue);
    });

    // 7. Backend HTTP errors and malformed responses
    test('7. Backend HTTP errors and malformed responses handled gracefully',
        () async {
      final errorClient = MockClient((request) async {
        return http.Response('Internal Server Error', 500);
      });

      final mockLocationService = LocationService(
        serviceEnabledChecker: () async => true,
        permissionChecker: () async => LocationPermission.always,
        positionRetriever: ({locationSettings}) async => Position(
          latitude: 26.8467,
          longitude: 80.9462,
          timestamp: DateTime.now(),
          accuracy: 10.0,
          altitude: 0.0,
          altitudeAccuracy: 0.0,
          heading: 0.0,
          headingAccuracy: 0.0,
          speed: 0.0,
          speedAccuracy: 0.0,
        ),
      );

      final provider = FacilityProvider(
        apiService: ApiService(client: errorClient),
        locationService: mockLocationService,
      );

      await provider.useCurrentLocationAndSearch();
      expect(provider.status, FacilitySearchStatus.backendError);
      expect(provider.backendErrorMessage, contains('500'));
    });

    // 8. ASV UNKNOWN status displayed accurately in UI
    testWidgets('8. ASV UNKNOWN status displayed accurately in UI',
        (WidgetTester tester) async {
      final facility = FacilityModel(
        facilityId: 'HCF-018470',
        facilityName: 'Tala PHC',
        facilityType: 'PHC',
        stateName: 'Uttar Pradesh',
        districtName: 'Lucknow',
        latitude: 27.0543,
        longitude: 80.9321,
        distanceKm: 3.8,
        asvStockStatus: 'UNKNOWN',
        asvDataMode: 'REAL',
        asvVerificationSource: 'NOT_VERIFIED',
      );

      final mockClient = MockClient((request) async {
        return http.Response(
          jsonEncode({
            'query_latitude': 26.8467,
            'query_longitude': 80.9462,
            'search_radius_km': 30.0,
            'total_found': 1,
            'facilities': [
              {
                'facility_id': facility.facilityId,
                'facility_name': facility.facilityName,
                'facility_type': facility.facilityType,
                'state_name': facility.stateName,
                'district_name': facility.districtName,
                'latitude': facility.latitude,
                'longitude': facility.longitude,
                'distance_km': facility.distanceKm,
                'asv_stock_status': facility.asvStockStatus,
                'asv_data_mode': facility.asvDataMode,
                'asv_verification_source': facility.asvVerificationSource,
              }
            ],
            'safety_disclaimer': 'ASV is unverified without confirmation.',
          }),
          200,
          headers: {'content-type': 'application/json'},
        );
      });

      final mockLocationService = LocationService(
        serviceEnabledChecker: () async => true,
        permissionChecker: () async => LocationPermission.always,
        positionRetriever: ({locationSettings}) async => Position(
          latitude: 26.8467,
          longitude: 80.9462,
          timestamp: DateTime.now(),
          accuracy: 10.0,
          altitude: 0.0,
          altitudeAccuracy: 0.0,
          heading: 0.0,
          headingAccuracy: 0.0,
          speed: 0.0,
          speedAccuracy: 0.0,
        ),
      );

      final provider = FacilityProvider(
        apiService: ApiService(client: mockClient),
        locationService: mockLocationService,
      );

      await tester.pumpWidget(
        ChangeNotifierProvider<FacilityProvider>.value(
          value: provider,
          child: const MaterialApp(
            home: HomeScreen(),
          ),
        ),
      );
      await tester.pumpAndSettle();

      // Trigger search on provider
      await provider.useCurrentLocationAndSearch();
      await tester.pumpAndSettle();

      expect(provider.facilities.length, 1);
      expect(provider.facilities.first.asvStockStatus, 'UNKNOWN');
      expect(find.text('Tala PHC'), findsOneWidget);
      expect(find.text('ASV Stock: Unverified'), findsOneWidget);
    });

    // 9. Repeated location searches do not create duplicate emergency cases
    test(
        '9. Repeated location searches do not create duplicate emergency cases',
        () async {
      int requestCount = 0;
      final mockClient = MockClient((request) async {
        requestCount++;
        return http.Response(
          jsonEncode({
            'query_latitude': 26.8467,
            'query_longitude': 80.9462,
            'search_radius_km': 30.0,
            'total_found': 1,
            'facilities': [],
            'safety_disclaimer': 'Test disclaimer',
          }),
          200,
          headers: {'content-type': 'application/json'},
        );
      });

      final mockLocationService = LocationService(
        serviceEnabledChecker: () async => true,
        permissionChecker: () async => LocationPermission.always,
        positionRetriever: ({locationSettings}) async => Position(
          latitude: 26.8467,
          longitude: 80.9462,
          timestamp: DateTime.now(),
          accuracy: 10.0,
          altitude: 0.0,
          altitudeAccuracy: 0.0,
          heading: 0.0,
          headingAccuracy: 0.0,
          speed: 0.0,
          speedAccuracy: 0.0,
        ),
      );

      final provider = FacilityProvider(
        apiService: ApiService(client: mockClient),
        locationService: mockLocationService,
      );

      // Fire multiple simultaneous searches
      final future1 = provider.useCurrentLocationAndSearch();
      final future2 = provider.useCurrentLocationAndSearch();
      await Future.wait([future1, future2]);

      // Only one network request should have been dispatched
      expect(requestCount, 1);
    });

    // 10. Existing emergency flow still works without GPS coordinates
    test(
        '10. Existing emergency flow works via manual village search without GPS',
        () async {
      final mockClient = MockClient((request) async {
        final body = jsonDecode(request.body);
        expect(body['location']['village'], 'Bakshi Ka Talab');
        expect(body['channel'], 'FLUTTER');

        return http.Response(
          jsonEncode({
            'conversation_id': 'conv-12345',
            'intent': 'location_response',
            'intent_confidence': 0.9,
            'case_id': 'DS-2026-TEST',
            'case_status': 'REFERRAL_MADE',
            'next_action': 'TRANSPORT',
            'response_text': 'Referred to nearest facility.',
            'nearby_facilities': [
              {
                'facility_id': 'HCF-018470',
                'facility_name': 'Tala PHC',
                'facility_type': 'PHC',
                'state_name': 'Uttar Pradesh',
                'district_name': 'Lucknow',
                'latitude': 27.0543,
                'longitude': 80.9321,
                'distance_km': 3.8,
                'asv_stock_status': 'UNKNOWN',
                'asv_data_mode': 'REAL',
                'asv_verification_source': 'NOT_VERIFIED',
              }
            ],
            'referral': {
              'facility_id': 'HCF-018470',
              'referral_status': 'PENDING',
              'timestamp': '2026-10-18T00:00:00',
            },
            'safety_metadata': {},
          }),
          200,
          headers: {'content-type': 'application/json'},
        );
      });

      // Disabled GPS location service
      final disabledLocationService = LocationService(
        serviceEnabledChecker: () async => false,
      );

      final provider = FacilityProvider(
        apiService: ApiService(client: mockClient),
        locationService: disabledLocationService,
      );

      // User performs manual search without GPS
      await provider.searchByManualLocation('Bakshi Ka Talab');

      expect(provider.status, FacilitySearchStatus.resultsAvailable);
      expect(provider.facilities.length, 1);
      expect(provider.conversationId, 'conv-12345');
      expect(provider.caseId, 'DS-2026-TEST');
      expect(provider.activeReferral?.facilityId, 'HCF-018470');
    });
  });
}
