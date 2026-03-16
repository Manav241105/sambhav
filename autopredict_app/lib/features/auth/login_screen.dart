import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import '../../core/theme/app_theme.dart';
import '../../core/theme/colors.dart';
import '../../core/theme/typography.dart';

class LoginScreen extends StatefulWidget {
  const LoginScreen({super.key});
  @override
  State<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen> {
  final _phone = TextEditingController();
  final _otp   = TextEditingController();
  bool _otpSent = false;
  bool _loading = false;

  Future<void> _sendOtp() async {
    setState(() => _loading = true);
    await Future.delayed(const Duration(seconds: 1));
    setState(() { _otpSent = true; _loading = false; });
  }

  Future<void> _verify() async {
    setState(() => _loading = true);
    await Future.delayed(const Duration(seconds: 1));
    if (mounted) context.go('/home');
  }

  @override
  Widget build(BuildContext context) {
    final colors = context.appColors;

    return Scaffold(
      backgroundColor: colors.scaffoldBg,
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.all(28),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const SizedBox(height: 40),
              Text('Welcome Back', style: kTitle(color: colors.textPrimary)),
              const SizedBox(height: 8),
              Text('Sign in to continue', style: kBody(color: colors.textSecondary)),
              const SizedBox(height: 48),

              // Phone field
              _Field(controller: _phone, hint: 'Phone number', type: TextInputType.phone),
              const SizedBox(height: 16),

              // OTP field
              if (_otpSent) ...[
                _Field(controller: _otp, hint: 'Enter OTP', type: TextInputType.number),
                const SizedBox(height: 16),
              ],

              // CTA
              GestureDetector(
                onTap: _loading ? null : (_otpSent ? _verify : _sendOtp),
                child: Container(
                  height: 52, width: double.infinity,
                  decoration: BoxDecoration(color: kAccent, borderRadius: BorderRadius.circular(rMD)),
                  child: Center(child: _loading
                    ? const SizedBox(width: 20, height: 20,
                        child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white))
                    : Text(_otpSent ? 'Verify OTP' : 'Send OTP', style: kSubtitle(color: kDark)),
                  ),
                ),
              ),

              const Spacer(),
              Center(child: Text('v1.0.0 · AutoPredict', style: kCaption(color: colors.textSecondary))),
            ],
          ),
        ),
      ),
    );
  }
}

class _Field extends StatelessWidget {
  final TextEditingController controller;
  final String hint;
  final TextInputType type;
  const _Field({required this.controller, required this.hint, required this.type});

  @override
  Widget build(BuildContext context) {
    final colors = context.appColors;

    return TextField(
      controller: controller,
      keyboardType: type,
      style: TextStyle(color: colors.textPrimary),
      decoration: InputDecoration(
        hintText: hint,
        hintStyle: kBody(color: colors.textHint),
        filled: true, fillColor: colors.surface,
        border: OutlineInputBorder(borderRadius: BorderRadius.circular(rMD), borderSide: BorderSide.none),
        contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 16),
      ),
    );
  }
}
