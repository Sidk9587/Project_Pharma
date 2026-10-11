import 'dart:async';

import 'package:flutter_bloc/flutter_bloc.dart';

import '../data/chat_websocket.dart';
import 'chat_event.dart';
import 'chat_state.dart';

class ChatBloc extends Bloc<ChatEvent, ChatState> {
  final ChatWebSocket webSocket;

  StreamSubscription? _subscription;

  ChatBloc({
    required this.webSocket,
  }) : super(ChatState()) {
    on<ChatStarted>(_onChatStarted);
    on<SendMessage>(_onSendMessage);
    on<ChatDisconnected>(_onChatDisconnected);
  }

  void _onChatStarted(
    ChatStarted event,
    Emitter<ChatState> emit,
  ) {
    webSocket.connect();

    emit(
      state.copyWith(
        connected: true,
      ),
    );

    _subscription = webSocket.messages?.listen(
      (data) {
        _handleWebSocketMessage(data);
      },
      onError: (error) {
        addError(error);
      },
    );
  }

  void _onSendMessage(
    SendMessage event,
    Emitter<ChatState> emit,
  ) {
    final message = event.message.trim();

    if (message.isEmpty) {
      return;
    }

    final updatedMessages = [
      ...state.messages,
      ChatMessage(
        text: message,
        isUser: true,
      ),
      ChatMessage(
        text: '',
        isUser: false,
        isStreaming: true,
      ),
    ];

    emit(
      state.copyWith(
        messages: updatedMessages,
        isGenerating: true,
        status: 'Searching documents...',
        sources: [],
      ),
    );

    webSocket.sendQuestion(message);
  }

  void _handleWebSocketMessage(
    Map<String, dynamic> data,
  ) {
    final type = data['type'];

    switch (type) {
      case 'status':
        final status = data['message'] as String? ?? '';

        emit(
          state.copyWith(
            status: status,
            isGenerating: true,
          ),
        );
        break;

      case 'sources':
        final sources = List<Map<String, dynamic>>.from(
          data['sources'] ?? [],
        );

        emit(
          state.copyWith(
            sources: sources,
          ),
        );
        break;

      case 'token':
        final token = data['content'] as String? ?? '';

        if (token.isEmpty || state.messages.isEmpty) {
          return;
        }

        final messages = [...state.messages];

        final lastMessage = messages.last;

        messages[messages.length - 1] = ChatMessage(
          text: lastMessage.text + token,
          isUser: false,
          isStreaming: true,
        );

        emit(
          state.copyWith(
            messages: messages,
          ),
        );

        break;

      case 'complete':
        if (state.messages.isEmpty) {
          return;
        }

        final messages = [...state.messages];

        final lastMessage = messages.last;

        messages[messages.length - 1] = ChatMessage(
          text: lastMessage.text,
          isUser: false,
          isStreaming: false,
        );

        emit(
          state.copyWith(
            messages: messages,
            isGenerating: false,
            status: '',
          ),
        );

        break;

      case 'error':
        emit(
          state.copyWith(
            isGenerating: false,
            error: data['message'] as String?,
          ),
        );

        break;
    }
  }

  Future<void> _onChatDisconnected(
    ChatDisconnected event,
    Emitter<ChatState> emit,
  ) async {
    await _subscription?.cancel();
    await webSocket.disconnect();

    emit(
      state.copyWith(
        connected: false,
      ),
    );
  }

  @override
  Future<void> close() async {
    await _subscription?.cancel();
    await webSocket.disconnect();

    return super.close();
  }
}