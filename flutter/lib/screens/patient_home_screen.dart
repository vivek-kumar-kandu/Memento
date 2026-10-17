import 'package:flutter/material.dart';
import 'package:url_launcher/url_launcher.dart';
import '../core/constants/api_constants.dart';
import '../core/theme/app_theme.dart';
import '../widgets/sanjeevini_logo.dart';
import 'first_aid_screen.dart';
import 'home_screen.dart';
import 'safety_products_screen.dart';

/// Patient / Family emergency guidance and facilities placeholder screen.
/// Accessible immediately without login or account creation.
class PatientHomeScreen extends StatelessWidget {
  const PatientHomeScreen({super.key});

  Future<void> _callEmergency(BuildContext context) async {
    final Uri phoneUri = Uri.parse('tel:${ApiConstants.ambulanceNumber}');
    if (await canLaunchUrl(phoneUri)) {
      await launchUrl(phoneUri);
    } else {
      if (context.mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('Could not open phone dialer. Please dial 108 manually.'),
            backgroundColor: AppTheme.primaryDark,
          ),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppTheme.sanjeeviniBg,
      appBar: AppBar(
        backgroundColor: AppTheme.sanjeeviniPrimary,
        foregroundColor: Colors.white,
        elevation: 0,
        title: Row(
          children: const [
            SanjeeviniLogo(size: 28),
            SizedBox(width: 10),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    'Patient Emergency Care',
                    style: TextStyle(fontSize: 17, fontWeight: FontWeight.bold),
                  ),
                  Text(
                    'Immediate public assistance • No login required',
                    style: TextStyle(fontSize: 11.5, color: Colors.white70),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(16.0),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Urgent 108 Ambulance Call Box
              Container(
                width: double.infinity,
                padding: const EdgeInsets.all(18.0),
                decoration: BoxDecoration(
                  color: Colors.red.shade50,
                  borderRadius: BorderRadius.circular(12.0),
                  border: Border.all(color: Colors.red.shade200, width: 1.2),
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: [
                        Icon(Icons.emergency, color: Colors.red.shade800, size: 24),
                        const SizedBox(width: 8),
                        Text(
                          'Call Emergency Ambulance',
                          style: TextStyle(
                            fontSize: 17,
                            fontWeight: FontWeight.bold,
                            color: Colors.red.shade900,
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 8),
                    const Text(
                      'If a snakebite has occurred, do not delay. Request immediate transport to a government hospital equipped with anti-snake venom.',
                      style: TextStyle(fontSize: 13.5, color: AppTheme.textPrimary, height: 1.4),
                    ),
                    const SizedBox(height: 14),
                    SizedBox(
                      width: double.infinity,
                      child: ElevatedButton.icon(
                        style: ElevatedButton.styleFrom(
                          backgroundColor: AppTheme.primaryEmergency,
                          foregroundColor: Colors.white,
                          padding: const EdgeInsets.symmetric(vertical: 13),
                          shape: RoundedRectangleBorder(
                            borderRadius: BorderRadius.circular(8),
                          ),
                        ),
                        onPressed: () => _callEmergency(context),
                        icon: const Icon(Icons.phone_in_talk, size: 20),
                        label: const Text(
                          'Call 108 Ambulance',
                          style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
                        ),
                      ),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 16),

              // NAPSE First Aid Guidance Button Card
              Container(
                width: double.infinity,
                padding: const EdgeInsets.all(16.0),
                decoration: BoxDecoration(
                  color: AppTheme.sanjeeviniCard,
                  borderRadius: BorderRadius.circular(12.0),
                  border: Border.all(color: AppTheme.sanjeeviniBorder, width: 1.2),
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Row(
                      children: [
                        Icon(Icons.medical_information_outlined, color: AppTheme.sanjeeviniPrimary),
                        SizedBox(width: 8),
                        Text(
                          'Official First Aid Guidelines',
                          style: TextStyle(
                            fontSize: 16,
                            fontWeight: FontWeight.bold,
                            color: AppTheme.sanjeeviniTextDark,
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 8),
                    const Text(
                      'Review the Ministry of Health & Family Welfare NAPSE R.I.G.H.T. protocol for snakebite victim immobilization and do\'s & don\'ts.',
                      style: TextStyle(fontSize: 13.5, color: AppTheme.sanjeeviniTextMuted, height: 1.4),
                    ),
                    const SizedBox(height: 12),
                    OutlinedButton.icon(
                      style: OutlinedButton.styleFrom(
                        foregroundColor: AppTheme.sanjeeviniPrimary,
                        side: const BorderSide(color: AppTheme.sanjeeviniPrimary),
                        shape: RoundedRectangleBorder(
                          borderRadius: BorderRadius.circular(8),
                        ),
                        padding: const EdgeInsets.symmetric(vertical: 10, horizontal: 14),
                      ),
                      onPressed: () {
                        Navigator.push(
                          context,
                          MaterialPageRoute(
                            builder: (context) => const FirstAidScreen(),
                          ),
                        );
                      },
                      icon: const Icon(Icons.book, size: 18),
                      label: const Text(
                        'View First Aid Protocol',
                        style: TextStyle(fontWeight: FontWeight.w600),
                      ),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 16),

              // Prevention & Safety Products Section
              Container(
                width: double.infinity,
                padding: const EdgeInsets.all(16.0),
                decoration: BoxDecoration(
                  color: AppTheme.sanjeeviniCard,
                  borderRadius: BorderRadius.circular(12.0),
                  border: Border.all(color: AppTheme.sanjeeviniBorder, width: 1.2),
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: const [
                        Icon(Icons.shield_outlined, color: AppTheme.sanjeeviniPrimary),
                        SizedBox(width: 8),
                        Text(
                          'Prevention & Safety Products',
                          style: TextStyle(
                            fontSize: 16,
                            fontWeight: FontWeight.bold,
                            color: AppTheme.sanjeeviniTextDark,
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 8),
                    const Text(
                      'Explore products that support safer homes and outdoor work.',
                      style: TextStyle(fontSize: 13.5, color: AppTheme.sanjeeviniTextMuted, height: 1.4),
                    ),
                    const SizedBox(height: 12),
                    OutlinedButton.icon(
                      style: OutlinedButton.styleFrom(
                        foregroundColor: AppTheme.sanjeeviniPrimary,
                        side: const BorderSide(color: AppTheme.sanjeeviniPrimary),
                        shape: RoundedRectangleBorder(
                          borderRadius: BorderRadius.circular(8),
                        ),
                        padding: const EdgeInsets.symmetric(vertical: 10, horizontal: 14),
                      ),
                      onPressed: () {
                        Navigator.push(
                          context,
                          MaterialPageRoute(
                            builder: (context) => const SafetyProductsScreen(),
                          ),
                        );
                      },
                      icon: const Icon(Icons.arrow_forward, size: 18),
                      label: const Text(
                        'Browse Safety Products',
                        style: TextStyle(fontWeight: FontWeight.w600),
                      ),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 20),

              // Nearby Facilities Header
              const Text(
                'Nearby Healthcare Facilities',
                style: TextStyle(
                  fontSize: 17,
                  fontWeight: FontWeight.bold,
                  color: AppTheme.sanjeeviniTextDark,
                ),
              ),
              const SizedBox(height: 4),
              const Text(
                'Discover closest verified PHCs and CHCs using GPS or village search. Anti-snake venom availability is unverified until confirmed.',
                style: TextStyle(fontSize: 13, color: AppTheme.sanjeeviniTextMuted, height: 1.3),
              ),
              const SizedBox(height: 12),

              // Primary "Use My Current Location" Button
              SizedBox(
                width: double.infinity,
                child: ElevatedButton.icon(
                  key: const Key('patient_use_current_location_button'),
                  style: ElevatedButton.styleFrom(
                    backgroundColor: AppTheme.sanjeeviniPrimary,
                    foregroundColor: Colors.white,
                    padding: const EdgeInsets.symmetric(vertical: 13),
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(8),
                    ),
                  ),
                  onPressed: () {
                    Navigator.push(
                      context,
                      MaterialPageRoute(
                        builder: (context) => const HomeScreen(),
                      ),
                    );
                  },
                  icon: const Icon(Icons.my_location, size: 20),
                  label: const Text(
                    'Use My Current Location',
                    style: TextStyle(fontWeight: FontWeight.bold, fontSize: 15),
                  ),
                ),
              ),
              const SizedBox(height: 12),

              // Placeholder Facility Card 1
              _buildPlaceholderFacilityCard(
                name: 'Community Health Centre (CHC) Rampur',
                type: 'CHC • 24/7 Emergency',
                distance: '4.2 km away',
                status: 'Sample Facility (Unverified Stock)',
                statusColor: Colors.orange.shade800,
              ),
              const SizedBox(height: 10),

              // Placeholder Facility Card 2
              _buildPlaceholderFacilityCard(
                name: 'Sub-District Hospital (SDH) Chandpur',
                type: 'Sub-District Hospital',
                distance: '9.8 km away',
                status: 'Sample Facility (Unverified Stock)',
                statusColor: Colors.orange.shade800,
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildPlaceholderFacilityCard({
    required String name,
    required String type,
    required String distance,
    required String status,
    required Color statusColor,
  }) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(14.0),
      decoration: BoxDecoration(
        color: AppTheme.sanjeeviniCard,
        borderRadius: BorderRadius.circular(10.0),
        border: Border.all(color: AppTheme.sanjeeviniBorder, width: 1.0),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Expanded(
                child: Text(
                  name,
                  style: const TextStyle(
                    fontSize: 15,
                    fontWeight: FontWeight.bold,
                    color: AppTheme.sanjeeviniTextDark,
                  ),
                ),
              ),
              Text(
                distance,
                style: const TextStyle(
                  fontSize: 12.5,
                  fontWeight: FontWeight.w600,
                  color: AppTheme.sanjeeviniPrimary,
                ),
              ),
            ],
          ),
          const SizedBox(height: 4),
          Text(
            type,
            style: const TextStyle(fontSize: 13, color: AppTheme.sanjeeviniTextMuted),
          ),
          const SizedBox(height: 8),
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
            decoration: BoxDecoration(
              color: statusColor.withValues(alpha: 0.1),
              borderRadius: BorderRadius.circular(4),
            ),
            child: Text(
              status,
              style: TextStyle(
                fontSize: 11.5,
                fontWeight: FontWeight.w600,
                color: statusColor,
              ),
            ),
          ),
        ],
      ),
    );
  }
}
