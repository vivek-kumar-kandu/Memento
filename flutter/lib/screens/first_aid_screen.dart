import 'package:flutter/material.dart';
import 'package:url_launcher/url_launcher.dart';
import '../core/constants/api_constants.dart';
import '../core/theme/app_theme.dart';

class FirstAidScreen extends StatelessWidget {
  const FirstAidScreen({super.key});

  Future<void> _callAmbulance() async {
    final Uri phoneUri = Uri.parse('tel:${ApiConstants.ambulanceNumber}');
    if (await canLaunchUrl(phoneUri)) {
      await launchUrl(phoneUri);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Snakebite First Aid (NAPSE)'),
      ),
      bottomNavigationBar: Container(
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          color: Colors.white,
          boxShadow: [
            BoxShadow(
              color: Colors.black.withValues(alpha: 0.05),
              blurRadius: 10,
              offset: const Offset(0, -4),
            ),
          ],
        ),
        child: ElevatedButton.icon(
          onPressed: _callAmbulance,
          icon: const Icon(Icons.phone_in_talk),
          label: const Text('CALL 108 AMBULANCE NOW'),
          style: ElevatedButton.styleFrom(
            backgroundColor: AppTheme.primaryEmergency,
            padding: const EdgeInsets.symmetric(vertical: 14),
            textStyle: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
          ),
        ),
      ),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          // Banner
          Container(
            padding: const EdgeInsets.all(16),
            decoration: BoxDecoration(
              color: Colors.red.shade50,
              borderRadius: BorderRadius.circular(12),
              border: Border.all(color: Colors.red.shade200),
            ),
            child: Row(
              children: [
                const Icon(Icons.warning_amber_rounded, size: 36, color: AppTheme.primaryEmergency),
                const SizedBox(width: 12),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: const [
                      Text(
                        'Time is Life in Snakebite!',
                        style: TextStyle(
                          fontSize: 16,
                          fontWeight: FontWeight.bold,
                          color: AppTheme.primaryEmergency,
                        ),
                      ),
                      SizedBox(height: 4),
                      Text(
                        'Anti-Snake Venom (ASV) is the only definitive cure. Reach the nearest hospital immediately.',
                        style: TextStyle(fontSize: 13, color: Colors.black87),
                      ),
                    ],
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(height: 20),

          // DO'S - The R.I.G.H.T Protocol
          const Text(
            'DOs: The "R.I.G.H.T." Protocol',
            style: TextStyle(
              fontSize: 18,
              fontWeight: FontWeight.bold,
              color: AppTheme.textPrimary,
            ),
          ),
          const SizedBox(height: 10),
          _buildStepCard(
            letter: 'R',
            title: 'Reassure the Victim',
            desc: '70% of snakebites are from non-venomous snakes or are dry bites. Keep the victim calm and still.',
            color: Colors.teal,
          ),
          _buildStepCard(
            letter: 'I',
            title: 'Immobilize the Bitten Limb',
            desc: 'Immobilize the limb like a fractured bone using a splint or sling. Do not move the bitten area.',
            color: Colors.teal,
          ),
          _buildStepCard(
            letter: 'G',
            title: 'Get to Hospital Immediately',
            desc: 'Transport the patient quickly to the nearest Primary or Community Health Centre (PHC/CHC).',
            color: Colors.teal,
          ),
          _buildStepCard(
            letter: 'H',
            title: 'Hospital Details & Symptoms',
            desc: 'Tell the treating doctor about the exact time of bite and any symptoms (swelling, bleeding, drooping eyelids).',
            color: Colors.teal,
          ),
          _buildStepCard(
            letter: 'T',
            title: 'Tell About Snake (If Seen Safely)',
            desc: 'Provide description if seen safely. DO NOT attempt to catch, handle, or kill the snake.',
            color: Colors.teal,
          ),

          const SizedBox(height: 20),

          // DONT'S
          const Text(
            'STRICT DONTs (Harmful Practices)',
            style: TextStyle(
              fontSize: 18,
              fontWeight: FontWeight.bold,
              color: AppTheme.primaryDark,
            ),
          ),
          const SizedBox(height: 10),
          _buildDontItem('NO Tight Tourniquets (Rassi ya kapda mat bandhein - can cause gangrene and limb loss)'),
          _buildDontItem('NO Cutting or Slashing the bite wound'),
          _buildDontItem('NO Sucking the venom by mouth or mechanical suction devices'),
          _buildDontItem('NO Applying ice, potassium permanganate, or herbal pastes'),
          _buildDontItem('NO Wasting crucial golden-hour time visiting traditional faith healers'),
          _buildDontItem('NO Giving alcohol, tea, coffee, or aspirin to the patient'),

          const SizedBox(height: 30),
        ],
      ),
    );
  }

  Widget _buildStepCard({
    required String letter,
    required String title,
    required String desc,
    required MaterialColor color,
  }) {
    return Card(
      margin: const EdgeInsets.only(bottom: 10),
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            CircleAvatar(
              backgroundColor: color.shade700,
              radius: 18,
              child: Text(
                letter,
                style: const TextStyle(
                  color: Colors.white,
                  fontWeight: FontWeight.bold,
                  fontSize: 16,
                ),
              ),
            ),
            const SizedBox(width: 12),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    title,
                    style: const TextStyle(
                      fontWeight: FontWeight.bold,
                      fontSize: 15,
                    ),
                  ),
                  const SizedBox(height: 4),
                  Text(
                    desc,
                    style: const TextStyle(
                      fontSize: 13,
                      color: AppTheme.textSecondary,
                    ),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildDontItem(String text) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Icon(Icons.cancel, color: Colors.red, size: 20),
          const SizedBox(width: 8),
          Expanded(
            child: Text(
              text,
              style: const TextStyle(fontSize: 14, height: 1.3),
            ),
          ),
        ],
      ),
    );
  }
}
