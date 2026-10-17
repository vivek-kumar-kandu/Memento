import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:url_launcher/url_launcher.dart';
import '../core/constants/api_constants.dart';
import '../core/theme/app_theme.dart';
import '../providers/facility_provider.dart';
import '../widgets/facility_card.dart';
import 'first_aid_screen.dart';

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      context.read<FacilityProvider>().initLocationAndSearch();
    });
  }

  Future<void> _callAmbulance() async {
    final Uri phoneUri = Uri.parse('tel:${ApiConstants.ambulanceNumber}');
    if (await canLaunchUrl(phoneUri)) {
      await launchUrl(phoneUri);
    }
  }

  @override
  Widget build(BuildContext context) {
    final provider = context.watch<FacilityProvider>();

    return Scaffold(
      appBar: AppBar(
        title: const Row(
          children: [
            Icon(Icons.health_and_safety, color: Colors.white),
            SizedBox(width: 8),
            Text(
              'Dhwani-Sanjeevani',
              style: TextStyle(fontWeight: FontWeight.bold, fontSize: 18),
            ),
          ],
        ),
        actions: [
          IconButton(
            icon: const Icon(Icons.menu_book),
            tooltip: 'First Aid Guide',
            onPressed: () {
              Navigator.push(
                context,
                MaterialPageRoute(builder: (context) => const FirstAidScreen()),
              );
            },
          ),
          IconButton(
            icon: const Icon(Icons.refresh),
            tooltip: 'Refresh Location & Results',
            onPressed: () => provider.initLocationAndSearch(),
          ),
        ],
      ),
      body: RefreshIndicator(
        onRefresh: () => provider.initLocationAndSearch(),
        child: CustomScrollView(
          slivers: [
            // Top Emergency SOS Bar
            SliverToBoxAdapter(
              child: Container(
                color: AppTheme.primaryEmergency,
                padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                child: Row(
                  children: [
                    Expanded(
                      child: ElevatedButton.icon(
                        onPressed: _callAmbulance,
                        icon: const Icon(Icons.phone_in_talk, color: AppTheme.primaryEmergency),
                        label: const Text(
                          'EMERGENCY: CALL 108',
                          style: TextStyle(
                            color: AppTheme.primaryEmergency,
                            fontWeight: FontWeight.bold,
                            fontSize: 15,
                          ),
                        ),
                        style: ElevatedButton.styleFrom(
                          backgroundColor: Colors.white,
                          padding: const EdgeInsets.symmetric(vertical: 12),
                          elevation: 2,
                        ),
                      ),
                    ),
                    const SizedBox(width: 10),
                    ElevatedButton.icon(
                      onPressed: () {
                        Navigator.push(
                          context,
                          MaterialPageRoute(builder: (context) => const FirstAidScreen()),
                        );
                      },
                      icon: const Icon(Icons.medical_services_outlined, size: 18),
                      label: const Text('First Aid'),
                      style: ElevatedButton.styleFrom(
                        backgroundColor: Colors.red.shade900,
                        foregroundColor: Colors.white,
                        padding: const EdgeInsets.symmetric(vertical: 12, horizontal: 12),
                      ),
                    ),
                  ],
                ),
              ),
            ),

            // Location & Search Config Card
            SliverToBoxAdapter(
              child: Padding(
                padding: const EdgeInsets.fromLTRB(16, 16, 16, 8),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    // Location status
                    Row(
                      children: [
                        Icon(
                          provider.hasRealLocation ? Icons.my_location : Icons.location_searching,
                          size: 18,
                          color: AppTheme.accentTeal,
                        ),
                        const SizedBox(width: 6),
                        Expanded(
                          child: Text(
                            provider.hasRealLocation
                                ? 'GPS Active: (${provider.currentLatitude.toStringAsFixed(4)}, ${provider.currentLongitude.toStringAsFixed(4)})'
                                : 'Using Reference Coordinates (${provider.currentLatitude.toStringAsFixed(2)}, ${provider.currentLongitude.toStringAsFixed(2)})',
                            style: const TextStyle(
                              fontSize: 13,
                              fontWeight: FontWeight.w600,
                              color: AppTheme.textSecondary,
                            ),
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 12),

                    // Radius and Type Filter Chips
                    Row(
                      children: [
                        const Text(
                          'Radius:',
                          style: TextStyle(fontWeight: FontWeight.bold, fontSize: 13),
                        ),
                        const SizedBox(width: 8),
                        Wrap(
                          spacing: 6,
                          children: [15.0, 30.0, 50.0, 100.0].map((r) {
                            final selected = provider.searchRadiusKm == r;
                            return ChoiceChip(
                              label: Text('${r.toInt()}km'),
                              selected: selected,
                              onSelected: (_) => provider.updateSearchRadius(r),
                              selectedColor: AppTheme.primaryEmergency.withValues(alpha: 0.15),
                              labelStyle: TextStyle(
                                fontSize: 12,
                                color: selected ? AppTheme.primaryEmergency : AppTheme.textPrimary,
                                fontWeight: selected ? FontWeight.bold : FontWeight.normal,
                              ),
                            );
                          }).toList(),
                        ),
                      ],
                    ),
                    const SizedBox(height: 6),
                    Row(
                      children: [
                        const Text(
                          'Type:',
                          style: TextStyle(fontWeight: FontWeight.bold, fontSize: 13),
                        ),
                        const SizedBox(width: 14),
                        Wrap(
                          spacing: 6,
                          children: <Map<String, String?>>[
                              {'label': 'All', 'val': null},
                              {'label': 'PHC', 'val': 'PHC'},
                              {'label': 'CHC', 'val': 'CHC'},
                            ].map((item) {
                              final val = item['val'];
                              final selected = provider.selectedFacilityType == val;
                              return ChoiceChip(
                                label: Text(item['label']!),
                              selected: selected,
                              onSelected: (_) => provider.updateFacilityType(val),
                              selectedColor: AppTheme.accentTeal.withValues(alpha: 0.15),
                              labelStyle: TextStyle(
                                fontSize: 12,
                                color: selected ? AppTheme.accentTeal : AppTheme.textPrimary,
                                fontWeight: selected ? FontWeight.bold : FontWeight.normal,
                              ),
                            );
                          }).toList(),
                        ),
                      ],
                    ),
                  ],
                ),
              ),
            ),

            // Section Header: Nearest Facilities
            SliverToBoxAdapter(
              child: Padding(
                padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                child: Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    const Text(
                      'Nearest Health Facilities',
                      style: TextStyle(
                        fontSize: 16,
                        fontWeight: FontWeight.bold,
                        color: AppTheme.textPrimary,
                      ),
                    ),
                    if (!provider.isLoading && provider.facilities.isNotEmpty)
                      Text(
                        '${provider.facilities.length} found',
                        style: const TextStyle(fontSize: 12, color: AppTheme.textSecondary),
                      ),
                  ],
                ),
              ),
            ),

            // Content State: Loading, Error, or Facility List
            if (provider.isLoading)
              const SliverFillRemaining(
                child: Center(
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      CircularProgressIndicator(color: AppTheme.primaryEmergency),
                      SizedBox(height: 16),
                      Text('Searching nearest PHCs & CHCs...'),
                    ],
                  ),
                ),
              )
            else if (provider.errorMessage != null)
              SliverFillRemaining(
                child: Center(
                  child: Padding(
                    padding: const EdgeInsets.all(24),
                    child: Column(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        const Icon(Icons.cloud_off, size: 48, color: Colors.grey),
                        const SizedBox(height: 12),
                        const Text(
                          'Backend Connection Needed',
                          style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16),
                        ),
                        const SizedBox(height: 6),
                        Text(
                          'Make sure FastAPI backend is running at http://localhost:8000\nError: ${provider.errorMessage}',
                          textAlign: TextAlign.center,
                          style: const TextStyle(fontSize: 12, color: AppTheme.textSecondary),
                        ),
                        const SizedBox(height: 16),
                        ElevatedButton.icon(
                          onPressed: () => provider.searchFacilities(),
                          icon: const Icon(Icons.refresh),
                          label: const Text('Retry Search'),
                        ),
                      ],
                    ),
                  ),
                ),
              )
            else if (provider.facilities.isEmpty)
              SliverFillRemaining(
                child: Center(
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      const Icon(Icons.local_hospital_outlined, size: 48, color: Colors.grey),
                      const SizedBox(height: 12),
                      const Text(
                        'No facilities found in this radius',
                        style: TextStyle(fontWeight: FontWeight.bold),
                      ),
                      const SizedBox(height: 8),
                      ElevatedButton(
                        onPressed: () => provider.updateSearchRadius(100.0),
                        child: const Text('Expand to 100 km'),
                      ),
                    ],
                  ),
                ),
              )
            else
              SliverList(
                delegate: SliverChildBuilderDelegate(
                  (context, index) {
                    final facility = provider.facilities[index];
                    return FacilityCard(facility: facility);
                  },
                  childCount: provider.facilities.length,
                ),
              ),

            // Bottom Disclaimer
            SliverToBoxAdapter(
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: Container(
                  padding: const EdgeInsets.all(12),
                  decoration: BoxDecoration(
                    color: Colors.amber.shade50,
                    borderRadius: BorderRadius.circular(8),
                    border: Border.all(color: Colors.amber.shade200),
                  ),
                  child: Row(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Icon(Icons.info_outline, size: 16, color: Colors.amber.shade900),
                      const SizedBox(width: 8),
                      Expanded(
                        child: Text(
                          provider.safetyDisclaimer,
                          style: TextStyle(
                            fontSize: 12,
                            color: Colors.amber.shade900,
                            height: 1.3,
                          ),
                        ),
                      ),
                    ],
                  ),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
