import 'package:dio/dio.dart';
import 'package:uuid/uuid.dart';
import '../core/api_client.dart';
import '../models/models.dart';

class AcademicRepository {
  AcademicRepository(this.api);
  final ApiClient api;
  Future<List<AcademicRecord>> list(String path) async {
    final response = await api.dio.get(path);
    dynamic data = response.data['data'];
    if (data is Map) data = data['items'];
    return (data as List)
        .map((e) => AcademicRecord(Map<String, dynamic>.from(e)))
        .toList();
  }

  Future<AcademicRecord> upload({
    required String imagePath,
    required AcademicRecord student,
    required AcademicRecord offering,
    required AcademicRecord assessment,
    String source = 'MOBILE_CAMERA',
  }) async {
    final form = FormData.fromMap({
      'student_id': student.id,
      'course_offering_id': offering.id,
      'assessment_id': assessment.id,
      'client_request_id': const Uuid().v4(),
      'source': source,
      'file': await MultipartFile.fromFile(
        imagePath,
        filename: 'marksheet_${student.text('register_number')}.jpg',
      ),
    });
    final response = await api.dio.post('/marksheets', data: form);
    return AcademicRecord(Map<String, dynamic>.from(response.data['data']));
  }

  Future<Map<String, dynamic>> processOcr(String marksheetId) async {
    final response = await api.dio.post('/marksheets/$marksheetId/process');
    return Map<String, dynamic>.from(response.data['data']);
  }

  Future<Map<String, dynamic>> reviewOcr(
    String marksheetId,
    List<Map<String, dynamic>> corrections,
  ) async {
    final response = await api.dio.put(
      '/marksheets/$marksheetId/review',
      data: {'corrections': corrections},
    );
    return Map<String, dynamic>.from(response.data['data']);
  }

  Future<void> approve(String marksheetId) async {
    await api.dio.post('/marksheets/$marksheetId/approve');
  }
}
