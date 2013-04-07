#!/usr/bin/env python

import os
import sys
import boto
import glob
import tempfile
import pprint
import contextlib

from settings import Settings

# -----------------------------------------------------------------------------
#   Constants.
# -----------------------------------------------------------------------------
APP_NAME = "deploy_web"
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

    # -------------------------------------------------------------------------
    #   Parse inputs.
    # -------------------------------------------------------------------------
    settings = Settings()
    s3_bucket_name = settings.deploy_s3_bucket_name
    cloudfront_id = settings.deploy_cloudfront_id
    web_output_directory = settings.deploy_web_output_directory

    logger.debug("S3 bucket name: '%s'" % s3_bucket_name)
    logger.debug("Cloudfront ID: '%s'" % cloudfront_id)
    logger.debug("directory: '%s'" % web_output_directory)
    # -------------------------------------------------------------------------

    # -------------------------------------------------------------------------
    #   Determine what files needs uploading.
    # -------------------------------------------------------------------------
    root_dir_elems = web_output_directory.split(os.sep)
    files_to_upload = []

    # root files
    root_files = [elem for elem in glob.glob(os.path.join(web_output_directory, "*.*"))
                  if not os.path.isdir(elem) and
                     "output.json" not in elem]
    files_to_upload.extend(root_files)

    # CSS
    css_files = [elem for elem in glob.glob(os.path.join(web_output_directory, "css", "min", "*.*"))
                 if not os.path.isdir(elem)]
    files_to_upload.extend(css_files)

    # JS
    js_files = [elem for elem in glob.glob(os.path.join(web_output_directory, "js", "*.*"))
                 if not os.path.isdir(elem)]
    files_to_upload.extend(js_files)

    # packages
    # !!AI TODO

    # !!AI REMOVEME
    files_to_upload = [elem for elem in glob.glob(os.path.join(web_output_directory, "dart.html"))]
    destination_subpaths = [os.sep.join(elem.split(os.sep)[len(root_dir_elems):])
                            for elem in files_to_upload]
    # -------------------------------------------------------------------------

    logger.debug("files_to_upload:\n%s" % pprint.pformat(files_to_upload))
    logger.debug("destination_subpaths:\n%s" % pprint.pformat(destination_subpaths))

    # -------------------------------------------------------------------------
    #   Compress then upload each file.
    # -------------------------------------------------------------------------
    with contextlib.closing(boto.connect_s3()) as conn:
        with contextlib.closing(boto.connect_cloudfront()) as conn_cloudfront:
            cloudfront_distribution = [elem for elem in conn_cloudfront.get_all_distributions()
                                       if elem.id == cloudfront_id][0]
            cloudfront_distribution = cloudfront_distribution.get_distribution()
            bucket = conn.get_bucket(s3_bucket_name)

            for (full_filepath, subpath) in zip(files_to_upload, destination_subpaths):
                logger.debug("compressing '%s', then uploading to '%s'" % (full_filepath, subpath))
                compressed_full_filepath = compress_filepath(full_filepath)
                try:
                    logger.debug("starting upload...")
                    key = bucket.delete_key(subpath)
                    key = bucket.new_key(subpath)
                    key.set_metadata("Content-Encoding", "gzip")
                    key.set_contents_from_filename(compressed_full_filepath)
                    key.make_public()
                    logger.debug("finished upload.")
                finally:
                    os.remove(compressed_full_filepath)

            logger.debug("creating cloudfront invalidation request.")
            conn_cloudfront.create_invalidation_request(cloudfront_distribution.id, destination_subpaths)
    # -------------------------------------------------------------------------

    # -------------------------------------------------------------------------
    #   Execute a Cloudfront invalidation of all subpaths.
    # -------------------------------------------------------------------------
    # -------------------------------------------------------------------------

def compress_filepath(filepath):
    logger = logging.getLogger("%s.compress_filepath" % APP_NAME)
    extension = os.path.splitext(filepath)[-1]
    tf = tempfile.NamedTemporaryFile(delete = False, suffix=extension)
    logger.debug("compressing '%s' to '%s'" % (filepath, tf.name))
    os.system("pigz -11 --stdout -- %s > %s" % (filepath, tf.name))
    tf.close()
    return tf.name

if __name__ == "__main__":
    main()
