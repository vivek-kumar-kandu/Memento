import 'package:flutter/material.dart';
import '../core/theme/app_theme.dart';
import '../widgets/sanjeevini_logo.dart';

/// ASHA Worker Dashboard placeholder screen.
/// Shown only after completing field authentication.
class AshaDashboardScreen extends StatelessWidget {
  final String workerId;

  const AshaDashboardScreen({
    super.key,
    required this.workerId,
  });

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppTheme.sanjeeviniBg,
      appBar: AppBar(
        backgroundColor: AppTheme.sanjeeviniPrimary,
        foregroundColor: Colors.white,
        elevation: 0,
        title: Row(
          children: const [
            SanjeeviniLogo(size: 28),
            SizedBox(width: 10),
            Text(
              'ASHA Field Dashboard',
              style: TextStyle(fontSize: 17, fontWeight: FontWeight.bold),
            ),
          ],
        ),
        actions: [
          IconButton(
            icon: const Icon(Icons.logout),
            tooltip: 'Logout',
            onPressed: () {
              Navigator.pop(context);
            },
          ),
        ],
      ),
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(16.0),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Worker Profile Banner
              Container(
                width: double.infinity,
                padding: const EdgeInsets.all(16.0),
                decoration: BoxDecoration(
                  color: AppTheme.sanjeeviniCard,
                  borderRadius: BorderRadius.circular(12.0),
                  border: Border.all(color: AppTheme.sanjeeviniBorder, width: 1.2),
                ),
                child: Row(
                  children: [
                    CircleAvatar(
                      radius: 24,
                      backgroundColor: AppTheme.sanjeeviniIconBg,
                      child: const Icon(
                        Icons.person_pin,
                        color: AppTheme.sanjeeviniPrimary,
                        size: 28,
                      ),
                    ),
                    const SizedBox(width: 14),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            'Worker ID: $workerId',
                            style: const TextStyle(
                              fontSize: 15,
                              fontWeight: FontWeight.bold,
                              color: AppTheme.sanjeeviniTextDark,
                            ),
                          ),
                          const SizedBox(height: 2),
                          const Text(
                            'Sector: Sub-Centre Rampur • Active Duty',
                            style: TextStyle(
                              fontSize: 12.5,
                              color: AppTheme.sanjeeviniTextMuted,
                            ),
                          ),
                        ],
                      ),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 20),

              // Assigned Cases Section
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  const Text(
                    'Assigned Bite Cases',
                    style: TextStyle(
                      fontSize: 17,
                      fontWeight: FontWeight.bold,
                      color: AppTheme.sanjeeviniTextDark,
                    ),
                  ),
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                    decoration: BoxDecoration(
                      color: AppTheme.sanjeeviniIconBg,
                      borderRadius: BorderRadius.circular(12),
                    ),
                    child: const Text(
                      '2 Active',
                      style: TextStyle(
                        fontSize: 12,
                        fontWeight: FontWeight.w600,
                        color: AppTheme.sanjeeviniPrimary,
                      ),
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 10),

              // Case 1
              _buildCaseCard(
                caseId: '#SB-2026-104',
                village: 'Village Madanpur, Ward 3',
                time: 'Reported 28 min ago',
                status: 'Patient in transit to CHC',
                statusColor: Colors.amber.shade900,
                statusBg: Colors.amber.shade50,
              ),
              const SizedBox(height: 10),

              // Case 2
              _buildCaseCard(
                caseId: '#SB-2026-098',
                village: 'Village Shivpuri, Near Primary School',
                time: 'Reported 2 hr ago',
                status: 'Stabilized at SDH • Follow-up scheduled',
                statusColor: Colors.green.shade800,
                statusBg: Colors.green.shade50,
              ),
              const SizedBox(height: 24),

              // Facility Readiness Section
              const Text(
                'Facility Readiness & ASV Stocks',
                style: TextStyle(
                  fontSize: 17,
                  fontWeight: FontWeight.bold,
                  color: AppTheme.sanjeeviniTextDark,
                ),
              ),
              const SizedBox(height: 4),
              const Text(
                'Verify anti-snake venom availability before routing patients.',
                style: TextStyle(fontSize: 13, color: AppTheme.sanjeeviniTextMuted),
              ),
              const SizedBox(height: 10),

              _buildFacilityReadinessCard(
                facilityName: 'CHC Rampur Emergency',
                asvVials: '14 Vials (Polyvalent)',
                ventilatorStatus: '2 Functional Beds',
                updated: 'Updated today 08:30 AM',
              ),
              const SizedBox(height: 10),

              _buildFacilityReadinessCard(
                facilityName: 'PHC Chandpur',
                asvVials: '4 Vials (Low Reserve)',
                ventilatorStatus: 'Ambulance Oxygen Only',
                updated: 'Updated yesterday 06:15 PM',
              ),
              const SizedBox(height: 20),

              // Action Buttons
              SizedBox(
                width: double.infinity,
                child: ElevatedButton.icon(
                  style: ElevatedButton.styleFrom(
                    backgroundColor: AppTheme.sanjeeviniPrimary,
                    foregroundColor: Colors.white,
                    padding: const EdgeInsets.symmetric(vertical: 13),
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(8),
                    ),
                  ),
                  onPressed: () {
                    ScaffoldMessenger.of(context).showSnackBar(
                      const SnackBar(
                        content: Text('Field reporting form placeholder opened.'),
                        duration: Duration(seconds: 2),
                      ),
                    );
                  },
                  icon: const Icon(Icons.add_alert, size: 20),
                  label: const Text(
                    'Log New Snakebite Incident',
                    style: TextStyle(fontWeight: FontWeight.w600, fontSize: 15),
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildCaseCard({
    required String caseId,
    required String village,
    required String time,
    required String status,
    required Color statusColor,
    required Color statusBg,
  }) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(14.0),
      decoration: BoxDecoration(
        color: AppTheme.sanjeeviniCard,
        borderRadius: BorderRadius.circular(10.0),
        border: Border.all(color: AppTheme.sanjeeviniBorder, width: 1.0),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text(
                caseId,
                style: const TextStyle(
                  fontSize: 14.5,
                  fontWeight: FontWeight.bold,
                  color: AppTheme.sanjeeviniTextDark,
                ),
              ),
              Text(
                time,
                style: const TextStyle(
                  fontSize: 12,
                  color: AppTheme.sanjeeviniTextMuted,
                ),
              ),
            ],
          ),
          const SizedBox(height: 4),
          Text(
            village,
            style: const TextStyle(fontSize: 13, color: AppTheme.sanjeeviniTextDark),
          ),
          const SizedBox(height: 8),
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
            decoration: BoxDecoration(
              color: statusBg,
              borderRadius: BorderRadius.circular(4),
            ),
            child: Text(
              status,
              style: TextStyle(
                fontSize: 11.5,
                fontWeight: FontWeight.w600,
                color: statusColor,
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildFacilityReadinessCard({
    required String facilityName,
    required String asvVials,
    required String ventilatorStatus,
    required String updated,
  }) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(14.0),
      decoration: BoxDecoration(
        color: AppTheme.sanjeeviniCard,
        borderRadius: BorderRadius.circular(10.0),
        border: Border.all(color: AppTheme.sanjeeviniBorder, width: 1.0),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            facilityName,
            style: const TextStyle(
              fontSize: 15,
              fontWeight: FontWeight.bold,
              color: AppTheme.sanjeeviniTextDark,
            ),
          ),
          const SizedBox(height: 6),
          Row(
            children: [
              const Icon(Icons.medication, size: 16, color: AppTheme.sanjeeviniPrimary),
              const SizedBox(width: 6),
              Text(
                asvVials,
                style: const TextStyle(fontSize: 13, color: AppTheme.sanjeeviniTextDark),
              ),
              const SizedBox(width: 14),
              const Icon(Icons.airline_seat_flat, size: 16, color: AppTheme.sanjeeviniTextMuted),
              const SizedBox(width: 6),
              Expanded(
                child: Text(
                  ventilatorStatus,
                  style: const TextStyle(fontSize: 13, color: AppTheme.sanjeeviniTextMuted),
                  overflow: TextOverflow.ellipsis,
                ),
              ),
            ],
          ),
          const SizedBox(height: 6),
          Text(
            updated,
            style: const TextStyle(fontSize: 11.5, color: AppTheme.sanjeeviniFooter),
          ),
        ],
      ),
    );
  }
}
