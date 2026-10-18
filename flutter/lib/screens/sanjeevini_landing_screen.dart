import 'package:flutter/material.dart';
import '../core/theme/app_theme.dart';
import '../widgets/role_option_card.dart';
import '../widgets/sanjeevini_logo.dart';
import 'asha_login_screen.dart';
import 'patient_home_screen.dart';

/// Sanjeevini landing and role selection screen.
/// Designed for rural Indian emergency assistance with high clarity,
/// direct patient access without login, and secure ASHA worker login.
class SanjeeviniLandingScreen extends StatelessWidget {
  const SanjeeviniLandingScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppTheme.sanjeeviniBg,
      body: SafeArea(
        child: SingleChildScrollView(
          physics: const ClampingScrollPhysics(),
          padding: const EdgeInsets.symmetric(horizontal: 20.0, vertical: 20.0),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // 1. App Header / Branding
              Row(
                crossAxisAlignment: CrossAxisAlignment.center,
                children: [
                  const SanjeeviniLogo(size: 48.0),
                  const SizedBox(width: 14.0),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      mainAxisSize: MainAxisSize.min,
                      children: const [
                        Text(
                          'Sanjeevini',
                          style: TextStyle(
                            fontSize: 22.0,
                            fontWeight: FontWeight.w700,
                            color: AppTheme.sanjeeviniTextDark,
                            letterSpacing: -0.3,
                          ),
                        ),
                        SizedBox(height: 2.0),
                        Text(
                          'Snakebite emergency assistance',
                          style: TextStyle(
                            fontSize: 13.5,
                            color: AppTheme.sanjeeviniTextMuted,
                          ),
                        ),
                      ],
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 32.0),

              // 2. Main Heading & Subtitle
              const Text(
                'How can we help?',
                style: TextStyle(
                  fontSize: 29.0,
                  fontWeight: FontWeight.w800,
                  color: AppTheme.sanjeeviniTextDark,
                  letterSpacing: -0.5,
                ),
              ),
              const SizedBox(height: 10.0),
              const Text(
                'Support for suspected snakebite emergencies.\nChoose an option to continue.',
                style: TextStyle(
                  fontSize: 15.0,
                  color: AppTheme.sanjeeviniTextMuted,
                  height: 1.45,
                ),
              ),
              const SizedBox(height: 26.0),

              // 3. Option 1: Patient / Family Card
              RoleOptionCard(
                title: 'Patient / Family',
                description: 'No account or login needed.',
                benefits: const [
                  'Get emergency guidance',
                  'Find nearby health facilities',
                ],
                actionWidget: SizedBox(
                  width: double.infinity,
                  child: ElevatedButton(
                    style: ElevatedButton.styleFrom(
                      backgroundColor: AppTheme.sanjeeviniPrimary,
                      foregroundColor: Colors.white,
                      elevation: 0,
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(8.0),
                      ),
                      padding: const EdgeInsets.symmetric(
                        horizontal: 16.0,
                        vertical: 13.0,
                      ),
                    ),
                    onPressed: () {
                      Navigator.push(
                        context,
                        MaterialPageRoute(
                          builder: (context) => const PatientHomeScreen(),
                        ),
                      );
                    },
                    child: Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: const [
                        Expanded(
                          child: Text(
                            'Continue as Patient',
                            style: TextStyle(
                              fontSize: 15.5,
                              fontWeight: FontWeight.w600,
                              letterSpacing: -0.2,
                            ),
                          ),
                        ),
                        Icon(
                          Icons.chevron_right,
                          color: Colors.white,
                          size: 22.0,
                        ),
                      ],
                    ),
                  ),
                ),
              ),
              const SizedBox(height: 16.0),

              // 4. Option 2: ASHA Worker Card
              RoleOptionCard(
                title: 'ASHA Worker',
                description: 'Login required for field coordination.',
                benefits: const [
                  'View assigned cases',
                  'Update facility readiness',
                ],
                actionWidget: InkWell(
                  borderRadius: BorderRadius.circular(6.0),
                  onTap: () {
                    Navigator.push(
                      context,
                      MaterialPageRoute(
                        builder: (context) => const AshaLoginScreen(),
                      ),
                    );
                  },
                  child: const Padding(
                    padding: EdgeInsets.symmetric(vertical: 6.0, horizontal: 2.0),
                    child: Text(
                      'ASHA Worker Login',
                      style: TextStyle(
                        fontSize: 15.0,
                        fontWeight: FontWeight.w600,
                        color: AppTheme.sanjeeviniPrimary,
                      ),
                    ),
                  ),
                ),
              ),
              const SizedBox(height: 28.0),

              // 5. Emergency Safety Section
              const Text(
                'If a snakebite may have occurred',
                style: TextStyle(
                  fontSize: 16.5,
                  fontWeight: FontWeight.w700,
                  color: AppTheme.sanjeeviniTextDark,
                  letterSpacing: -0.2,
                ),
              ),
              const SizedBox(height: 8.0),
              const Text(
                'Seek urgent medical care. Keep the person still and avoid cutting, sucking or tightly tying the limb.',
                style: TextStyle(
                  fontSize: 14.0,
                  color: AppTheme.sanjeeviniTextMuted,
                  height: 1.45,
                ),
              ),
              const SizedBox(height: 22.0),

              // 6. Subtle Divider
              const Divider(
                color: AppTheme.sanjeeviniDivider,
                thickness: 1.0,
                height: 1.0,
              ),
              const SizedBox(height: 16.0),

              // 7. Footer text
              const Text(
                'Simple access. Clear guidance. Local coordination.',
                style: TextStyle(
                  fontSize: 13.5,
                  color: AppTheme.sanjeeviniTextMuted,
                ),
              ),
              const SizedBox(height: 32.0),

              // 8. Bottom Tagline
              const Text(
                'Sanjeevini • Emergency assistance',
                style: TextStyle(
                  fontSize: 12.0,
                  color: AppTheme.sanjeeviniFooter,
                ),
              ),
              const SizedBox(height: 8.0),
            ],
          ),
        ),
      ),
    );
  }
}
