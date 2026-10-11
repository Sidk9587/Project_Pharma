import 'package:flutter/material.dart';

abstract final class AppTheme {
  static final light = ThemeData(
    colorScheme: ColorScheme.fromSeed(seedColor: Colors.teal),
    useMaterial3: true,
  );
}