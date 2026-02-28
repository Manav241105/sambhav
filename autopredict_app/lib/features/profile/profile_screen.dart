import 'package:flutter/material.dart';
import '../../core/theme/colors.dart';
import '../../core/theme/typography.dart';

class ProfileScreen extends StatelessWidget {
  const ProfileScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: kBg,
      appBar: AppBar(backgroundColor: kBg, elevation: 0, title: Text('Profile', style: kTitle())),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          // Avatar
          Center(child: Column(children: [
            Container(width: 80, height: 80,
              decoration: const BoxDecoration(color: kAccent, shape: BoxShape.circle),
              child: const Icon(Icons.person, size: 40, color: Colors.black)),
            const SizedBox(height: 10),
            Text('Manav Parekh', style: kTitle()),
            Text('+91 98765 43210', style: kBody()),
          ])),
          const SizedBox(height: 28),

          // Vehicles section
          Text('MY VEHICLES', style: kLabel()),
          const SizedBox(height: 10),
          _VehicleCard(id: 'VEH001', make: 'Tesla', model: 'Model 3', year: 2022, health: 82),
          const SizedBox(height: 8),
          GestureDetector(onTap: () {},
            child: Container(height: 52,
              decoration: BoxDecoration(border: Border.all(color: kAccent), borderRadius: BorderRadius.circular(rMD)),
              child: Row(mainAxisAlignment: MainAxisAlignment.center, children: [
                const Icon(Icons.add, color: Colors.grey),
                const SizedBox(width: 8),
                Text('Add Vehicle via VIN', style: kBody()),
              ]),
            ),
          ),
          const SizedBox(height: 24),

          // Settings tiles
          Text('SETTINGS', style: kLabel()),
          const SizedBox(height: 10),
          ...[
            ('Notification Preferences', Icons.notifications_outlined),
            ('Language', Icons.language),
            ('Linked Service Center', Icons.business_outlined),
            ('Contact Support', Icons.headset_mic_outlined),
            ('Logout', Icons.logout),
          ].map((e) => Container(
            margin: const EdgeInsets.only(bottom: 8),
            decoration: BoxDecoration(color: kSurface, borderRadius: BorderRadius.circular(rMD),
              boxShadow: const [cardShadow]),
            child: ListTile(
              leading: Icon(e.$2, size: 20, color: e.$1 == 'Logout' ? kDanger : kMid),
              title: Text(e.$1, style: kBody(color: e.$1 == 'Logout' ? kDanger : kDark)),
              trailing: e.$1 != 'Logout'
                ? const Icon(Icons.chevron_right, size: 18, color: Colors.grey) : null,
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
  Widget build(BuildContext context) => Container(
    padding: const EdgeInsets.all(14),
    decoration: BoxDecoration(color: kSurface, borderRadius: BorderRadius.circular(rLG),
      boxShadow: const [cardShadow]),
    child: Row(children: [
      Container(width: 48, height: 48,
        decoration: BoxDecoration(color: kAccent.withOpacity(0.15), borderRadius: BorderRadius.circular(rMD)),
        child: const Icon(Icons.directions_car, color: Color(0xFF8FB82E))),
      const SizedBox(width: 12),
      Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        Text('$make $model', style: kSubtitle()),
        Text('$year · $id', style: kCaption()),
      ])),
      Text('$health%', style: kLabel(color: health >= 80 ? kGood : kWarning)),
    ]),
  );
}
