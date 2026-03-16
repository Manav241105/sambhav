import 'package:flutter/material.dart';
import '../../core/theme/app_theme.dart';
import '../../core/theme/colors.dart';
import '../../core/theme/typography.dart';

class ProfileScreen extends StatelessWidget {
  const ProfileScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final colors = context.appColors;

    return Scaffold(
      backgroundColor: colors.scaffoldBg,
      appBar: AppBar(
        backgroundColor: colors.scaffoldBg,
        elevation: 0,
        title: Text('Profile', style: kTitle(color: colors.textPrimary)),
      ),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          // Avatar
          Center(child: Column(children: [
            Container(width: 80, height: 80,
              decoration: const BoxDecoration(color: kAccent, shape: BoxShape.circle),
              child: const Icon(Icons.person, size: 40, color: Colors.black)),
            const SizedBox(height: 10),
            Text('Manav Parekh', style: kTitle(color: colors.textPrimary)),
            Text('+91 98765 43210', style: kBody(color: colors.textSecondary)),
          ])),
          const SizedBox(height: 28),

          // Vehicles section
          Text('MY VEHICLES', style: kLabel(color: colors.textSecondary)),
          const SizedBox(height: 10),
          _VehicleCard(id: 'VEH001', make: 'Tesla', model: 'Model 3', year: 2022, health: 82),
          const SizedBox(height: 8),
          GestureDetector(onTap: () {},
            child: Container(height: 52,
              decoration: BoxDecoration(
                border: Border.all(color: kAccent),
                borderRadius: BorderRadius.circular(rMD),
              ),
              child: Row(mainAxisAlignment: MainAxisAlignment.center, children: [
                Icon(Icons.add, color: colors.textSecondary),
                const SizedBox(width: 8),
                Text('Add Vehicle via VIN', style: kBody(color: colors.textSecondary)),
              ]),
            ),
          ),
          const SizedBox(height: 24),

          // Settings tiles
          Text('SETTINGS', style: kLabel(color: colors.textSecondary)),
          const SizedBox(height: 10),
          ...[
            ('Notification Preferences', Icons.notifications_outlined),
            ('Language', Icons.language),
            ('Linked Service Center', Icons.business_outlined),
            ('Contact Support', Icons.headset_mic_outlined),
            ('Logout', Icons.logout),
          ].map((e) => Container(
            margin: const EdgeInsets.only(bottom: 8),
            decoration: BoxDecoration(
              color: colors.surface,
              borderRadius: BorderRadius.circular(rMD),
              boxShadow: [colors.cardShadowStyle],
            ),
            child: ListTile(
              leading: Icon(e.$2, size: 20,
                  color: e.$1 == 'Logout' ? kDanger : colors.textSecondary),
              title: Text(e.$1,
                  style: kBody(color: e.$1 == 'Logout' ? kDanger : colors.textPrimary)),
              trailing: e.$1 != 'Logout'
                ? Icon(Icons.chevron_right, size: 18, color: colors.textSecondary) : null,
              onTap: () {},
            ),
          )),
        ],
      ),
    );
  }
}

class _VehicleCard extends StatelessWidget {
  final String id, make, model;
  final int year;
  final int health;
  const _VehicleCard({required this.id, required this.make, required this.model,
    required this.year, required this.health});

  @override
  Widget build(BuildContext context) {
    final colors = context.appColors;

    return Container(
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: colors.surface,
        borderRadius: BorderRadius.circular(rLG),
        boxShadow: [colors.cardShadowStyle],
      ),
      child: Row(children: [
        Container(width: 48, height: 48,
          decoration: BoxDecoration(
            color: kAccent.withValues(alpha: 0.15),
            borderRadius: BorderRadius.circular(rMD),
          ),
          child: const Icon(Icons.directions_car, color: Color(0xFF8FB82E))),
        const SizedBox(width: 12),
        Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Text('$make $model', style: kSubtitle(color: colors.textPrimary)),
          Text('$year · $id', style: kCaption(color: colors.textSecondary)),
        ])),
        Text('$health%', style: kLabel(color: health >= 80 ? kGood : kWarning)),
      ]),
    );
  }
}
