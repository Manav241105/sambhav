import 'package:flutter/material.dart';
import '../../core/theme/colors.dart';
import '../../core/theme/typography.dart';

class DiagnosticsScreen extends StatelessWidget {
  const DiagnosticsScreen({super.key});

  static const _components = [
    _ComponentData(name: 'Brake Pads', reading: '2.1 mm', status: 'critical', icon: Icons.settings),
    _ComponentData(name: 'Battery', reading: '11.8 V', status: 'warning', icon: Icons.battery_3_bar),
    _ComponentData(name: 'Coolant', reading: '88 °C', status: 'good', icon: Icons.water_drop_outlined),
    _ComponentData(name: 'Engine', reading: '94%', status: 'good', icon: Icons.settings_input_component),
    _ComponentData(name: 'Transmission', reading: '87%', status: 'good', icon: Icons.settings_suggest),
    _ComponentData(name: 'Tires', reading: '28 PSI', status: 'warning', icon: Icons.tire_repair),
  ];

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: kBg,
      appBar: AppBar(
        backgroundColor: kBg, elevation: 0,
        title: Text('Diagnostics', style: kTitle()),
        actions: [
          IconButton(icon: const Icon(Icons.refresh, color: Colors.grey), onPressed: () {}),
        ],
      ),
      body: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 16),
        child: Column(
          children: [
            // Overall health bar
            Container(
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(color: kSurface, borderRadius: BorderRadius.circular(rLG),
                boxShadow: const [cardShadow]),
              child: Row(
                children: [
                  Expanded(child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text('Overall Health', style: kLabel()),
                      const SizedBox(height: 8),
                      ClipRRect(
                        borderRadius: BorderRadius.circular(rFull),
                        child: LinearProgressIndicator(
                          value: 0.82, minHeight: 8,
                          backgroundColor: kSubtle,
                          valueColor: const AlwaysStoppedAnimation(kGaugeFill),
                        ),
                      ),
                    ],
                  )),
                  const SizedBox(width: 16),
                  Text('82%', style: kTitle(color: kAccentDark)),
                ],
              ),
            ),
            const SizedBox(height: 16),

            // Component grid
            Expanded(
              child: GridView.builder(
                padding: const EdgeInsets.only(bottom: 16),
                gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
                  crossAxisCount: 2, mainAxisSpacing: 12, crossAxisSpacing: 12, childAspectRatio: 1.4,
                ),
                itemCount: _components.length,
                itemBuilder: (_, i) => _ComponentCard(data: _components[i]),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _ComponentData {
  final String name, reading, status;
  final IconData icon;
  const _ComponentData({required this.name, required this.reading, required this.status, required this.icon});
}

class _ComponentCard extends StatelessWidget {
  final _ComponentData data;
  const _ComponentCard({super.key, required this.data});

  Color get _statusColor => switch (data.status) {
    'critical' => kDanger,
    'warning'  => kWarning,
    _ => kGood,
  };

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(color: kSurface, borderRadius: BorderRadius.circular(rLG),
        boxShadow: const [cardShadow]),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Row(children: [
            Icon(data.icon, size: 18, color: _statusColor),
            const SizedBox(width: 8),
            Expanded(child: Text(data.name, style: kLabel())),
          ]),
          Text(data.reading, style: kStatValue().copyWith(fontSize: 20)),
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
            decoration: BoxDecoration(
              color: _statusColor.withOpacity(0.12),
              borderRadius: BorderRadius.circular(rFull),
            ),
            child: Text(data.status.toUpperCase(), style: kCaption(color: _statusColor)),
          ),
        ],
      ),
    );
  }
}
