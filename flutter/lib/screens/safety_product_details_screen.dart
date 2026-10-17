import 'package:flutter/material.dart';
import 'package:url_launcher/url_launcher.dart';
import '../core/theme/app_theme.dart';
import '../models/safety_product.dart';

/// Detailed view for a safety or prevention product.
/// Displays intended use, specifications, safety limitations, and verified seller/marketplace links.
class SafetyProductDetailsScreen extends StatelessWidget {
  final SafetyProduct product;

  const SafetyProductDetailsScreen({
    super.key,
    required this.product,
  });

  /// Opens an external marketplace or seller URL safely with error handling and fallback.
  Future<void> _openSellerLink(BuildContext context, ProductSellerLink link) async {
    if (!link.isValidUrl) {
      if (context.mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Invalid link format for ${link.sellerName}.'),
            backgroundColor: AppTheme.primaryDark,
          ),
        );
      }
      return;
    }

    final uri = Uri.parse(link.url.trim());
    bool launched = false;

    // 1. Attempt external application launch (opens marketplace app or external browser)
    try {
      launched = await launchUrl(
        uri,
        mode: LaunchMode.externalApplication,
      );
    } catch (_) {
      launched = false;
    }

    // 2. Fall back to platformDefault if externalApplication failed
    if (!launched) {
      try {
        launched = await launchUrl(
          uri,
          mode: LaunchMode.platformDefault,
        );
      } catch (_) {
        launched = false;
      }
    }

    // 3. Graceful failure notification
    if (!launched && context.mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('Could not open ${link.sellerName} page. Please check your browser or network settings.'),
          backgroundColor: AppTheme.primaryDark,
          action: SnackBarAction(
            label: 'OK',
            textColor: Colors.white,
            onPressed: () {},
          ),
        ),
      );
    }
  }

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
    return Scaffold(
      backgroundColor: AppTheme.sanjeeviniBg,
      appBar: AppBar(
        backgroundColor: Colors.transparent,
        foregroundColor: AppTheme.sanjeeviniTextDark,
        elevation: 0,
        title: const Text(
          'Product Details',
          style: TextStyle(
            fontSize: 18.0,
            fontWeight: FontWeight.bold,
            color: AppTheme.sanjeeviniTextDark,
          ),
        ),
      ),
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.symmetric(horizontal: 20.0, vertical: 12.0),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Mandatory Emergency Snakebite Medical Advisory
              Container(
                width: double.infinity,
                padding: const EdgeInsets.all(14.0),
                decoration: BoxDecoration(
                  color: Colors.amber.shade50,
                  borderRadius: BorderRadius.circular(10.0),
                  border: Border.all(color: Colors.amber.shade300, width: 1.2),
                ),
                child: Row(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Icon(Icons.warning_amber_rounded, color: Colors.amber.shade900, size: 20.0),
                    const SizedBox(width: 10.0),
                    Expanded(
                      child: Text(
                        'Suspected snakebite? Seek urgent medical care. Keep the person still. Do not cut or suck the wound or apply a tight tourniquet.',
                        style: TextStyle(
                          fontSize: 12.5,
                          fontWeight: FontWeight.w600,
                          color: Colors.amber.shade900,
                          height: 1.35,
                        ),
                      ),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 18.0),

              // Product Header Card
              Container(
                width: double.infinity,
                padding: const EdgeInsets.all(18.0),
                decoration: BoxDecoration(
                  color: AppTheme.sanjeeviniCard,
                  borderRadius: BorderRadius.circular(14.0),
                  border: Border.all(color: AppTheme.sanjeeviniBorder, width: 1.2),
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    // Category & Demonstration Tag
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        Container(
                          padding: const EdgeInsets.symmetric(horizontal: 9.0, vertical: 4.0),
                          decoration: BoxDecoration(
                            color: AppTheme.sanjeeviniIconBg,
                            borderRadius: BorderRadius.circular(6.0),
                          ),
                          child: Text(
                            product.category,
                            style: const TextStyle(
                              fontSize: 12.0,
                              fontWeight: FontWeight.w600,
                              color: AppTheme.sanjeeviniPrimary,
                            ),
                          ),
                        ),
                        if (product.isDemonstrationSample)
                          Container(
                            padding: const EdgeInsets.symmetric(horizontal: 8.0, vertical: 3.0),
                            decoration: BoxDecoration(
                              color: Colors.grey.shade100,
                              borderRadius: BorderRadius.circular(4.0),
                              border: Border.all(color: Colors.grey.shade300, width: 0.8),
                            ),
                            child: const Text(
                              'Sample Demonstration Listing',
                              style: TextStyle(
                                fontSize: 11.0,
                                fontWeight: FontWeight.w500,
                                color: AppTheme.sanjeeviniTextMuted,
                              ),
                            ),
                          ),
                      ],
                    ),
                    const SizedBox(height: 14.0),

                    // Product Icon / Visual Box
                    Center(
                      child: Container(
                        width: 72.0,
                        height: 72.0,
                        decoration: BoxDecoration(
                          color: AppTheme.sanjeeviniBg,
                          borderRadius: BorderRadius.circular(12.0),
                          border: Border.all(color: AppTheme.sanjeeviniBorder, width: 1.0),
                        ),
                        child: Icon(
                          _getCategoryIcon(product.category),
                          color: AppTheme.sanjeeviniPrimary,
                          size: 38.0,
                        ),
                      ),
                    ),
                    const SizedBox(height: 16.0),

                    // Product Name
                    Text(
                      product.name,
                      style: const TextStyle(
                        fontSize: 20.0,
                        fontWeight: FontWeight.w700,
                        color: AppTheme.sanjeeviniTextDark,
                        letterSpacing: -0.3,
                      ),
                    ),
                    const SizedBox(height: 8.0),

                    // Full Description
                    Text(
                      product.description,
                      style: const TextStyle(
                        fontSize: 14.5,
                        color: AppTheme.sanjeeviniTextMuted,
                        height: 1.45,
                      ),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 16.0),

              // Intended Use Section
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
                        Icon(Icons.check_circle_outline, size: 18.0, color: AppTheme.sanjeeviniPrimary),
                        SizedBox(width: 8.0),
                        Text(
                          'Intended Use & Prevention Role',
                          style: TextStyle(
                            fontSize: 15.5,
                            fontWeight: FontWeight.bold,
                            color: AppTheme.sanjeeviniTextDark,
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 8.0),
                    Text(
                      product.intendedUse,
                      style: const TextStyle(
                        fontSize: 13.5,
                        color: AppTheme.sanjeeviniTextDark,
                        height: 1.4,
                      ),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 16.0),

              // Specifications (if available)
              if (product.specifications != null && product.specifications!.isNotEmpty) ...[
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
                      const Text(
                        'Product Specifications',
                        style: TextStyle(
                          fontSize: 15.5,
                          fontWeight: FontWeight.bold,
                          color: AppTheme.sanjeeviniTextDark,
                        ),
                      ),
                      const SizedBox(height: 10.0),
                      ...product.specifications!.entries.map(
                        (entry) => Padding(
                          padding: const EdgeInsets.symmetric(vertical: 4.0),
                          child: Row(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              SizedBox(
                                width: 120.0,
                                child: Text(
                                  entry.key,
                                  style: const TextStyle(
                                    fontSize: 13.0,
                                    fontWeight: FontWeight.w600,
                                    color: AppTheme.sanjeeviniTextMuted,
                                  ),
                                ),
                              ),
                              Expanded(
                                child: Text(
                                  entry.value,
                                  style: const TextStyle(
                                    fontSize: 13.0,
                                    color: AppTheme.sanjeeviniTextDark,
                                  ),
                                ),
                              ),
                            ],
                          ),
                        ),
                      ),
                    ],
                  ),
                ),
                const SizedBox(height: 16.0),
              ],

              // Safety Notes & Limitations Card (Mandatory medical framing)
              Container(
                width: double.infinity,
                padding: const EdgeInsets.all(16.0),
                decoration: BoxDecoration(
                  color: Colors.blueGrey.shade50,
                  borderRadius: BorderRadius.circular(12.0),
                  border: Border.all(color: Colors.blueGrey.shade200, width: 1.2),
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: [
                        Icon(Icons.shield_outlined, size: 18.0, color: Colors.blueGrey.shade800),
                        const SizedBox(width: 8.0),
                        Text(
                          'Safety Notes & Limitations',
                          style: TextStyle(
                            fontSize: 15.0,
                            fontWeight: FontWeight.bold,
                            color: Colors.blueGrey.shade900,
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 8.0),
                    Text(
                      product.safetyNotes,
                      style: TextStyle(
                        fontSize: 13.0,
                        color: Colors.blueGrey.shade900,
                        height: 1.45,
                      ),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 16.0),

              // Pricing, Seller & Purchase Options Card
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
                    const Text(
                      'Marketplace & Price Information',
                      style: TextStyle(
                        fontSize: 15.5,
                        fontWeight: FontWeight.bold,
                        color: AppTheme.sanjeeviniTextDark,
                      ),
                    ),
                    const SizedBox(height: 10.0),

                    // Price row
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        const Text(
                          'Estimated Price:',
                          style: TextStyle(fontSize: 13.5, color: AppTheme.sanjeeviniTextMuted),
                        ),
                        const SizedBox(width: 12.0),
                        Expanded(
                          child: Text(
                            product.displayPrice,
                            textAlign: TextAlign.end,
                            style: TextStyle(
                              fontSize: 16.0,
                              fontWeight: FontWeight.bold,
                              color: product.isPriceVerified
                                  ? AppTheme.sanjeeviniPrimary
                                  : AppTheme.sanjeeviniTextMuted,
                            ),
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 8.0),

                    // Primary Provider
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        const Text(
                          'Primary Provider:',
                          style: TextStyle(fontSize: 13.5, color: AppTheme.sanjeeviniTextMuted),
                        ),
                        const SizedBox(width: 12.0),
                        Expanded(
                          child: Text(
                            product.sellerName ?? 'Seller not verified',
                            textAlign: TextAlign.end,
                            style: const TextStyle(
                              fontSize: 13.5,
                              fontWeight: FontWeight.w500,
                              color: AppTheme.sanjeeviniTextDark,
                            ),
                          ),
                        ),
                      ],
                    ),

                    if (product.priceCheckedAt != null) ...[
                      const SizedBox(height: 8.0),
                      Row(
                        mainAxisAlignment: MainAxisAlignment.spaceBetween,
                        children: [
                          const Text(
                            'Price Checked:',
                            style: TextStyle(fontSize: 13.0, color: AppTheme.sanjeeviniTextMuted),
                          ),
                          const SizedBox(width: 12.0),
                          Expanded(
                            child: Text(
                              product.priceCheckedAt!,
                              textAlign: TextAlign.end,
                              style: const TextStyle(
                                fontSize: 13.0,
                                color: AppTheme.sanjeeviniTextDark,
                              ),
                            ),
                          ),
                        ],
                      ),
                    ],

                    if (product.availabilityStatus != null) ...[
                      const SizedBox(height: 8.0),
                      Row(
                        mainAxisAlignment: MainAxisAlignment.spaceBetween,
                        children: [
                          const Text(
                            'Stock Status:',
                            style: TextStyle(fontSize: 13.0, color: AppTheme.sanjeeviniTextMuted),
                          ),
                          const SizedBox(width: 12.0),
                          Expanded(
                            child: Text(
                              product.availabilityStatus!,
                              textAlign: TextAlign.end,
                              style: const TextStyle(
                                fontSize: 13.0,
                                color: AppTheme.sanjeeviniTextMuted,
                              ),
                            ),
                          ),
                        ],
                      ),
                    ],

                    const SizedBox(height: 18.0),

                    // Dedicated Seller Buttons (Amazon, Flipkart, etc.)
                    _buildSellerButtons(context),
                  ],
                ),
              ),
              const SizedBox(height: 24.0),
            ],
          ),
        ),
      ),
    );
  }

  /// Builds the seller buttons list based on verified direct links and fallback search links
  Widget _buildSellerButtons(BuildContext context) {
    final links = product.sellerLinks;

    if (links.isEmpty) {
      return Container(
        width: double.infinity,
        padding: const EdgeInsets.symmetric(vertical: 14.0, horizontal: 16.0),
        decoration: BoxDecoration(
          color: Colors.grey.shade100,
          borderRadius: BorderRadius.circular(8.0),
          border: Border.all(color: Colors.grey.shade300),
        ),
        child: Column(
          children: const [
            Text(
              'Purchase link unavailable',
              style: TextStyle(
                fontSize: 14.5,
                fontWeight: FontWeight.w600,
                color: AppTheme.sanjeeviniTextDark,
              ),
            ),
            SizedBox(height: 4.0),
            Text(
              'No direct seller or marketplace links are verified for this item.',
              textAlign: TextAlign.center,
              style: TextStyle(
                fontSize: 12.0,
                color: AppTheme.sanjeeviniTextMuted,
              ),
            ),
          ],
        ),
      );
    }

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Text(
          'Available Purchase & Search Options:',
          style: TextStyle(
            fontSize: 13.5,
            fontWeight: FontWeight.w600,
            color: AppTheme.sanjeeviniTextDark,
          ),
        ),
        const SizedBox(height: 10.0),
        ...links.map((link) {
          return Padding(
            padding: const EdgeInsets.only(bottom: 10.0),
            child: SizedBox(
              width: double.infinity,
              child: ElevatedButton(
                style: ElevatedButton.styleFrom(
                  backgroundColor: link.isDirect
                      ? AppTheme.sanjeeviniPrimary
                      : Colors.white,
                  foregroundColor: link.isDirect
                      ? Colors.white
                      : AppTheme.sanjeeviniTextDark,
                  elevation: link.isDirect ? 1 : 0,
                  side: link.isDirect
                      ? null
                      : const BorderSide(color: AppTheme.sanjeeviniBorder, width: 1.2),
                  padding: const EdgeInsets.symmetric(vertical: 12.0, horizontal: 16.0),
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(8.0),
                  ),
                ),
                onPressed: () => _openSellerLink(context, link),
                child: Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Row(
                      children: [
                        Icon(
                          link.isDirect ? Icons.shopping_bag_outlined : Icons.search,
                          size: 18.0,
                          color: link.isDirect ? Colors.white : AppTheme.sanjeeviniPrimary,
                        ),
                        const SizedBox(width: 8.0),
                        Text(
                          link.buttonLabel,
                          style: TextStyle(
                            fontSize: 14.5,
                            fontWeight: FontWeight.w600,
                            color: link.isDirect ? Colors.white : AppTheme.sanjeeviniTextDark,
                          ),
                        ),
                      ],
                    ),
                    Icon(
                      Icons.open_in_new,
                      size: 16.0,
                      color: link.isDirect ? Colors.white70 : AppTheme.sanjeeviniTextMuted,
                    ),
                  ],
                ),
              ),
            ),
          );
        }),
      ],
    );
  }
}
