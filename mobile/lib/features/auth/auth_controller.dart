import 'package:flutter/foundation.dart';
import '../../core/api_client.dart';
import '../../models/models.dart';
import 'auth_repository.dart';

class AuthController extends ChangeNotifier {
  AuthController(this.repository);
  final AuthRepository repository;
  UserProfile? user;
  bool loading = true;
  String? error;
  Future<void> restoreSession() async {
    try {
      user = await repository.me();
      if (user?.userType == 'STUDENT') {
        user = null;
        await repository.clear();
      }
    } catch (_) {
      await repository.clear();
    }
    loading = false;
    notifyListeners();
  }

  Future<bool> login(String username, String password) async {
    loading = true;
    error = null;
    notifyListeners();
    try {
      final profile = await repository.login(username.trim(), password);
      if (profile.userType == 'STUDENT') {
        await repository.clear();
        throw Exception(
          'The mobile app is available only to professors and administrators.',
        );
      }
      user = profile;
      return true;
    } catch (exception) {
      error = exception.toString().startsWith('Exception: ')
          ? exception.toString().substring(11)
          : ApiClient.message(exception);
      return false;
    } finally {
      loading = false;
      notifyListeners();
    }
  }

  Future<void> logout() async {
    await repository.logout();
    user = null;
    notifyListeners();
  }
}
