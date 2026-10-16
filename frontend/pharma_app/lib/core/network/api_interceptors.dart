abstract interface class ApiInterceptor {
  Map<String, String> apply(Map<String, String> headers);
}
