import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import '../../core/theme/app_theme.dart';
import '../../core/theme/colors.dart';
import '../../core/theme/typography.dart';

class OnboardingScreen extends StatefulWidget {
  const OnboardingScreen({super.key});
  @override
  State<OnboardingScreen> createState() => _OnboardingScreenState();
}

class _OnboardingScreenState extends State<OnboardingScreen> {
  final PageController _ctrl = PageController();
  int _page = 0;

  final _slides = const [
    _SlideData(icon: Icons.directions_car, title: 'Know Your Car Better',
        body: 'AI-powered real-time diagnostics at your fingertips.'),
    _SlideData(icon: Icons.analytics_outlined, title: 'AI Diagnosis, No Mechanic Needed',
        body: 'Instant health scores, RUL predictions, and component breakdowns.'),
    _SlideData(icon: Icons.calendar_today_outlined, title: 'Book Service in 30 Seconds',
        body: 'Chat with AI, pick a slot, get confirmed. Simple.'),
  ];

  @override
  Widget build(BuildContext context) {
    final colors = context.appColors;

    return Scaffold(
      backgroundColor: colors.scaffoldBg,
      body: SafeArea(
        child: Column(
          children: [
            Expanded(
              child: PageView.builder(
                controller: _ctrl,
                onPageChanged: (i) => setState(() => _page = i),
                itemCount: _slides.length,
                itemBuilder: (_, i) => _SlidePage(data: _slides[i]),
              ),
            ),
            // Dots
            Row(
              mainAxisAlignment: MainAxisAlignment.center,
              children: List.generate(_slides.length, (i) => AnimatedContainer(
                duration: const Duration(milliseconds: 300),
                margin: const EdgeInsets.symmetric(horizontal: 4, vertical: 16),
                width: _page == i ? 24 : 8, height: 8,
                decoration: BoxDecoration(
                  color: _page == i ? kAccent : colors.neuBg,
                  borderRadius: BorderRadius.circular(rFull),
                ),
              )),
            ),
            // Next / Get Started
            Padding(
              padding: const EdgeInsets.fromLTRB(24, 0, 24, 32),
              child: GestureDetector(
                onTap: () {
                  if (_page < _slides.length - 1) {
                    _ctrl.nextPage(duration: const Duration(milliseconds: 300), curve: Curves.easeOut);
                  } else {
                    context.go('/login');
                  }
                },
                child: Container(
                  height: 52,
                  decoration: BoxDecoration(color: kAccent, borderRadius: BorderRadius.circular(rMD)),
                  child: Center(child: Text(
                    _page == _slides.length - 1 ? 'Get Started' : 'Next',
                    style: kSubtitle(color: kDark),
                  )),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _SlideData {
  final IconData icon;
  final String title;
  final String body;
  const _SlideData({required this.icon, required this.title, required this.body});
}

class _SlidePage extends StatelessWidget {
  final _SlideData data;
  const _SlidePage({required this.data});

  @override
  Widget build(BuildContext context) {
    final colors = context.appColors;

    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 32),
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Container(
            width: 120, height: 120,
            decoration: BoxDecoration(
              color: kAccent.withValues(alpha: 0.15),
              shape: BoxShape.circle,
            ),
            child: Icon(data.icon, size: 56, color: kAccent),
          ),
          const SizedBox(height: 40),
          Text(data.title, style: kTitle(color: colors.textPrimary), textAlign: TextAlign.center),
          const SizedBox(height: 16),
          Text(data.body, style: kBody(color: colors.textSecondary), textAlign: TextAlign.center),
        ],
      ),
    );
  }
}
