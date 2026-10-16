class ChatMessage {
  final String text;
  final bool isUser;
  final bool isStreaming;
  final List<Map<String, dynamic>> sources;
  final DateTime? createdAt;

  ChatMessage({
    required this.text,
    required this.isUser,
    this.isStreaming = false,
    this.sources = const [],
    this.createdAt,
  });
}

class ChatState {
  final List<ChatMessage> messages;
  final bool connected;
  final bool isGenerating;
  final String status;
  final List<Map<String, dynamic>> sources;
  final String? error;
  final String? conversationId;

  ChatState({
    this.messages = const [],
    this.connected = false,
    this.isGenerating = false,
    this.status = '',
    this.sources = const [],
    this.error,
    this.conversationId,
  });

  ChatState copyWith({
    List<ChatMessage>? messages,
    bool? connected,
    bool? isGenerating,
    String? status,
    List<Map<String, dynamic>>? sources,
    String? error,
    String? conversationId,
    bool clearConversation = false,
  }) {
    return ChatState(
      messages: messages ?? this.messages,
      connected: connected ?? this.connected,
      isGenerating: isGenerating ?? this.isGenerating,
      status: status ?? this.status,
      sources: sources ?? this.sources,
      error: error,
      conversationId: clearConversation
          ? null
          : (conversationId ?? this.conversationId),
    );
  }
}
