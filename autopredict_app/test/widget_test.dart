import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:autopredict_app/core/theme/app_theme.dart';
import 'package:autopredict_app/features/auth/login_screen.dart';

Widget _wrap(Widget child) => MaterialApp(theme: buildLightTheme(), home: child);

void main() {
  testWidgets('Login starts with the phone step', (tester) async {
    await tester.pumpWidget(_wrap(const LoginScreen()));

    expect(find.text('Send OTP'), findsOneWidget);
    expect(find.text('Verify OTP'), findsNothing);
  });

  testWidgets('Login validates the phone number before calling the server', (tester) async {
    await tester.pumpWidget(_wrap(const LoginScreen()));

    await tester.enterText(find.byType(TextField).first, '123');
    await tester.tap(find.text('Send OTP'));
    await tester.pump();

    expect(find.text('Enter your 10-digit mobile number'), findsOneWidget);
    expect(find.text('Verify OTP'), findsNothing);
  });
}
