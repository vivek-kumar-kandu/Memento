import 'package:flutter/material.dart';
import '../core/theme/app_theme.dart';
import '../data/safety_product_repository.dart';
import '../models/safety_product.dart';
import '../widgets/safety_product_card.dart';
import 'safety_product_details_screen.dart';

/// Screen listing rural snakebite prevention and outdoor safety products.
/// Includes category filter chips, search query input, and medical disclaimer.
class SafetyProductsScreen extends StatefulWidget {
  const SafetyProductsScreen({super.key});

  @override
  State<SafetyProductsScreen> createState() => _SafetyProductsScreenState();
}

class _SafetyProductsScreenState extends State<SafetyProductsScreen> {
  final SafetyProductRepository _repository = SafetyProductRepository();
  final TextEditingController _searchController = TextEditingController();

  String _selectedCategory = 'All';
  List<SafetyProduct> _products = [];
  bool _isLoading = true;

  @override
  void initState() {
    super.initState();
    _loadProducts();
  }

  @override
  void dispose() {
    _searchController.dispose();
    super.dispose();
  }

  Future<void> _loadProducts() async {
    setState(() {
      _isLoading = true;
    });

    final results = await _repository.getProducts(
      category: _selectedCategory,
      searchQuery: _searchController.text,
    );

    if (mounted) {
      setState(() {
        _products = results;
        _isLoading = false;
      });
    }
  }

  void _onCategorySelected(String category) {
    setState(() {
      _selectedCategory = category;
    });
    _loadProducts();
  }

  void _onSearchChanged(String query) {
    _loadProducts();
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
          'Prevention & Safety Products',
          style: TextStyle(
            fontSize: 18.0,
            fontWeight: FontWeight.bold,
            color: AppTheme.sanjeeviniTextDark,
          ),
        ),
      ),
      body: SafeArea(
        child: Column(
          children: [
            // Header Intro & Search Section
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 20.0, vertical: 8.0),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text(
                    'Explore products that support safer homes and outdoor work.',
                    style: TextStyle(
                      fontSize: 13.5,
                      color: AppTheme.sanjeeviniTextMuted,
                      height: 1.35,
                    ),
                  ),
                  const SizedBox(height: 12.0),

                  // Search Field
                  TextField(
                    controller: _searchController,
                    onChanged: _onSearchChanged,
                    decoration: InputDecoration(
                      hintText: 'Search safety products...',
                      hintStyle: const TextStyle(fontSize: 13.5, color: Colors.grey),
                      prefixIcon: const Icon(Icons.search, color: AppTheme.sanjeeviniTextMuted, size: 20.0),
                      suffixIcon: _searchController.text.isNotEmpty
                          ? IconButton(
                              icon: const Icon(Icons.clear, size: 18.0),
                              onPressed: () {
                                _searchController.clear();
                                _loadProducts();
                              },
                            )
                          : null,
                      filled: true,
                      fillColor: Colors.white,
                      contentPadding: const EdgeInsets.symmetric(horizontal: 14.0, vertical: 10.0),
                      border: OutlineInputBorder(
                        borderRadius: BorderRadius.circular(8.0),
                        borderSide: const BorderSide(color: AppTheme.sanjeeviniBorder),
                      ),
                      enabledBorder: OutlineInputBorder(
                        borderRadius: BorderRadius.circular(8.0),
                        borderSide: const BorderSide(color: AppTheme.sanjeeviniBorder),
                      ),
                      focusedBorder: OutlineInputBorder(
                        borderRadius: BorderRadius.circular(8.0),
                        borderSide: const BorderSide(color: AppTheme.sanjeeviniPrimary, width: 1.5),
                      ),
                    ),
                  ),
                  const SizedBox(height: 10.0),

                  // Category Filter Chips
                  SingleChildScrollView(
                    scrollDirection: Axis.horizontal,
                    child: Row(
                      children: SafetyProductRepository.categories.map((category) {
                        final isSelected = _selectedCategory == category;
                        return Padding(
                          padding: const EdgeInsets.only(right: 8.0),
                          child: ChoiceChip(
                            label: Text(category),
                            selected: isSelected,
                            onSelected: (_) => _onCategorySelected(category),
                            selectedColor: AppTheme.sanjeeviniPrimary,
                            backgroundColor: Colors.white,
                            side: BorderSide(
                              color: isSelected
                                  ? AppTheme.sanjeeviniPrimary
                                  : AppTheme.sanjeeviniBorder,
                            ),
                            labelStyle: TextStyle(
                              fontSize: 12.5,
                              fontWeight: isSelected ? FontWeight.w600 : FontWeight.normal,
                              color: isSelected ? Colors.white : AppTheme.sanjeeviniTextDark,
                            ),
                          ),
                        );
                      }).toList(),
                    ),
                  ),
                ],
              ),
            ),

            // Mandatory Medical Notice Banner
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 20.0, vertical: 4.0),
              child: Container(
                width: double.infinity,
                padding: const EdgeInsets.all(12.0),
                decoration: BoxDecoration(
                  color: Colors.amber.shade50,
                  borderRadius: BorderRadius.circular(8.0),
                  border: Border.all(color: Colors.amber.shade300, width: 1.0),
                ),
                child: Row(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Icon(Icons.info_outline, size: 16.0, color: Colors.amber.shade900),
                    const SizedBox(width: 8.0),
                    Expanded(
                      child: Text(
                        'Suspected snakebite? Seek urgent medical care. Keep the person still. Do not cut or suck the wound or apply a tight tourniquet.',
                        style: TextStyle(
                          fontSize: 11.5,
                          fontWeight: FontWeight.w600,
                          color: Colors.amber.shade900,
                          height: 1.35,
                        ),
                      ),
                    ),
                  ],
                ),
              ),
            ),
            const SizedBox(height: 8.0),

            // Product List / State views
            Expanded(
              child: _isLoading
                  ? const Center(
                      child: CircularProgressIndicator(
                        color: AppTheme.sanjeeviniPrimary,
                      ),
                    )
                  : _products.isEmpty
                      ? Center(
                          child: Padding(
                            padding: const EdgeInsets.all(24.0),
                            child: Column(
                              mainAxisAlignment: MainAxisAlignment.center,
                              children: const [
                                Icon(Icons.inventory_2_outlined, size: 48.0, color: Colors.grey),
                                SizedBox(height: 12.0),
                                Text(
                                  'No verified products found',
                                  style: TextStyle(
                                    fontSize: 16.0,
                                    fontWeight: FontWeight.bold,
                                    color: AppTheme.sanjeeviniTextDark,
                                  ),
                                ),
                                SizedBox(height: 6.0),
                                Text(
                                  'Products will be added after safety and supply verification.',
                                  textAlign: TextAlign.center,
                                  style: TextStyle(
                                    fontSize: 13.0,
                                    color: AppTheme.sanjeeviniTextMuted,
                                  ),
                                ),
                              ],
                            ),
                          ),
                        )
                      : ListView.builder(
                          padding: const EdgeInsets.symmetric(horizontal: 20.0, vertical: 8.0),
                          itemCount: _products.length,
                          itemBuilder: (context, index) {
                            final product = _products[index];
                            return SafetyProductCard(
                              product: product,
                              onTap: () {
                                Navigator.push(
                                  context,
                                  MaterialPageRoute(
                                    builder: (context) => SafetyProductDetailsScreen(
                                      product: product,
                                    ),
                                  ),
                                );
                              },
                            );
                          },
                        ),
            ),
          ],
        ),
      ),
    );
  }
}
