import '../models/safety_product.dart';

/// Repository providing prevention and safety products for rural homes and outdoor work.
/// Configured with seller-specific marketplace links (Amazon India, Flipkart, verified third parties).
class SafetyProductRepository {
  static const List<String> categories = [
    'All',
    'Lighting',
    'Footwear & Workwear',
    'First Aid',
    'Preparedness',
  ];

  static const List<SafetyProduct> _demoProducts = [
    SafetyProduct(
      id: 'prod-001',
      name: 'High-Beam Rechargeable LED Torch',
      category: 'Lighting',
      description:
          'Long-range rechargeable LED torch with wide floodlight mode, designed for path inspection and night walking in rural village areas.',
      imageUrl: null,
      price: 499.0,
      currency: '₹',
      isPriceVerified: true,
      sellerName: 'Sample Indian Hardware & Electronics',
      amazonDirectUrl: 'https://www.amazon.in/dp/B07W5KJ19H',
      flipkartDirectUrl: null, // Triggers "Search on Flipkart" fallback
      otherSellerUrl: 'https://agribegri.com/products/rechargeable-led-torch',
      otherSellerName: 'AgriBegri Rural Supplies',
      enableMarketplaceSearchFallback: true,
      priceCheckedAt: '15 Oct 2026',
      availabilityStatus: 'Demonstration stock sample',
      intendedUse:
          'Illuminating unpaved paths, outdoor latrines, boundary walls, and agricultural perimeters after sundown to detect resting snakes from a safe distance.',
      specifications: {
        'Battery': '2600 mAh Rechargeable Lithium-Ion',
        'Runtime': '6 to 8 hours on high mode',
        'Beam Range': 'Up to 150 meters',
        'Water Resistance': 'IPX4 Splash-proof body',
      },
      safetyNotes:
          'A torch improves visibility along paths but cannot eliminate snakebite risks. Snakes may rest concealed beneath leaf litter, shrubs, or stone piles. Keep eyes on the path and step carefully.',
      isDemonstrationSample: true,
    ),
    SafetyProduct(
      id: 'prod-002',
      name: 'Knee-High Agricultural Protective Gumboots',
      category: 'Footwear & Workwear',
      description:
          'Durable knee-length PVC boots with reinforced toe caps and anti-skid cleated soles, suitable for wet paddy fields and muddy terrain.',
      imageUrl: null,
      price: 650.0,
      currency: '₹',
      isPriceVerified: false,
      sellerName: 'Sample Rural Agro Cooperative',
      amazonDirectUrl: null, // Fallback search on Amazon
      flipkartDirectUrl: null, // Fallback search on Flipkart
      enableMarketplaceSearchFallback: true,
      priceCheckedAt: null,
      availabilityStatus: 'Price & availability unverified',
      intendedUse:
          'Provides a physical barrier on feet, ankles, and shins where the majority of agricultural snake strikes occur during irrigation and harvesting.',
      specifications: {
        'Material': 'Virgin heavy-duty PVC rubber',
        'Height': '14-inch knee height',
        'Sole Type': 'Deep-cleat anti-skid tread',
        'Available Sizes': '6 to 10 UK / India',
      },
      safetyNotes:
          'Protective gumboots provide a barrier against accidental strikes on lower limbs, but DO NOT make a wearer invulnerable. Never step blindly into burrows, deep unharvested grain, or rat holes.',
      isDemonstrationSample: true,
    ),
    SafetyProduct(
      id: 'prod-003',
      name: 'Heavy-Duty Split-Cowhide Farm Work Gloves',
      category: 'Footwear & Workwear',
      description:
          'Puncture-resistant split leather work gloves with extended canvas safety cuffs for manual field tasks, clearing brush, and moving firewood.',
      imageUrl: null,
      price: null,
      currency: '₹',
      isPriceVerified: false,
      sellerName: null,
      amazonDirectUrl: null,
      flipkartDirectUrl: null,
      marketplaceSearchQuery: 'Split Cowhide Farm Work Gloves',
      enableMarketplaceSearchFallback: true,
      priceCheckedAt: null,
      availabilityStatus: 'Price not verified',
      intendedUse:
          'Hand protection while handling stored crop stalks, moving firewood stacks, and clearing stone piles where vipers and kraits seek shelter.',
      specifications: {
        'Material': 'Full-grain split cowhide leather',
        'Cuff Style': 'Extended rubberized safety cuff',
        'Lining': 'Absorbent cotton palm lining',
      },
      safetyNotes:
          'Always probe firewood, straw piles, and stone stacks with a stick before reaching with hands. Gloves do not prevent crushing or high-force fang penetration.',
      isDemonstrationSample: true,
    ),
    SafetyProduct(
      id: 'prod-004',
      name: 'Essential Household First-Aid Kit (Trauma & Scrapes)',
      category: 'First Aid',
      description:
          'General household wound-care kit containing sterile cotton gauze, roller bandages, antiseptic lotion, and medical tape for minor domestic injuries.',
      imageUrl: null,
      price: 380.0,
      currency: '₹',
      isPriceVerified: true,
      sellerName: 'Sample Community Health Supply',
      amazonDirectUrl: 'https://www.amazon.in/dp/B07RFLQ73Q',
      flipkartDirectUrl: 'https://www.flipkart.com/first-aid-kit/p/itm12345',
      enableMarketplaceSearchFallback: true,
      priceCheckedAt: '12 Oct 2026',
      availabilityStatus: 'Demonstration stock sample',
      intendedUse:
          'Cleaning and dressing routine scrapes, minor cuts, and surface abrasions sustained during agricultural and home chores.',
      specifications: {
        'Contents': '10 Sterile Gauze Pads, 2 Elastic Crepe Bandages, Antiseptic Wash, Medical Tape, Blunt Scissors',
        'Packaging': 'Dust-resistant plastic carry box',
      },
      safetyNotes:
          'CRITICAL MEDICAL ADVISORY: This kit is strictly for everyday minor cuts and scrapes. It CANNOT treat a venomous snakebite. In a suspected snakebite emergency, DO NOT apply tight tourniquets, DO NOT cut or suction the wound. Keep the victim calm and still, and rush immediately to a hospital with Anti-Snake Venom (ASV).',
      isDemonstrationSample: true,
    ),
    SafetyProduct(
      id: 'prod-005',
      name: 'Telescopic Aluminum Snake Safety Hook (40")',
      category: 'Preparedness',
      description:
          'Lightweight aluminum handling hook for safely clearing obstacles or keeping a respectful distance when a reptile is sighted inside living areas.',
      imageUrl: null,
      price: null,
      currency: '₹',
      isPriceVerified: false,
      sellerName: 'Sample Wildlife Field Equipment',
      amazonDirectUrl: null,
      flipkartDirectUrl: null,
      enableMarketplaceSearchFallback: false, // Testing unverified / missing link state
      priceCheckedAt: null,
      availabilityStatus: 'Availability unverified',
      intendedUse:
          'Safe non-contact probing of dark corners and moving items from a distance while awaiting trained forest department or wildlife rescue personnel.',
      specifications: {
        'Length': '40-inch extended length',
        'Shaft': 'Tubular aircraft aluminum',
        'Grip': 'Ergonomic non-slip rubber handle',
      },
      safetyNotes:
          'Handling live venomous snakes should ONLY be undertaken by trained professionals or designated forest officials. If a snake is sighted indoors, keep family and pets away and call local rescue services immediately.',
      isDemonstrationSample: true,
    ),
  ];

  /// Retrieve safety products with optional category and search query filters.
  Future<List<SafetyProduct>> getProducts({
    String? category,
    String? searchQuery,
  }) async {
    await Future.delayed(const Duration(milliseconds: 150));

    var results = List<SafetyProduct>.from(_demoProducts);

    if (category != null && category != 'All' && category.isNotEmpty) {
      results = results.where((p) => p.category.toLowerCase() == category.toLowerCase()).toList();
    }

    if (searchQuery != null && searchQuery.trim().isNotEmpty) {
      final query = searchQuery.trim().toLowerCase();
      results = results.where((p) {
        final nameMatch = p.name.toLowerCase().contains(query);
        final descMatch = p.description.toLowerCase().contains(query);
        final catMatch = p.category.toLowerCase().contains(query);
        return nameMatch || descMatch || catMatch;
      }).toList();
    }

    return results;
  }

  /// Get a single product by ID
  Future<SafetyProduct?> getProductById(String id) async {
    try {
      return _demoProducts.firstWhere((p) => p.id == id);
    } catch (_) {
      return null;
    }
  }
}
