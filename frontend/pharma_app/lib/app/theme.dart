import 'package:flutter/material.dart';

abstract final class AppTheme {
  static final light = ThemeData(
    colorScheme: ColorScheme.fromSeed(
      seedColor: const Color(0xFF116B63),
      surface: const Color(0xFFF7F9F8),
    ),
    useMaterial3: true,
    fontFamily: 'PharmaSans',
    scaffoldBackgroundColor: const Color(0xFFF7F9F8),
    cardTheme: CardThemeData(
      color: Colors.white,
      elevation: 0,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(18),
        side: const BorderSide(color: Color(0xFFE7ECEA)),
      ),
    ),
    appBarTheme: const AppBarTheme(
      backgroundColor: Color(0xFFF7F9F8),
      foregroundColor: Color(0xFF16302D),
      elevation: 0,
    ),
    inputDecorationTheme: InputDecorationTheme(
      filled: true,
      fillColor: Colors.white,
      border: OutlineInputBorder(
        borderRadius: BorderRadius.circular(14),
        borderSide: const BorderSide(color: Color(0xFFE0E7E4)),
      ),
      enabledBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(14),
        borderSide: const BorderSide(color: Color(0xFFE0E7E4)),
      ),
    ),
  );
}
