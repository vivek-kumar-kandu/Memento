import 'package:flutter/material.dart';
import 'package:url_launcher/url_launcher.dart';
import '../models/facility_model.dart';
import '../core/theme/app_theme.dart';
import '../screens/facility_detail_screen.dart';
import 'asv_badge.dart';

class FacilityCard extends StatelessWidget {
  final FacilityModel facility;

  const FacilityCard({super.key, required this.facility});

  Future<void> _openMapNavigation(double lat, double lon) async {
    final Uri mapUri = Uri.parse('https://www.google.com/maps/search/?api=1&query=$lat,$lon');
    if (await canLaunchUrl(mapUri)) {
      await launchUrl(mapUri, mode: LaunchMode.externalApplication);
    }
  }

  @override
  Widget build(BuildContext context) {
    final isChc = facility.facilityType.toUpperCase() == 'CHC';

    return Card(
      margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 6),
      child: InkWell(
        borderRadius: BorderRadius.circular(12),
        onTap: () {
          Navigator.push(
            context,
            MaterialPageRoute(
              builder: (context) => FacilityDetailScreen(facility: facility),
            ),
          );
        },
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  // Facility Type Tag (PHC / CHC)
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                    decoration: BoxDecoration(
                      color: isChc ? Colors.indigo.shade50 : Colors.teal.shade50,
                      borderRadius: BorderRadius.circular(6),
                      border: Border.all(
                        color: isChc ? Colors.indigo.shade200 : Colors.teal.shade200,
                      ),
                    ),
                    child: Text(
                      facility.facilityType,
                      style: TextStyle(
                        fontSize: 12,
                        fontWeight: FontWeight.bold,
                        color: isChc ? Colors.indigo.shade800 : Colors.teal.shade800,
                      ),
                    ),
                  ),
                  const SizedBox(width: 8),
                  Expanded(
                    child: Text(
                      facility.facilityName,
                      style: const TextStyle(
                        fontSize: 16,
                        fontWeight: FontWeight.bold,
                        color: AppTheme.textPrimary,
                      ),
                      maxLines: 2,
                      overflow: TextOverflow.ellipsis,
                    ),
                  ),
                  const SizedBox(width: 8),
                  // Distance badge
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                    decoration: BoxDecoration(
                      color: Colors.red.shade50,
                      borderRadius: BorderRadius.circular(6),
                    ),
                    child: Text(
                      '${facility.distanceKm.toStringAsFixed(1)} km',
                      style: const TextStyle(
                        fontWeight: FontWeight.bold,
                        fontSize: 13,
                        color: AppTheme.primaryEmergency,
                      ),
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 8),
              // Location text
              Row(
                children: [
                  const Icon(Icons.location_on_outlined, size: 16, color: AppTheme.textSecondary),
                  const SizedBox(width: 4),
                  Expanded(
                    child: Text(
                      '${facility.districtName}, ${facility.stateName}',
                      style: const TextStyle(
                        fontSize: 13,
                        color: AppTheme.textSecondary,
                      ),
                      overflow: TextOverflow.ellipsis,
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 12),
              const Divider(height: 1),
              const SizedBox(height: 10),
              // Bottom row: ASV status badge + Direction Action
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  AsvBadge(
                    status: facility.asvStockStatus,
                    quantity: facility.asvQuantityVials,
                  ),
                  TextButton.icon(
                    style: TextButton.styleFrom(
                      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                      visualDensity: VisualDensity.compact,
                    ),
                    icon: const Icon(Icons.navigation_outlined, size: 16),
                    label: const Text('Directions'),
                    onPressed: () => _openMapNavigation(facility.latitude, facility.longitude),
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
