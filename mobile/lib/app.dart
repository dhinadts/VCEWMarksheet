import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'core/theme.dart';
import 'features/auth/auth_controller.dart';
import 'features/auth/change_password_screen.dart';
import 'features/auth/login_screen.dart';
import 'features/dashboard/dashboard_screen.dart';

class MarksheetApp extends StatelessWidget {
  const MarksheetApp({super.key});
  @override
  Widget build(BuildContext context) => MaterialApp(
    title: 'VCEW Marksheets',
    debugShowCheckedModeBanner: false,
    theme: buildAppTheme(),
    home: Consumer<AuthController>(
      builder: (context, auth, child) {
        if (auth.loading) {
          return const Scaffold(
            body: Center(child: CircularProgressIndicator()),
          );
        }
        if (auth.user == null) {
          return const LoginScreen();
        }
        if (auth.user!.mustChangePassword) {
          return const ChangePasswordScreen();
        }
        return const DashboardScreen();
      },
    ),
  );
}
