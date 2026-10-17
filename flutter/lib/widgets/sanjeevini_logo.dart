import 'package:flutter/material.dart';
import '../core/theme/app_theme.dart';

/// Sanjeevini brand emblem widget.
/// Renders the signature medical-nature emblem inside a rounded squircle.
class SanjeeviniLogo extends StatelessWidget {
  final double size;

  const SanjeeviniLogo({
    super.key,
    this.size = 48.0,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      width: size,
      height: size,
      decoration: BoxDecoration(
        color: AppTheme.sanjeeviniIconBg,
        borderRadius: BorderRadius.circular(size * 0.25),
      ),
      child: Center(
        child: CustomPaint(
          size: Size(size * 0.58, size * 0.58),
          painter: _SanjeeviniEmblemPainter(
            color: AppTheme.sanjeeviniPrimary,
          ),
        ),
      ),
    );
  }
}

class _SanjeeviniEmblemPainter extends CustomPainter {
  final Color color;

  _SanjeeviniEmblemPainter({required this.color});

  @override
  void paint(Canvas canvas, Size size) {
    final paint = Paint()
      ..color = color
      ..style = PaintingStyle.fill;

    final w = size.width;
    final h = size.height;

    // Stem (vertical pillar with rounded bottom)
    final stemWidth = w * 0.22;
    final stemRect = RRect.fromRectAndRadius(
      Rect.fromCenter(
        center: Offset(w * 0.5, h * 0.62),
        width: stemWidth,
        height: h * 0.72,
      ),
      Radius.circular(stemWidth * 0.5),
    );
    canvas.drawRRect(stemRect, paint);

    // Cross arms (horizontal bar with rounded ends)
    final armHeight = h * 0.18;
    final armWidth = w * 0.88;
    final armRect = RRect.fromRectAndRadius(
      Rect.fromCenter(
        center: Offset(w * 0.5, h * 0.56),
        width: armWidth,
        height: armHeight,
      ),
      Radius.circular(armHeight * 0.5),
    );
    canvas.drawRRect(armRect, paint);

    // Top leaf / crown dome
    final crownPath = Path();
    crownPath.moveTo(w * 0.18, h * 0.42);
    crownPath.cubicTo(
      w * 0.18,
      h * 0.12,
      w * 0.38,
      0,
      w * 0.5,
      0,
    );
    crownPath.cubicTo(
      w * 0.62,
      0,
      w * 0.82,
      h * 0.12,
      w * 0.82,
      h * 0.42,
    );
    crownPath.close();
    canvas.drawPath(crownPath, paint);
  }

  @override
  bool shouldRepaint(covariant _SanjeeviniEmblemPainter oldDelegate) {
    return oldDelegate.color != color;
  }
}
