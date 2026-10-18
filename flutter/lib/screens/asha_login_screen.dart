import 'package:flutter/material.dart';
import '../core/theme/app_theme.dart';
import '../widgets/sanjeevini_logo.dart';
import 'asha_dashboard_screen.dart';

/// ASHA Worker authentication screen.
/// Requires valid format of worker ID / phone and PIN before granting dashboard access.
class AshaLoginScreen extends StatefulWidget {
  const AshaLoginScreen({super.key});

  @override
  State<AshaLoginScreen> createState() => _AshaLoginScreenState();
}

class _AshaLoginScreenState extends State<AshaLoginScreen> {
  final _formKey = GlobalKey<FormState>();
  final _idController = TextEditingController();
  final _pinController = TextEditingController();

  bool _obscurePin = true;
  bool _isLoading = false;
  String? _authError;

  @override
  void dispose() {
    _idController.dispose();
    _pinController.dispose();
    super.dispose();
  }

  Future<void> _handleLogin() async {
    setState(() {
      _authError = null;
    });

    if (!_formKey.currentState!.validate()) {
      return;
    }

    setState(() {
      _isLoading = true;
    });

    // Simulate authenticating against government health worker registry
    await Future.delayed(const Duration(milliseconds: 600));

    if (!mounted) return;

    final id = _idController.text.trim();
    final pin = _pinController.text.trim();

    // Check placeholder authentication condition (e.g. valid non-test format)
    // Avoid fake hardcoded credentials
    if (id.length < 5 || pin.length < 4) {
      setState(() {
        _isLoading = false;
        _authError = 'Invalid credentials format. Please check your ASHA ID and PIN.';
      });
      return;
    }

    setState(() {
      _isLoading = false;
    });

    // Navigate to dashboard only when authentication permits it
    Navigator.pushReplacement(
      context,
      MaterialPageRoute(
        builder: (context) => AshaDashboardScreen(workerId: id),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppTheme.sanjeeviniBg,
      appBar: AppBar(
        backgroundColor: Colors.transparent,
        elevation: 0,
        foregroundColor: AppTheme.sanjeeviniTextDark,
        title: const Text(
          'ASHA Worker Login',
          style: TextStyle(
            fontSize: 18,
            fontWeight: FontWeight.bold,
            color: AppTheme.sanjeeviniTextDark,
          ),
        ),
      ),
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.symmetric(horizontal: 24.0, vertical: 16.0),
          child: Form(
            key: _formKey,
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                // Logo and Intro
                const SanjeeviniLogo(size: 48),
                const SizedBox(height: 16),
                const Text(
                  'Field Coordination Login',
                  style: TextStyle(
                    fontSize: 24,
                    fontWeight: FontWeight.bold,
                    color: AppTheme.sanjeeviniTextDark,
                    letterSpacing: -0.3,
                  ),
                ),
                const SizedBox(height: 6),
                const Text(
                  'Access assigned bite cases and update facility anti-snake venom readiness in your sector.',
                  style: TextStyle(
                    fontSize: 14,
                    color: AppTheme.sanjeeviniTextMuted,
                    height: 1.4,
                  ),
                ),
                const SizedBox(height: 28),

                if (_authError != null) ...[
                  Container(
                    width: double.infinity,
                    padding: const EdgeInsets.all(12),
                    decoration: BoxDecoration(
                      color: Colors.red.shade50,
                      borderRadius: BorderRadius.circular(8),
                      border: Border.all(color: Colors.red.shade200),
                    ),
                    child: Row(
                      children: [
                        Icon(Icons.error_outline, color: Colors.red.shade800, size: 20),
                        const SizedBox(width: 8),
                        Expanded(
                          child: Text(
                            _authError!,
                            style: TextStyle(fontSize: 13, color: Colors.red.shade900),
                          ),
                        ),
                      ],
                    ),
                  ),
                  const SizedBox(height: 16),
                ],

                // Worker ID or Phone Field
                const Text(
                  'ASHA Worker ID or Registered Phone',
                  style: TextStyle(
                    fontSize: 13.5,
                    fontWeight: FontWeight.w600,
                    color: AppTheme.sanjeeviniTextDark,
                  ),
                ),
                const SizedBox(height: 8),
                TextFormField(
                  controller: _idController,
                  keyboardType: TextInputType.text,
                  decoration: InputDecoration(
                    hintText: 'e.g. ASHA-90214 or 10-digit mobile',
                    hintStyle: const TextStyle(fontSize: 14, color: Colors.grey),
                    prefixIcon: const Icon(Icons.person_outline, color: AppTheme.sanjeeviniTextMuted),
                    filled: true,
                    fillColor: Colors.white,
                    contentPadding: const EdgeInsets.symmetric(horizontal: 14, vertical: 14),
                    border: OutlineInputBorder(
                      borderRadius: BorderRadius.circular(8),
                      borderSide: const BorderSide(color: AppTheme.sanjeeviniBorder),
                    ),
                    enabledBorder: OutlineInputBorder(
                      borderRadius: BorderRadius.circular(8),
                      borderSide: const BorderSide(color: AppTheme.sanjeeviniBorder),
                    ),
                    focusedBorder: OutlineInputBorder(
                      borderRadius: BorderRadius.circular(8),
                      borderSide: const BorderSide(color: AppTheme.sanjeeviniPrimary, width: 1.5),
                    ),
                  ),
                  validator: (value) {
                    if (value == null || value.trim().isEmpty) {
                      return 'Please enter your ASHA ID or registered mobile number.';
                    }
                    if (value.trim().length < 5) {
                      return 'ID must be at least 5 characters.';
                    }
                    return null;
                  },
                ),
                const SizedBox(height: 20),

                // PIN or Password Field
                const Text(
                  'Security PIN',
                  style: TextStyle(
                    fontSize: 13.5,
                    fontWeight: FontWeight.w600,
                    color: AppTheme.sanjeeviniTextDark,
                  ),
                ),
                const SizedBox(height: 8),
                TextFormField(
                  controller: _pinController,
                  obscureText: _obscurePin,
                  keyboardType: TextInputType.number,
                  decoration: InputDecoration(
                    hintText: 'Enter 4-6 digit PIN',
                    hintStyle: const TextStyle(fontSize: 14, color: Colors.grey),
                    prefixIcon: const Icon(Icons.lock_outline, color: AppTheme.sanjeeviniTextMuted),
                    suffixIcon: IconButton(
                      icon: Icon(
                        _obscurePin ? Icons.visibility_off : Icons.visibility,
                        color: AppTheme.sanjeeviniTextMuted,
                      ),
                      onPressed: () {
                        setState(() {
                          _obscurePin = !_obscurePin;
                        });
                      },
                    ),
                    filled: true,
                    fillColor: Colors.white,
                    contentPadding: const EdgeInsets.symmetric(horizontal: 14, vertical: 14),
                    border: OutlineInputBorder(
                      borderRadius: BorderRadius.circular(8),
                      borderSide: const BorderSide(color: AppTheme.sanjeeviniBorder),
                    ),
                    enabledBorder: OutlineInputBorder(
                      borderRadius: BorderRadius.circular(8),
                      borderSide: const BorderSide(color: AppTheme.sanjeeviniBorder),
                    ),
                    focusedBorder: OutlineInputBorder(
                      borderRadius: BorderRadius.circular(8),
                      borderSide: const BorderSide(color: AppTheme.sanjeeviniPrimary, width: 1.5),
                    ),
                  ),
                  validator: (value) {
                    if (value == null || value.trim().isEmpty) {
                      return 'Please enter your 4-6 digit security PIN.';
                    }
                    if (value.trim().length < 4) {
                      return 'PIN must be at least 4 digits.';
                    }
                    return null;
                  },
                ),
                const SizedBox(height: 28),

                // Submit Button
                SizedBox(
                  width: double.infinity,
                  child: ElevatedButton(
                    style: ElevatedButton.styleFrom(
                      backgroundColor: AppTheme.sanjeeviniPrimary,
                      foregroundColor: Colors.white,
                      padding: const EdgeInsets.symmetric(vertical: 14),
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(8),
                      ),
                      elevation: 0,
                    ),
                    onPressed: _isLoading ? null : _handleLogin,
                    child: _isLoading
                        ? const SizedBox(
                            width: 20,
                            height: 20,
                            child: CircularProgressIndicator(
                              strokeWidth: 2,
                              color: Colors.white,
                            ),
                          )
                        : const Text(
                            'Login to Dashboard',
                            style: TextStyle(
                              fontSize: 16,
                              fontWeight: FontWeight.w600,
                            ),
                          ),
                  ),
                ),
                const SizedBox(height: 20),

                // Notice Box
                Container(
                  padding: const EdgeInsets.all(12),
                  decoration: BoxDecoration(
                    color: AppTheme.sanjeeviniIconBg.withValues(alpha: 0.5),
                    borderRadius: BorderRadius.circular(8),
                  ),
                  child: const Row(
                    children: [
                      Icon(Icons.security, size: 18, color: AppTheme.sanjeeviniPrimary),
                      SizedBox(width: 8),
                      Expanded(
                        child: Text(
                          'Authorized health workers only. All access logs are monitored for public health coordination.',
                          style: TextStyle(fontSize: 12, color: AppTheme.sanjeeviniTextMuted),
                        ),
                      ),
                    ],
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
