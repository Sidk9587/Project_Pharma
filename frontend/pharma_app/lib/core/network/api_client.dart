import 'package:dio/dio.dart';

class ApiClient {
  final Dio dio = Dio(
    BaseOptions(
      baseUrl: 'http://127.0.0.1:8000',
      connectTimeout: const Duration(seconds: 10),
      receiveTimeout: const Duration(seconds: 10),
    ),
  );

  Future<String> checkHealth() async {
    final response = await dio.get('/health');

    return response.data['message'];
  }
}