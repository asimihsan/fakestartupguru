#!/usr/bin/env python

import os
import sys
import json
import glob
import re

from settings import Settings

# -----------------------------------------------------------------------------
#   Constants.
# -----------------------------------------------------------------------------
APP_NAME = "build_json"
# -----------------------------------------------------------------------------

# -----------------------------------------------------------------------------
#   Logging.
# -----------------------------------------------------------------------------
import logging
logger = logging.getLogger(APP_NAME)
logger.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)
logger.addHandler(ch)
# -----------------------------------------------------------------------------

def main():
    logger = logging.getLogger("%s.main" % APP_NAME)
    logger.debug("entry.")

    settings = Settings()
    output = {}
    data_directory = settings.builder_data_directory
    minimum_sentence_length = settings.builder_minimum_sentence_length
    re_reject = re.compile(settings.builder_re_reject)
    for (filename, key) in settings.builder_filename_to_key.items():
        logger.debug("filename: '%s', key: '%s'." % (filename, key))
        filepath = os.path.join(data_directory, filename)
        if not os.path.isfile(filepath):
            logger.error("filepath: '%s' does not exist." % filepath)
            continue
        output[key] = []
        with open(filepath) as f_in:
            input_lines = (line.strip() for line in f_in
                           if len(line) >= minimum_sentence_length and
                              re_reject.search(line) is None)
            output[key].extend(input_lines)

    with open(settings.builder_output_json, "w") as f_out:
        json.dump(output, f_out, indent=2)

    os.system("pigz -11 --force --stdout -- %s > %s.gz" % (settings.builder_output_json, settings.builder_output_json))

if __name__ == "__main__":
    main()

