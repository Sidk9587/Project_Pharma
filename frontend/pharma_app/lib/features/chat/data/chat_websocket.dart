import 'dart:async';
import 'dart:convert';

import 'package:web_socket_channel/web_socket_channel.dart';

class ChatWebSocket {
  WebSocketChannel? _channel;
  String? _conversationId;

  Stream<Map<String, dynamic>>? get messages =>
      _channel?.stream.map(
        (event) {
          final message = jsonDecode(event as String) as Map<String, dynamic>;
          if (message['type'] == 'status' &&
              message['conversation_id'] is String) {
            _conversationId = message['conversation_id'] as String;
          }
          return message;
        },
      );

  void connect() {
    _channel = WebSocketChannel.connect(
      Uri.parse(
        'ws://127.0.0.1:8000/api/v1/chat/ws',
      ),
    );
  }

  void sendQuestion(String question) {
    if (_channel == null) {
      throw StateError('WebSocket is not connected.');
    }

    _channel!.sink.add(
      jsonEncode({
        'question': question,
        if (_conversationId != null)
          'conversation_id': _conversationId,
      }),
    );
  }

  void startNewConversation() {
    _conversationId = null;
  }

  Future<void> disconnect() async {
    await _channel?.sink.close();
    _channel = null;
  }
}
