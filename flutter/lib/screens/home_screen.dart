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
  final TextEditingController _manualLocationController =
      TextEditingController();

  @override
  void dispose() {
    _manualLocationController.dispose();
    super.dispose();
  }

  Future<void> _callAmbulance() async {
    final Uri phoneUri = Uri.parse('tel:${ApiConstants.ambulanceNumber}');
    if (await canLaunchUrl(phoneUri)) {
      await launchUrl(phoneUri);
    } else {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content:
                Text('Could not launch dialer. Please call 108 immediately.'),
            backgroundColor: AppTheme.primaryEmergency,
          ),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final provider = context.watch<FacilityProvider>();

    return Scaffold(
      backgroundColor: AppTheme.sanjeeviniBg,
      appBar: AppBar(
        backgroundColor: AppTheme.sanjeeviniPrimary,
        foregroundColor: Colors.white,
        title: const Row(
          children: [
            Icon(Icons.health_and_safety, color: Colors.white),
            SizedBox(width: 8),
            Expanded(
              child: Text(
                'Nearby Facility Finder',
                style: TextStyle(fontWeight: FontWeight.bold, fontSize: 17),
              ),
            ),
          ],
        ),
        actions: [
          IconButton(
            icon: const Icon(Icons.medical_information_outlined),
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
            tooltip: 'Refresh Location & Search',
            onPressed: provider.isLoading
                ? null
                : () => provider.useCurrentLocationAndSearch(),
          ),
        ],
      ),
      body: CustomScrollView(
        slivers: [
          // 1. Top Emergency SOS Bar (Always visible)
          SliverToBoxAdapter(
            child: Container(
              color: AppTheme.primaryEmergency,
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
              child: Row(
                children: [
                  Expanded(
                    child: ElevatedButton.icon(
                      onPressed: _callAmbulance,
                      icon: const Icon(Icons.phone_in_talk,
                          color: AppTheme.primaryEmergency),
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
                        MaterialPageRoute(
                            builder: (context) => const FirstAidScreen()),
                      );
                    },
                    icon: const Icon(Icons.medical_services_outlined, size: 18),
                    label: const Text('First Aid'),
                    style: ElevatedButton.styleFrom(
                      backgroundColor: Colors.red.shade900,
                      foregroundColor: Colors.white,
                      padding: const EdgeInsets.symmetric(
                          vertical: 12, horizontal: 12),
                    ),
                  ),
                ],
              ),
            ),
          ),

          // 2. Action & Filter Controls Card
          SliverToBoxAdapter(
            child: Padding(
              padding: const EdgeInsets.fromLTRB(16, 14, 16, 8),
              child: Container(
                padding: const EdgeInsets.all(14),
                decoration: BoxDecoration(
                  color: AppTheme.sanjeeviniCard,
                  borderRadius: BorderRadius.circular(10),
                  border: Border.all(color: AppTheme.sanjeeviniBorder),
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    // Primary Action: "Use My Current Location"
                    SizedBox(
                      width: double.infinity,
                      child: ElevatedButton.icon(
                        key: const Key('use_current_location_button'),
                        style: ElevatedButton.styleFrom(
                          backgroundColor: AppTheme.sanjeeviniPrimary,
                          foregroundColor: Colors.white,
                          padding: const EdgeInsets.symmetric(vertical: 13),
                          shape: RoundedRectangleBorder(
                            borderRadius: BorderRadius.circular(8),
                          ),
                        ),
                        onPressed: provider.isLoading
                            ? null
                            : () => provider.useCurrentLocationAndSearch(),
                        icon: provider.isLoading
                            ? const SizedBox(
                                width: 18,
                                height: 18,
                                child: CircularProgressIndicator(
                                  strokeWidth: 2,
                                  color: Colors.white,
                                ),
                              )
                            : const Icon(Icons.my_location, size: 20),
                        label: Text(
                          provider.status ==
                                  FacilitySearchStatus.requestingLocation
                              ? 'Requesting GPS Location...'
                              : provider.status ==
                                      FacilitySearchStatus.searchingBackend
                                  ? 'Searching Nearby Facilities...'
                                  : 'Use My Current Location',
                          style: const TextStyle(
                            fontSize: 15,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                      ),
                    ),
                    const SizedBox(height: 12),

                    // Manual Village / Landmark Input Option
                    Row(
                      children: [
                        Expanded(
                          child: TextField(
                            controller: _manualLocationController,
                            decoration: InputDecoration(
                              hintText: 'Or enter village / landmark...',
                              hintStyle: const TextStyle(fontSize: 13),
                              isDense: true,
                              contentPadding: const EdgeInsets.symmetric(
                                horizontal: 12,
                                vertical: 10,
                              ),
                              border: OutlineInputBorder(
                                borderRadius: BorderRadius.circular(8),
                                borderSide: const BorderSide(
                                    color: AppTheme.sanjeeviniBorder),
                              ),
                            ),
                            onSubmitted: (val) {
                              if (val.trim().isNotEmpty) {
                                provider.searchByManualLocation(val.trim());
                              }
                            },
                          ),
                        ),
                        const SizedBox(width: 8),
                        IconButton.filled(
                          style: IconButton.styleFrom(
                            backgroundColor: AppTheme.sanjeeviniPrimary,
                            foregroundColor: Colors.white,
                          ),
                          onPressed: () {
                            final val = _manualLocationController.text.trim();
                            if (val.isNotEmpty) {
                              provider.searchByManualLocation(val);
                            }
                          },
                          icon: const Icon(Icons.search, size: 20),
                          tooltip: 'Search village/landmark',
                        ),
                      ],
                    ),
                    const SizedBox(height: 12),

                    // Filters: Radius & Type
                    Row(
                      children: [
                        const Text(
                          'Radius:',
                          style: TextStyle(
                              fontWeight: FontWeight.bold, fontSize: 13),
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
                              selectedColor: AppTheme.sanjeeviniPrimary
                                  .withValues(alpha: 0.15),
                              labelStyle: TextStyle(
                                fontSize: 12,
                                color: selected
                                    ? AppTheme.sanjeeviniPrimary
                                    : AppTheme.sanjeeviniTextDark,
                                fontWeight: selected
                                    ? FontWeight.bold
                                    : FontWeight.normal,
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
                          style: TextStyle(
                              fontWeight: FontWeight.bold, fontSize: 13),
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
                            final selected =
                                provider.selectedFacilityType == val;
                            return ChoiceChip(
                              label: Text(item['label']!),
                              selected: selected,
                              onSelected: (_) =>
                                  provider.updateFacilityType(val),
                              selectedColor: AppTheme.sanjeeviniPrimary
                                  .withValues(alpha: 0.15),
                              labelStyle: TextStyle(
                                fontSize: 12,
                                color: selected
                                    ? AppTheme.sanjeeviniPrimary
                                    : AppTheme.sanjeeviniTextDark,
                                fontWeight: selected
                                    ? FontWeight.bold
                                    : FontWeight.normal,
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
          ),

          // 3. Status Display Banner
          if (provider.hasRealLocation)
            SliverToBoxAdapter(
              child: Padding(
                padding:
                    const EdgeInsets.symmetric(horizontal: 16, vertical: 4),
                child: Container(
                  padding:
                      const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                  decoration: BoxDecoration(
                    color: Colors.green.shade50,
                    borderRadius: BorderRadius.circular(6),
                    border: Border.all(color: Colors.green.shade200),
                  ),
                  child: Row(
                    children: [
                      Icon(Icons.check_circle,
                          color: Colors.green.shade700, size: 16),
                      const SizedBox(width: 6),
                      Expanded(
                        child: Text(
                          provider.accuracyMeters != null
                              ? 'Current location obtained (Accuracy: ±${provider.accuracyMeters!.toInt()}m)'
                              : 'Current location obtained.',
                          style: TextStyle(
                            fontSize: 12.5,
                            color: Colors.green.shade900,
                            fontWeight: FontWeight.w600,
                          ),
                        ),
                      ),
                    ],
                  ),
                ),
              ),
            ),

          // 4. Main Body: Switch according to 8 States
          ..._buildStateSlivers(context, provider),

          // 5. Safety Disclaimer at Bottom
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
                    Icon(Icons.info_outline,
                        size: 16, color: Colors.amber.shade900),
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
    );
  }

  List<Widget> _buildStateSlivers(
      BuildContext context, FacilityProvider provider) {
    switch (provider.status) {
      // State 1: Idle
      case FacilitySearchStatus.idle:
        return [
          SliverFillRemaining(
            hasScrollBody: false,
            child: Center(
              child: Padding(
                padding: const EdgeInsets.all(24.0),
                child: Column(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    Icon(Icons.location_on_outlined,
                        size: 56, color: Colors.grey.shade400),
                    const SizedBox(height: 14),
                    const Text(
                      'Find Nearby Healthcare Facilities',
                      style: TextStyle(
                        fontSize: 17,
                        fontWeight: FontWeight.bold,
                        color: AppTheme.sanjeeviniTextDark,
                      ),
                    ),
                    const SizedBox(height: 8),
                    const Text(
                      'Sharing your device location helps discover verified Primary Health Centres (PHCs) and Community Health Centres (CHCs) equipped for emergency snakebite care.',
                      textAlign: TextAlign.center,
                      style: TextStyle(
                        fontSize: 13.5,
                        color: AppTheme.sanjeeviniTextMuted,
                        height: 1.4,
                      ),
                    ),
                    const SizedBox(height: 18),
                    OutlinedButton.icon(
                      style: OutlinedButton.styleFrom(
                        foregroundColor: AppTheme.sanjeeviniPrimary,
                        side:
                            const BorderSide(color: AppTheme.sanjeeviniPrimary),
                      ),
                      onPressed: () => provider.useCurrentLocationAndSearch(),
                      icon: const Icon(Icons.my_location, size: 18),
                      label: const Text('Share Location Now'),
                    ),
                  ],
                ),
              ),
            ),
          ),
        ];

      // State 2: Requesting permission/location
      case FacilitySearchStatus.requestingLocation:
        return [
          const SliverFillRemaining(
            hasScrollBody: false,
            child: Center(
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  CircularProgressIndicator(color: AppTheme.sanjeeviniPrimary),
                  SizedBox(height: 16),
                  Text(
                    'Accessing device GPS location...',
                    style: TextStyle(
                      fontSize: 15,
                      fontWeight: FontWeight.w600,
                      color: AppTheme.sanjeeviniTextDark,
                    ),
                  ),
                  SizedBox(height: 6),
                  Text(
                    'Please grant location permission if prompted.',
                    style: TextStyle(
                      fontSize: 12.5,
                      color: AppTheme.sanjeeviniTextMuted,
                    ),
                  ),
                ],
              ),
            ),
          ),
        ];

      // State 3: Location found & State 4: Searching backend
      case FacilitySearchStatus.locationFound:
      case FacilitySearchStatus.searchingBackend:
        return [
          SliverFillRemaining(
            hasScrollBody: false,
            child: Center(
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  const CircularProgressIndicator(
                      color: AppTheme.sanjeeviniPrimary),
                  const SizedBox(height: 16),
                  Text(
                    'Searching verified facilities within ${provider.searchRadiusKm.toInt()} km...',
                    style: const TextStyle(
                      fontSize: 15,
                      fontWeight: FontWeight.w600,
                      color: AppTheme.sanjeeviniTextDark,
                    ),
                  ),
                  const SizedBox(height: 6),
                  const Text(
                    'Querying 34,000+ government health centres in directory...',
                    style: TextStyle(
                      fontSize: 12.5,
                      color: AppTheme.sanjeeviniTextMuted,
                    ),
                  ),
                ],
              ),
            ),
          ),
        ];

      // State 5: Results available
      case FacilitySearchStatus.resultsAvailable:
        return [
          SliverToBoxAdapter(
            child: Padding(
              padding: const EdgeInsets.fromLTRB(16, 12, 16, 6),
              child: Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  const Text(
                    'Nearest Health Facilities',
                    style: TextStyle(
                      fontSize: 16,
                      fontWeight: FontWeight.bold,
                      color: AppTheme.sanjeeviniTextDark,
                    ),
                  ),
                  Text(
                    '${provider.facilities.length} found',
                    style: const TextStyle(
                      fontSize: 12.5,
                      color: AppTheme.sanjeeviniTextMuted,
                      fontWeight: FontWeight.w600,
                    ),
                  ),
                ],
              ),
            ),
          ),
          SliverList(
            delegate: SliverChildBuilderDelegate(
              (context, index) {
                final facility = provider.facilities[index];
                return FacilityCard(facility: facility);
              },
              childCount: provider.facilities.length,
            ),
          ),
        ];

      // State 6: No results
      case FacilitySearchStatus.noResults:
        return [
          SliverFillRemaining(
            hasScrollBody: false,
            child: Center(
              child: Padding(
                padding: const EdgeInsets.all(24.0),
                child: Column(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    const Icon(Icons.search_off, size: 52, color: Colors.grey),
                    const SizedBox(height: 12),
                    Text(
                      'No facilities found within ${provider.searchRadiusKm.toInt()} km',
                      style: const TextStyle(
                        fontSize: 16,
                        fontWeight: FontWeight.bold,
                        color: AppTheme.sanjeeviniTextDark,
                      ),
                    ),
                    const SizedBox(height: 6),
                    const Text(
                      'No indexed health centres were found in this immediate radius. Expand the search radius or enter your village name above.',
                      textAlign: TextAlign.center,
                      style: TextStyle(
                        fontSize: 13,
                        color: AppTheme.sanjeeviniTextMuted,
                      ),
                    ),
                    const SizedBox(height: 16),
                    ElevatedButton(
                      style: ElevatedButton.styleFrom(
                        backgroundColor: AppTheme.sanjeeviniPrimary,
                        foregroundColor: Colors.white,
                      ),
                      onPressed: () => provider.updateSearchRadius(100.0),
                      child: const Text('Expand to 100 km'),
                    ),
                  ],
                ),
              ),
            ),
          ),
        ];

      // State 7: Permission denied or GPS unavailable
      case FacilitySearchStatus.locationError:
        return [
          SliverFillRemaining(
            hasScrollBody: false,
            child: Center(
              child: Padding(
                padding: const EdgeInsets.all(24.0),
                child: Column(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    Icon(Icons.location_disabled,
                        size: 52, color: Colors.orange.shade800),
                    const SizedBox(height: 14),
                    const Text(
                      'GPS Location Unavailable',
                      style: TextStyle(
                        fontSize: 17,
                        fontWeight: FontWeight.bold,
                        color: AppTheme.sanjeeviniTextDark,
                      ),
                    ),
                    const SizedBox(height: 8),
                    Text(
                      provider.locationErrorMessage ??
                          'Location permission was denied or device GPS is disabled.',
                      textAlign: TextAlign.center,
                      style: const TextStyle(
                        fontSize: 13.5,
                        color: AppTheme.sanjeeviniTextMuted,
                        height: 1.4,
                      ),
                    ),
                    const SizedBox(height: 18),
                    Row(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        OutlinedButton.icon(
                          onPressed: () =>
                              provider.useCurrentLocationAndSearch(),
                          icon: const Icon(Icons.refresh, size: 18),
                          label: const Text('Retry GPS'),
                        ),
                      ],
                    ),
                  ],
                ),
              ),
            ),
          ),
        ];

      // State 8: Backend unreachable
      case FacilitySearchStatus.backendError:
        return [
          SliverFillRemaining(
            hasScrollBody: false,
            child: Center(
              child: Padding(
                padding: const EdgeInsets.all(24.0),
                child: Column(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    const Icon(Icons.cloud_off, size: 52, color: Colors.grey),
                    const SizedBox(height: 14),
                    const Text(
                      'Backend Unreachable',
                      style: TextStyle(
                        fontSize: 17,
                        fontWeight: FontWeight.bold,
                        color: AppTheme.sanjeeviniTextDark,
                      ),
                    ),
                    const SizedBox(height: 8),
                    Text(
                      provider.backendErrorMessage ??
                          'Could not connect to backend server at ${ApiConstants.baseUrl}.',
                      textAlign: TextAlign.center,
                      style: const TextStyle(
                        fontSize: 13,
                        color: AppTheme.sanjeeviniTextMuted,
                      ),
                    ),
                    const SizedBox(height: 18),
                    ElevatedButton.icon(
                      style: ElevatedButton.styleFrom(
                        backgroundColor: AppTheme.sanjeeviniPrimary,
                        foregroundColor: Colors.white,
                      ),
                      onPressed: () => provider.retrySearch(),
                      icon: const Icon(Icons.refresh, size: 18),
                      label: const Text('Retry Connection'),
                    ),
                  ],
                ),
              ),
            ),
          ),
        ];
    }
  }
}
