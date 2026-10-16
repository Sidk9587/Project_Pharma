import 'package:dio/dio.dart';
import 'dart:typed_data';
import '../constants/api_constants.dart';

class ApiClient {
  ApiClient()
    : dio = Dio(
        BaseOptions(
          baseUrl: ApiConstants.baseUrl,
          connectTimeout: const Duration(seconds: 10),
          receiveTimeout: const Duration(minutes: 3),
        ),
      );

  final Dio dio;

  String friendlyError(Object error) {
    if (error is DioException) {
      final detail = error.response?.data is Map
          ? error.response?.data['detail']
          : null;
      if (detail is String && detail.isNotEmpty) return detail;
      if (error.type == DioExceptionType.connectionTimeout ||
          error.type == DioExceptionType.connectionError) {
        return 'Could not reach the backend at ${ApiConstants.baseUrl}. Check that the API is running.';
      }
      return 'Request failed (${error.response?.statusCode ?? 'network error'}). Please try again.';
    }
    return 'Something went wrong. Please try again.';
  }

  Future<String> checkHealth() async {
    final response = await dio.get('/health');

    return response.data['message'];
  }

  Future<List<dynamic>> documents() async =>
      (await dio.get('/api/v1/documents')).data as List<dynamic>;
  Future<Map<String, dynamic>> documentDetail(String id) async =>
      Map<String, dynamic>.from((await dio.get('/api/v1/documents/$id')).data);
  Future<Map<String, dynamic>> documentStatus(String id) async =>
      Map<String, dynamic>.from(
        (await dio.get('/api/v1/documents/$id/status')).data,
      );
  Future<Map<String, dynamic>> uploadPdf(
    String filename,
    Uint8List bytes,
    void Function(int, int) progress,
  ) async {
    final response = await dio.post(
      '/api/v1/documents/upload',
      data: FormData.fromMap({
        'file': MultipartFile.fromBytes(bytes, filename: filename),
      }),
      onSendProgress: progress,
    );
    return Map<String, dynamic>.from(response.data);
  }

  Future<void> deleteDocument(String id) async =>
      dio.delete('/api/v1/documents/$id');
  Future<List<dynamic>> sources() async =>
      (await dio.get('/api/v1/sources')).data as List<dynamic>;
  Future<Map<String, dynamic>> createSource(String name, String url) async =>
      Map<String, dynamic>.from(
        (await dio.post(
          '/api/v1/sources',
          data: {'name': name, 'base_url': url},
        )).data,
      );
  Future<Map<String, dynamic>> patchSource(
    String id,
    Map<String, dynamic> changes,
  ) async => Map<String, dynamic>.from(
    (await dio.patch('/api/v1/sources/$id', data: changes)).data,
  );
  Future<Map<String, dynamic>> crawlSource(String id) async =>
      Map<String, dynamic>.from(
        (await dio.post('/api/v1/sources/$id/crawl')).data,
      );
  Future<Map<String, dynamic>> sourceStatus(String id) async =>
      Map<String, dynamic>.from(
        (await dio.get('/api/v1/sources/$id/status')).data,
      );
  Future<void> deleteSource(String id) async =>
      dio.delete('/api/v1/sources/$id');
  Future<List<dynamic>> conversations() async =>
      (await dio.get('/api/v1/conversations')).data as List<dynamic>;
  Future<Map<String, dynamic>> createConversation([String? title]) async =>
      Map<String, dynamic>.from(
        (await dio.post('/api/v1/conversations', data: {'title': title})).data,
      );
  Future<Map<String, dynamic>> conversation(String id) async =>
      Map<String, dynamic>.from(
        (await dio.get('/api/v1/conversations/$id')).data,
      );
  Future<void> deleteConversation(String id) async =>
      dio.delete('/api/v1/conversations/$id');
  Future<Map<String, dynamic>> providerSettings() async =>
      Map<String, dynamic>.from(
        (await dio.get('/api/v1/settings/provider')).data,
      );
  Future<List<int>> export(String format, Map<String, dynamic> payload) async =>
      (await dio.post(
            '/api/v1/exports/$format',
            data: payload,
            options: Options(responseType: ResponseType.bytes),
          )).data
          as List<int>;
}
