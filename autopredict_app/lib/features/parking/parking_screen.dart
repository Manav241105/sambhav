import 'package:flutter/material.dart';
import 'package:flutter_map/flutter_map.dart';
import 'package:latlong2/latlong.dart';
import 'package:google_fonts/google_fonts.dart';
import '../../core/theme/app_theme.dart';
import '../../core/theme/colors.dart';

class ParkingScreen extends StatefulWidget {
  const ParkingScreen({super.key});
  @override
  State<ParkingScreen> createState() => _ParkingScreenState();
}

class _ParkingScreenState extends State<ParkingScreen> {
  // Mumbai coords (demo)
  static const _parkedLocation = LatLng(19.0760, 72.8777);
  bool _geofenceActive = true;
  final _mapCtrl = MapController();

  @override
  Widget build(BuildContext context) {
    final colors = context.appColors;

    return Scaffold(
      backgroundColor: colors.scaffoldBg,
      body: SafeArea(
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Padding(
              padding: const EdgeInsets.fromLTRB(16, 16, 16, 12),
              child: Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                    Text('Parking', style: GoogleFonts.inter(
                      fontSize: 22, fontWeight: FontWeight.w700, color: colors.textPrimary,
                    )),
                    Text('Last known location', style: GoogleFonts.inter(
                      fontSize: 12, color: colors.textSecondary,
                    )),
                  ]),
                  // Geofence toggle
                  GestureDetector(
                    onTap: () => setState(() => _geofenceActive = !_geofenceActive),
                    child: Container(
                      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
                      decoration: BoxDecoration(
                        color: _geofenceActive
                            ? kAccent.withValues(alpha: 0.15)
                            : colors.neuBg,
                        borderRadius: BorderRadius.circular(rFull),
                        border: Border.all(
                          color: _geofenceActive ? kAccent : colors.navBorder,
                        ),
                      ),
                      child: Row(children: [
                        Icon(Icons.radar, size: 14,
                            color: _geofenceActive ? kAccentDark : colors.textSecondary),
                        const SizedBox(width: 6),
                        Text(_geofenceActive ? 'Geofence ON' : 'Geofence OFF',
                            style: GoogleFonts.inter(
                              fontSize: 12, fontWeight: FontWeight.w600,
                              color: _geofenceActive ? kAccentDark : colors.textSecondary,
                            )),
                      ]),
                    ),
                  ),
                ],
              ),
            ),

            // Map
            Expanded(
              flex: 3,
              child: ClipRRect(
                borderRadius: const BorderRadius.vertical(top: Radius.circular(rLG)),
                child: FlutterMap(
                  mapController: _mapCtrl,
                  options: MapOptions(
                    initialCenter: _parkedLocation,
                    initialZoom: 15,
                  ),
                  children: [
                    TileLayer(
                      urlTemplate: 'https://tile.openstreetmap.org/{z}/{x}/{y}.png',
                      userAgentPackageName: 'com.autopredict.app',
                    ),
                    // Geofence circle
                    if (_geofenceActive)
                      CircleLayer(circles: [
                        CircleMarker(
                          point: _parkedLocation,
                          radius: 120,
                          color: kAccent.withValues(alpha: 0.12),
                          borderColor: kAccent.withValues(alpha: 0.5),
                          borderStrokeWidth: 2,
                        ),
                      ]),
                    MarkerLayer(markers: [
                      Marker(
                        point: _parkedLocation,
                        width: 44, height: 44,
                        child: Container(
                          decoration: BoxDecoration(
                            color: kAccent,
                            shape: BoxShape.circle,
                            boxShadow: [
                              BoxShadow(
                                color: kAccent.withValues(alpha: 0.4),
                                blurRadius: 12, spreadRadius: 3,
                              ),
                            ],
                          ),
                          child: const Icon(Icons.directions_car, size: 22, color: Colors.black),
                        ),
                      ),
                    ]),
                  ],
                ),
              ),
            ),

            // Info panel
            Expanded(
              flex: 2,
              child: SingleChildScrollView(
                child: Padding(
                  padding: const EdgeInsets.all(16),
                  child: Column(children: [
                    // Location card
                    _InfoCard(
                      icon: Icons.location_on_outlined,
                      title: 'Parked at',
                      subtitle: 'Mumbai, Maharashtra, India\n19.0760° N, 72.8777° E',
                      colors: colors,
                    ),
                    const SizedBox(height: 12),
                    Row(children: [
                      Expanded(child: _InfoCard(
                        icon: Icons.access_time,
                        title: 'Parked for',
                        subtitle: '2h 14m',
                        colors: colors,
                      )),
                      const SizedBox(width: 12),
                      Expanded(child: _InfoCard(
                        icon: Icons.local_parking,
                        title: 'Zone',
                        subtitle: 'Free · No limit',
                        colors: colors,
                      )),
                    ]),
                    const SizedBox(height: 12),

                    // Nearby EV chargers
                    Container(
                      padding: const EdgeInsets.all(14),
                      decoration: BoxDecoration(
                        color: colors.surface,
                        borderRadius: BorderRadius.circular(rLG),
                        boxShadow: [colors.cardShadowStyle],
                      ),
                      child: Row(children: [
                        Container(
                          width: 36, height: 36,
                          decoration: BoxDecoration(
                            color: kGood.withValues(alpha: 0.12),
                            shape: BoxShape.circle,
                          ),
                          child: const Icon(Icons.ev_station, size: 18, color: kGood),
                        ),
                        const SizedBox(width: 12),
                        Expanded(child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text('2 EV Chargers Nearby', style: GoogleFonts.inter(
                              fontSize: 13, fontWeight: FontWeight.w600, color: colors.textPrimary,
                            )),
                            Text('Closest: 340m away · Available',
                                style: GoogleFonts.inter(fontSize: 11, color: colors.textSecondary)),
                          ],
                        )),
                        Icon(Icons.arrow_forward_ios, size: 14, color: colors.textSecondary),
                      ]),
                    ),
                    const SizedBox(height: 80),
                  ]),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _InfoCard extends StatelessWidget {
  final IconData icon;
  final String title, subtitle;
  final dynamic colors;
  const _InfoCard({required this.icon, required this.title, required this.subtitle, required this.colors});

  @override
  Widget build(BuildContext context) => Container(
    padding: const EdgeInsets.all(14),
    decoration: BoxDecoration(
      color: colors.surface,
      borderRadius: BorderRadius.circular(rMD),
      boxShadow: [colors.cardShadowStyle],
    ),
    child: Row(children: [
      Icon(icon, size: 18, color: colors.textSecondary),
      const SizedBox(width: 10),
      Expanded(child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(title, style: GoogleFonts.inter(fontSize: 11, color: colors.textSecondary)),
          Text(subtitle, style: GoogleFonts.inter(
            fontSize: 13, fontWeight: FontWeight.w600, color: colors.textPrimary,
          )),
        ],
      )),
    ]),
  );
}
