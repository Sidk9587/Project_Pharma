import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';

import 'features/chat/bloc/chat_bloc.dart';
import 'features/chat/data/chat_websocket.dart';
import 'features/chat/presentation/chat_screen.dart';

void main() {
  runApp(const PharmaApp());
}

class PharmaApp extends StatelessWidget {
  const PharmaApp({
    super.key,
  });

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      debugShowCheckedModeBanner: false,
      title: 'Pharma AI',
      home: BlocProvider(
        create: (_) => ChatBloc(
          webSocket: ChatWebSocket(),
        ),
        child: const ChatScreen(),
      ),
    );
  }
}