import 'package:web_ui/web_ui.dart';
import 'dart:html';
import 'dart:json' as json;
import 'dart:async';
import 'dart:math';
import 'package:web_ui/watcher.dart' as watchers;

// ----------------------------------------------------------------------------
//  Some headshot pictures.
// ----------------------------------------------------------------------------
String headshotURLsJSON = """
[
  "http://farm4.staticflickr.com/3369/3505501979_e0ffab0545_m.jpg",
  "http://farm1.staticflickr.com/165/341274142_cfb67ca7c7_m.jpg",
  "http://farm3.staticflickr.com/2794/4444217155_a0502e7569_m.jpg",
  "http://farm3.staticflickr.com/2512/4056615366_c109db7b3c_m.jpg",
  "http://farm5.staticflickr.com/4045/4626436855_65e363ef96_m.jpg",
  "http://farm1.staticflickr.com/36/91551486_66a56b79df_m.jpg",
  "http://farm1.staticflickr.com/41/110636259_1c2f5385ec_m.jpg",
  "http://farm4.staticflickr.com/3581/3457981362_5efb7ab360_m.jpg",
  "http://farm8.staticflickr.com/7140/7150029717_2010eb3d47_m.jpg",
  "http://farm5.staticflickr.com/4033/4389823374_37294ff5fd_m.jpg",
  "http://farm5.staticflickr.com/4045/4303690389_10a9821cd0_m.jpg",
  "http://farm3.staticflickr.com/2802/4389055879_f47a49dea6_m.jpg",
  "http://farm4.staticflickr.com/3535/3232410067_b5de0776b0_m.jpg",
  "http://farm2.staticflickr.com/1017/5178017393_1eee02f214_m.jpg",
  "http://farm8.staticflickr.com/7145/6528187483_ed685427ed_m.jpg",
  "http://farm4.staticflickr.com/3510/3313572644_208df0f42c_m.jpg",
  "http://farm8.staticflickr.com/7013/6626065189_3d7ed69d40_m.jpg",
  "http://farm8.staticflickr.com/7140/7623542982_64d0e62b5b_m.jpg",
  "http://farm3.staticflickr.com/2458/3588101233_f91aa5e3a3_m.jpg",
  "http://farm4.staticflickr.com/3502/3859555660_245269de60_m.jpg",
  "http://farm3.staticflickr.com/2603/3859541562_658d919358_m.jpg",
  "http://farm3.staticflickr.com/2604/3859541980_53450c66f0_m.jpg",
  "http://farm4.staticflickr.com/3430/3858753387_61e67c79f7_m.jpg",
  "http://farm4.staticflickr.com/3252/2940220068_78cd2f00e3_m.jpg",
  "http://farm3.staticflickr.com/2474/3536552962_969534beaf_m.jpg",
  "http://farm4.staticflickr.com/3187/2987735388_da79f4d2d9_m.jpg",
  "http://farm3.staticflickr.com/2634/3859575026_c79314256f_m.jpg"
]
""";
List<String> headshotURLs = json.parse(headshotURLsJSON);
Random random = new Random();
// ----------------------------------------------------------------------------

class TextGeneratorComponent extends WebComponent {

  void inserted() {
    generate_text();
  }
  
  void generate_text() {
    set_headshot_image();
  }
  
  void set_headshot_image() {
    ImageElement headshot_image = query("#headshot_image");
    int headshot_index = random.nextInt(headshotURLs.length);
    String headshot_url = headshotURLs[headshot_index];
    headshot_image.src = headshot_url;
  }
  
}


