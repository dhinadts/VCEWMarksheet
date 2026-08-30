import 'package:flutter_test/flutter_test.dart';
import 'package:marksheet_mobile/models/models.dart';

void main() {
  test('academic records preserve backend snake_case fields', () {
    final record = AcademicRecord({
      'id': 'student-1',
      'register_number': 'CST23001',
      'current_semester': 3,
    });
    expect(record.id, 'student-1');
    expect(record.text('register_number'), 'CST23001');
    expect(record.integer('current_semester'), 3);
  });
}
