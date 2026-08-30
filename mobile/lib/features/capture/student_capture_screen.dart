import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';

import '../../models/models.dart';
import '../../repositories/academic_repository.dart';
import 'preview_upload_screen.dart';

class StudentCaptureScreen extends StatefulWidget {
  const StudentCaptureScreen({
    super.key,
    required this.repository,
    required this.students,
    required this.offering,
    required this.assessment,
    required this.contextTitle,
  });
  final AcademicRepository repository;
  final List<AcademicRecord> students;
  final AcademicRecord offering;
  final AcademicRecord assessment;
  final String contextTitle;
  @override
  State<StudentCaptureScreen> createState() => _StudentCaptureScreenState();
}

class _StudentCaptureScreenState extends State<StudentCaptureScreen> {
  final completed = <String>{};

  Future<void> capture(AcademicRecord student, ImageSource source) async {
    final image = await ImagePicker().pickImage(
      source: source,
      imageQuality: 92,
      maxWidth: 2400,
    );
    if (image == null || !mounted) return;
    final saved = await Navigator.push<bool>(
      context,
      MaterialPageRoute(
        builder: (_) => PreviewUploadScreen(
          repository: widget.repository,
          image: image,
          student: student,
          offering: widget.offering,
          assessment: widget.assessment,
          source: source == ImageSource.camera
              ? 'MOBILE_CAMERA'
              : 'MOBILE_GALLERY',
        ),
      ),
    );
    if (saved == true) setState(() => completed.add(student.id));
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Capture students')),
      body: Column(
        children: [
          Container(
            width: double.infinity,
            color: const Color(0xFFEAF2FF),
            padding: const EdgeInsets.all(16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  widget.contextTitle,
                  style: const TextStyle(fontWeight: FontWeight.bold),
                ),
                const SizedBox(height: 4),
                Text(
                  '${completed.length} / ${widget.students.length} completed',
                  style: const TextStyle(color: Color(0xFF66788A)),
                ),
              ],
            ),
          ),
          Expanded(
            child: ListView.separated(
              padding: const EdgeInsets.all(16),
              itemCount: widget.students.length,
              separatorBuilder: (_, _) => const SizedBox(height: 8),
              itemBuilder: (_, index) {
                final student = widget.students[index];
                final done = completed.contains(student.id);
                return Card(
                  child: ListTile(
                    leading: CircleAvatar(
                      backgroundColor: done
                          ? const Color(0xFFE5F6F1)
                          : const Color(0xFFEAF2FF),
                      child: Icon(
                        done ? Icons.check : Icons.person_outline,
                        color: done ? Colors.green : const Color(0xFF1F6FEB),
                      ),
                    ),
                    title: Text(
                      student.text('register_number'),
                      style: const TextStyle(fontWeight: FontWeight.bold),
                    ),
                    subtitle: Text(student.text('name')),
                    trailing: done
                        ? const Text(
                            'Uploaded',
                            style: TextStyle(
                              color: Colors.green,
                              fontWeight: FontWeight.bold,
                            ),
                          )
                        : PopupMenuButton<ImageSource>(
                            tooltip: 'Add marksheet',
                            onSelected: (source) => capture(student, source),
                            itemBuilder: (_) => const [
                              PopupMenuItem(
                                value: ImageSource.camera,
                                child: ListTile(
                                  leading: Icon(Icons.camera_alt_outlined),
                                  title: Text('Take photo'),
                                ),
                              ),
                              PopupMenuItem(
                                value: ImageSource.gallery,
                                child: ListTile(
                                  leading: Icon(Icons.photo_library_outlined),
                                  title: Text('Upload photo'),
                                ),
                              ),
                            ],
                            child: const Chip(
                              avatar: Icon(
                                Icons.add_a_photo_outlined,
                                size: 18,
                              ),
                              label: Text('Add sheet'),
                            ),
                          ),
                  ),
                );
              },
            ),
          ),
        ],
      ),
    );
  }
}
