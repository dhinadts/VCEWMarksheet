import '../../core/api_client.dart';
import '../../models/models.dart';

class AuthRepository {
  AuthRepository(this.api);
  final ApiClient api;
  Future<UserProfile> login(String username, String password) async {
    final response = await api.dio.post(
      '/auth/login',
      data: {'username': username, 'password': password},
    );
    final tokens = response.data['data'] as Map<String, dynamic>;
    await ApiClient.storage.write(
      key: 'access_token',
      value: tokens['access_token'],
    );
    await ApiClient.storage.write(
      key: 'refresh_token',
      value: tokens['refresh_token'],
    );
    return me();
  }

  Future<UserProfile> me() async {
    final response = await api.dio.get('/auth/me');
    return UserProfile.fromJson(
      Map<String, dynamic>.from(response.data['data']),
    );
  }

  Future<void> changePassword(String current, String next) async {
    await api.dio.post(
      '/auth/change-password',
      data: {'current_password': current, 'new_password': next},
    );
    await clear();
  }

  Future<void> logout() async {
    final refresh = await ApiClient.storage.read(key: 'refresh_token');
    if (refresh != null) {
      try {
        await api.dio.post('/auth/logout', data: {'refresh_token': refresh});
      } catch (_) {}
    }
    await clear();
  }

  Future<void> clear() => ApiClient.storage.deleteAll();
}
