import 'dart:io';
import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';
import '../../core/api_client.dart';
import '../../models/models.dart';
import '../../repositories/academic_repository.dart';
import '../review/ocr_review_screen.dart';

class PreviewUploadScreen extends StatefulWidget {
  const PreviewUploadScreen({
    super.key,
    required this.repository,
    required this.image,
    required this.student,
    required this.offering,
    required this.assessment,
    required this.source,
  });
  final AcademicRepository repository;
  final XFile image;
  final AcademicRecord student, offering, assessment;
  final String source;
  @override
  State<PreviewUploadScreen> createState() => _PreviewUploadScreenState();
}

class _PreviewUploadScreenState extends State<PreviewUploadScreen> {
  bool uploading = false;
  String? error;
  Future<void> upload() async {
    setState(() {
      uploading = true;
      error = null;
    });
    try {
      final uploaded = await widget.repository.upload(
        imagePath: widget.image.path,
        student: widget.student,
        offering: widget.offering,
        assessment: widget.assessment,
        source: widget.source,
      );
      if (mounted) {
        final approved = await Navigator.push<bool>(
          context,
          MaterialPageRoute(
            builder: (_) => OcrReviewScreen(
              repository: widget.repository,
              marksheetId: uploaded.id,
              imagePath: widget.image.path,
              studentLabel:
                  '${widget.student.text('register_number')} · ${widget.student.text('name')}',
            ),
          ),
        );
        if (mounted && approved == true) Navigator.pop(context, true);
      }
    } catch (e) {
      setState(() => error = ApiClient.message(e));
    } finally {
      if (mounted) setState(() => uploading = false);
    }
  }

  @override
  Widget build(BuildContext context) => Scaffold(
    backgroundColor: Colors.black,
    appBar: AppBar(
      title: const Text('Review capture'),
      actions: [
        IconButton(
          tooltip: 'Discard',
          onPressed: () => Navigator.pop(context, false),
          icon: const Icon(Icons.close),
        ),
      ],
    ),
    body: Column(
      children: [
        Expanded(
          child: Center(
            child: Image.file(
              File(widget.image.path),
              fit: BoxFit.contain,
              errorBuilder: (context, error, stackTrace) => const Text(
                'Preview unavailable',
                style: TextStyle(color: Colors.white),
              ),
            ),
          ),
        ),
        Container(
          color: Colors.white,
          padding: EdgeInsets.fromLTRB(
            20,
            16,
            20,
            16 + MediaQuery.paddingOf(context).bottom,
          ),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              Text(
                '${widget.student.text('register_number')} · ${widget.student.text('name')}',
                style: const TextStyle(fontWeight: FontWeight.bold),
              ),
              const SizedBox(height: 6),
              const Text(
                'The original photo is stored securely before handwritten marks are extracted.',
                style: TextStyle(color: Color(0xFF66788A)),
              ),
              if (error != null) ...[
                const SizedBox(height: 10),
                Text(error!, style: const TextStyle(color: Colors.red)),
              ],
              const SizedBox(height: 14),
              Row(
                children: [
                  Expanded(
                    child: OutlinedButton(
                      onPressed: uploading
                          ? null
                          : () => Navigator.pop(context, false),
                      child: const Text('Retake'),
                    ),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: ElevatedButton(
                      onPressed: uploading ? null : upload,
                      child: Text(
                        uploading ? 'Storing securely…' : 'Store & extract',
                      ),
                    ),
                  ),
                ],
              ),
            ],
          ),
        ),
      ],
    ),
  );
}
