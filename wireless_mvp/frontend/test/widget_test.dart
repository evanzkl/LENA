// Basic smoke test: the app should build without throwing.

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:wireless_mvp_frontend/main.dart';

void main() {
  testWidgets('App builds without throwing', (WidgetTester tester) async {
    await tester.pumpWidget(const OcrTranslatorApp());
    expect(find.byType(MaterialApp), findsOneWidget);
  });
}
