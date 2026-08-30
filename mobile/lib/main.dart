import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'app.dart';
import 'core/api_client.dart';
import 'features/auth/auth_controller.dart';
import 'features/auth/auth_repository.dart';

void main() {
  WidgetsFlutterBinding.ensureInitialized();
  final api = ApiClient();
  runApp(
    ChangeNotifierProvider(
      create: (_) => AuthController(AuthRepository(api))..restoreSession(),
      child: const MarksheetApp(),
    ),
  );
}
