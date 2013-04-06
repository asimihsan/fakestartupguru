import os
import sys
import yaml

# -----------------------------------------------------------------------------
#   Constants.
# -----------------------------------------------------------------------------
SETTINGS_YAML_FILEPATH = os.path.abspath(os.path.join(__file__, os.pardir, "settings.yaml"))
# -----------------------------------------------------------------------------

class Settings(object):
    def __init__(self, settings_yaml_filepath = SETTINGS_YAML_FILEPATH):
        self.settings_yaml_filepath = settings_yaml_filepath
        with open(self.settings_yaml_filepath) as f_in:
            self.yaml_object = yaml.safe_load(f_in)

    @property
    def gatherer_swoop_json_uri(self):
        return self.yaml_object['gatherer']['swoop_json_uri']

    @property
    def gatherer_sqlite_filepath(self):
        relative_path = self.yaml_object['gatherer']['sqlite_filepath']
        return os.path.abspath(os.path.join(__file__, os.pardir, relative_path))

    @property
    def analyzer_tagged_chunked_filepath(self):
        relative_path = self.yaml_object['analyzer']['tagged_chunked_filepath']
        return os.path.abspath(os.path.join(__file__, os.pardir, relative_path))

    @property
    def generator_use_kfold_cross_validation(self):
        return self.yaml_object['generator']['use_kfold_cross_validation']

    @property
    def generator_number_of_k_folds(self):
        return self.yaml_object['generator']['number_of_k_folds']

    @property
    def generator_kfold_testing_proportion(self):
        return self.yaml_object['generator']['kfold_testing_proportion']

    @property
    def generator_non_kfold_cross_validation_proportion(self):
        return self.yaml_object['generator']['non_kfold_cross_validation_proportion']

    @property
    def generator_non_kfold_testing_proportion(self):
        return self.yaml_object['generator']['non_kfold_testing_proportion']

