import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'core/theme/app_theme.dart';
import 'providers/facility_provider.dart';
import 'screens/sanjeevini_landing_screen.dart';

void main() {
  WidgetsFlutterBinding.ensureInitialized();
  runApp(const DhwaniSanjeevaniApp());
}

class DhwaniSanjeevaniApp extends StatelessWidget {
  const DhwaniSanjeevaniApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MultiProvider(
      providers: [
        ChangeNotifierProvider(create: (_) => FacilityProvider()),
      ],
      child: MaterialApp(
        title: 'Sanjeevini',
        debugShowCheckedModeBanner: false,
        theme: AppTheme.lightTheme,
        home: const SanjeeviniLandingScreen(),
      ),
    );
  }
}
