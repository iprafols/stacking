"""This file contains configuration tests"""
import os
import unittest
from configparser import ConfigParser

from stacking.config import Config
from stacking.errors import ConfigError
from stacking.tests.abstract_test import AbstractTest

THIS_DIR = os.path.dirname(os.path.abspath(__file__))
os.environ["THIS_DIR"] = THIS_DIR


class ConfigTest(AbstractTest):
    """Test the configuration.

    Methods
    -------
    (see AbstractTest in stacking/tests/abstract_test.py)
    test_config
    """

    def check_error(self, in_file, expected_message, startswith=False):
        """Load a Configuration instance expecting an error
        Check the error message

        Arguments
        ---------
        in_file: str
        Input configuration file to construct the Configuration instance

        expected_message: str
        Expected error message

        startswith: bool - Default: False
        If True, check that expected_message is the beginning of the actual error
        message. Otherwise check that expected_message is the entire message
        """
        with self.assertRaises(ConfigError) as context_manager:
            Config(in_file)

        self.compare_error_message(context_manager,
                                   expected_message,
                                   startswith=startswith)

    def compare_config(self, orig_file, new_file):
        """Compares two configuration files to check that they are equal

        Arguments
        ---------
        orig_file: str
        Control file

        new_file: str
        New file
        """
        orig_config = ConfigParser()
        orig_config.read(orig_file)
        new_config = ConfigParser()
        new_config.read(new_file)

        error_report_string = f"Original file: {orig_file}. New file: {new_file}"

        # check that sections in the original file are present in the new file
        for section in orig_config.sections():
            if not section in new_config.sections():
                print(
                    f"Section [{section}] missing in new file. {error_report_string}"
                )
            self.assertTrue(section in new_config.sections())

            orig_section = orig_config[section]
            new_section = new_config[section]

            # check that options in the original file are present in the new file
            if section == "run specs":
                # The values in run specs might have been updated, check only that
                # they are present
                for key in orig_section.keys():
                    self.assertTrue(key in new_section.keys())
            else:
                for key, orig_value in orig_section.items():
                    if key not in new_section.keys():
                        print(
                            f"key '{key}' in section [{new_section}] missing in "
                            f"new file. {error_report_string}")
                    self.assertTrue(key in new_section.keys())
                    new_value = new_section.get(key)
                    # this is necessary to remove the system dependent bits of
                    # the paths
                    base_path = "stacking/tests/"
                    if base_path in new_value:
                        new_value = new_value.split(base_path)[-1]
                        orig_value = orig_value.split(base_path)[-1]

                    if not orig_value == new_value:
                        print(f"In section [{section}], for key '{key}'' found "
                              f"orig value = {orig_value} but new value = "
                              f"{new_value}. {error_report_string}")
                    self.assertTrue(orig_value == new_value)

            # check that options in the new file are present in the original file
            for key in new_section.keys():
                if key not in orig_section.keys():
                    print(
                        f"key '{key}' in section [{section}] missing in original "
                        f"file. {error_report_string}")
                self.assertTrue(key in orig_section.keys())

        # check that sections in the new file are present in the original file
        for section in new_config.sections():
            if not section in orig_config.sections():
                print(
                    f"Section [{section}] missing in original file. {error_report_string}"
                )

            self.assertTrue(section in orig_config.sections())

    def test_config(self):
        """Basic test for config.

        Load a config file and then print it
        """
        in_file = f"{THIS_DIR}/data/config_tests/config_overwrite.ini"
        out_file = f"{THIS_DIR}/results/config_tests/config.ini"
        test_file = f"{THIS_DIR}/data/config_tests/config_full.ini"

        config = Config(in_file)
        config.write_config()
        self.compare_config(test_file, out_file)

        # this should raise an error as folder exists and overwrite is False
        in_file = f"{THIS_DIR}/data/config_tests/config.ini"
        expected_message = (
            "Specified folder contains a previous run. Pass overwrite "
            "option in configuration file in order to ignore the "
            "previous run or change the output path variable to point "
            f"elsewhere. Folder: {THIS_DIR}/results/config_tests/")
        self.check_error(in_file, expected_message)

        # this should not raise an error as folder exists and overwrite is True
        in_file = f"{THIS_DIR}/data/config_tests/config_overwrite.ini"
        config = Config(in_file)

        # check that out dir has an ending /
        self.assertTrue(config.output_directory.endswith("/"))

    def test_config_no_file(self):
        """Check behaviour of config when the file is not valid"""
        in_file = f"{THIS_DIR}/data/non_existent_config_overwrite.ini"
        expected_message = f"Config file not found: {in_file}"
        self.check_error(in_file, expected_message)

    def test_config_undefined_environment_variable(self):
        """Check the behaviour for undefined environment variables"""
        in_file = f"{THIS_DIR}/data/config_tests/config_undefined_environment.ini"
        expected_message = (
            "In section [general], undefined environment variable UNDEFINED "
            "was found")
        self.check_error(in_file, expected_message)


if __name__ == '__main__':
    unittest.main()