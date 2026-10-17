import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';

class AppTheme {
  static const Color primaryEmergency = Color(0xFFD32F2F); // Crimson Red
  static const Color primaryDark = Color(0xFFB71C1C);
  static const Color accentTeal = Color(0xFF00897B); // Medical Teal
  static const Color alertAmber = Color(0xFFFFA000); // Warning/Unverified
  static const Color surfaceDark = Color(0xFF1E293B); // Slate
  static const Color backgroundLight = Color(0xFFF8FAFC);
  static const Color textPrimary = Color(0xFF0F172A);
  static const Color textSecondary = Color(0xFF64748B);

  // Sanjeevini Brand Palette
  static const Color sanjeeviniBg = Color(0xFFFAFAF7);
  static const Color sanjeeviniPrimary = Color(0xFF1F5B4A);
  static const Color sanjeeviniPrimaryDark = Color(0xFF164437);
  static const Color sanjeeviniTextDark = Color(0xFF182923);
  static const Color sanjeeviniTextMuted = Color(0xFF52635B);
  static const Color sanjeeviniCard = Color(0xFFFFFFFF);
  static const Color sanjeeviniBorder = Color(0xFFE2E7E4);
  static const Color sanjeeviniIconBg = Color(0xFFE5EDE9);
  static const Color sanjeeviniDivider = Color(0xFFEBF0ED);
  static const Color sanjeeviniFooter = Color(0xFF83948C);

  static ThemeData lightTheme = ThemeData(
    useMaterial3: true,
    brightness: Brightness.light,
    colorScheme: ColorScheme.fromSeed(
      seedColor: primaryEmergency,
      primary: primaryEmergency,
      secondary: accentTeal,
      surface: backgroundLight,
    ),
    scaffoldBackgroundColor: backgroundLight,
    textTheme: GoogleFonts.interTextTheme(),
    appBarTheme: const AppBarTheme(
      backgroundColor: primaryEmergency,
      foregroundColor: Colors.white,
      elevation: 0,
      centerTitle: false,
    ),
    cardTheme: CardThemeData(
      elevation: 1,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(12),
        side: BorderSide(color: Colors.grey.shade200),
      ),
      color: Colors.white,
    ),
    elevatedButtonTheme: ElevatedButtonThemeData(
      style: ElevatedButton.styleFrom(
        backgroundColor: primaryEmergency,
        foregroundColor: Colors.white,
        elevation: 0,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(8),
        ),
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
        textStyle: const TextStyle(fontWeight: FontWeight.w600),
      ),
    ),
  );
}
