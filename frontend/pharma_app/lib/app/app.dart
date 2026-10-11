import 'package:flutter/material.dart';

import '../core/constants/app_constants.dart';
import 'router.dart';
import 'theme.dart';

class AppShell extends StatelessWidget {
  const AppShell({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: AppConstants.appName,
      theme: AppTheme.light,
      initialRoute: AppRoutes.home,
      routes: {
        AppRoutes.home: (context) => const Scaffold(
              body: Center(child: Text(AppConstants.appName)),
            ),
      },
    );
  }
}