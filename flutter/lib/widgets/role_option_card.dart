import 'package:flutter/material.dart';
import '../core/theme/app_theme.dart';

/// Reusable card component for role selection (Patient / Family, ASHA Worker).
class RoleOptionCard extends StatelessWidget {
  final String title;
  final String description;
  final List<String> benefits;
  final Widget actionWidget;

  const RoleOptionCard({
    super.key,
    required this.title,
    required this.description,
    required this.benefits,
    required this.actionWidget,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(20.0),
      decoration: BoxDecoration(
        color: AppTheme.sanjeeviniCard,
        borderRadius: BorderRadius.circular(14.0),
        border: Border.all(
          color: AppTheme.sanjeeviniBorder,
          width: 1.2,
        ),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Title
          Text(
            title,
            style: const TextStyle(
              fontSize: 18.5,
              fontWeight: FontWeight.w700,
              color: AppTheme.sanjeeviniTextDark,
              letterSpacing: -0.2,
            ),
          ),
          const SizedBox(height: 4.0),
          // Subtitle / Description
          Text(
            description,
            style: const TextStyle(
              fontSize: 14.0,
              color: AppTheme.sanjeeviniTextMuted,
            ),
          ),
          const SizedBox(height: 14.0),
          // Subtle Divider
          const Divider(
            color: AppTheme.sanjeeviniDivider,
            thickness: 1.0,
            height: 1.0,
          ),
          const SizedBox(height: 14.0),
          // Benefits list with custom green bullet points
          ...benefits.map(
            (benefit) => Padding(
              padding: const EdgeInsets.only(bottom: 8.0),
              child: Row(
                crossAxisAlignment: CrossAxisAlignment.center,
                children: [
                  Container(
                    width: 6.0,
                    height: 6.0,
                    decoration: const BoxDecoration(
                      color: AppTheme.sanjeeviniPrimary,
                      shape: BoxShape.circle,
                    ),
                  ),
                  const SizedBox(width: 10.0),
                  Expanded(
                    child: Text(
                      benefit,
                      style: const TextStyle(
                        fontSize: 14.5,
                        fontWeight: FontWeight.w500,
                        color: AppTheme.sanjeeviniTextDark,
                      ),
                    ),
                  ),
                ],
              ),
            ),
          ),
          const SizedBox(height: 8.0),
          // Action button / link
          actionWidget,
        ],
      ),
    );
  }
}
