"""This file contains tests for functions in stacking.utils"""
import os
import unittest

from stacking.errors import StackingError
from stacking.readers.dr16_reader import defaults as defaults_dr16_reader
from stacking.readers.dr16_reader import accepted_options as accepted_options_dr16_reader
from stacking.readers.dr16_reader import required_options as required_options_dr16_reader
from stacking.rebin import defaults as defaults_rebin
from stacking.rebin import accepted_options as accepted_options_rebin
from stacking.rebin import required_options as required_options_rebin
from stacking.tests.abstract_test import AbstractTest
from stacking.utils import (attribute_from_string, class_from_string,
                            update_accepted_options, update_default_options,
                            update_required_options)

THIS_DIR = os.path.dirname(os.path.abspath(__file__))


class UtilsTest(AbstractTest):
    """Test the functions in stacking.utils

    Methods
    -------
    (see AbstractTest in stacking/tests/abstract_test.py)
    test_attribute_from_string
    test_class_from_string
    test_update_accepted_options
    test_update_default_options
    test_update_required_options
    """

    def test_attribute_from_string(self):
        """Test function attribute_from_string"""
        # case: missing module
        expected_message = "No module named 'invalid_module'"
        with self.assertRaises(ImportError) as context_manager:
            attribute_from_string("invalid_atribute", "invalid_module")
        self.compare_error_message(context_manager, expected_message)

        # case: missing attribute
        expected_message = (
            "module 'stacking.tests.utils' has no attribute 'invalid_atribute'")
        with self.assertRaises(AttributeError) as context_manager:
            attribute_from_string("invalid_atribute", "stacking.tests.utils")
        self.compare_error_message(context_manager, expected_message)

        # case: correct execution
        this_dir = attribute_from_string("THIS_DIR", "stacking.tests.utils")
        self.assertEqual(this_dir, THIS_DIR)

    def test_class_from_string(self):
        """Test function class_from_string"""
        # case: missing module
        expected_message = "No module named 'stacking.invalid_module'"
        with self.assertRaises(ImportError) as context_manager:
            class_from_string("InvalidClass", "invalid_module")
        self.compare_error_message(context_manager, expected_message)

        # case: missing class
        expected_message = (
            "module 'stacking.tests.utils' has no attribute 'Utils'")
        with self.assertRaises(AttributeError) as context_manager:
            class_from_string("Utils", "tests")
        self.compare_error_message(context_manager, expected_message)

        # case: correct execution - load AbstractTest
        class_object, default_args, accepted_options, required_options = class_from_string(
            "AbstractTest", "tests")
        self.assertTrue(isinstance(class_object, type))
        self.assertTrue(default_args == {})
        self.assertTrue(accepted_options == [])
        self.assertTrue(required_options == [])

        # case: correct execution - load Dr16Reader
        class_object, default_args, accepted_options, required_options = class_from_string(
            "Dr16Reader", "readers")
        self.assertTrue(isinstance(class_object, type))
        self.assertTrue(default_args == defaults_dr16_reader)
        self.assertTrue(accepted_options == accepted_options_dr16_reader)
        self.assertTrue(required_options == required_options_dr16_reader)

        # case: correct execution - load Rebin
        class_object, default_args, accepted_options, required_options = class_from_string(
            "Rebin", ".")
        self.assertTrue(isinstance(class_object, type))
        self.assertTrue(default_args == defaults_rebin)
        self.assertTrue(accepted_options == accepted_options_rebin)
        self.assertTrue(required_options == required_options_rebin)

    def test_update_accepted_options(self):
        """Test function update_accepted_options"""

        accepted_options = ["1", "2", "3"]

        cases = [
            # (new_options, expected_result, remove?)
            (["1"], ["2", "3"], True),
            (["3"], ["1", "2"], True),
            (["2"], ["1", "3"], True),
            (["1", "2"], ["3"], True),
            (["2"], ["1", "2", "3"], False),
            (["0"], ["0", "1", "2", "3"], False),
        ]

        for new_options, expected_result, remove in cases:
            new_accepted_options = update_accepted_options(accepted_options,
                                                           new_options,
                                                           remove=remove)
            self.assertTrue(len(new_accepted_options) == len(expected_result))
            self.assertTrue(new_accepted_options == expected_result)

    def test_update_default_options(self):
        """Test function update_default_options"""

        default_options = {"1": 1, "2": 2, "3": 3}

        cases = [
            # (new_options, expected_result, force_overwrite?, expected_message)
            ({
                "1": "0"
            }, {}, False, "Incompatible defaults are being added. Key 1 "
             "found to have values with different type: <class 'int'> and "
             "<class 'str'>. Revise your recent changes or contact stacking "
             "developpers."),
            ({
                "1": 0
            }, {}, False, "Incompatible defaults are being added. Key 1 "
             "found to have two default values: '0' and '1' "
             "Please revise your recent changes. If you really want to "
             "overwrite the default values of a parent class, then pass "
             "`force_overload=True`. If you are unsure what this message "
             "means contact stacking developpers."),
            ({
                "1": 0
            }, {
                "1": 0,
                "2": 2,
                "3": 3
            }, True, None),
            ({
                "0": 0
            }, {
                "0": 0,
                "1": 1,
                "2": 2,
                "3": 3
            }, False, None),
        ]

        for new_options, expected_result, force_overwrite, expected_message in cases:
            if expected_message is None:
                new_default_options = update_default_options(
                    default_options,
                    new_options,
                    force_overwrite=force_overwrite)
                self.assertTrue(
                    len(new_default_options) == len(expected_result))
                for key, value in expected_result.items():
                    self.assertTrue(key in new_default_options)
                    self.assertTrue(new_default_options[key] == value)
            else:
                with self.assertRaises(StackingError) as context_manager:
                    update_default_options(default_options,
                                           new_options,
                                           force_overwrite=force_overwrite)
                self.compare_error_message(context_manager, expected_message)

    def test_update_required_options(self):
        """Test function updaterequired_options"""

        required_options = ["1", "2", "3"]

        cases = [
            # (new_options, expected_result)
            (["2"], ["1", "2", "3"]),
            (["0"], ["0", "1", "2", "3"]),
        ]

        for new_options, expected_result in cases:
            new_accepted_options = update_required_options(
                required_options, new_options)
            self.assertTrue(len(new_accepted_options) == len(expected_result))
            self.assertTrue(new_accepted_options == expected_result)


if __name__ == '__main__':
    unittest.main()
