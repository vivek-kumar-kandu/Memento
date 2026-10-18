import 'package:flutter/material.dart';
import '../core/theme/app_theme.dart';
import '../models/safety_product.dart';

/// Product card widget matching Sanjeevini's clean, subtle-bordered design.
class SafetyProductCard extends StatelessWidget {
  final SafetyProduct product;
  final VoidCallback onTap;

  const SafetyProductCard({
    super.key,
    required this.product,
    required this.onTap,
  });

  IconData _getCategoryIcon(String category) {
    switch (category.toLowerCase()) {
      case 'lighting':
        return Icons.flashlight_on_outlined;
      case 'footwear & workwear':
        return Icons.hiking_outlined;
      case 'first aid':
        return Icons.medical_services_outlined;
      case 'preparedness':
        return Icons.shield_outlined;
      default:
        return Icons.health_and_safety_outlined;
    }
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      margin: const EdgeInsets.only(bottom: 12.0),
      decoration: BoxDecoration(
        color: AppTheme.sanjeeviniCard,
        borderRadius: BorderRadius.circular(12.0),
        border: Border.all(
          color: AppTheme.sanjeeviniBorder,
          width: 1.2,
        ),
      ),
      child: InkWell(
        borderRadius: BorderRadius.circular(12.0),
        onTap: onTap,
        child: Padding(
          padding: const EdgeInsets.all(16.0),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Top Row: Category Badge & Demo Tag
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 8.0, vertical: 3.5),
                    decoration: BoxDecoration(
                      color: AppTheme.sanjeeviniIconBg,
                      borderRadius: BorderRadius.circular(6.0),
                    ),
                    child: Row(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        Icon(
                          _getCategoryIcon(product.category),
                          size: 13.0,
                          color: AppTheme.sanjeeviniPrimary,
                        ),
                        const SizedBox(width: 5.0),
                        Text(
                          product.category,
                          style: const TextStyle(
                            fontSize: 11.5,
                            fontWeight: FontWeight.w600,
                            color: AppTheme.sanjeeviniPrimary,
                          ),
                        ),
                      ],
                    ),
                  ),
                  if (product.isDemonstrationSample)
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 7.0, vertical: 2.5),
                      decoration: BoxDecoration(
                        color: Colors.grey.shade100,
                        borderRadius: BorderRadius.circular(4.0),
                        border: Border.all(color: Colors.grey.shade300, width: 0.8),
                      ),
                      child: const Text(
                        'Sample Data',
                        style: TextStyle(
                          fontSize: 10.5,
                          fontWeight: FontWeight.w500,
                          color: AppTheme.sanjeeviniTextMuted,
                        ),
                      ),
                    ),
                ],
              ),
              const SizedBox(height: 10.0),

              // Product Info Row (Icon/Image placeholder + details)
              Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  // Image or Category Icon Box
                  Container(
                    width: 56.0,
                    height: 56.0,
                    decoration: BoxDecoration(
                      color: AppTheme.sanjeeviniBg,
                      borderRadius: BorderRadius.circular(8.0),
                      border: Border.all(color: AppTheme.sanjeeviniBorder, width: 1.0),
                    ),
                    child: Center(
                      child: Icon(
                        _getCategoryIcon(product.category),
                        color: AppTheme.sanjeeviniPrimary,
                        size: 28.0,
                      ),
                    ),
                  ),
                  const SizedBox(width: 14.0),

                  // Title & Short Description
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          product.name,
                          style: const TextStyle(
                            fontSize: 15.5,
                            fontWeight: FontWeight.w700,
                            color: AppTheme.sanjeeviniTextDark,
                            height: 1.25,
                          ),
                        ),
                        const SizedBox(height: 4.0),
                        Text(
                          product.description,
                          maxLines: 2,
                          overflow: TextOverflow.ellipsis,
                          style: const TextStyle(
                            fontSize: 13.0,
                            color: AppTheme.sanjeeviniTextMuted,
                            height: 1.35,
                          ),
                        ),
                      ],
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 12.0),

              const Divider(
                color: AppTheme.sanjeeviniDivider,
                thickness: 1.0,
                height: 1.0,
              ),
              const SizedBox(height: 10.0),

              // Bottom Row: Price, Seller & Verification Status
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  // Price Status
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          product.displayPrice,
                          style: TextStyle(
                            fontSize: 15.0,
                            fontWeight: FontWeight.w700,
                            color: product.isPriceVerified
                                ? AppTheme.sanjeeviniPrimary
                                : AppTheme.sanjeeviniTextMuted,
                          ),
                        ),
                        Text(
                          product.sellerName ??
                              (product.sellerLinks.isNotEmpty
                                  ? product.sellerLinks.map((l) => l.sellerName).toSet().join(' • ')
                                  : 'Seller not verified'),
                          maxLines: 1,
                          overflow: TextOverflow.ellipsis,
                          style: const TextStyle(
                            fontSize: 11.5,
                            color: AppTheme.sanjeeviniTextMuted,
                          ),
                        ),
                      ],
                    ),
                  ),
                  const SizedBox(width: 8.0),

                  // Details arrow indicator
                  Row(
                    children: const [
                      Text(
                        'Details',
                        style: TextStyle(
                          fontSize: 13.0,
                          fontWeight: FontWeight.w600,
                          color: AppTheme.sanjeeviniPrimary,
                        ),
                      ),
                      SizedBox(width: 2.0),
                      Icon(
                        Icons.chevron_right,
                        size: 18.0,
                        color: AppTheme.sanjeeviniPrimary,
                      ),
                    ],
                  ),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }
}
