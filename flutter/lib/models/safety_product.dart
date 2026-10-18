/// Represents an external marketplace or seller link for a product.
class ProductSellerLink {
  final String sellerName;
  final String url;
  final bool isDirect;

  const ProductSellerLink({
    required this.sellerName,
    required this.url,
    this.isDirect = true,
  });

  /// Clear button label according to requirements:
  /// - "Buy on Amazon" / "Buy on Flipkart" for verified direct pages
  /// - "Search on Amazon" / "Search on Flipkart" for search fallbacks
  String get buttonLabel {
    if (isDirect) {
      return 'Buy on $sellerName';
    } else {
      return 'Search on $sellerName';
    }
  }

  /// Validates whether the link is a well-formed HTTPS/HTTP URL
  bool get isValidUrl {
    final trimmed = url.trim();
    if (trimmed.isEmpty) return false;
    final uri = Uri.tryParse(trimmed);
    return uri != null && (uri.isScheme('https') || uri.isScheme('http')) && uri.host.isNotEmpty;
  }
}

/// Model representing a rural prevention & safety product.
/// Supports multiple seller URLs (Amazon, Flipkart, verified third parties)
/// and distinguishes direct product URLs from encoded marketplace searches.
class SafetyProduct {
  final String id;
  final String name;
  final String category;
  final String description;
  final String? imageUrl;
  final double? price;
  final String currency;
  final bool isPriceVerified;
  final String? sellerName;
  final String? priceCheckedAt;
  final String? availabilityStatus;
  final String intendedUse;
  final Map<String, String>? specifications;
  final String safetyNotes;
  final bool isDemonstrationSample;

  // Seller-specific link options
  final String? amazonDirectUrl;
  final String? flipkartDirectUrl;
  final String? otherSellerUrl;
  final String? otherSellerName;
  final bool enableMarketplaceSearchFallback;
  final String? marketplaceSearchQuery;

  const SafetyProduct({
    required this.id,
    required this.name,
    required this.category,
    required this.description,
    this.imageUrl,
    this.price,
    this.currency = '₹',
    this.isPriceVerified = false,
    this.sellerName,
    this.priceCheckedAt,
    this.availabilityStatus,
    required this.intendedUse,
    this.specifications,
    required this.safetyNotes,
    this.isDemonstrationSample = true,
    this.amazonDirectUrl,
    this.flipkartDirectUrl,
    this.otherSellerUrl,
    this.otherSellerName,
    this.enableMarketplaceSearchFallback = true,
    this.marketplaceSearchQuery,
  });

  /// Human-readable price or explicit unverified disclaimer
  String get displayPrice {
    if (price != null && isPriceVerified) {
      return '$currency${price!.toStringAsFixed(0)}';
    }
    return 'Price not verified';
  }

  /// Backward-compatible primary URL getter
  String? get productUrl {
    if (amazonDirectUrl != null && amazonDirectUrl!.trim().isNotEmpty) {
      return amazonDirectUrl;
    }
    if (flipkartDirectUrl != null && flipkartDirectUrl!.trim().isNotEmpty) {
      return flipkartDirectUrl;
    }
    if (otherSellerUrl != null && otherSellerUrl!.trim().isNotEmpty) {
      return otherSellerUrl;
    }
    final links = sellerLinks;
    if (links.isNotEmpty) {
      return links.first.url;
    }
    return null;
  }

  /// Whether any valid seller or marketplace link is available
  bool get hasValidUrl {
    return sellerLinks.any((link) => link.isValidUrl);
  }

  /// Computes all seller buttons for the product:
  /// - Direct Amazon URL or fallback search on Amazon
  /// - Direct Flipkart URL or fallback search on Flipkart
  /// - Other verified seller URLs
  List<ProductSellerLink> get sellerLinks {
    final links = <ProductSellerLink>[];
    final searchQuery = (marketplaceSearchQuery != null && marketplaceSearchQuery!.trim().isNotEmpty)
        ? marketplaceSearchQuery!.trim()
        : name.trim();

    // 1. Amazon India Link
    if (amazonDirectUrl != null && amazonDirectUrl!.trim().isNotEmpty) {
      links.add(ProductSellerLink(
        sellerName: 'Amazon',
        url: amazonDirectUrl!.trim(),
        isDirect: true,
      ));
    } else if (enableMarketplaceSearchFallback) {
      final encoded = Uri.encodeComponent(searchQuery);
      links.add(ProductSellerLink(
        sellerName: 'Amazon',
        url: 'https://www.amazon.in/s?k=$encoded',
        isDirect: false,
      ));
    }

    // 2. Flipkart Link
    if (flipkartDirectUrl != null && flipkartDirectUrl!.trim().isNotEmpty) {
      links.add(ProductSellerLink(
        sellerName: 'Flipkart',
        url: flipkartDirectUrl!.trim(),
        isDirect: true,
      ));
    } else if (enableMarketplaceSearchFallback) {
      final encoded = Uri.encodeComponent(searchQuery);
      links.add(ProductSellerLink(
        sellerName: 'Flipkart',
        url: 'https://www.flipkart.com/search?q=$encoded',
        isDirect: false,
      ));
    }

    // 3. Other verified seller link
    if (otherSellerUrl != null && otherSellerUrl!.trim().isNotEmpty) {
      links.add(ProductSellerLink(
        sellerName: otherSellerName ?? 'Verified Seller',
        url: otherSellerUrl!.trim(),
        isDirect: true,
      ));
    }

    return links;
  }
}
