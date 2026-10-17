import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:dhwani_sanjeevani/main.dart';
import 'package:dhwani_sanjeevani/models/safety_product.dart';
import 'package:dhwani_sanjeevani/screens/safety_product_details_screen.dart';

void main() {
  testWidgets('Sanjeevini landing screen renders all key sections', (WidgetTester tester) async {
    await tester.pumpWidget(const DhwaniSanjeevaniApp());
    await tester.pumpAndSettle();

    // Verify App Name and Subtitle
    expect(find.text('Sanjeevini'), findsWidgets);
    expect(find.text('Snakebite emergency assistance'), findsOneWidget);

    // Verify Main Heading and Description
    expect(find.text('How can we help?'), findsOneWidget);
    expect(
      find.text('Support for suspected snakebite emergencies.\nChoose an option to continue.'),
      findsOneWidget,
    );

    // Verify Option 1: Patient / Family
    expect(find.text('Patient / Family'), findsOneWidget);
    expect(find.text('No account or login needed.'), findsOneWidget);
    expect(find.text('Get emergency guidance'), findsOneWidget);
    expect(find.text('Find nearby health facilities'), findsOneWidget);
    expect(find.text('Continue as Patient'), findsOneWidget);

    // Verify Option 2: ASHA Worker
    expect(find.text('ASHA Worker'), findsOneWidget);
    expect(find.text('Login required for field coordination.'), findsOneWidget);
    expect(find.text('View assigned cases'), findsOneWidget);
    expect(find.text('Update facility readiness'), findsOneWidget);
    expect(find.text('ASHA Worker Login'), findsOneWidget);

    // Verify Safety Section & Footer
    expect(find.text('If a snakebite may have occurred'), findsOneWidget);
    expect(
      find.text('Seek urgent medical care. Keep the person still and avoid cutting, sucking or tightly tying the limb.'),
      findsOneWidget,
    );
    expect(find.text('Simple access. Clear guidance. Local coordination.'), findsOneWidget);
  });

  testWidgets('Patient / Family navigates directly to Patient Home screen without login', (WidgetTester tester) async {
    await tester.pumpWidget(const DhwaniSanjeevaniApp());
    await tester.pumpAndSettle();

    // Tap "Continue as Patient"
    final patientBtn = find.text('Continue as Patient');
    expect(patientBtn, findsOneWidget);
    await tester.tap(patientBtn);
    await tester.pumpAndSettle();

    // Verify Patient Home screen is displayed directly without login
    expect(find.text('Patient Emergency Care'), findsOneWidget);
    expect(find.text('Call 108 Ambulance'), findsOneWidget);
    expect(find.text('Official First Aid Guidelines'), findsOneWidget);
    expect(find.text('Nearby Health Facilities (Prototype)'), findsOneWidget);

    // Verify back navigation works
    final backBtn = find.byType(BackButton);
    expect(backBtn, findsOneWidget);
    await tester.tap(backBtn);
    await tester.pumpAndSettle();

    expect(find.text('How can we help?'), findsOneWidget);
  });

  testWidgets('ASHA Worker opens login screen and enforces validation before dashboard', (WidgetTester tester) async {
    await tester.pumpWidget(const DhwaniSanjeevaniApp());
    await tester.pumpAndSettle();

    // Tap "ASHA Worker Login"
    final ashaBtn = find.text('ASHA Worker Login');
    expect(ashaBtn, findsOneWidget);
    await tester.ensureVisible(ashaBtn);
    await tester.pumpAndSettle();
    await tester.tap(ashaBtn);
    await tester.pumpAndSettle();

    // Verify ASHA login screen
    expect(find.text('Field Coordination Login'), findsOneWidget);
    expect(find.text('Login to Dashboard'), findsOneWidget);

    // Attempt login with empty fields -> should show validation error
    final loginBtn = find.text('Login to Dashboard');
    await tester.ensureVisible(loginBtn);
    await tester.pumpAndSettle();
    await tester.tap(loginBtn);
    await tester.pumpAndSettle();

    expect(find.text('Please enter your ASHA ID or registered mobile number.'), findsOneWidget);

    // Fill valid credentials
    await tester.enterText(find.byType(TextFormField).first, 'ASHA-88214');
    await tester.enterText(find.byType(TextFormField).last, '1234');
    await tester.pumpAndSettle();

    // Submit login
    await tester.tap(loginBtn);
    await tester.pump();
    await tester.pump(const Duration(milliseconds: 700));
    await tester.pumpAndSettle();

    // Verify dashboard is shown
    expect(find.text('ASHA Field Dashboard'), findsOneWidget);
    expect(find.text('Worker ID: ASHA-88214'), findsOneWidget);
    expect(find.text('Assigned Bite Cases'), findsOneWidget);
  });

  testWidgets('Screen renders cleanly on small mobile screen (320x480) without overflow', (WidgetTester tester) async {
    tester.view.physicalSize = const Size(320, 480);
    tester.view.devicePixelRatio = 1.0;
    addTearDown(() {
      tester.view.resetPhysicalSize();
      tester.view.resetDevicePixelRatio();
    });

    await tester.pumpWidget(const DhwaniSanjeevaniApp());
    await tester.pumpAndSettle();

    expect(find.text('How can we help?'), findsOneWidget);
    expect(find.text('Patient / Family'), findsOneWidget);

    await tester.drag(find.byType(SingleChildScrollView), const Offset(0, -500));
    await tester.pumpAndSettle();

    expect(find.text('Simple access. Clear guidance. Local coordination.'), findsOneWidget);
    expect(tester.takeException(), isNull);
  });

  testWidgets('Patient Home navigates to Prevention & Safety Products screen', (WidgetTester tester) async {
    await tester.pumpWidget(const DhwaniSanjeevaniApp());
    await tester.pumpAndSettle();

    // Tap "Continue as Patient"
    await tester.tap(find.text('Continue as Patient'));
    await tester.pumpAndSettle();

    // Verify Prevention & Safety Products section exists
    expect(find.text('Prevention & Safety Products'), findsOneWidget);
    expect(
      find.text('Explore products that support safer homes and outdoor work.'),
      findsOneWidget,
    );

    // Scroll to and tap "Browse Safety Products"
    final browseBtn = find.text('Browse Safety Products');
    await tester.ensureVisible(browseBtn);
    await tester.pumpAndSettle();
    await tester.tap(browseBtn);
    await tester.pumpAndSettle();

    // Verify Safety Products listing screen
    expect(find.text('Prevention & Safety Products'), findsWidgets);
    expect(
      find.text('Suspected snakebite? Seek urgent medical care. Keep the person still. Do not cut or suck the wound or apply a tight tourniquet.'),
      findsOneWidget,
    );
    expect(find.text('High-Beam Rechargeable LED Torch'), findsOneWidget);
    expect(find.text('Knee-High Agricultural Protective Gumboots'), findsOneWidget);
  });

  testWidgets('Safety products screen displays seller buttons (Buy on Amazon, Search on Flipkart)', (WidgetTester tester) async {
    await tester.pumpWidget(const DhwaniSanjeevaniApp());
    await tester.pumpAndSettle();

    // Navigate to Patient Home then to Safety Products
    await tester.tap(find.text('Continue as Patient'));
    await tester.pumpAndSettle();

    final browseBtn = find.text('Browse Safety Products');
    await tester.ensureVisible(browseBtn);
    await tester.pumpAndSettle();
    await tester.tap(browseBtn);
    await tester.pumpAndSettle();

    // Filter by "Lighting"
    final lightingChip = find.widgetWithText(ChoiceChip, 'Lighting');
    await tester.tap(lightingChip);
    await tester.pump();
    await tester.pump(const Duration(milliseconds: 200));
    await tester.pumpAndSettle();

    expect(find.text('High-Beam Rechargeable LED Torch'), findsOneWidget);
    expect(find.text('Knee-High Agricultural Protective Gumboots'), findsNothing);

    // Tap on the Torch card to view details
    await tester.tap(find.text('High-Beam Rechargeable LED Torch'));
    await tester.pumpAndSettle();

    // Verify Product Details Screen with seller-specific buttons
    expect(find.text('Product Details'), findsOneWidget);
    expect(find.text('₹499'), findsOneWidget);
    expect(find.text('Buy on Amazon'), findsOneWidget); // Direct verified Amazon URL
    expect(find.text('Search on Flipkart'), findsOneWidget); // Encoded search fallback on Flipkart
    expect(find.text('Buy on AgriBegri Rural Supplies'), findsOneWidget); // Verified third-party seller

    // Back to product listing
    await tester.tap(find.byType(BackButton));
    await tester.pumpAndSettle();

    // Filter by "Preparedness" to test product with no seller links
    final prepChip = find.widgetWithText(ChoiceChip, 'Preparedness');
    await tester.ensureVisible(prepChip);
    await tester.pumpAndSettle();
    await tester.tap(prepChip);
    await tester.pump();
    await tester.pump(const Duration(milliseconds: 200));
    await tester.pumpAndSettle();

    final hookCard = find.text('Telescopic Aluminum Snake Safety Hook (40")');
    expect(hookCard, findsOneWidget);
    await tester.tap(hookCard);
    await tester.pumpAndSettle();

    // Verify unverified price and link unavailable states
    expect(find.text('Price not verified'), findsWidgets);
    expect(find.text('Purchase link unavailable'), findsOneWidget);
  });

  testWidgets('Handles invalid URL launch gracefully with user notification', (WidgetTester tester) async {
    // Create product with malformed / invalid URL
    const invalidProduct = SafetyProduct(
      id: 'test-invalid-url',
      name: 'Testing Malformed Link Product',
      category: 'Preparedness',
      description: 'Test description',
      amazonDirectUrl: 'ftp://invalid-protocol.com/item', // Invalid scheme
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

    // Attempt to tap the invalid seller button
    final amazonBtn = find.text('Buy on Amazon');
    expect(amazonBtn, findsOneWidget);
    await tester.ensureVisible(amazonBtn);
    await tester.pumpAndSettle();
    await tester.tap(amazonBtn);
    await tester.pumpAndSettle();

    // Verify error SnackBar is displayed gracefully
    expect(find.text('Invalid link format for Amazon.'), findsOneWidget);
  });

  test('SafetyProduct model unit test: validates direct vs search fallback URLs', () {
    // 1. Direct URL test
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
    expect(directLinks[0].url, 'https://www.amazon.in/dp/B001');

    expect(directLinks[1].buttonLabel, 'Buy on Flipkart');
    expect(directLinks[1].isDirect, isTrue);

    // 2. Search fallback test
    const productWithSearch = SafetyProduct(
      id: 'p2',
      name: 'Agricultural Gumboots Size 8',
      category: 'Footwear & Workwear',
      description: 'Desc',
      enableMarketplaceSearchFallback: true,
      intendedUse: 'Protection',
      safetyNotes: 'Notes',
    );

    final searchLinks = productWithSearch.sellerLinks;
    expect(searchLinks.length, 2);
    expect(searchLinks[0].buttonLabel, 'Search on Amazon');
    expect(searchLinks[0].isDirect, isFalse);
    expect(searchLinks[0].url, contains('https://www.amazon.in/s?k=Agricultural%20Gumboots%20Size%208'));

    expect(searchLinks[1].buttonLabel, 'Search on Flipkart');
    expect(searchLinks[1].isDirect, isFalse);
    expect(searchLinks[1].url, contains('https://www.flipkart.com/search?q=Agricultural%20Gumboots%20Size%208'));

    // 3. Unavailable link test
    const productNoLinks = SafetyProduct(
      id: 'p3',
      name: 'Custom Hook',
      category: 'Preparedness',
      description: 'Desc',
      enableMarketplaceSearchFallback: false,
      intendedUse: 'Handling',
      safetyNotes: 'Notes',
    );

    expect(productNoLinks.sellerLinks.isEmpty, isTrue);
    expect(productNoLinks.hasValidUrl, isFalse);
  });
}
