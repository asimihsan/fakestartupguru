Using the [Startup Weekend Operations and Organizers Portal](https://github.com/StartupWeekend/googleio_contest) (SWOOP) dataset I scraped every Startup Weekend (SW) event's webpage for the past year and used [Natural Language Processing](http://en.wikipedia.org/wiki/Natural_language_processing) methods to create [generative models](http://en.wikipedia.org/wiki/Generative_model) based on the language used. I've then used these models to create not-so-random
gibberish.

In order to create this page I've used [Google Dart](http://www.dartlang.org/), which is easy enough to both learn and use within 24 hours and also compiles down to [JavaScript](http://en.wikipedia.org/wiki/JavaScript). Moreover in order to compress the HTML/CSS/JS resources as much as possible I've used the [Zopfli algorithm](http://googledevelopers.blogspot.co.uk/2013/02/compress-data-more-densely-with-zopfli.html) developed by Google Software Engineer Lode Vandevenne,
via the [pigz](http://zlib.net/pigz/) command-line tool.

I'd like to thank Professor Michael Collins and the classmates of the [Natural Language Processing course on Coursera](https://www.coursera.org/course/nlangp) for opening up the world of NLP to me!
