import 'package:web_ui/web_ui.dart';
import 'dart:html';
import 'dart:json' as json;
import 'dart:async';

class TextGeneratorComponent extends WebComponent {
  int count = 0;

  void increment() {
    count++;
  }
}


