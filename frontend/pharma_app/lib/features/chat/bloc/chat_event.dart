abstract class ChatEvent {}

class ChatStarted extends ChatEvent {}

class SendMessage extends ChatEvent {
  final String message;

  SendMessage(this.message);
}

class ChatDisconnected extends ChatEvent {}