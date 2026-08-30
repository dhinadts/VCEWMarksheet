import 'package:flutter/material.dart';

import '../../core/api_client.dart';
import '../../models/models.dart';
import '../../repositories/academic_repository.dart';
import 'student_capture_screen.dart';

class CaptureSetupScreen extends StatefulWidget {
  const CaptureSetupScreen({super.key, required this.repository});
  final AcademicRepository repository;
  @override
  State<CaptureSetupScreen> createState() => _CaptureSetupScreenState();
}

class _CaptureSetupScreenState extends State<CaptureSetupScreen> {
  bool loading = true;
  String? error;
  List<AcademicRecord> courses = [],
      offerings = [],
      assessments = [],
      students = [];
  AcademicRecord? course, offering, assessment;

  @override
  void initState() {
    super.initState();
    load();
  }

  Future<void> load() async {
    try {
      final result = await Future.wait([
        widget.repository.list('/courses?semester_number=6&page_size=100'),
        widget.repository.list('/course-offerings'),
        widget.repository.list('/assessments'),
        widget.repository.list('/students?page_size=100'),
      ]);
      if (!mounted) return;
      setState(() {
        courses = result[0];
        offerings = result[1];
        assessments = result[2];
        students = result[3];
        loading = false;
      });
    } catch (exception) {
      if (mounted) {
        setState(() {
          error = ApiClient.message(exception);
          loading = false;
        });
      }
    }
  }

  List<AcademicRecord> get availableCourses {
    final assignedCourseIds = offerings
        .map((item) => item.text('course_id'))
        .toSet();
    return courses
        .where((item) => assignedCourseIds.contains(item.id))
        .toList();
  }

  List<AcademicRecord> get availableAssessments => offering == null
      ? []
      : assessments
            .where((item) => item.text('course_offering_id') == offering!.id)
            .toList();

  void selectCourse(AcademicRecord? selected) {
    setState(() {
      course = selected;
      offering = selected == null
          ? null
          : offerings
                .where((item) => item.text('course_id') == selected.id)
                .firstOrNull;
      assessment = null;
    });
  }

  @override
  Widget build(BuildContext context) => Scaffold(
    appBar: AppBar(title: const Text('Biotechnology marks')),
    body: loading
        ? const Center(child: CircularProgressIndicator())
        : error != null
        ? Center(
            child: Padding(
              padding: const EdgeInsets.all(24),
              child: Text(error!),
            ),
          )
        : ListView(
            padding: const EdgeInsets.all(20),
            children: [
              Text(
                'Choose subject',
                style: Theme.of(context).textTheme.headlineSmall?.copyWith(
                  fontWeight: FontWeight.bold,
                ),
              ),
              const SizedBox(height: 8),
              const Text(
                'B.Tech Biotechnology · Semester VI · 50 students',
                style: TextStyle(color: Color(0xFF66788A)),
              ),
              const SizedBox(height: 24),
              _picker(
                'Assigned subject',
                course,
                availableCourses,
                selectCourse,
                (item) => '${item.text('code')} · ${item.text('name')}',
              ),
              _picker(
                'Internal assessment',
                assessment,
                availableAssessments,
                (value) => setState(() => assessment = value),
                (item) => item.text('name'),
              ),
              const SizedBox(height: 12),
              ElevatedButton.icon(
                onPressed: offering == null || assessment == null
                    ? null
                    : () {
                        final selectedStudents = students
                            .where(
                              (item) =>
                                  item.text('class_id') ==
                                  offering!.text('class_id'),
                            )
                            .toList();
                        Navigator.push(
                          context,
                          MaterialPageRoute(
                            builder: (_) => StudentCaptureScreen(
                              repository: widget.repository,
                              students: selectedStudents,
                              offering: offering!,
                              assessment: assessment!,
                              contextTitle:
                                  '${course!.text('code')} · ${assessment!.text('name')}',
                            ),
                          ),
                        );
                      },
                icon: const Icon(Icons.people_outline),
                label: const Text('Open 50-student capture list'),
              ),
            ],
          ),
  );

  Widget _picker(
    String label,
    AcademicRecord? value,
    List<AcademicRecord> items,
    ValueChanged<AcademicRecord?> changed,
    String Function(AcademicRecord) title,
  ) => Padding(
    padding: const EdgeInsets.only(bottom: 16),
    child: DropdownButtonFormField<AcademicRecord>(
      initialValue: value,
      decoration: InputDecoration(labelText: label),
      isExpanded: true,
      items: items
          .map(
            (item) => DropdownMenuItem(
              value: item,
              child: Text(title(item), overflow: TextOverflow.ellipsis),
            ),
          )
          .toList(),
      onChanged: changed,
    ),
  );
}
