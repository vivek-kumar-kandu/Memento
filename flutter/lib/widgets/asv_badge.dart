import 'package:flutter/material.dart';

class AsvBadge extends StatelessWidget {
  final String status;
  final int? quantity;

  const AsvBadge({
    super.key,
    required this.status,
    this.quantity,
  });

  @override
  Widget build(BuildContext context) {
    Color bg;
    Color fg;
    String label;
    IconData icon;

    switch (status.toUpperCase()) {
      case 'AVAILABLE':
        bg = const Color(0xFFDCFCE7); // Light green
        fg = const Color(0xFF15803D); // Forest green
        label = quantity != null ? 'ASV: $quantity Vials' : 'ASV Available';
        icon = Icons.check_circle_outline;
        break;
      case 'OUT_OF_STOCK':
        bg = const Color(0xFFFEE2E2); // Light red
        fg = const Color(0xFFB91C1C); // Dark red
        label = 'ASV Out of Stock';
        icon = Icons.cancel_outlined;
        break;
      case 'UNKNOWN':
      default:
        bg = const Color(0xFFFEF3C7); // Light amber
        fg = const Color(0xFFB45309); // Dark amber
        label = 'ASV Stock: Unverified';
        icon = Icons.help_outline;
        break;
    }

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
      decoration: BoxDecoration(
        color: bg,
        borderRadius: BorderRadius.circular(6),
        border: Border.all(color: fg.withValues(alpha: 0.3)),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(icon, size: 14, color: fg),
          const SizedBox(width: 4),
          Text(
            label,
            style: TextStyle(
              color: fg,
              fontSize: 12,
              fontWeight: FontWeight.w600,
            ),
          ),
        ],
      ),
    );
  }
}
